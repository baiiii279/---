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
├── api/           # 8 个路由模块
│   ├── auth.py    # /api/auth/* — 注册/登录/当前用户（返回 role）
│   ├── user.py    # /api/user/* — 资料/密码/API Key
│   ├── references.py # /api/user/references/* — 文献 CRUD + 文件上传
│   ├── papers.py  # /api/papers/* — 论文 CRUD + /export/docx（Markdown→Word）
│   ├── agent.py   # /api/papers/{id}/agent/* — 同步/异步执行、SSE、反馈
│   ├── admin.py   # /api/admin/* — 管理后台（用户管理、角色变更、论文管理、日志）
├── agents/        # CrewAI Agent 层
│   ├── base.py    # BaseAgent 基类 + litellm.completion 拦截器（流式输出）+ httpx 代理 patch
│   ├── orchestrator.py # 编排器 (create_task/run_agent/handle_feedback)
│   └── parse_agent.py / outline_agent.py / write_agent.py / polish_agent.py / cite_check_agent.py
├── services/
│   ├── pipeline_runner.py # 异步 Agent 编排（线程池执行 CrewAI，注册 SSE 流式回调）
│   └── sse_manager.py     # SSEEventManager — asyncio.Queue 事件分发
```

**关键 API 模式:**
- **鉴权**: 所有受保护端点通过 `get_current_user` 依赖注入（JWT Bearer），管理端点额外使用 `_require_admin`
- **Admin API** (`/api/admin`):
  - `GET /users?keyword=` — 用户列表（支持搜索），含分页
  - `PUT /users/{id}/role?role=admin|user` — 提升/降级用户角色
  - `DELETE /users/{id}` — 删除用户（级联删除论文、引用、任务、日志）
  - `GET /papers?status=` — 所有论文列表（支持状态筛选），含分页
  - `DELETE /papers/{id}` — 强制删除任意论文
  - `GET /stats` — 用户/论文计数统计
  - `GET /logs?level=&user_id=&paper_id=` — Agent 日志（支持多维度筛选）
- 登录/注册接口返回 `AuthResponse` 包含 `role` 字段
- **管理员自动创建**: `main.py` 启动时调用 `_seed_admin()`，检测 `admin` 用户不存在则创建（用户名: admin, 密码: admin123），已存在但非管理员则升级角色

### 前端角色系统

- `Login.tsx` / `Register.tsx` 登录/注册后将 `role` 存入 `localStorage`
- `Layout.tsx` 根据 `localStorage.getItem('role')` 条件渲染「管理后台」导航链接（仅管理员可见）
- `Admin.tsx` 管理后台页面包含 4 个标签页：概览、用户管理（含搜索/角色变更/删除）、论文管理（含状态筛选/删除）、系统日志
- `Home.tsx` 右上角显示用户名和退出按钮
- `Profile.tsx` 底部含退出按钮
- 前端 Axios 拦截器自动附加 `Authorization: Bearer <token>` 到每个请求，401 响应自动跳转登录页

### Agent 流式输出架构

```
DeepSeek API ──SSE stream──→ litellm.completion ──monkey-patch──→ base.py
  (token by token)                                    │
                                               广播到所有 paper 回调
                                                     │
                                                     ↓
Frontend ←──EventSource── SSE Manager ←── sse_manager.emit()──┘
```

关键实现：
- `base.py` 启动时 monkey-patch `litellm.completion`，拦截 stream=True 的调用
- CrewAI 新版默认走 native provider（不经过 litellm），必须设置 `is_litellm=True` 强制走 litellm 路径
- CrewAI 的 `kickoff()` 在 asyncio 线程池中调用 LLM，threading.local() 无法传递上下文，因此使用广播模式
- `sse_manager.emit()` 在跨线程调用 `asyncio.Queue.put_nowait()` 后，需要 `loop.call_soon_threadsafe(lambda: None)` 唤醒事件循环
- SSE 事件类型: `agent_start` → `agent_stream` (逐 token) → `agent_stream_end` → `agent_complete` / `agent_error`

### Frontend (React + Vite)

| 路径 | 页面 | 说明 |
|------|------|------|
| `/login` / `/register` | Login / Register | 公开，注册/登录后保存 role |
| `/` | Home | 首页（Hero + 功能卡片 + 退出按钮） |
| `/papers` | PaperList | 论文列表 + 创建模态框 |
| `/papers/:id` | PaperWorkbench | 核心写作台 |
| `/references` | References | 文献库（上传 + 表格 + 详情弹窗） |
| `/profile` | Profile | 个人中心（资料/密码/API Key/退出） |
| `/admin` | Admin | 管理后台（仅管理员可见） |

**Paper 状态流:** `draft → parsing → outlining → writing → polishing → checking → complete`
中文标签: 草稿/解析中/大纲生成中/撰写中/润色中/检查中/已完成

## Environment

`backend/.env`:
- `DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/papercraft`
- `SECRET_KEY=123456`
- `DEEPSEEK_API_KEY=sk-...` + `DEEPSEEK_BASE_URL=https://api.deepseek.com`
- `JWT_EXPIRATION_DAYS=7`
- `CORS_ORIGINS=["http://localhost:5173",...]`

表在应用启动时通过 `Base.metadata.create_all()` 自动创建。管理员账号在启动时通过 `_seed_admin()` 自动创建（admin/admin123）。

## Important Caveats

- **端口**: 8000-8003 有 uvicorn 僵尸进程（无法 kill），请使用 8004。`vite.config.ts` proxy 指向 8004。
- **代理**: `base.py` 启动时 patch `httpx.Client.__init__(trust_env=False)` 和 `urllib.request.getproxies=lambda: {}`，避免 Windows 系统代理（Clash/TUN socks5）阻塞 DeepSeek API。如果 DeepSeek 连接报错，检查代理 patch 是否已加载。Bash 环境变量 `HTTP_PROXY=http://127.0.0.1:7897` 可能存在，按需 `unset`。
- **流式依赖**: 流式输出依赖 `litellm.completion` monkey-patch（在 `base.py` 模块加载时执行）。如果升级 CrewAI/LiteLLM，需验证拦截器仍有效。
- 无数据库迁移工具，表由 `create_all` 自动创建。
- 无测试文件（前后端均无）
- 密码使用 SHA-256 + salt 哈希，非 bcrypt
- Agent 同步端点可能因 DeepSeek API 响应慢而超时（~15秒），推荐使用异步端点 + SSE
