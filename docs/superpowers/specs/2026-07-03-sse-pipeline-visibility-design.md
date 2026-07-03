# 多智能体流水线实时可视化方案设计

## 概述

为 PaperCraft 的多智能体协作系统增加实时可见性，让用户在 Web UI 中直观地看到 5 个 Agent（parse → outline → write → polish → cite_check）的执行过程、中间输出和状态流转。

## 现状与问题

- Agent 通过同步 POST 调用，用户等待期间看不到执行进度
- SSE 端点仅发送心跳，未携带真实 Agent 事件
- AgentPipeline 组件是纯静态进度条，不反映实际执行状态
- 用户无法确认 Agent 是否真正在调用 DeepSeek API 并产出内容

## 架构

```
┌──────────────────────────────────────────────────────────┐
│                    前端 (React)                           │
│                                                          │
│  ┌──────────┐    SSE (EventSource)    ┌────────────────┐│
│  │ useSSE   │◄══════════════════════  │ AgentPipeline  ││
│  │ (增强)   │    agent_start          │  □ parse ✅    ││
│  │          │    agent_complete       │  □ outline ⏳  ││
│  │          │    agent_error          │  □ write ☐    ││
│  │          │    pipeline_complete    │  ...           ││
│  └──────────┘                         └───────┬────────┘│
│                                                │         │
│                                         ┌──────▼──────┐ │
│                                         │ FeedbackPanel│ │
│                                         └─────────────┘ │
└──────────────┬───────────────────────────────────────────┘
               │ POST /api/papers/{id}/agent/{type}/run
               │ → 202 {run_id: paper_id}
               │
┌──────────────▼───────────────────────────────────────────┐
│                   后端 (FastAPI)                          │
│                                                          │
│  ┌──────────────────────┐                                │
│  │ SSEEventManager      │ ◄── emit(paper_id, event,     │
│  │ (全局单例, asyncio   │         data)                  │
│  │  Queue 分发器)       │                                │
│  └──────┬───────────────┘                                │
│         │ emit()                                         │
│  ┌──────▼──────────────────────────────────────────┐     │
│  │ BackgroundTasks / asyncio                        │     │
│  │                                                  │     │
│  │ run_single_agent(paper_id, agent_key):           │     │
│  │   1. emit(agent_start, {agent, timestamp})       │     │
│  │   2. result = run_in_executor(orchestrator.run)  │     │
│  │   3. update paper.status + content               │     │
│  │   4. emit(agent_complete, {agent, output})       │     │
│  │                                                  │     │
│  │ run_full_pipeline(paper_id):                     │     │
│  │   遍历 5 个 Agent, 每个按上述流程                  │     │
│  └──────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────┘
```

### 设计原则

- 保留现有单 Agent 逐步执行按钮，新增异步支持
- SSE 是点到点的推送通道，按 paper_id 隔离
- 失败时立即停止并推送 error 事件
- 队列有界（100），非 critical 事件在满时丢弃

## SSEEventManager 设计

```python
class SSEEventManager:
    _subscribers: dict[int, list[asyncio.Queue]]  # paper_id → 订阅者队列
    _max_queue_size: int = 100
```

| 方法 | 作用 |
|------|------|
| `subscribe(paper_id) → Queue` | 为 paper 创建一个事件队列 |
| `unsubscribe(paper_id, queue)` | 断开时清理 |
| `emit(paper_id, event, data)` | 广播事件给所有订阅者 |

### 事件类型

| event | data | critical | 说明 |
|-------|------|----------|------|
| `agent_start` | `{agent, paper_id, timestamp}` | 是 | Agent 开始执行 |
| `agent_complete` | `{agent, output, paper_id, status}` | 是 | Agent 执行成功 |
| `agent_error` | `{agent, error, paper_id}` | 是 | Agent 执行失败 |
| `pipeline_complete` | `{paper_id, final_status}` | 是 | 全流程结束 |
| `heartbeat` | `{timestamp}` | 否 | 连接保活 |

### 队列满处理

- critical 事件：尝试 put_nowait，失败则丢弃（极罕见）
- 非 critical 事件（heartbeat）：直接丢弃
- 清理已断开的订阅者队列

### 全局单例

```python
sse_manager = SSEEventManager()
```

## 后端 API 改造

### 新增异步端点

