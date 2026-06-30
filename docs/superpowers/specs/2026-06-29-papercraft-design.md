# PaperCraft — 多智能体论文写作助手 · 设计文档

## 概述

**PaperCraft** 是一个基于 Multi-Agent 架构的智能论文写作协作平台。用户输入论文主题并提交参考文献后，由多个 AI Agent 分工协作，经过文献解析→大纲生成→内容撰写→润色→引用检查的完整流程，辅助用户完成论文写作。每个环节用户均可审阅、确认或驳回修改，实现 Human-in-the-loop 的协作模式。

## 技术栈

| 层级       | 技术             | 说明                       |
| ---------- | ---------------- | -------------------------- |
| 前端       | React (Vite)     | SPA 单页应用               |
| 后端       | FastAPI (Python) | RESTful API + SSE 实时推送 |
| Agent 框架 | CrewAI           | 多 Agent 编排与协作        |
| LLM API    | DeepSeek         | 国内大模型 API，成本低     |
| 数据库     | MySQL            | 关系型数据库               |
| 认证       | JWT              | 前后端分离认证方案         |

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (React)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │
│  │ 登录/注册 │ │ 个人中心  │ │ 论文工作台 │ │ 管理员  │  │
│  │          │ │ 文献库   │ │ SSE状态   │ │ 日志   │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │ REST API + SSE
┌──────────────────────▼──────────────────────────────┐
│                 Backend (FastAPI)                     │
│  ┌──────┐ ┌──────┐ ┌───────────┐ ┌────────────────┐ │
│  │ Auth │ │ User │ │ Paper CRUD│ │ Agent Orchest.  │ │
│  └──────┘ └──────┘ └───────────┘ └────────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Agent Layer (CrewAI)                     │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │
│  │文献   │ │大纲  │ │撰写  │ │润色  │ │引用检查  │  │
│  │解析   │ │生成  │ │内容  │ │优化  │ │Agent    │  │
│  │Agent  │ │Agent │ │Agent │ │Agent │ │          │  │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────────┘  │
│              共享记忆 (Shared Context)                │
└──────────────────────┬──────────────────────────────┘
                       │ DeepSeek API
