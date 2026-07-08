from app.agents.base import BaseAgent, SharedContext
from crewai import Task

WRITE_PROMPT = """你是一位顶尖的学术写手。你的任务是根据已确认的论文大纲，逐章撰写高质量的论文正文。

论文主题：{topic}

已确认的大纲：
{outline}

可用参考文献：
{references}

**重要：论文必须以「摘要/关键词」开头，然后才是引言和各章正文。** 摘要必须在论文第一章之前单独成节。

请先不要输出正文。按照以下思维链逐章思考和撰写，每章思考完成后再写那章的内容。

**思考与写作流程：**

**步骤0 - 摘要（必须首先完成）**：
- 先用200-300字高度概括全文：研究背景、核心问题、采用方法、主要发现、研究意义
- 格式：标题为"[摘要]"加粗居中，空一格后接内容
- 摘要内容后空一行，然后输出"[关键词]"加粗居中，空一格后接3-5个关键词，词间空两格
- 完成摘要和关键词后再开始写第一章引言

对于每一章，按以下步骤迭代：

**步骤1 - 规划该章**：先想清楚——
- 本章要完成什么论证任务？
- 需要分几个小节？每节的核心论点是什么？
- 需要引用哪些文献？在什么位置引用？

**步骤2 - 写段首句**：把该章所有段落的段首句先列出来，确保每段一个论点，段与段之间形成递进关系

**步骤3 - 展开论证**：对每个段落，按"论点→论据→分析"结构展开——
- 段首句提出论点
- 中间用数据、文献、推理作为论据
- 段尾解释该论点的意义或与论文核心论点的关联

**步骤4 - 自检**：写完一章后检查——
- [ ] 每段段首是否是一个明确的论点句？
- [ ] 所有非常识断言是否有文献引用？
- [ ] 是否避免了空泛套话？
- [ ] 引用编号是否在文献列表中存在？

逐章完成上述流程。检查通过后继续下一章。

## 写作规范

### 章节字数
- 摘要：200-300字 | 引言：550-700字 | 结论：500-700字
- 正文各章：每章800-1200字，总字数5000-7000字

### 写作质量
- 每段5-8句，段首句为论点
- 论点+论据+分析黄金三角
- 引用格式：[1][2]方括号上标，按出现顺序编号
- 参考文献不少于10条
- 学术正式，一般现在时为主

### 禁止
- 禁止编造内容或参考文献
- 禁止空泛套话
- 禁止"此处插入图表"等占位符

使用 Markdown，从论文题目开始撰写。"""


class WriteAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="学术写手",
            goal="按照已确认大纲逐章撰写高质量学术论文正文，逻辑严谨、论证充分、引用规范",
            backstory="""你是一位高产且严谨的学术写手，在多个SCI期刊担任过审稿人。
你的写作信条是：好的学术写作不是炫耀词汇量，而是以最清晰的逻辑传递最扎实的研究。
你擅长将复杂的研究过程转化为流畅、准确、有说服力的书面表达。
你深知每篇论文都是在和审稿人对话——你的任务是用文字让审稿人毫无困惑地理解你的研究价值。""",
        )

    def run(self, context: SharedContext) -> str:
        refs_text = "\n".join(
            f"[{i+1}] {r['title']}. {r.get('authors', '未知')}. {r.get('source', '')}"
            for i, r in enumerate(context.references)
        )
        outline_text = str(context.outline) if isinstance(context.outline, str) else \
            "\n".join(f"- {c.get('chapter', '?')}: {c.get('objective', '')}" for c in (context.outline or []))
        task = Task(
            description=WRITE_PROMPT.format(
                topic=context.topic,
                outline=outline_text,
                references=refs_text,
            ),
            agent=self._get_or_create_agent(),
            expected_output="完整的 Markdown 格式学术论文正文，以摘要/关键词开头，包含引言和各章内容",
        )
        result = self._execute_task(task)
        if "摘要" not in result[:500]:
            task.description = "**【重要提醒】你上一次的输出没有包含摘要/关键词部分。请务必在论文开头先写摘要和关键词，再写引言。**\n\n" + task.description
            result = self._execute_task(task)
        return result
