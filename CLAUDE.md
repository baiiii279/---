# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PaperCraft — 多智能体论文写作助手。基于 CrewAI 编排 5 个 AI 智能体（文献解析→大纲生成→内容撰写→润色→引用检查），Human-in-the-loop 审阅，前后端分离。

## Commands

```bash
# 后端
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000      # 开发服务器
# API 文档: http://localhost:8000/docs

# 前端
cd frontend && npm install
npm run dev            # 开发服务器 (端口 5173, /api 代理到 :8000)
npm run build          # 生产构建 (tsc -b && vite build)
npm run lint           # oxlint 代码检查
npm run preview        # 预览生产构建 (端口 4173)
```

前后端需同时运行，Vite 将 `/api` 请求代理到 `http://localhost:8000`。

## Architecture

```
React SPA (localhost:5173) ⇅ REST API + SSE ⇅ FastAPI (localhost:8000) ⇅ MySQL (localhost:3306/papercraft)
                                          ⇅ CrewAI + DeepSeek API
```

### Backend (FastAPI)

分层结构：

- **`app/core/`** — 配置 (pydantic-settings)、数据库引擎 (SQLAlchemy)、JWT/密码 (SHA256+salt)
- **`app/models/`** — 6 张 ORM 表: `users`, `papers`, `user_references`, `paper_references`, `tasks`, `agent_logs`
- **`app/schemas/`** — Pydantic 请求/响应模型 (auth, user, paper, reference, task)
- **`app/api/`** — 6 个路由模块:
  - `auth.py`: `/api/auth/*` — 注册/登录/获取当前用户 (JWT Bearer)
  - `user.py`: `/api/user/*` — 更新资料/改密
  - `references.py`: `/api/user/references/*` — 文献 CRUD + 文件上传 (PDF/Word/TXT，自动解析标题和摘要)
  - `papers.py`: `/api/papers/*` — 论文 CRUD
  - `agent.py`: `/api/papers/{id}/agent/*` — Agent 同步/异步分步执行、全流程、SSE 事件流、用户反馈
  - `admin.py`: `/api/admin/*` — 管理后台 (统计/用户/论文/日志)
- **`app/services/`** — 业务服务层:
  - `pipeline_runner.py`: 异步 Agent 编排器 (后台线程依次执行 Agent，通过 SSE 推送进度)
  - `sse_manager.py`: `SSEEventManager` — 基于 `asyncio.Queue` 的 SSE 事件分发，每个 paper_id 维护独立订阅者列表
- **`app/agents/`** — CrewAI Agent 层:
  - `base.py`: `BaseAgent` 基类 (DeepSeek LLM 配置，`crew.kickoff()` 执行) + `SharedContext` dataclass
  - `orchestrator.py`: `Orchestrator` 编排器 (create_task/run_agent/handle_feedback)
  - 5 个 Agent: `parse_agent` → `outline_agent` → `write_agent` → `polish_agent` → `cite_check_agent`

关键 API 模式:
- **鉴权**: `get_current_user` 依赖注入 (`from app.api.auth import get_current_user`)，返回值类型 `User`
- **Agent 执行**: `orchestrator.create_task(db, paper.id, agent_key)` → `orchestrator.run_agent(db, task, context)` (内部创建 `Crew(agents=[self.agent], tasks=[task])` 后调用 `crew.kickoff()`)
- **SSE 认证**: EventSource 不支持自定义请求头，JWT 通过查询参数 `?token=xxx` 传递
- **异步 Agent**: `POST /{agent_type}/run` 返回 202，`BackgroundTasks` + `run_in_executor` 在线程池中执行 CrewAI (同步库阻塞)
- **文件上传**: `UploadFile` + pdfplumber (PDF) / python-docx (DOCX) 解析文本，存储至 `uploads/references/{user_id}/`
- **密码哈希**: `hashlib.sha256` + `secrets.token_hex(16)` salt，格式 `"{salt}${hash}"`

### Frontend (React + Vite)

**Tech stack:** React 19, TypeScript 6, Vite 8, Tailwind CSS v4 (通过 `@tailwindcss/vite` 插件配置), Axios, react-router-dom v7

路由 (react-router-dom):

| 路径 | 页面 | 说明 |
|------|------|------|
| `/login` / `/register` | Login / Register | 公开 |
| `/` | Home | 首页 |
| `/papers` | PaperList | 论文列表 + 创建 |
| `/papers/:id` | PaperWorkbench | 核心写作台 |
| `/references` | References | 文献库管理 |
| `/profile` | Profile | 个人中心 |
| `/admin` | Admin | 管理后台 |

认证: JWT 存 `localStorage('token')`，`frontend/src/services/api.ts` (Axios 实例) 通过请求拦截器自动附加 `Authorization: Bearer` 头，响应 401 时自动清除并跳转 `/login`。

前端关键组件/Hooks:
- `AgentPipeline.tsx` — 5 阶段流水线 UI，状态颜色编码 (蓝/绿/红/灰)，支持展开输出、批准/驳回/编辑
- `FeedbackPanel.tsx` — 单 Agent 反馈面板 (审批/驳回/编辑)
- `useSSE.ts` — EventSource Hook，自动带 token 连接 SSE，3 秒自动重连，监听 4 种事件 (`agent_start`/`agent_complete`/`agent_error`/`pipeline_complete`)

### Paper Status Flow

```
draft → parsing → outlining → writing → polishing → checking → complete
   (parse)  (outline)   (write)    (polish)   (cite-check)
```

论文模板类型: `"course"` (课程设计) 和 `"journal"` (期刊)。前端 `PaperWorkbench.tsx` 的 `AGENTS` 数组和 `NEXT_STATUS` 映射控制步骤顺序。

### Agent API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/papers/{id}/agent/{agent_type}` | 同步执行单个 Agent |
| POST | `/api/papers/{id}/agent/{agent_type}/run` | 异步执行 (202) + SSE 推送 |
| POST | `/api/papers/{id}/agent/start` | 一键全流程 (同步) |
| POST | `/api/papers/{id}/agent/feedback` | 用户反馈 (approve/reject/edit) |
| GET | `/api/papers/{id}/agent/events` | SSE 事件流 |
| GET | `/api/papers/{id}/agent/tasks` | 任务列表 |

## Environment

`backend/.env`:
- `DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/papercraft`
- `SECRET_KEY=your-secret-key-change-this` (JWT signing)
- `DEEPSEEK_API_KEY=sk-...` + `DEEPSEEK_BASE_URL=https://api.deepseek.com`
- `JWT_EXPIRATION_DAYS=7`, `CORS_ORIGINS=["http://localhost:5173"]`

表在应用启动时通过 `Base.metadata.create_all()` 自动创建。

## Important Caveats

- 无数据库迁移工具，表由 `create_all` 自动创建
- 无测试文件（前后端均无）
- SSE 端点是简化心跳实现（每 2 秒），未推送实际 Agent 事件
- DeepSeek API Key 在 `.env` 中为真实密钥，注意 `.gitignore` 中包含了 `.env` (以及 `.superpowers/`)
- 管理员通过 `user.role == "admin"` 判断，需手动在数据库中将用户角色设为 admin
- Agent 同步端点可能因 DeepSeek API 响应慢而超时，推荐使用异步端点 (`POST /{agent_type}/run`)
- `.doc` 文件兼容性有限，推荐使用 `.docx` 格式
- weasyprint 已安装在依赖中 (PDF 导出用)
