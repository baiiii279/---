# PaperCraft - 多智能体论文写作助手 🧠✍️

基于 CrewAI 多智能体框架的智能论文写作协作平台。6 个 AI 智能体协同工作，Human-in-the-loop 审阅，前后端分离架构。支持上传 Word 模板自动解析格式规则。

## ✨ 功能特性

| 阶段 | 智能体 | 功能 |
|------|--------|------|
| 📚 | **文献解析 Agent** | 上传 PDF/Word/TXT，AI 自动提取研究问题、方法和结论 |
| 📋 | **大纲生成 Agent** | 根据文献摘要和模板，生成结构化论文大纲（JSON） |
| ✍️ | **内容撰写 Agent** | 按已确认大纲逐章撰写完整论文正文 |
| ✨ | **润色优化 Agent** | 学术编辑智能润色，统一术语时态，提升语言质量 |
| 🔍 | **引用检查 Agent** | 自动审计引用完整性和格式规范 |
| 📐 | **格式排版 Agent** | 上传 Word 模板自动解析格式规则，按规范编排论文 |

**核心特点：**
- 🔄 **Human-in-the-loop** — 每个 Agent 执行后等待用户审阅，可批准/驳回/编辑
- ⚡ **实时流式输出** — SSE 逐 token 推送 Agent 执行过程，前端实时渲染
- 📄 **一键导出 Word** — Markdown 自动转换为规范 Word 文档，支持自定义格式模板
- 📐 **格式模板** — 上传 .docx 模板自动解析字体/字号/行距/页边距等规则
- 👥 **双角色权限** — 普通用户 + 管理员，管理后台独立

## 🖥️ 技术栈

| 层 | 技术 |
|------|------|
| **前端** | React 19 + TypeScript + Vite + React Router |
| **后端** | FastAPI + SQLAlchemy + MySQL |
| **AI 编排** | CrewAI 0.76 + DeepSeek API (via LiteLLM) |
| **流式传输** | Server-Sent Events (SSE) |
| **文档导出** | python-docx |

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- Git

### 一键安装

```bash
# 克隆项目
git clone https://github.com/baiiii279/PaperCraft.git
cd PaperCraft

# 方式一：使用安装脚本（推荐）
bash setup.sh              # Linux / Mac / Git Bash
# 或
.\setup.ps1                # Windows PowerShell

# 方式二：手动安装
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

### 配置

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS papercraft DEFAULT CHARACTER SET utf8mb4;"

# 配置环境变量
cp backend/.env.example backend/.env
# 然后编辑 backend/.env，填入你的数据库密码和 DeepSeek API Key
```

### 启动

```bash
# 终端 1：启动后端（会自动创建数据库表和管理员账号）
cd backend
uvicorn app.main:app --reload --port 8005

# 终端 2：启动前端
cd frontend
npm run dev
```

打开浏览器访问 `http://localhost:5173` 即可使用。

### 默认管理员账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| `admin` | `admin123` | 管理员 |

> 管理员账号在后端首次启动时自动创建。

## 📁 项目结构

```
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/           # 路由模块（auth, papers, agent, admin, format_templates...）
│   │   ├── agents/        # CrewAI Agent 定义（6 个 Agent + 编排器）
│   │   ├── core/          # 配置、数据库引擎、JWT/密码
│   │   ├── models/        # SQLAlchemy ORM 模型（7 张表）
│   │   ├── schemas/       # Pydantic 请求/响应模型
│   │   ├── services/      # SSE 管理、Agent 异步执行、模板解析
│   │   └── main.py        # 应用入口
│   ├── .env.example       # 环境变量模板
│   └── requirements.txt
├── frontend/               # React + Vite 前端
│   ├── src/
│   │   ├── components/    # 共享组件（Layout, AgentPipeline, StreamPanel, FormatTemplateSelector）
│   │   ├── pages/         # 页面（Home, Login, PaperWorkbench, Admin...）
│   │   ├── hooks/         # 自定义 Hook（useSSE）
│   │   ├── services/      # Axios API 客户端
│   │   └── App.tsx        # 路由配置
│   └── package.json
├── docs/                   # 文档
├── setup.sh                # 一键安装脚本（Bash）
├── setup.ps1               # 一键安装脚本（PowerShell）
└── README.md
```

## 📄 论文状态流转

```
草稿 → 解析中 → 大纲生成中 → 撰写中 → 润色中 → 检查中 → 排版中 → 已完成
draft → parsing → outlining → writing → polishing → checking → formatting → complete
```

## 🔌 API 概览

| 前缀 | 模块 | 主要功能 |
|------|------|---------|
| `/api/auth` | 认证 | 注册、登录、获取当前用户 |
| `/api/user` | 用户 | 资料修改、密码修改、API Key 配置 |
| `/api/papers` | 论文 | 论文 CRUD、导出 Word |
| `/api/papers/{id}/agent` | Agent | 同步/异步执行 Agent、SSE 流式输出、用户反馈 |
| `/api/user/references` | 文献 | 文献 CRUD、文件上传解析 |
| `/api/admin` | 管理后台 | 用户管理、角色变更、论文管理、日志查看 |
| `/api/format-templates` | 格式模板 | 上传 docx 解析格式规则、模板列表、删除 |

## ⚠️ 注意事项

- 后端默认端口为 8005（8000-8004 可能有僵尸进程，TIME_WAIT 会阻塞端口绑定）
- SSE 流式输出依赖 `litellm.completion` 的 monkey-patch，升级 CrewAI/LiteLLM 时需验证
- Windows 系统代理（Clash/TUN）可能阻塞 DeepSeek API 连接，后端已自动处理
- 如果 Bash 环境变量有 `HTTP_PROXY=http://127.0.0.1:7897`，运行 curl/npm 前需 `unset`

## 📝 License

本项目为课程设计作品，仅供学习参考。
