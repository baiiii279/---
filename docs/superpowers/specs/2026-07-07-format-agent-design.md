# FormatAgent 格式排版 Agent 设计文档

## 概述
在现有5个Agent流水线之后，增加第6个Agent——`FormatAgent`（排版格式化Agent），负责按用户指定的格式要求对论文进行排版。支持上传Word模板自动解析格式规则。

## 论文状态流转（更新后）
```
draft → parsing → outlining → writing → polishing → checking → formatting → complete
```

## 数据库设计

### format_templates 表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| user_id | INT | FK→users.id, NOT NULL | 所属用户 |
| name | VARCHAR(100) | NOT NULL | 模板名称 |
| rules | TEXT | NOT NULL | 从docx提取的格式规则文本 |
| is_default | BOOLEAN | DEFAULT FALSE | 是否默认模板 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

预置数据：系统启动时自动创建一条 `user_id=0` 的默认模板，名为「嘉庚学院标准」，rules 内容基于厦门大学嘉庚学院本科生毕业论文格式要求(摘选).docx 提取。

## API 设计

### 格式模板管理（`/api/format-templates`）

| 方法 | 路径 | 功能 | 请求 | 响应 |
|------|------|------|------|------|
| GET | `/api/format-templates` | 获取模板列表 | - | 模板数组 |
| POST | `/api/format-templates/upload` | 上传docx解析为模板 | multipart: file + name | 新建的模板对象 |
| DELETE | `/api/format-templates/{id}` | 删除模板 | - | {message} |

### 排版 Agent 执行（`/api/papers/{id}/agent/format`）

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/papers/{id}/agent/format` | 执行排版Agent（同步，SSE流式） |
| POST | `/api/papers/{id}/agent/format/run` | 执行排版Agent（异步） |

请求参数：`template_id`（格式模板ID，不传则使用默认模板）

## FormatAgent 设计

### 输入
- 论文正文（经过润色后的 Markdown）
- 格式规则文本（从 format_templates.rules 读取）

### 处理流程
1. 读取格式规则，理解字体/字号/行距/页边距/标题规范/参考文献格式
2. 按规则重新编排论文结构：
   - 标题层级对齐（一级标题用黑体小三居中、二级标题用黑体四号等）
   - 添加必要的章节间距和分页
   - 参考文献按 GB/T 7714 标准格式化
3. 在Markdown中添加排版标记（如 `<!-- page-break -->`、`<!-- heading-1-style -->` 等）
4. 输出重新编排后的完整论文 Markdown

### 输出
带排版标记的 Markdown 文本，供 Word 导出时渲染为正确的格式。

## 上传模板解析逻辑

用户上传 `.docx` 文件后，后端用 `python-docx` 自动提取：

```python
# 提取内容示例（存入 rules 字段作为结构化自然语言文本）：
默认样式: 宋体, 小四(12pt), 首行缩进2字符, 行距固定值20磅
一级标题: 黑体, 小三(15pt), 居中, 加粗
二级标题: 黑体, 四号(14pt), 左对齐, 加粗
三级标题: 黑体, 小四(12pt), 左对齐
页边距: 上2.54cm 下2.54cm 左3.18cm 右3.18cm
参考文献: GB/T 7714格式
```

### FormatAgent 输出格式
FormatAgent 输出带有排版指令的 Markdown，Word 导出函数根据指令应用格式：

```markdown
<!-- format: page-break -->
# 第一章 引言
<!-- format: body-text -->
论文正文内容...
<!-- format: ref-list -->
[1] 作者. 题名[J]. 刊名, 年, 卷(期): 页码.
```

Word 导出函数 `_md_to_docx()` 识别这些 `<!-- format: xxx -->` 注释标记，将其转换为对应的 python-docx 格式设置（字体、字号、行距等）。

## 前端变更

### 论文工作台（PaperWorkbench.tsx）
- 流水线阶段从5个变为6个，增加「排版中」阶段
- 新增格式模板选择器：下拉框显示可用模板 + 「上传模板」按钮
- 论文进入排版阶段前确认使用的模板

### 格式模板管理弹窗
- 「上传模板」按钮 → 选择 .docx 文件 → 输入模板名称 → 上传解析
- 模板列表展示（名称 + 创建时间）+ 删除按钮

## Word导出更新

`_md_to_docx()` 函数更新：
- 识别 FormatAgent 添加的排版标记，应用对应的 Word 格式
- 使用论文关联的格式模板中的规则来设置字体/字号/行距

## 边界情况

- 无格式模板时使用内置的嘉庚学院默认规则
- 上传非 .docx 文件时返回错误提示
- 上传的模板解析失败时返回具体错误信息
- 格式模板删除时不影响已排版的论文
- 多用户模板隔离（每个用户只能看到自己的模板 + 默认模板）
