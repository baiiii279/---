from app.agents.base import BaseAgent, SharedContext
from crewai import Task

PARSE_PROMPT = """你是一位文献分析师。用户提供以下文献列表，请逐篇提取核心信息。

对每篇文献输出：
- 研究问题
- 采用方法
- 主要发现/结论
- 可能适用于论文的哪些章节

文献列表：
{references}

请以结构化 Markdown 格式输出，每篇文献用 --- 分隔。"""

class ParseAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="文献分析师",
            goal="解析用户提供的文献，提取每篇的核心观点、方法论和结论",
            backstory="你是一位经验丰富的学术研究员，擅长快速理解文献核心内容并提取关键信息。",
        )

    def run(self, context: SharedContext) -> str:
        refs_text = "\n\n".join(
            f"标题: {r['title']}\n摘要: {r.get('abstract', '无')}"
            for r in context.references
        )
        task = Task(
            description=PARSE_PROMPT.format(references=refs_text),
            agent=self.agent,
            expected_output="结构化文献摘要，每篇包含研究问题、方法、发现、适用章节",
        )
        return task.execute()
