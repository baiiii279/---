from dataclasses import dataclass, field
from typing import Optional

from crewai import Agent, Crew, Task

from app.core.config import settings


@dataclass
class SharedContext:
    paper_id: int
    topic: str
    template: str = "course"
    references: list[dict] = field(default_factory=list)
    outline: Optional[dict] = None
    content: Optional[str] = None
    polished_content: Optional[str] = None
    cite_check_report: Optional[str] = None
    feedback_history: list[dict] = field(default_factory=list)


class BaseAgent:
    """所有 Agent 的基类，统一配置 DeepSeek LLM"""

    def __init__(self, role: str, goal: str, backstory: str):
        self.agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            llm=self._create_llm(),
            verbose=True,
            allow_delegation=False,
        )

    def _create_llm(self):
        from crewai import LLM
        return LLM(
            model="openai/deepseek-chat",
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )

    def _execute_task(self, task: Task) -> str:
        crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        return str(result.raw if hasattr(result, 'raw') else result)

    def run(self, context: SharedContext, **kwargs) -> str:
        raise NotImplementedError
