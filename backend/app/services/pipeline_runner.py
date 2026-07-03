import json
import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.paper import Paper
from app.models.reference import UserReference, PaperReference
from app.agents.orchestrator import Orchestrator, SharedContext
from app.services.sse_manager import sse_manager

orchestrator = Orchestrator()

_NEXT_STATUS = {
    "parse": "parsing", "outline": "outlining", "write": "writing",
    "polish": "polishing", "cite_check": "checking",
}


async def run_single_agent(paper_id: int, agent_key: str):
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
        context = SharedContext(
            paper_id=paper.id,
            topic=paper.topic,
            template=paper.template,
            references=refs,
            outline=json.loads(paper.outline) if paper.outline else None,
            content=paper.content,
        )

        task = orchestrator.create_task(db, paper.id, agent_key)

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, orchestrator.run_agent, db, task, context)

        if agent_key == "outline":
            paper.outline = result
        elif agent_key in ("write", "polish"):
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
        db.close()
