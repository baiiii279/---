# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PaperCraft — 多智能体论文写作助手。基于 CrewAI 编排 5 个 AI 智能体（文献解析→大纲生成→内容撰写→润色→引用检查），Human-in-the-loop 审阅，前后端分离。支持上传 PDF/Word/TXT 文献、逐 token 流式输出、Word 文档导出。

## Commands

```bash
# 后端
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8004   # 开发服务器（端口避开 8000-8003 的僵尸进程）
# API 文档: http://localhost:8004/docs

# 前端
cd frontend && npm install
npm run dev            # 开发服务器（自动分配端口，/api 代理到 :8004）
npm run build          # 生产构建 (tsc -b && vite build)
npm run lint           # oxlint 代码检查
```

前后端需同时运行。Vite 代理见 `frontend/vite.config.ts`。

## Architecture

```
React SPA (localhost:517x) ⇅ REST + SSE ⇅ FastAPI (localhost:8004) ⇅ MySQL (localhost:3306/papercraft)
                                          ⇅ CrewAI + DeepSeek API (via litellm)
```

### Backend (FastAPI)

```
app/
├── core/          # 配置 (pydantic-settings)、数据库引擎、JWT/密码
├── models/        # 6 张 ORM 表: users, papers, user_references, paper_references, tasks, agent_logs
├── schemas/       # Pydantic 请求/响应模型
├── api/           # 7 个路由模块
│   ├── auth.py    # /api/auth/* — 注册/登录/当前用户
│   ├── user.py    # /api/user/* — 资料/密码
│   ├── references.py # /api/user/references/* — 文献 CRUD + 文件上传（存 full_text + abstract）
│   ├── papers.py  # /api/papers/* — 论文 CRUD + /export/docx（Markdown→Word）
│   ├── agent.py   # /api/papers/{id}/agent/* — 同步/异步执行、全流程、SSE、反馈
│   ├── admin.py   # /api/admin/* — 管理后台
├── agents/        # CrewAI Agent 层
│   ├── base.py    # BaseAgent 基类 + litellm.completion 拦截器（流式输出）+ httpx 代理 patch
│   ├── orchestrator.py # 编排器 (create_task/run_agent/handle_feedback)
│   └── parse_agent.py / outline_agent.py / write_agent.py / polish_agent.py / cite_check_agent.py
├── services/
│   ├── pipeline_runner.py # 异步 Agent 编排（线程池执行 CrewAI，注册 SSE 流式回调）
│   └── sse_manager.py     # SSEEventManager — asyncio.Queue 事件分发，call_soon_threadsafe 跨线程唤醒
```

**关键 API 模式:**
- **鉴权**: `get_current_user` 依赖注入，JWT Bearer
- `/api/papers/{id}/agent/{agent_type}` — 同步执行（带 SSE 流式输出）
- `/api/papers/{id}/agent/{agent_type}/run` — 异步执行（202 + BackgroundTasks + SSE）
- `/api/papers/{id}/agent/start` — 一键全流程（同步）
- `/api/papers/{id}/export/docx` — 导出 Word（Markdown→python-docx，宋体小四/首行缩进/表格/标题层级）
- `/api/user/references/upload` — 文件上传，自动解析全文存储到 `full_text` 字段
- `/api/user/references/{ref_id}` — 获取单篇文献详情（含 full_text）

### Agent 流式输出架构

```
DeepSeek API ──SSE stream──→ litellm.completion ──monkey-patch──→ base.py
  (token by token)                                    │
                                               广播到所有 paper 回调
                                                     │
                                                     ↓
Frontend ←──EventSource── SSE Manager ←── sse_manager.emit()──┘
  │
  ↓
StreamPanel 组件：逐字渲染 + 自动滚动 + 闪烁光标 + 计时器
```

