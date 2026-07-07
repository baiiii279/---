# FormatAgent 排版格式化 Agent 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在5个Agent流水线后增加第6个排版Agent，支持上传Word模板自动解析格式规则，按规则排版论文并导出。

**Architecture:** format_templates表存格式规则 → FormatAgent读取规则编排论文 → 排版标记Markdown → Word导出渲染

**Tech Stack:** FastAPI, SQLAlchemy, python-docx, CrewAI, React

## Global Constraints

- Python 3.11+, FastAPI 0.115+, SQLAlchemy 2.0+
- 论文状态枚举增加 `formatting` 阶段
- 所有新增文本使用中文
- 遵循现有代码风格（现有agent、api、model的命名和结构）

---

## File Structure

### 新建文件
| 文件 | 职责 |
|------|------|
| `backend/app/models/format_template.py` | FormatTemplate ORM 模型 |
| `backend/app/agents/format_agent.py` | 第6个排版 Agent |
| `backend/app/api/format_templates.py` | 格式模板 CRUD + 上传解析 API |
| `backend/app/services/template_parser.py` | docx 模板解析工具函数 |
| `frontend/src/components/FormatTemplateSelector.tsx` | 模板选择 + 上传 UI 组件 |

### 修改文件
| 文件 | 改动 |
|------|------|
| `backend/app/models/__init__.py` | 导入 FormatTemplate |
| `backend/app/models/paper.py` | status 枚举增加 `formatting` |
| `backend/app/main.py` | 注册 format_templates 路由 + 启动时种子默认模板 |
| `backend/app/agents/orchestrator.py` | agents 字典增加 FormatAgent |
| `backend/app/services/pipeline_runner.py` | 增加 formatting 阶段处理 |
| `backend/app/api/agent.py` | 增加 format 端点 + `_build_context` 传格式规则 |
| `backend/app/api/papers.py` | Word 导出识别 `<!-- format: xxx -->` 标记 |
| `frontend/src/pages/PaperWorkbench.tsx` | 增加格式模板选择器 + 排版阶段按钮 |
| `frontend/src/components/AgentPipeline.tsx` | 增加 formatting 阶段 |

---

### Task 1: FormatTemplate 模型 + 数据库迁移

**Files:**
- Create: `backend/app/models/format_template.py`
- Modify: `backend/app/models/__init__.py`

**Interfaces:**
- Produces: `FormatTemplate` SQLAlchemy model with fields: id, user_id, name, rules, is_default, created_at

- [ ] **Step 1: 创建 model 文件**

```python
# backend/app/models/format_template.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from app.core.database import Base


class FormatTemplate(Base):
    __tablename__ = "format_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    rules = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 2: 更新 __init__.py**

```python
# backend/app/models/__init__.py
from app.models.format_template import FormatTemplate
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/models/format_template.py backend/app/models/__init__.py
git commit -m "feat: add FormatTemplate model"
```

---

### Task 2: docx 模板解析器

**Files:**
- Create: `backend/app/services/template_parser.py`

**Interfaces:**
- Produces: `parse_template(file_path: str) -> dict` — 提取字体/字号/行距/页边距等规则
- Produces: `rules_to_text(rules: dict) -> str` — 将结构化规则转为自然语言文本

- [ ] **Step 1: 创建 template_parser.py**

```python
# backend/app/services/template_parser.py
"""从 .docx 模板文件中提取格式规则"""
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn


