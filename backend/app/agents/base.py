import os
import sys

_print_err = lambda *a: print(*a, file=sys.stderr)

# ⚠️ 彻底禁用 httpx 的代理读取：
# Windows 上 Clash/TUN 通过注册表设置系统代理 (socks5://127.0.0.1:7897)，
# httpx 在 trust_env=True（默认）时会读取这些代理，而 socksio 未安装会报错。
# 解决方案：打开 httpx 源码直接注射 trust_env=False 到 Client 构造器中。
import httpx._client as _hc
_hc_orig_init = _hc.Client.__init__
def _hc_no_proxy_init(self, *args, **kwargs):
    kwargs["trust_env"] = False
    _hc_orig_init(self, *args, **kwargs)
_hc.Client.__init__ = _hc_no_proxy_init
_print_err(f"[base.py] Patched httpx.Client.__init__ → trust_env=False")

# 同时处理 urllib.getproxies 以防万一
import urllib.request
urllib.request.getproxies = lambda: {}

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