┌──────────────────────▼──────────────────────────────┐
│                     MySQL                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │
│  │users │ │papers│ │tasks │ │refs  │ │agent_logs│  │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────────┘  │
└─────────────────────────────────────────────────────┘
```

## 数据库设计

### users — 用户表

| 字段          | 类型                 | 约束                    | 说明     |
| ------------- | -------------------- | ----------------------- | -------- |
| id            | INT                  | PK AUTO_INCREMENT       | 用户ID   |
| username      | VARCHAR(50)          | UNIQUE NOT NULL         | 用户名   |
| email         | VARCHAR(100)         | UNIQUE                  | 邮箱     |
| password_hash | VARCHAR(255)         | NOT NULL                | 密码哈希 |
| role          | ENUM('user','admin') | NOT NULL DEFAULT 'user' | 角色     |
| avatar        | VARCHAR(255)         | NULL                    | 头像URL  |
| created_at    | DATETIME             | DEFAULT NOW()           | 创建时间 |
| updated_at    | DATETIME             | ON UPDATE NOW()         | 更新时间 |

### papers — 论文表

| 字段       | 类型                                                                            | 约束              | 说明             |
| ---------- | ------------------------------------------------------------------------------- | ----------------- | ---------------- |
| id         | INT                                                                             | PK AUTO_INCREMENT | 论文ID           |
| user_id    | INT                                                                             | FK → users.id    | 所属用户         |
| title      | VARCHAR(200)                                                                    | NULL              | 论文标题         |
| topic      | VARCHAR(500)                                                                    | NOT NULL          | 主题描述         |
| template   | ENUM('course','journal')                                                        | DEFAULT 'course'  | 论文模板         |
| status     | ENUM('draft','parsing','outlining','writing','polishing','checking','complete') | DEFAULT 'draft'   | 当前状态         |
| outline    | TEXT                                                                            | NULL              | 已确认大纲(JSON) |
| content    | LONGTEXT                                                                        | NULL              | 最终全文         |
| created_at | DATETIME                                                                        | DEFAULT NOW()     | 创建时间         |
| updated_at | DATETIME                                                                        | ON UPDATE NOW()   | 更新时间         |

### user_references — 用户文献库

| 字段       | 类型         | 约束              | 说明      |
| ---------- | ------------ | ----------------- | --------- |
| id         | INT          | PK AUTO_INCREMENT | 文献ID    |
| user_id    | INT          | FK → users.id    | 所属用户  |
| title      | VARCHAR(300) | NOT NULL          | 文献标题  |
| authors    | VARCHAR(500) | NULL              | 作者      |
| source     | VARCHAR(500) | NULL              | 出处/期刊 |
| abstract   | TEXT         | NULL              | 摘要      |
| url        | VARCHAR(500) | NULL              | 链接      |
| keywords   | VARCHAR(300) | NULL              | 关键词    |
| created_at | DATETIME     | DEFAULT NOW()     | 添加时间  |

### paper_references — 论文-文献关联表

| 字段         | 类型 | 约束                     | 说明   |
| ------------ | ---- | ------------------------ | ------ |
| id           | INT  | PK AUTO_INCREMENT        |        |
| paper_id     | INT  | FK → papers.id          | 论文ID |
| reference_id | INT  | FK → user_references.id | 文献ID |

### tasks — Agent 任务记录

| 字段             | 类型                                                  | 约束              | 说明      |
| ---------------- | ----------------------------------------------------- | ----------------- | --------- |
| id               | INT                                                   | PK AUTO_INCREMENT | 任务ID    |
| paper_id         | INT                                                   | FK → papers.id   | 关联论文  |
| agent_type       | ENUM('parse','outline','write','polish','cite_check') | NOT NULL          | Agent类型 |
| status           | ENUM('pending','running','success','failed')          | DEFAULT 'pending' | 状态      |
| input_data       | TEXT                                                  | NULL              | 输入内容  |
| output_data      | TEXT                                                  | NULL              | 输出内容  |
| user_feedback    | ENUM('pending','approve','reject','edit')             | DEFAULT 'pending' | 用户反馈  |
| feedback_comment | TEXT                                                  | NULL              | 反馈意见  |
| started_at       | DATETIME                                              | NULL              | 开始时间  |
| finished_at      | DATETIME                                              | NULL              | 完成时间  |

### agent_logs — Agent 执行日志

| 字段       | 类型                        | 约束              | 说明         |
| ---------- | --------------------------- | ----------------- | ------------ |
| id         | BIGINT                      | PK AUTO_INCREMENT | 日志ID       |
| task_id    | INT                         | FK → tasks.id    | 关联任务     |
| step       | VARCHAR(50)                 | NOT NULL          | 执行步骤名称 |
| message    | TEXT                        | NOT NULL          | 日志内容     |
| level      | ENUM('info','warn','error') | DEFAULT 'info'    | 日志级别     |
| created_at | DATETIME                    | DEFAULT NOW()     | 记录时间     |

**ER 关系：**

- users 1:N papers (一人多篇论文)
- users 1:N user_references (个人文献库)
- papers 1:N paper_references N:1 user_references (多对多关联)
- papers 1:N tasks (一篇论文多条Agent执行记录)
- tasks 1:N agent_logs (详细执行日志)

## API 接口设计

### 认证模块

| 方法 | 路径               | 说明                                                 |
| ---- | ------------------ | ---------------------------------------------------- |
| POST | /api/auth/register | 注册（含表单验证：用户名唯一性、密码强度、邮箱格式） |
| POST | /api/auth/login    | 登录，返回 JWT token                                 |
| GET  | /api/auth/me       | 获取当前用户信息                                     |

### 用户模块

| 方法 | 路径               | 说明         |
| ---- | ------------------ | ------------ |
| PUT  | /api/user/profile  | 更新个人信息 |
| PUT  | /api/user/password | 修改密码     |
| POST | /api/user/avatar   | 上传头像     |

### 文献库模块

| 方法   | 路径                      | 说明               |
| ------ | ------------------------- | ------------------ |
| GET    | /api/user/references      | 获取我的文献库列表 |
| POST   | /api/user/references      | 新增文献           |
| DELETE | /api/user/references/{id} | 删除文献           |

### 论文模块

| 方法   | 路径             | 说明                                         |
| ------ | ---------------- | -------------------------------------------- |
| POST   | /api/papers      | 创建论文（topic + template + reference_ids） |
| GET    | /api/papers      | 我的论文列表（含状态筛选）                   |
| GET    | /api/papers/{id} | 论文详情                                     |
| PUT    | /api/papers/{id} | 更新论文（修改大纲、内容等）                 |
| DELETE | /api/papers/{id} | 删除论文                                     |

### Agent 模块

| 方法 | 路径                              | 说明                                       |
| ---- | --------------------------------- | ------------------------------------------ |
| POST | /api/papers/{id}/agent/parse      | 启动文献解析 Agent                         |
| POST | /api/papers/{id}/agent/outline    | 启动大纲生成 Agent                         |
| POST | /api/papers/{id}/agent/write      | 启动撰写 Agent                             |
| POST | /api/papers/{id}/agent/polish     | 启动润色 Agent                             |
| POST | /api/papers/{id}/agent/cite-check | 启动引用检查 Agent                         |
| POST | /api/papers/{id}/agent/start      | 一键全流程                                 |
| GET  | /api/papers/{id}/agent/tasks      | 获取所有 Agent 任务记录                    |
| GET  | /api/papers/{id}/agent/events     | SSE 实时状态推送                           |
| POST | /api/papers/{id}/agent/feedback   | 提交审阅反馈（task_id + action + comment） |

### 管理员模块

| 方法 | 路径             | 说明                                                  |
| ---- | ---------------- | ----------------------------------------------------- |
| GET  | /api/admin/users | 用户列表（分页）                                      |
| GET  | /api/admin/stats | 系统统计                                              |
| GET  | /api/admin/logs  | Agent 日志（?user_id=&paper_id=&status=&page=&size=） |

## Agent 层详细设计

### 共享记忆 (Shared Context)

所有 Agent 共享一个上下文对象，存储：

- 论文主题
- 已确认文献列表（结构化摘要）
- 已确认大纲（JSON 结构）
- 已撰写内容（分章节）
- 用户反馈记录（历史修改意见）

### Agent 1：文献解析 Agent

- **Role**：文献分析师
- **Goal**：解析用户提供的文献，提取核心观点、方法论、结论
- **Tools**：无外部工具，读取用户提交的文献信息
- **Output**：结构化文献摘要（每篇：研究问题、方法、发现、适用章节标注）
- **异常处理**：文献数量为0 → 提示用户至少添加1篇文献

### Agent 2：大纲生成 Agent

- **Role**：论文架构师
- **Goal**：根据文献摘要和论文模板，生成结构化大纲
- **Tools**：读取共享记忆中已确认的文献库
- **Output**：JSON 格式大纲（章节标题 + 写作要点 + 引用文献 ID）
- **模板支持**：
  - `course`：引言 → 相关工作 → 方法 → 实验 → 结论
  - `journal`：摘要/关键词 → 引言 → 方法论 → 结果 → 讨论 → 参考文献
- **Human-in-loop**：用户可调整章节顺序、增删要点、修改标题

### Agent 3：内容撰写 Agent

- **Role**：学术写手
- **Goal**：按已确认大纲逐章撰写论文内容
- **Tools**：读取大纲 + 文献库
- **Output**：Markdown 格式章节内容，引用标记 [1][2]
- **Human-in-loop**：可选逐章确认或全量确认

### Agent 4：润色 Agent（可选）

- **Role**：学术编辑
- **Goal**：提升学术语言流畅度，检测重复表达并改写，统一术语时态
- **Output**：润色后的全文，附带修改说明（可选展示 Diff）

### Agent 5：引用检查 Agent

- **Role**：学术审计员
- **Goal**：检查引用准确性、格式规范、遗漏引用
- **Output**：检查报告（格式问题、遗漏引用、修正建议）
- **异常处理**：发现严重引用问题 → 自动触发撰写 Agent 重新修正

### Orchestrator（编排管理器）

职责：

- 接收分步或一键启动请求
- 管理共享记忆上下文传递
- 处理用户反馈：approve → 下一步；reject → 重跑带反馈意见
- 条件分支：
  - 文献不足 → 提示用户补充
  - 大纲驳回 → 保留驳回理由传递给 Agent 重新生成
  - 引用检查失败 → 自动触发修正
- 异常处理：超时重试、LLM 调用失败回退
- SSE 推送：每步状态变更实时推送到前端

```
Agent 完整流程：