def parse_template(file_path: str) -> dict:
    """解析docx文件，提取格式规则"""
    doc = Document(file_path)
    rules = {}

    # 1. 页面设置
    section = doc.sections[0]
    rules['page'] = {
        'top_margin_cm': round(section.top_margin.cm, 2),
        'bottom_margin_cm': round(section.bottom_margin.cm, 2),
        'left_margin_cm': round(section.left_margin.cm, 2),
        'right_margin_cm': round(section.right_margin.cm, 2),
    }

    # 2. 默认样式
    style = doc.styles['Normal']
    font = style.font
    pf = style.paragraph_format
    rules['default'] = {
        'font_name': font.name,
        'font_size_pt': round(font.size.pt) if font.size else 12,
        'bold': font.bold,
        'first_line_indent_cm': round(pf.first_line_indent.cm, 2) if pf.first_line_indent else 0,
        'line_spacing': pf.line_spacing,
        'space_before_pt': round(pf.space_before.pt) if pf.space_before else 0,
        'space_after_pt': round(pf.space_after.pt) if pf.space_after else 0,
    }

    # 3. 标题样式
    for level in ['Heading 1', 'Heading 2', 'Heading 3']:
        try:
            hs = doc.styles[level]
            hf = hs.font
            hp = hs.paragraph_format
            # 获取中文字体名
            rpr = hs.element.find(qn('w:rPr'))
            ea_font = None
            if rpr is not None:
                rFonts = rpr.find(qn('w:rFonts'))
                if rFonts is not None:
                    ea_font = rFonts.get(qn('w:eastAsia'))

            rules[level.replace(' ', '_').lower()] = {
                'font_name': hf.name,
                'east_asian_font': ea_font,
                'font_size_pt': round(hf.size.pt) if hf.size else 16,
                'bold': hf.bold,
                'alignment': str(hp.alignment) if hp.alignment else 'LEFT',
            }
        except KeyError:
            continue

    return rules


def rules_to_text(rules: dict) -> str:
    """将结构化规则转为自然语言文本"""
    lines = []
    d = rules.get('default', {})
    lines.append(f"默认样式: {d.get('font_name', '宋体')}, {d.get('font_size_pt', 12)}pt")
    if d.get('first_line_indent_cm'):
        lines.append(f"首行缩进: {d['first_line_indent_cm']}cm")
    if d.get('line_spacing'):
        lines.append(f"行距: 固定值{round(d['line_spacing'])}磅")
    lines.append(f"段前: {d.get('space_before_pt', 0)}pt, 段后: {d.get('space_after_pt', 0)}pt")

    p = rules.get('page', {})
    lines.append(f"页边距: 上{p.get('top_margin_cm', 2.54)}cm 下{p.get('bottom_margin_cm', 2.54)}cm 左{p.get('left_margin_cm', 3.18)}cm 右{p.get('right_margin_cm', 3.18)}cm")

    for level_key in ['heading_1', 'heading_2', 'heading_3']:
        h = rules.get(level_key)
        if h:
            label = {'heading_1': '一级标题', 'heading_2': '二级标题', 'heading_3': '三级标题'}[level_key]
            font_name = h.get('east_asian_font') or h.get('font_name', '黑体')
            lines.append(f"{label}: {font_name}, {h.get('font_size_pt', 16)}pt, {'加粗' if h.get('bold') else '常规'}, {h.get('alignment', 'LEFT')}")

    return '\n'.join(lines)


def get_default_rules() -> str:
    """返回嘉庚学院默认格式规则"""
    return """默认样式: 宋体, 12pt, 首行缩进2字符, 行距固定值20磅
页边距: 上2.54cm 下2.54cm 左3.18cm 右3.18cm
一级标题: 黑体, 15pt, 居中, 加粗
二级标题: 黑体, 14pt, 左对齐, 加粗
三级标题: 宋体, 12pt, 左对齐
参考文献: GB/T 7714格式"""
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/services/template_parser.py
git commit -m "feat: add docx template parser"
```

---

### Task 3: 默认模板种子 + 路由注册

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: 更新 main.py 的 _seed_admin 函数，增加模板种子**

```python
# 在 backend/app/main.py 的 _seed_admin 函数后增加：

def _seed_default_template():
    """创建默认格式模板"""
    from app.core.database import SessionLocal
    from app.models.format_template import FormatTemplate
    from app.services.template_parser import get_default_rules
    db = SessionLocal()
    try:
        existing = db.query(FormatTemplate).filter(FormatTemplate.is_default == True).first()
        if existing:
            return
        db.add(FormatTemplate(
            user_id=0, name="嘉庚学院标准",
            rules=get_default_rules(),
            is_default=True,
        ))
        db.commit()
        print("[init] 默认格式模板已创建: 嘉庚学院标准")
    finally:
        db.close()
