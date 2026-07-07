from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.paper import Paper
from app.models.task import Task as TaskModel
from app.models.user import User
from app.models.reference import UserReference, PaperReference
from app.schemas.task import FeedbackRequest, TaskResponse
from app.api.auth import get_current_user
from app.core.security import decode_access_token
from app.agents.orchestrator import Orchestrator, SharedContext
from app.agents.format_agent import FormatAgent
from app.models.format_template import FormatTemplate
from app.services.pipeline_runner import run_single_agent
from app.services.sse_manager import sse_manager
from sse_starlette.sse import EventSourceResponse
import json
import re
import asyncio

router = APIRouter(prefix="/api/papers/{paper_id}/agent", tags=["agent"])
orchestrator = Orchestrator()


def _get_paper(paper_id: int, user: User, db: Session) -> Paper:
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    return paper


def _parse_outline(text: str):
    """解析大纲JSON，处理可能的markdown代码块包裹"""
    text = text.strip()
    # 去掉 markdown 代码块标记
    text = re.sub(r'^```(?:json)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _build_context(paper: Paper, db: Session, template_id: int = None) -> SharedContext:
    ref_links = db.query(PaperReference).filter(PaperReference.paper_id == paper.id).all()
    refs = []
    for link in ref_links:
        ref = db.query(UserReference).get(link.reference_id)
        if ref:
            refs.append({"title": ref.title, "abstract": ref.abstract, "authors": ref.authors})
    # 获取格式规则
    format_rules = ""
    if template_id:
        tmpl = db.query(FormatTemplate).get(template_id)
        if tmpl:
            format_rules = tmpl.rules
    if not format_rules:
        tmpl = db.query(FormatTemplate).filter(FormatTemplate.is_default == True).first()
        if tmpl:
            format_rules = tmpl.rules
    return SharedContext(
        paper_id=paper.id,
        topic=paper.topic,
        template=paper.template,
        references=refs,
        outline=_parse_outline(paper.outline) if paper.outline else None,
        content=paper.content,
        format_rules=format_rules,
    )


@router.post("/start")
def run_all(paper_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """一键全流程：依次执行所有 Agent"""
    results = {}
    for agent_key in ["parse", "outline", "write", "polish", "cite_check", "format"]:
        paper = _get_paper(paper_id, current_user, db)
        context = _build_context(paper, db)
        task = orchestrator.create_task(db, paper.id, agent_key)

        if agent_key == "parse" and not context.references:
            return {"error": "请先添加文献", "status": "failed"}

        _inject_user_api_key(agent_key, current_user)
        result = orchestrator.run_agent(db, task, context)
        results[agent_key] = result

        if agent_key == "outline":
            paper.outline = result
        elif agent_key in ("write", "polish", "format"):
            paper.content = result

    paper.status = "complete"
    db.commit()
    return {"results": results, "status": "complete"}


@router.post("/format")
def run_format(
    paper_id: int,
    template_id: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """同步执行 FormatAgent，应用格式模板排版"""
    from app.agents.base import register_stream_callback, unregister_stream_callback

    paper = _get_paper(paper_id, current_user, db)
    paper.status = "formatting"
    db.commit()

    context = _build_context(paper, db, template_id)
    agent = FormatAgent()

    _inject_user_api_key("format", current_user)

    # 注册流式回调
    def _sse_stream(token: str, _ag: str):
        sse_manager.emit(paper_id, "agent_stream", {"agent": "format", "token": token})

    register_stream_callback(paper_id, _sse_stream)

    try:
        result = agent.run(context, format_rules=context.format_rules)

        sse_manager.emit(paper_id, "agent_stream_end", {"agent": "format"})

        paper.content = result
        paper.status = "complete"
        db.commit()

        sse_manager.emit(paper_id, "agent_complete", {
            "agent": "format", "output": result, "status": "success", "critical": True,
        })
        return {"result": result, "status": "success"}
    except Exception as e:
        sse_manager.emit(paper_id, "agent_error", {
            "agent": "format", "error": str(e), "critical": True,
        })
        return {"error": str(e), "status": "failed"}
    finally:
        unregister_stream_callback(paper_id)


@router.post("/format/run", status_code=202)
async def run_format_async(
    paper_id: int,
    template_id: int = Query(None),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """异步执行 FormatAgent"""
    paper = _get_paper(paper_id, current_user, db)
    paper.status = "formatting"
    db.commit()
    background_tasks.add_task(run_single_agent, paper_id, "format")
    return {"run_id": paper_id, "template_id": template_id, "status": "accepted"}


def _next_status(agent_key: str) -> str:
    mapping = {
        "parse": "parsing", "outline": "outlining", "write": "writing",
        "polish": "polishing", "cite_check": "checking", "format": "complete"
    }
    return mapping.get(agent_key, "draft")


def _inject_user_api_key(agent_key: str, user: User):
    """将用户的 API Key 注入到 Agent 实例"""
    agent = orchestrator.agents.get(agent_key)
    if agent and user.api_key:
        agent.set_user_llm_config(user.api_key, user.api_base)


@router.post("/{agent_type}")
def run_agent(paper_id: int, agent_type: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    valid_types = ["parse", "outline", "write", "polish", "cite-check", "format"]
    agent_key = agent_type.replace("-", "_")  # cite-check → cite_check
    if agent_key not in orchestrator.agents:
        raise HTTPException(status_code=400, detail=f"无效的 Agent 类型: {agent_type}")

    paper = _get_paper(paper_id, current_user, db)
    context = _build_context(paper, db)
    task = orchestrator.create_task(db, paper.id, agent_key)

    try:
        # 发送 agent_start SSE 事件
        from datetime import datetime, timezone
        sse_manager.emit(paper_id, "agent_start", {
            "agent": agent_key,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "critical": True,
        })

        _inject_user_api_key(agent_key, current_user)

        # 注册流式 token 回调
        from app.agents.base import register_stream_callback, unregister_stream_callback
        def _sse_stream(token: str, _ag: str):
            sse_manager.emit(paper_id, "agent_stream", {"agent": agent_key, "token": token})

        register_stream_callback(paper_id, _sse_stream)

        result = orchestrator.run_agent(db, task, context)

        # 流式结束
        sse_manager.emit(paper_id, "agent_stream_end", {"agent": agent_key})

        # 保存 Agent 输出到 paper
        if agent_key == "outline":
            paper.outline = result
        elif agent_key in ("write", "polish", "format"):
            paper.content = result

        paper.status = _next_status(agent_key)
        db.commit()

        sse_manager.emit(paper_id, "agent_complete", {
            "agent": agent_key,
            "output": result,
            "status": "success",
            "critical": True,
        })
        return {"task_id": task.id, "output": result, "status": "success"}
    except Exception as e:
        sse_manager.emit(paper_id, "agent_error", {
            "agent": agent_key,
            "error": str(e),
            "critical": True,
        })
        return {"task_id": task.id, "error": str(e), "status": "failed"}
    finally:
        from app.agents.base import unregister_stream_callback
        unregister_stream_callback(paper_id)


@router.post("/{agent_type}/run", status_code=202)
async def run_agent_async(
    paper_id: int,
    agent_type: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent_key = agent_type.replace("-", "_")
    if agent_key not in orchestrator.agents:
        raise HTTPException(status_code=400, detail=f"无效的 Agent 类型: {agent_type}")
    _get_paper(paper_id, current_user, db)
    background_tasks.add_task(run_single_agent, paper_id, agent_key)
    return {"run_id": paper_id, "status": "accepted"}


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(paper_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_paper(paper_id, current_user, db)
    return db.query(TaskModel).filter(TaskModel.paper_id == paper_id).order_by(TaskModel.id).all()


@router.post("/feedback")
def submit_feedback(paper_id: int, req: FeedbackRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_paper(paper_id, current_user, db)
    task = db.query(TaskModel).filter(TaskModel.id == req.task_id, TaskModel.paper_id == paper_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    result = orchestrator.handle_feedback(db, task, req.action, req.comment, req.edited_content)

    if req.action == "edit" and req.edited_content:
        paper = _get_paper(paper_id, current_user, db)
        if task.agent_type in ("write", "polish", "format"):
            paper.content = req.edited_content
        elif task.agent_type == "outline":
            paper.outline = req.edited_content
        db.commit()

    return result


async def _get_user_from_token(token: str = Query(None), db: Session = Depends(get_db)) -> User:
    """Extract user from query token (for SSE which can't set Auth header)."""
    if token:
        payload = decode_access_token(token)
        if payload:
            user_id_str = payload.get("sub")
            if user_id_str:
                user = db.query(User).get(int(user_id_str))
                if user:
                    return user
    raise HTTPException(status_code=401, detail="未认证")


@router.get("/events")
async def agent_events(
    paper_id: int,
    current_user: User = Depends(_get_user_from_token),
):
    queue = sse_manager.subscribe(paper_id)

    async def event_generator():
        try:
            while True:
                msg = await queue.get()
                yield {"event": msg["event"], "data": json.dumps(msg["data"])}
                if msg["event"] == "pipeline_complete":
                    break
        except asyncio.CancelledError:
            pass
        finally:
            sse_manager.unsubscribe(paper_id, queue)

    return EventSourceResponse(event_generator())