用户输入主题 + 文献列表
    │
    ▼
┌────────────────────┐
│ 文献解析 Agent      │──→ 输出：文献摘要
│ (自动执行)           │
└─────────┬──────────┘
          │ 用户确认？
          ├── 驳回 → 修改后再次解析
          │
          ▼
┌────────────────────┐
│ 大纲生成 Agent      │──→ 输出：论文大纲
│ (按模板生成)         │
└─────────┬──────────┘
          │ 用户确认？
          ├── 驳回 → 带意见重新生成
          │
          ▼
┌────────────────────┐
│ 内容撰写 Agent      │──→ 输出：章节内容
│ (逐章或全量)         │
└─────────┬──────────┘
          │ 用户确认？
          ├── 驳回 → 带意见重新撰写
          │
          ▼
┌────────────────────┐
│ 润色 Agent (可选)   │──→ 输出：润色后全文
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ 引用检查 Agent      │──→ 输出：检查报告
└─────────┬──────────┘
          │
          ▼
      论文完成 ✓
```

## 前端页面设计

### 页面结构

| 页面       | 路由              | 功能                                 |
| ---------- | ----------------- | ------------------------------------ |
| 首页       | /                 | 产品介绍、快速开始                   |
| 登录       | /login            | 账号密码登录，表单验证               |
| 注册       | /register         | 注册，用户名唯一性/密码强度/邮箱验证 |
| 个人中心   | /profile          | 头像、修改密码、我的论文列表         |
| 文献库     | /references       | 用户个人文献管理（CRUD）             |
| 论文工作台 | /papers/{id}      | Agent 流程可视化、分步审阅           |
| 论文详情   | /papers/{id}/view | 查看最终论文全文                     |
| 管理员     | /admin            | 用户管理、系统日志、统计             |

### 论文工作台（核心页面）

设计为**横向流程管道**视图：

- 顶部：5 个流程节点（解析→大纲→撰写→润色→引用），当前活跃节点高亮
- 中间：当前 Agent 的输出内容展示区
- 底部：审阅操作区（通过 / 驳回+意见 / 编辑）
- 右侧（可选）：SSE 推送的实时 Agent 执行日志滚动

## Human-in-the-loop 设计

| 节点         | 用户操作           | 编排器响应                             |
| ------------ | ------------------ | -------------------------------------- |
| 文献解析完成 | 确认/驳回+修改意见 | 驳回 → 重跑文献解析；确认 → 启动大纲 |
| 大纲生成完成 | 确认/驳回+结构修改 | 驳回 → 重跑大纲；确认 → 启动撰写     |
| 撰写完成     | 逐章确认/驳回      | 驳回 → 重跑章节；全确认 → 启动润色   |
| 润色完成     | 确认/驳回          | 驳回 → 重新润色；确认 → 启动引用检查 |
| 引用检查完成 | 确认/驳回          | 驳回 → 触发修正；确认 → 论文完成     |

## 实时推送 (SSE)

`GET /api/papers/{id}/agent/events` 返回 SSE 流，事件格式：

```json
{
  "event": "agent_status",
  "data": {
    "task_id": 1,
    "agent_type": "parse",
    "status": "running",
    "progress": "正在解析第 2/5 篇文献..."
  }
}
```

事件类型：

- `agent_start`：Agent 开始执行
- `agent_progress`：执行进度更新
- `agent_complete`：Agent 完成，等待用户确认
- `agent_failed`：Agent 执行失败

## 项目目录结构

```
PaperCraft/
├── frontend/                # React 前端
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── hooks/          # 自定义 hooks
│   │   ├── services/       # API 调用封装
│   │   └── App.tsx
│   └── package.json
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # 路由
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── schemas/        # Pydantic 校验
│   │   ├── agents/         # CrewAI Agent 定义
│   │   │   ├── parse_agent.py
│   │   │   ├── outline_agent.py
│   │   │   ├── write_agent.py
│   │   │   ├── polish_agent.py
│   │   │   ├── cite_check_agent.py
│   │   │   └── orchestrator.py
│   │   └── core/           # 配置、JWT、数据库连接
│   ├── requirements.txt
│   └── main.py
├── docs/
│   └── superpowers/specs/  # 设计文档
└── README.md
```
