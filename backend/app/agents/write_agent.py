from app.agents.base import BaseAgent, SharedContext
from crewai import Task

WRITE_PROMPT = """你是一位学术写手。请严格按照以下大纲撰写论文内容。

论文主题：{topic}
大纲：
{outline}

可用文献：
{references}

请逐章撰写，使用 Markdown 格式。引用文献时使用 [1][2] 格式标记。
每个段落要有论点和论据，语言流畅、逻辑严谨。"""

class WriteAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="学术写手",
            goal="按已确认大纲逐章撰写论文内容",
            backstory="你是一位高产学术写手，擅长将研究思路转化为规范的学术论文。",
        )

    def run(self, context: SharedContext) -> str:
        refs_text = "\n".join(
            f"[{i+1}] {r['title']} - {r.get('authors', '未知')}"
            for i, r in enumerate(context.references)
        )
        task = Task(
            description=WRITE_PROMPT.format(
                topic=context.topic,
                outline=context.outline,
                references=refs_text,
            ),
            agent=self._get_or_create_agent(),
            expected_output="完整的 Markdown 格式论文，包含引用标记",
        )
        return self._execute_task(task)
