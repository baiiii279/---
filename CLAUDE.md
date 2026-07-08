# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PaperCraft — 多智能体论文写作助手。基于 CrewAI 编排 6 个 AI 智能体（文献解析→大纲生成→内容撰写→润色→引用检查→格式排版），Human-in-the-loop 审阅，前后端分离。支持上传 PDF/Word/TXT 文献、逐 token 流式输出、Word 文档导出、上传Word模板自动解析格式规则。

## Commands

```bash
# 后端
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8005   # 开发服务器（8000-8004可能有僵尸进程）
# API 文档: http://localhost:8005/docs

# 运行后端测试
cd backend && python -m pytest tests/ -v

# 前端
cd frontend && npm install
npm run dev            # 开发服务器（自动分配端口，/api 代理到 :8005）
npm run build          # 生产构建 (tsc -b && vite build)
npm run test           # 运行前端测试 (vitest)
npm run lint           # oxlint 代码检查
```

前后端需同时运行。Vite 代理见 `frontend/vite.config.ts`。

## Architecture

```
React SPA (localhost:517x) ⇅ REST + SSE ⇅ FastAPI (localhost:8005) ⇅ MySQL (localhost:3306/papercraft)
                                          ⇅ CrewAI + DeepSeek API (via litellm)
```

### Backend (FastAPI)

```
app/
├── core/          # 配置 (pydantic-settings)、数据库引擎、JWT/密码
├── models/        # 7 张 ORM 表: users, papers, user_references, paper_references, tasks, agent_logs, format_templates
├── schemas/       # Pydantic 请求/响应模型
├── api/           # 9 个路由模块
│   ├── auth.py    # /api/auth/* — 注册/登录/当前用户（返回 role）
│   ├── user.py    # /api/user/* — 资料/密码/API Key
│   ├── references.py # /api/user/references/* — 文献 CRUD + 文件上传
│   ├── papers.py  # /api/papers/* — 论文 CRUD + /export/docx（Markdown→Word）
│   ├── agent.py   # /api/papers/{id}/agent/* — 同步/异步执行、SSE、反馈、全流程
│   ├── admin.py   # /api/admin/* — 管理后台（用户管理、角色变更、论文管理、日志）
│   ├── format_templates.py # /api/format-templates/* — 格式模板上传/解析/列表/删除
├── agents/        # CrewAI Agent 层
│   ├── base.py    # BaseAgent 基类 + litellm.completion 拦截器（流式输出）+ httpx 代理 patch
│   ├── orchestrator.py # 编排器 (create_task/run_agent/handle_feedback)
│   ├── parse_agent.py / outline_agent.py / write_agent.py / polish_agent.py
│   ├── cite_check_agent.py / format_agent.py  # 第6个排版Agent
├── services/
│   ├── pipeline_runner.py # 异步 Agent 编排（线程池执行 CrewAI，注册 SSE 流式回调）
│   ├── sse_manager.py     # SSEEventManager — asyncio.Queue 事件分发
│   └── template_parser.py # docx 模板解析（提取字体/字号/行距/页边距/标题样式）
```

### Paper 状态流（7阶段）

```
draft → parsing → outlining → writing → polishing → checking → formatting → complete
草稿    解析中    大纲生成中    撰写中    润色中    检查中    排版中      已完成
```

**注意**: MySQL 的 `papers.status` 是 ENUM 类型，新增 `formatting` 状态时需手动执行 ALTER TABLE：
```sql
ALTER TABLE papers MODIFY COLUMN status ENUM(
  'draft','parsing','outlining','writing','polishing','checking','formatting','complete'
) DEFAULT 'draft';
```

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

### 格式模板系统

用户可上传 `.docx` 模板文件，后端通过 `template_parser.py` 自动解析：
- Normal 样式的字体/字号/行距/首行缩进
- Heading 1/2/3 的字体/字号/加粗/对齐
- 页面设置（页边距）
- 解析结果存储为 `format_templates` 表

`FormatAgent`（第6个Agent）读取格式规则，输出带 `<!-- format: xxx -->` 标记的 Markdown。
Word 导出函数 `_md_to_docx()` 识别这些标记并应用对应格式。

### Frontend (React + Vite)

| 路径 | 页面 | 说明 |
|------|------|------|
| `/login` / `/register` | Login / Register | 公开，注册/登录后保存 role |
| `/` | Home | 首页（Hero + 功能卡片 + 退出按钮） |
| `/papers` | PaperList | 论文列表 + 创建模态框 |
| `/papers/:id` | PaperWorkbench | 核心写作台（含格式模板选择器） |
| `/references` | References | 文献库（上传 + 表格 + 详情弹窗） |
| `/profile` | Profile | 个人中心（资料/密码/API Key/退出） |
| `/admin` | Admin | 管理后台（仅管理员可见） |

## Environment

`backend/.env`:
- `DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/papercraft`
- `SECRET_KEY=123456`
- `DEEPSEEK_API_KEY=sk-...` + `DEEPSEEK_BASE_URL=https://api.deepseek.com`
- `JWT_EXPIRATION_DAYS=7`
- `CORS_ORIGINS=["http://localhost:5173",...]`

表在应用启动时通过 `Base.metadata.create_all()` 自动创建。管理员账号在启动时通过 `_seed_admin()` 自动创建（admin/admin123）。默认格式模板（嘉庚学院标准）通过 `_seed_default_template()` 自动创建。

## Testing

```bash
# 后端测试（pytest）
cd backend && python -m pytest tests/ -v

# 前端测试（vitest）
cd frontend && npx vitest run
```

后端测试文件：`test_format_agent.py`、`test_format_template.py`、`test_format_template_api.py`
前端测试文件：`FormatTemplateSelector.test.tsx`

## Important Caveats

- **端口**: 8000-8004 可能有 uvicorn 僵尸进程，推荐使用 8005。`vite.config.ts` proxy 应指向当前运行端口。
- **数据库 ENUM**: `papers.status` 是 MySQL ENUM 类型，修改 Python 模型中的枚举值后需手动执行 ALTER TABLE。
- **代理**: `base.py` 启动时 patch `httpx.Client.__init__(trust_env=False)` 和 `urllib.request.getproxies=lambda: {}`，避免 Windows 系统代理（Clash/TUN socks5）阻塞 DeepSeek API。Bash 环境变量 `HTTP_PROXY=http://127.0.0.1:7897` 可能存在，需 `unset` 才能通过 curl/npm 访问外网。
- **流式依赖**: 流式输出依赖 `litellm.completion` monkey-patch（在 `base.py` 模块加载时执行）。如果升级 CrewAI/LiteLLM，需验证拦截器仍有效。
- 无数据库迁移工具，表由 `create_all` 自动创建。
- 密码使用 SHA-256 + salt 哈希，非 bcrypt。
- Agent 同步端点可能因 DeepSeek API 响应慢而超时（~15秒），推荐使用异步端点 + SSE。
- 论文删除需级联清理 tasks 和 agent_logs（外键约束）。
- **Agent 提示词原则**：WriteAgent 用自然中文格式（「第一章 引言」「1.1 研究背景」），不要强制 Markdown `#`/`##`。不要加 CoT（思维链），LLM 会把思考过程输出到正文。提示词越简洁越好。
- **Word 导出**：识别中文章节（`第X章` 居中、`1.1` 左对齐）、`摘要`/`关键词：` 居中，兼容 Markdown 标题格式。
