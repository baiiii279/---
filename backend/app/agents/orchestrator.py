from app.agents.base import SharedContext
from app.agents.parse_agent import ParseAgent
from app.agents.outline_agent import OutlineAgent
from app.agents.write_agent import WriteAgent
from app.agents.polish_agent import PolishAgent
from app.agents.cite_check_agent import CiteCheckAgent
from app.agents.format_agent import FormatAgent
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.agent_log import AgentLog
from datetime import datetime, timezone


class Orchestrator:
    def __init__(self):
        self.agents = {
            "parse": ParseAgent(),
            "outline": OutlineAgent(),
            "write": WriteAgent(),
            "polish": PolishAgent(),
            "cite_check": CiteCheckAgent(),
            "format": FormatAgent(),
        }

    def create_task(self, db: Session, paper_id: int, agent_type: str) -> Task:
        task = Task(paper_id=paper_id, agent_type=agent_type, status="pending")
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def add_log(self, db: Session, task_id: int, step: str, message: str, level: str = "info"):
        log = AgentLog(task_id=task_id, step=step, message=message, level=level)
        db.add(log)
        db.commit()

    def run_agent(self, db: Session, task: Task, context: SharedContext) -> str:
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        db.commit()
        self.add_log(db, task.id, "start", f"Agent {task.agent_type} 开始执行")

        try:
            agent = self.agents[task.agent_type]
            task.input_data = str(context)
            result = agent.run(context)
            task.output_data = result
            task.status = "success"
            task.finished_at = datetime.now(timezone.utc)
            db.commit()
            self.add_log(db, task.id, "complete", f"Agent {task.agent_type} 执行完成")
            return result
        except Exception as e:
            task.status = "failed"
            task.finished_at = datetime.now(timezone.utc)
            db.commit()
            self.add_log(db, task.id, "error", str(e), "error")
            raise

    def handle_feedback(self, db: Session, task: Task, action: str, comment: str = None, edited_content: str = None):
        task.user_feedback = action
        task.feedback_comment = comment
        db.commit()
        self.add_log(db, task.id, "feedback", f"用户反馈: {action} - {comment or '无'}")

        if action == "approve":
            return {"next_step": "proceed"}
        elif action == "reject":
            return {"next_step": "retry", "comment": comment}
        elif action == "edit":
            return {"next_step": "proceed_with_edit", "edited_content": edited_content}
