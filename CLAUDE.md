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
npm run preview        # 预览生产构建
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
- **`app/models/`** — 6 张 ORM 表: users, papers, user_references, paper_references, tasks, agent_logs
- **`app/api/`** — 6 个路由模块:
  - `auth.py`: `/api/auth/*` — 注册/登录/获取当前用户 (JWT Bearer)
  - `user.py`: `/api/user/*` — 更新资料/改密
  - `references.py`: `/api/user/references/*` — 文献 CRUD + 文件上传 (PDF/Word/TXT)
  - `papers.py`: `/api/papers/*` — 论文 CRUD
  - `agent.py`: `/api/papers/{id}/agent/*` — Agent 分步/全流程/SSE/反馈
  - `admin.py`: `/api/admin/*` — 管理后台 (统计/用户/论文/日志)
- **`app/agents/`** — CrewAI Agent 层
  - `base.py`: `BaseAgent` 基类 (DeepSeek LLM 配置) + `SharedContext` dataclass
  - `orchestrator.py`: `Orchestrator` 编排器 (create_task/run_agent/handle_feedback)
  - 5 个 Agent: parse_agent → outline_agent → write_agent → polish_agent → cite_check_agent

### Frontend (React + Vite)

路由 (react-router-dom):

| 路径 | 页面 | 说明 |
|------|------|------|
| `/login` `/register` | Login / Register | 公开 |
| `/` | Home | 首页 |
| `/papers` | PaperList | 论文列表 + 创建 |
| `/papers/:id` | PaperWorkbench | 核心写作台 |
| `/references` | References | 文献库管理 |
| `/profile` | Profile | 个人中心 |
| `/admin` | Admin | 管理后台 |

认证: JWT 存 `localStorage('token')`，Axios 拦截器自动附加 `Authorization: Bearer` 头，401 时自动清除并跳转。

### Paper Status Flow

```
draft → parsing → outlining → writing → polishing → checking → complete
   (parse)  (outline)   (write)    (polish)   (cite-check)
```

前端 `PaperWorkbench.tsx` 的 `STATUS_ACTIONS` 映射控制当前状态显示的按钮。

## Environment

`backend/.env`:
- `DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/papercraft`
- `SECRET_KEY=your-secret-key-change-this` (JWT signing)
- `DEEPSEEK_API_KEY=sk-...` + `DEEPSEEK_BASE_URL=https://api.deepseek.com`
- `JWT_EXPIRATION_DAYS=7`, `CORS_ORIGINS=["http://localhost:5173"]`

表在应用启动时通过 `Base.metadata.create_all()` 自动创建。

## Key Patterns

- **API 鉴权**: `get_current_user` 依赖注入 (`from app.api.auth import get_current_user`)，返回值类型 `User`
- **Agent 调用**: `task = orchestrator.create_task(db, paper.id, agent_key)` → `result = orchestrator.run_agent(db, task, context)` → 需通过 `BaseAgent._execute_task(task)` 执行 CrewAI Task（创建 `Crew(agents=[self.agent], tasks=[task])` 后调用 `crew.kickoff()`）
- **文件上传**: `UploadFile` + 解析 (pdfplumber for PDF, python-docx for DOCX)
- **前端编辑器**: `@uiw/react-md-editor` + KaTeX 公式渲染
- **内联样式**: 所有组件使用 `style={{}}` 而非 Tailwind CSS 类
- **密码哈希**: 已改用 `hashlib.sha256` + `secrets.token_hex(16)` salt，格式 `f"{salt}${hash}"`

## Important Caveats

- 无数据库迁移工具，表由 `create_all` 自动创建
- 无测试文件（前后端均无）
- SSE 端点是简化心跳实现（每 2 秒），未推送实际 Agent 事件
- DeepSeek API Key 在 `.env` 中为真实密钥，注意 `.gitignore` 中包含了 `.env`
- 管理员通过 `user.role == "admin"` 判断，需手动在数据库中将用户角色设为 admin
