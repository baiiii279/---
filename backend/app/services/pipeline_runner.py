import json
import re
import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.paper import Paper
from app.models.reference import UserReference, PaperReference
from app.models.user import User
from app.models.format_template import FormatTemplate
from app.agents.orchestrator import Orchestrator, SharedContext
from app.agents.base import register_stream_callback, unregister_stream_callback
from app.services.sse_manager import sse_manager

orchestrator = Orchestrator()

_NEXT_STATUS = {
    "parse": "parsing", "outline": "outlining", "write": "writing",
    "polish": "polishing", "cite_check": "checking",
    "format": "complete",
}


def _parse_outline(text: str):
    """Parse outline JSON, stripping possible markdown code block fences."""
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


async def run_single_agent(paper_id: int, agent_key: str, template_id: int = None):
    db: Session = next(get_db())
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            sse_manager.emit(paper_id, "agent_error", {"agent": agent_key, "error": "论文不存在"})
            return

        sse_manager.emit(paper_id, "agent_start", {
            "agent": agent_key,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "critical": True,
        })

        # Build context (inlined to avoid circular import from app.api.agent)
        ref_links = db.query(PaperReference).filter(PaperReference.paper_id == paper.id).all()
        refs = []
        for link in ref_links:
            ref = db.query(UserReference).get(link.reference_id)
            if ref:
                refs.append({"title": ref.title, "abstract": ref.abstract, "authors": ref.authors})
        format_rules = ""
        if template_id:
            tmpl = db.query(FormatTemplate).get(template_id)
            if tmpl:
                format_rules = tmpl.rules
        if not format_rules:
            tmpl = db.query(FormatTemplate).filter(FormatTemplate.is_default == True).first()
            if tmpl:
                format_rules = tmpl.rules
        context = SharedContext(
            paper_id=paper.id,
            topic=paper.topic,
            template=paper.template,
            references=refs,
            outline=_parse_outline(paper.outline) if paper.outline else None,
            content=paper.content,
            format_rules=format_rules,
        )

        task = orchestrator.create_task(db, paper.id, agent_key)

        # 注入 paper_id + agent_key + 用户 API Key 到 Agent 实例
        agent = orchestrator.agents.get(agent_key)
        if agent:
            agent._paper_id = paper_id
            agent._agent_key = agent_key
            # 用户自定义 API Key 优先
            user = db.query(User).get(paper.user_id)
            if user and user.api_key:
                agent.set_user_llm_config(user.api_key, user.api_base)

        # 注册流式回调：每收到 token 就通过 SSE 推送给前端
        def stream_callback(token: str, ag_key: str):
            sse_manager.emit(paper_id, "agent_stream", {
                "agent": ag_key,
                "token": token,
            })

        register_stream_callback(paper_id, stream_callback)

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, orchestrator.run_agent, db, task, context)

        # 发送流式结束标记
        sse_manager.emit(paper_id, "agent_stream_end", {"agent": agent_key})

        if agent_key == "outline":
            paper.outline = result
        elif agent_key in ("write", "polish", "format"):
            paper.content = result
        paper.status = _NEXT_STATUS.get(agent_key, "draft")
        db.commit()

        sse_manager.emit(paper_id, "agent_complete", {
            "agent": agent_key,
            "output": result,
            "status": "success",
            "critical": True,
        })
    except Exception as e:
        sse_manager.emit(paper_id, "agent_error", {
            "agent": agent_key,
            "error": str(e),
            "critical": True,
        })
    finally:
        unregister_stream_callback(paper_id)
        db.close()
