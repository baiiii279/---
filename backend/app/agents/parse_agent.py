from app.agents.base import BaseAgent, SharedContext
from crewai import Task

PARSE_PROMPT = """你是文献分析师。逐篇解析以下文献，每篇输出：研究问题、理论基础、方法设计、核心发现、局限性、与论文主题的关联度。每篇用 --- 分隔。若文献信息不足则标注，严禁编造。最后用一段话总结：研究现状、研究空白、文献间的观点对话。

文献列表：
{references}"""


class ParseAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="文献分析师",
            goal="深度解析文献，提取研究问题、方法、发现、局限性和关联度",
            backstory="顶级文献分析师，精通跨学科研究，能快速识别文献核心贡献和研究空白。",
        )

    def run(self, context: SharedContext) -> str:
        refs_text = "\n\n".join(
            f"标题: {r['title']}\n作者: {r.get('authors', '未知')}\n摘要: {r.get('abstract', '无')}"
            for i, r in enumerate(context.references)
        )
        task = Task(
            description=PARSE_PROMPT.format(references=refs_text),
            agent=self._get_or_create_agent(),
            expected_output="结构化文献分析报告，包含逐篇解析和综合分析",
        )
        return self._execute_task(task)