```http
POST /api/papers/{paper_id}/agent/{agent_type}/run
Authorization: Bearer <token>

→ 202 { "run_id": paper_id, "status": "accepted" }
```

流程：
1. 验证 paper 存在 + 属于当前用户
2. 创建 Task 记录 (status="pending")
3. 通过 `BackgroundTasks` 启动后台任务
4. 立即返回 202

### 改造 SSE 端点

```http
GET /api/papers/{paper_id}/agent/events
Authorization: Bearer <token>

→ SSE stream (EventSourceResponse)
```

- 调用 `sse_manager.subscribe(paper_id)` 获取队列
- 循环从队列取事件并 yield
- 收到 `pipeline_complete` 或连接断开时退出
- finally 块中调用 `unsubscribe` 清理

### 后台任务

```python
async def run_single_agent(paper_id: int, agent_key: str):
    db = next(get_db())
    paper = db.query(Paper).filter(Paper.id == paper_id).first()

    sse_manager.emit(paper_id, "agent_start", {"agent": agent_key})

    try:
        context = _build_context(paper, db)
        task = orchestrator.create_task(db, paper.id, agent_key)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, orchestrator.run_agent, db, task, context)

        if agent_key == "outline":
            paper.outline = result
        elif agent_key in ("write", "polish"):
            paper.content = result
        paper.status = _next_status(agent_key)
        db.commit()

        sse_manager.emit(paper_id, "agent_complete", {
            "agent": agent_key, "output": result, "status": "success"
        })
    except Exception as e:
        sse_manager.emit(paper_id, "agent_error", {"agent": agent_key, "error": str(e)})
    finally:
        db.close()
```

## 前端改造

### AgentPipeline.tsx — 动态流水线面板

```typescript
interface AgentNode {
  key: string;
  label: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  output: string | null;
  error: string | null;
  finishedAt: string | null;
}

interface AgentPipelineProps {
  agents: AgentNode[];
  onApprove: () => void;
  onReject: (comment: string) => void;
  onEdit: (content: string) => void;
  running: boolean;
}
```

渲染逻辑：
- 每个 Agent 格显示状态图标（☐ pending / ⏳ running / ✅ success / ❌ failed）
- running 的 Agent 格子有脉冲动画
- 当前最新完成的 Agent 自动展开输出区（Markdown 预览）
- 输出区底部嵌入 FeedbackPanel

### useSSE.ts — 事件分发

```typescript
interface SSEOptions {
  onAgentStart?: (agent: string) => void;
  onAgentComplete?: (agent: string, output: string) => void;
  onAgentError?: (agent: string, error: string) => void;
  onPipelineComplete?: () => void;
}

function useSSE(url: string, options: SSEOptions): { status: string }
```

- 解析 SSE 消息的 `event` 和 `data` 字段
- 按事件类型调用对应回调
- 连接断开自动重连

### PaperWorkbench.tsx — 事件驱动

- 新增 `agentStates` 状态数组
- `handleRunAgent` 改为 POST 异步端点
- SSE 事件驱动 AgentPipeline 更新
- Agent 成功 → 面板显示输出 + FeedbackPanel
- 用户批准 → status 推进，下一按钮可用

## 文件改动清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `backend/app/services/sse_manager.py` | **新增** | SSEEventManager 全局单例 |
| `backend/app/services/__init__.py` | **新增** | 包初始化 |
| `backend/app/api/agent.py` | 修改 | 新增异步端点 + 改造 SSE 端点 |
| `frontend/src/hooks/useSSE.ts` | 修改 | 增加事件解析和回调分发 |
| `frontend/src/components/AgentPipeline.tsx` | 重写 | 改为动态面板 |
| `frontend/src/pages/PaperWorkbench.tsx` | 修改 | 事件驱动改造 |

未改：`orchestrator.py`（保持同步，由 run_in_executor 包装）

## 错误处理

- Agent 执行异常 → 推送 `agent_error` → 前端显示错误内容 → 用户可重试
- SSE 连接中断 → EventSource 自动重连
- 后台任务未处理异常 → 全局 except 捕获并 push error 事件
- 数据库会话 → 后台任务 finally 块中关闭

## 不在此次范围内

- 全流程一键执行
- Agent 执行日志文件持久化
- WebSocket 替代 SSE
