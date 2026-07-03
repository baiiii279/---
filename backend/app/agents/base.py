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


class BaseAgent:
    """所有 Agent 的基类，统一配置 DeepSeek LLM（流式输出）"""

    def __init__(self, role: str, goal: str, backstory: str):
        self.agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            llm=self._create_llm(),
            verbose=False,          # 关闭 verbose，避免干扰流式输出
            allow_delegation=False,
        )
        # 运行时注入（由 pipeline_runner 设置）
        self._paper_id: int = 0
        self._agent_key: str = ""

    def _create_llm(self):
        from crewai import LLM
        return LLM(
            model="openai/deepseek-chat",
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            stream=True,            # ← 启用流式输出
            is_litellm=True,        # ← 强制走 litellm 路径（新版 CrewAI 默认路由到 native provider）
        )

    def _execute_task(self, task: Task) -> str:
        # 设置线程上下文（供 litellm completion 拦截器使用）
        _stream_ctx.current = {
            'paper_id': self._paper_id,
            'agent_key': self._agent_key,
        }
        try:
            crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            return str(result.raw if hasattr(result, 'raw') else result)
        finally:
            _stream_ctx.current = None

    def run(self, context: SharedContext, **kwargs) -> str:
        raise NotImplementedError