关键实现：
- `base.py` 启动时 monkey-patch `litellm.completion`，拦截 stream=True 的调用
- CrewAI 新版默认走 native provider（不经过 litellm），必须设置 `is_litellm=True` 强制走 litellm 路径
- CrewAI 的 `kickoff()` 在 asyncio 线程池中调用 LLM，threading.local() 无法传递上下文，因此使用广播模式（所有注册的 paper 回调都会收到 token）
- `sse_manager.emit()` 在跨线程调用 `asyncio.Queue.put_nowait()` 后，需要 `loop.call_soon_threadsafe(lambda: None)` 唤醒事件循环
- SSE 事件类型: `agent_start` → `agent_stream` (逐 token) → `agent_stream_end` → `agent_complete` / `agent_error`

### Frontend (React + Vite)

**路由:**

| 路径 | 页面 | 说明 |
|------|------|------|
| `/login` / `/register` | Login / Register | 公开 |
| `/` | Home | 首页（Hero + 功能卡片 + 三步流程） |
| `/papers` | PaperList | 论文列表 + 创建模态框（带颜色状态标签） |
| `/papers/new` | → 重定向到 /papers | 避免被 /papers/:id 捕获 |
| `/papers/:id` | PaperWorkbench | 核心写作台 |
| `/references` | References | 文献库（上传 + 表格 + 查看详情弹窗） |
| `/profile` | Profile | 个人中心 + 密码修改 |
| `/admin` | Admin | 管理后台 |

**关键组件:**
- `AgentPipeline.tsx` — 5 阶段流水线 UI，状态颜色编码，展开输出、批准/驳回/编辑
- `StreamPanel.tsx` — 流式渲染面板，80ms 轮询 buffer 同步到 state，自动滚动 + 闪烁光标
- `useSSE.ts` — EventSource Hook，支持 6 种事件（agent_start/complete/error/stream/stream_end/pipeline_complete）
- `Layout.tsx` — 全局导航栏（含文献库入口、用户名显示、退出按钮），sticky + 响应式 clamp()
- 已完成论文（status=complete）显示只读 `MDEditor.Markdown` 预览，流水线按钮禁用

**Paper 状态流:** `draft → parsing → outlining → writing → polishing → checking → complete`
中文标签: 草稿/解析中/大纲生成中/撰写中/润色中/检查中/已完成（每种有独立颜色）

### Paper Status Flow

```
draft → parsing → outlining → writing → polishing → checking → complete
   (parse)  (outline)   (write)    (polish)   (cite-check)
```

## Environment

`backend/.env`:
- `DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/papercraft`
- `SECRET_KEY=123456`
- `DEEPSEEK_API_KEY=sk-...` + `DEEPSEEK_BASE_URL=https://api.deepseek.com`
- `JWT_EXPIRATION_DAYS=7`
- `CORS_ORIGINS=["http://localhost:5173",...]`（支持 5173-5177）

表在应用启动时通过 `Base.metadata.create_all()` 自动创建。

## Important Caveats

- **端口**: 8000-8003 有 uvicorn 僵尸进程（无法 kill），请使用 8004。`vite.config.ts` proxy 指向 8004。
- **代理**: `base.py` 启动时 patch `httpx.Client.__init__(trust_env=False)` 和 `urllib.request.getproxies=lambda: {}`，避免 Windows 系统代理（Clash/TUN socks5）阻塞 DeepSeek API。如果 DeepSeek 连接报 SOCKS proxy 错，检查代理 patch 是否已加载。
- **流式依赖**: 流式输出依赖 `litellm.completion` monkey-patch（在 `base.py` 模块加载时执行）。如果升级 CrewAI/LiteLLM，需验证拦截器仍有效。
- 无数据库迁移工具，表由 `create_all` 自动创建。`full_text` 列通过 `ALTER TABLE` 在首次上传时自动添加。
- 无测试文件（前后端均无）
- `.env` 中包含真实 API Key，`.gitignore` 已排除 `.env`
- Agent 同步端点可能因 DeepSeek API 响应慢而超时（~15秒），推荐使用异步端点 + SSE
- weasyprint 和 python-docx 已安装（PDF/Word 导出用）
