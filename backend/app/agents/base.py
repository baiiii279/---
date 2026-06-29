from dataclasses import dataclass, field
from typing import Optional

from crewai import Agent

from app.core.config import settings


@dataclass
class SharedContext:
    paper_id: int
    topic: str
    template: str = "course"
    references: list[dict] = field(default_factory=list)       # 已确认文献
    outline: Optional[dict] = None                               # 已确认大纲
    content: Optional[str] = None                                # 已撰写内容
    polished_content: Optional[str] = None                       # 润色后内容
    cite_check_report: Optional[str] = None                      # 引用检查报告
    feedback_history: list[dict] = field(default_factory=list)   # 用户反馈记录


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

    def run(self, context: SharedContext, **kwargs) -> str:
        raise NotImplementedError
