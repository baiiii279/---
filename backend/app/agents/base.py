import os
import sys
import threading

_print_err = lambda *a: print(*a, file=sys.stderr)

# ⚠️ 彻底禁用 httpx 的代理读取：
import httpx._client as _hc
_hc_orig_init = _hc.Client.__init__
def _hc_no_proxy_init(self, *args, **kwargs):
    kwargs["trust_env"] = False
    _hc_orig_init(self, *args, **kwargs)
_hc.Client.__init__ = _hc_no_proxy_init

import urllib.request
urllib.request.getproxies = lambda: {}

# ═══════════════════════════════════════════════════════════════
# 流式输出拦截：monkey-patch litellm.completion，在 stream=True 时
# 捕获每个 token chunk 并通过 SSE 推送到前端
# ═══════════════════════════════════════════════════════════════
import litellm
_original_litellm_completion = litellm.completion

# 全局流式回调注册表：{paper_id: callback(token, agent_key)}
_stream_registry: dict[int, callable] = {}
_stream_registry_lock = threading.Lock()

def register_stream_callback(paper_id: int, callback: callable):
    """注册某个 paper 的流式 token 回调"""
    with _stream_registry_lock:
        _stream_registry[paper_id] = callback

def unregister_stream_callback(paper_id: int):
    """取消注册"""
    with _stream_registry_lock:
        _stream_registry.pop(paper_id, None)

def _patched_litellm_completion(*args, **kwargs):
    """拦截 litellm.completion，在 stream=True 时捕获 token chunks"""
    response = _original_litellm_completion(*args, **kwargs)

    if not kwargs.get('stream'):
        return response

    _print_err(f"[litellm-patch] stream=True detected, registry_keys={list(_stream_registry.keys())}")
    # 因此直接广播到所有已注册的 paper（通常只有 1 个）。
    def intercepted_generator():
        buffer = []
        for chunk in response:
            try:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        token = delta.content
                        buffer.append(token)

                        if len(buffer) >= 3 or '\n' in token:
                            text = ''.join(buffer)
                            buffer.clear()
                            # 广播到所有已注册的 paper
                            for callback in list(_stream_registry.values()):
                                try:
                                    callback(text, '')
                                except Exception:
                                    pass
            except Exception:
                pass
            yield chunk

        # flush 剩余 buffer
        if buffer:
            text = ''.join(buffer)
            for callback in list(_stream_registry.values()):
                try:
                    callback(text, '')
                except Exception:
                    pass

    return intercepted_generator()

litellm.completion = _patched_litellm_completion

# 线程局部存储：传递 paper_id/agent_key 到 litellm completion 调用中
_stream_ctx = threading.local()
_stream_ctx.current = None

_print_err("[base.py] litellm.completion streaming interceptor active")


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
    format_rules: str = ""
    target_words: Optional[int] = None


class BaseAgent:
    """所有 Agent 的基类，统一配置 DeepSeek LLM（流式输出）"""

    def __init__(self, role: str, goal: str, backstory: str):
        # 运行时注入（由 pipeline_runner 设置）
        self._paper_id: int = 0
        self._agent_key: str = ""
        # 用户自定义 API Key（优先于系统默认）
        self._user_api_key: str | None = None
        self._user_api_base: str | None = None
        # 保存 Agent 构造参数，延迟创建 LLM
        self._role = role
        self._goal = goal
        self._backstory = backstory
        self._llm = None

    def set_user_llm_config(self, api_key: str | None, api_base: str | None = None):
        """设置用户自定义的 LLM 配置（在 run 之前调用）"""
        self._user_api_key = api_key
        self._user_api_base = api_base
        self._llm = None  # 重置，下次 _create_llm 会用新 key

    def _create_llm(self):
        from crewai import LLM
        ak = self._user_api_key or settings.DEEPSEEK_API_KEY
        url = self._user_api_base or settings.DEEPSEEK_BASE_URL
        return LLM(
            model="openai/deepseek-chat",
            api_key=ak,
            base_url=url,
            stream=True,
            is_litellm=True,
        )

    def _get_or_create_agent(self):
        """延迟创建 CrewAI Agent（在首次 run 时，此时 API Key 已确定）"""
        if self._llm is None:
            self._llm = self._create_llm()
            self.agent = Agent(
                role=self._role,
                goal=self._goal,
                backstory=self._backstory,
                llm=self._llm,
                verbose=False,
                allow_delegation=False,
            )
        return self.agent

    def _execute_task(self, task: Task) -> str:
        agent = self._get_or_create_agent()
        _stream_ctx.current = {
            'paper_id': self._paper_id,
            'agent_key': self._agent_key,
        }
        try:
            crew = Crew(agents=[agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            return str(result.raw if hasattr(result, 'raw') else result)
        finally:
            _stream_ctx.current = None

    def run(self, context: SharedContext, **kwargs) -> str:
        raise NotImplementedError
