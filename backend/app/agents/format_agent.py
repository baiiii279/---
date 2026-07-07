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
