from app.agents.base import BaseAgent, SharedContext
from crewai import Task

FORMAT_PROMPT = """你是排版编辑。按以下格式规则处理论文：

格式规则：
{format_rules}

排版要求：
1. 标题层级：一级标题居中，二级左对齐
2. 摘要和关键词前加 <!-- format: body-text --> 标记
3. 参考文献列表前加 <!-- format: ref-list --> 标记
4. 不要添加分页标记，章节连续书写
5. 保留原文内容不变，只调整格式标记

论文：
{content}"""


class FormatAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="排版编辑",
            goal="按格式规则添加排版标记，不修改文字内容",
            backstory="学术排版编辑，精通GB/T 7714和各校论文格式规范。",
        )

    def run(self, context: SharedContext, format_rules: str = "") -> str:
        task = Task(
            description=FORMAT_PROMPT.format(
                content=context.content,
                format_rules=format_rules or "宋体小四号，首行缩进2字符，行距20磅",
            ),
            agent=self._get_or_create_agent(),
            expected_output="按格式规则排版的论文正文（含排版标记）",
        )
        return self._execute_task(task)