```

在 `init_db()` 中调用 `_seed_default_template()`：

```python
@app.on_event("startup")
def init_db():
    Base.metadata.create_all(bind=engine)
    _seed_admin()
    _seed_default_template()
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/main.py
git commit -m "feat: seed default format template"
```

---

### Task 4: 格式模板管理 API

**Files:**
- Create: `backend/app/api/format_templates.py`

**Interfaces:**
- Consumes: `FormatTemplate` model, `parse_template()`, `rules_to_text()`
- Produces: `GET /api/format-templates`, `POST /api/format-templates/upload`, `DELETE /api/format-templates/{id}`

- [ ] **Step 1: 创建 API 路由**

```python
# backend/app/api/format_templates.py
import os, tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.format_template import FormatTemplate
from app.models.user import User
from app.api.auth import get_current_user
from app.services.template_parser import parse_template, rules_to_text

router = APIRouter(prefix="/api/format-templates", tags=["format-templates"])


@router.get("")
def list_templates(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户可用模板（自己的 + 默认模板）"""
    templates = db.query(FormatTemplate).filter(
        (FormatTemplate.user_id == current_user.id) | (FormatTemplate.is_default == True)
    ).order_by(FormatTemplate.is_default.desc(), FormatTemplate.created_at.desc()).all()
    return [{"id": t.id, "name": t.name, "is_default": t.is_default, "created_at": str(t.created_at)[:19]} for t in templates]


@router.post("/upload")
def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传docx模板，自动解析格式规则"""
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="仅支持 .docx 文件")
    # 保存临时文件
    suffix = '.docx'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = file.file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        rules_dict = parse_template(tmp_path)
        rules_text = rules_to_text(rules_dict)
        template = FormatTemplate(
            user_id=current_user.id,
            name=name,
            rules=rules_text,
            is_default=False,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return {"id": template.id, "name": template.name, "rules": rules_text, "created_at": str(template.created_at)[:19]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"模板解析失败: {str(e)}")
    finally:
        os.unlink(tmp_path)


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(FormatTemplate).filter(
        FormatTemplate.id == template_id,
        FormatTemplate.user_id == current_user.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或无权删除")
    if template.is_default:
        raise HTTPException(status_code=400, detail="不能删除默认模板")
    db.delete(template)
    db.commit()
    return {"message": "ok"}
```

- [ ] **Step 2: 在 main.py 注册路由**

```python
# 在 backend/app/main.py 顶部 import 区域增加：
from app.api import format_templates

# 在 app.include_router(admin.router) 后增加：
app.include_router(format_templates.router)
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/api/format_templates.py backend/app/main.py
git commit -m "feat: format template management API (upload/list/delete)"
```

---

### Task 5: FormatAgent

**Files:**
- Create: `backend/app/agents/format_agent.py`

**Interfaces:**
- Consumes: `SharedContext` (content, format_rules)
- Produces: 带排版标记的 Markdown 文本

- [ ] **Step 1: 创建 FormatAgent**

```python
# backend/app/agents/format_agent.py
from app.agents.base import BaseAgent, SharedContext
from crewai import Task

FORMAT_PROMPT = """你是一位顶级的论文排版编辑。请按照用户提供的格式规则，对论文进行完整的排版处理。

## 格式规则
{format_rules}

## 排版要求

请严格按照以下流程处理：

1. **标题层级规范化**：确保整篇论文的标题层级一致
   - 一级标题（#）对应格式规则中的一级标题格式
   - 二级标题（##）对应格式规则中的二级标题格式
   - 三级标题（###）对应格式规则中的三级标题格式

2. **段落格式调整**：
   - 正文段落按规定首行缩进
   - 确保段落间距一致

3. **章节分隔**：
   - 引言、正文各章、结论、参考文献等重要章节前添加分页标记 `<!-- format: page-break -->`
   - 章节标题与正文之间保持适当间距

4. **参考文献格式化**：
   - 按照 GB/T 7714 标准重新编排参考文献格式
   - 参考文献列表前添加 `<!-- format: ref-list -->` 标记

5. **添加格式标记**：在关键位置添加排版指令标记
   - 正文段落前: `<!-- format: body-text -->`
   - 列表前: `<!-- format: list -->`
   - 表格前: `<!-- format: table -->`

## 输出规范
- 严格保留原文内容和引用标记 [N] 不变
- 只修改结构、间距、格式标记，不修改文字内容
- 不要添加任何前言后记说明
- 直接从排版后的论文内容开始输出

论文内容：
{content}"""


class FormatAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="排版编辑",
            goal="按照用户指定的格式规则对论文进行完整排版，添加格式标记",
            backstory=(
                "你是一位顶级的学术论文排版编辑，精通各类学术论文的格式规范。"
                "你熟悉GB/T 7714参考文献标准、各种期刊和学校的论文格式要求。"
                "你的工作是在不改变任何文字内容的前提下，让论文的结构和格式达到出版标准。"
                "你通过在Markdown中添加排版指令标记的方式，指导下游的Word导出工具应用正确的格式。"
            ),
        )

    def run(self, context: SharedContext, format_rules: str = "") -> str:
        task = Task(
            description=FORMAT_PROMPT.format(
                content=context.content,
                format_rules=format_rules or "默认格式：宋体小四号，首行缩进2字符，行距固定值20磅",
            ),
            agent=self._get_or_create_agent(),
            expected_output="按格式规则排版后的论文正文（Markdown格式，包含排版指令标记）",
        )
        return self._execute_task(task)
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/agents/format_agent.py
git commit -m "feat: add FormatAgent (6th agent for formatting)"
```

---

### Task 6: 流水线集成 + 论文状态更新 + format 端点

**Files:**
- Modify: `backend/app/models/paper.py`
- Modify: `backend/app/agents/orchestrator.py`
- Modify: `backend/app/services/pipeline_runner.py`
- Modify: `backend/app/api/agent.py`

- [ ] **Step 1: 更新 Paper 模型，增加 formatting 状态**

```python
# backend/app/models/paper.py
status = Column(Enum(
    "draft", "parsing", "outlining", "writing", "polishing", "checking",
    "formatting",  # 新增
    "complete"
), nullable=False, default="draft")
```

同时更新 `frontend/src/components/AgentPipeline.tsx` 的状态颜色映射（在 Task 8 中做）。

- [ ] **Step 2: 更新 Orchestrator，增加 FormatAgent**

```python
# backend/app/agents/orchestrator.py
from app.agents.format_agent import FormatAgent

class Orchestrator:
    def __init__(self):
        self.agents = {
            "parse": ParseAgent(),
            "outline": OutlineAgent(),
            "write": WriteAgent(),
            "polish": PolishAgent(),
            "cite_check": CiteCheckAgent(),
            "format": FormatAgent(),  # 新增
        }
```

- [ ] **Step 3: 更新 pipeline_runner.py，增加 formatting 阶段处理**

```python
# 在 backend/app/services/pipeline_runner.py 的 agent 执行逻辑中，
# 确保 formatting 阶段与其他 agent 同等处理。
# 关键是 _run_single_agent_inner 函数中纸状态设置：
# 搜索 "checking" 字符串，在它之后增加 "formatting"

# 需要修改的位置：
# 1. 状态序列：执行完 cite_check 后，设置 paper.status = "formatting"
# 2. 执行 format 后，设置 paper.status = "complete"
```

- [ ] **Step 4: 更新 agent.py，增加 format 端点 + 传递格式规则**

在 `_build_context` 函数中增加 `format_rules` 参数：

```python
def _build_context(paper: Paper, db: Session, template_id: int = None) -> SharedContext:
    # ... 原有代码 ...
    # 获取格式规则
    format_rules = ""
    if template_id:
        tmpl = db.query(FormatTemplate).get(template_id)
        if tmpl:
            format_rules = tmpl.rules
    if not format_rules:
        tmpl = db.query(FormatTemplate).filter(FormatTemplate.is_default == True).first()
        if tmpl:
            format_rules = tmpl.rules
    # ... 返回 SharedContext 时带上 format_rules ...
```

增加 format agent 端点：

```python
@router.post("/format")
def run_format(
    paper_id: int, template_id: int = Query(None),
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    paper = _get_paper(paper_id, current_user, db)
    paper.status = "formatting"
    db.commit()
    context = _build_context(paper, db, template_id)
    agent = FormatAgent()
    # 注册流式回调...
    result = agent.run(context, format_rules=context.format_rules)
    paper.content = result
    paper.status = "complete"
    db.commit()
    return {"result": result}
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/models/paper.py backend/app/agents/orchestrator.py backend/app/services/pipeline_runner.py backend/app/api/agent.py
git commit -m "feat: integrate FormatAgent into pipeline, add formatting paper status"
```

---

### Task 7: 前端 - 格式模板选择器组件

**Files:**
- Create: `frontend/src/components/FormatTemplateSelector.tsx`

- [ ] **Step 1: 创建组件**

```tsx
// frontend/src/components/FormatTemplateSelector.tsx
import { useState, useEffect } from 'react';
import api from '../services/api';

interface Template {
  id: number;
  name: string;
  is_default: boolean;
  created_at: string;
}

interface Props {
  selectedId: number | null;
  onSelect: (id: number | null) => void;
}

export default function FormatTemplateSelector({ selectedId, onSelect }: Props) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadName, setUploadName] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get<Template[]>('/format-templates')
      .then(r => {
        setTemplates(r.data);
        if (!selectedId && r.data.length > 0) {
          const def = r.data.find((t: Template) => t.is_default);
          onSelect(def ? def.id : r.data[0].id);
        }
      })
      .catch(() => {});
  }, []);

  const handleUpload = async () => {
    if (!uploadFile || !uploadName.trim()) return;
    setUploading(true);
    setError('');
    const form = new FormData();
    form.append('file', uploadFile);
    form.append('name', uploadName.trim());
    try {
      const res = await api.post('/format-templates/upload', form);
      setTemplates(prev => [...prev, res.data]);
      onSelect(res.data.id);
      setShowUpload(false);
      setUploadName('');
      setUploadFile(null);
    } catch (err: unknown) {
      const detail = err && typeof err === 'object' && 'response' in err
        ? String((err as any).response?.data?.detail || '上传失败') : '上传失败';
      setError(detail);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ fontSize: 14, color: '#475569', fontWeight: 600, display: 'block', marginBottom: 8 }}>
        格式模板
      </label>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <select
          value={selectedId ?? ''}
          onChange={(e) => onSelect(e.target.value ? Number(e.target.value) : null)}
          style={{
            padding: '8px 12px', border: '1px solid #E2E8F0', borderRadius: 6,
            fontSize: 14, background: '#fff', color: '#0F172A', flex: 1,
          }}
        >
          {templates.map(t => (
            <option key={t.id} value={t.id}>
              {t.name} {t.is_default ? '(默认)' : ''}
            </option>
          ))}
        </select>
        <button
          onClick={() => setShowUpload(!showUpload)}
          style={{
            padding: '8px 16px', background: '#2563EB', color: '#fff',
            border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13, whiteSpace: 'nowrap',
          }}
        >
          上传模板
        </button>
      </div>

      {showUpload && (
        <div style={{ marginTop: 12, padding: 16, background: '#F8FAFC', borderRadius: 8, border: '1px solid #E2E8F0' }}>
          <input
            placeholder="模板名称"
            value={uploadName}
            onChange={(e) => setUploadName(e.target.value)}
            style={{ width: '100%', padding: 8, marginBottom: 8, border: '1px solid #E2E8F0', borderRadius: 4, fontSize: 13, boxSizing: 'border-box' }}
          />
          <input
            type="file" accept=".docx"
            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
            style={{ fontSize: 13, marginBottom: 8, display: 'block' }}
          />
          {error && <p style={{ color: '#EF4444', fontSize: 12, margin: '0 0 8px' }}>{error}</p>}
          <button
            onClick={handleUpload}
            disabled={uploading || !uploadFile || !uploadName.trim()}
            style={{
              padding: '6px 16px', background: uploading ? '#94A3B8' : '#2563EB', color: '#fff',
              border: 'none', borderRadius: 4, cursor: uploading ? 'default' : 'pointer', fontSize: 13,
            }}
          >
            {uploading ? '解析中...' : '上传并解析'}
          </button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/FormatTemplateSelector.tsx
git commit -m "feat: add FormatTemplateSelector component"
```

---

### Task 8: 前端 - 论文工作台集成

**Files:**
- Modify: `frontend/src/pages/PaperWorkbench.tsx`
- Modify: `frontend/src/components/AgentPipeline.tsx`

- [ ] **Step 1: 更新 AgentPipeline.tsx，增加 formatting 阶段**

在 `STATUS_COLORS` 和 `STATUS_LABELS` 映射中增加：

```typescript
// 在 frontend/src/components/AgentPipeline.tsx 中
const STATUS_COLORS: Record<string, string> = {
  // ... 现有 ...
  formatting: '#0891B2',  // 新增：青色
};
const STATUS_LABELS: Record<string, string> = {
  // ... 现有 ...
  formatting: '排版中',
};
// 在流水线阶段数组中增加:
const pipelineStages = [
  { key: 'parsing', label: '文献解析' },
  { key: 'outlining', label: '大纲生成' },
  { key: 'writing', label: '内容撰写' },
  { key: 'polishing', label: '润色优化' },
  { key: 'checking', label: '引用检查' },
  { key: 'formatting', label: '格式排版' },  // 新增
];
```

- [ ] **Step 2: 在 PaperWorkbench.tsx 中集成模板选择器和排版按钮**

```tsx
// 导入组件
import FormatTemplateSelector from '../components/FormatTemplateSelector';

// 在组件内部增加 state
const [formatTemplateId, setFormatTemplateId] = useState<number | null>(null);

// 在流水线 UI 区域，引用检查阶段之后增加格式排版阶段：
// （在现有的流水线渲染逻辑中，在 cite_check 之后增加 formatting 的处理）
// 并在该区域渲染 FormatTemplateSelector 组件

{/* 格式排版阶段 */}
{/* 在引用检查完成后显示 */}
{pipelineStatus === 'checking_done' && (
  <div style={{ marginTop: 16 }}>
    <FormatTemplateSelector selectedId={formatTemplateId} onSelect={setFormatTemplateId} />
    <button onClick={() => handleRunAgent('format')} style={btnStyle}>
      开始排版
    </button>
  </div>
)}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/AgentPipeline.tsx frontend/src/pages/PaperWorkbench.tsx
git commit -m "feat: integrate formatting stage and template selector into workbench"
```

---

### Task 9: Word 导出更新 - 识别排版标记

**Files:**
- Modify: `backend/app/api/papers.py` (函数 `_md_to_docx`)

- [ ] **Step 1: 更新 _md_to_docx 识别排版标记**

在 `_md_to_docx` 函数的行处理循环中，增加对 `<!-- format: xxx -->` 标记的识别：

```python
# 在 _md_to_docx 函数的 while 循环开头增加：

# 识别排版指令标记
format_cmd_match = re.match(r'<!-- format:\s*(\S+)', line)
if format_cmd_match:
    cmd = format_cmd_match.group(1)
    if cmd == 'page-break':
        # 分页：添加分页符
        run = doc.add_paragraph().add_run()
        run._element.makeelement(qn('w:br'), {qn('w:type'): 'page'})
    elif cmd == 'body-text':
        # 正文字体设置（后续段落会被应用）
        _current_format = 'body'
    elif cmd == 'ref-list':
        # 参考文献列表（缩小字号为五号）
        _current_format = 'ref'
    i += 1
    continue

# 在添加正文段落时，根据 _current_format 应用不同样式
# 原有添加段落的逻辑中，增加格式判断
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/api/papers.py
git commit -m "feat: Word export recognizes format markers from FormatAgent"
```

---

### Task 10: 端到端验证

- [ ] **Step 1: 启动后端，检查默认模板是否自动创建**

```bash
cd backend && uvicorn app.main:app --reload --port 8004
# 检查启动日志是否有 "[init] 默认格式模板已创建: 嘉庚学院标准"
# 访问 GET /api/format-templates 应返回包含默认模板的列表
```

- [ ] **Step 2: 上传模板测试**

```bash
curl -X POST http://localhost:8004/api/format-templates/upload \
  -F "file=@/path/to/template.docx" \
  -F "name=测试模板"
# 预期返回 200 和解析后的规则文本
```

- [ ] **Step 3: 执行排版 Agent 测试**

```bash
curl -X POST "http://localhost:8004/api/papers/{id}/agent/format?template_id={tid}"
# 预期返回排版后的论文内容
```

- [ ] **Step 4: 前端验证**
启动前端，验证论文工作台的格式模板选择器和上传功能正常。
