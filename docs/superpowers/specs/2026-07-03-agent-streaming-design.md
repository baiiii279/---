# Agent 流式输出设计文档

**日期**: 2026-07-03 | **状态**: 已批准

## 目标

让前端能看到 AI Agent 逐 token 生成内容的过程（类似 ChatGPT 打字效果），替代当前"蓝色方块等 40 秒"的体验。

## 方案：LiteLLM Streaming Callback（方案 A）

在 LiteLLM 层注册流式回调，每收到 token chunk 时通过 SSE 推送到前端。

## 数据流

```
DeepSeek API ──SSE stream──→ LiteLLM ──chunk callback──→ base.py
  (token by token)                                          │
                                                    sse_manager.emit("agent_stream",
                                                         {agent, token})
                                                            │
                                                            ↓
Frontend ←──EventSource── SSE Manager (asyncio.Queue) ←──┘
  │
  ↓
StreamPanel 组件：逐字渲染 + 自动滚动 + 闪烁光标
```

## 后端改动

### 1. `app/agents/base.py`

- `_create_llm()`: 设置 `stream=True`，通过 `additional_params` 或 LiteLLM callback 机制注入流式回调
- 基类新增 `_paper_id`、`_agent_key`、`_stream_buffer`、`_token_count` 属性
- 回调中每 3 个 token 推送一次 SSE 事件，避免队列爆炸
- Agent 完成时 flush 剩余 buffer

### 2. `app/services/pipeline_runner.py`

- `run_single_agent()` 在调用 `agent.run()` 前注入上下文属性

### 不动

`sse_manager.py`、`orchestrator.py`、CrewAI 源码

## 前端改动

### 1. `hooks/useSSE.ts`

新增 `agent_stream` 事件监听和 `onAgentStream` 回调

### 2. 新建 `components/StreamPanel.tsx`

- 实时流式渲染当前运行 Agent 的输出
- 自动滚动到底部
- 显示 Agent 名称标签 + 运行时长计时器
- 末端模拟闪烁光标
- Agent 完成后保留流式内容 2 秒后消失

### 3. `pages/PaperWorkbench.tsx`

在 AgentPipeline 和内容编辑区之间插入 StreamPanel

## 线程安全

`asyncio.Queue.put_nowait()` 在 Python 3.9+ 是线程安全的，当前回调在 CrewAI 同步线程中直接调用即可。
