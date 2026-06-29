from app.agents.base import BaseAgent, SharedContext
from crewai import Task

COURSE_TEMPLATE = ["引言", "相关工作", "方法", "实验", "结论"]
JOURNAL_TEMPLATE = ["摘要/关键词", "引言", "方法论", "结果", "讨论", "参考文献"]

OUTLINE_PROMPT = """你是一位论文架构师。基于以下文献摘要和论文主题，生成一份详细的论文大纲。

论文主题：{topic}
论文类型：{template}

使用以下章节结构：{chapters}

文献摘要：
{references}

请为每个章节输出：
- 章节标题
- 3-5 个写作要点
- 建议引用的文献编号

以 JSON 格式输出：
[
  {{"chapter": "引言", "points": ["要点1", "要点2"], "ref_ids": [1, 2]}}
]"""


class OutlineAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="论文架构师",
            goal="根据文献摘要和论文模板，生成结构化论文大纲",
            backstory="你是一位资深的学术论文架构师，擅长设计逻辑严谨的论文结构。",
        )

    def run(self, context: SharedContext) -> str:
        chapters = COURSE_TEMPLATE if context.template == "course" else JOURNAL_TEMPLATE
        refs_text = "\n\n".join(
            f"[{i+1}] {r['title']}" for i, r in enumerate(context.references)
        )
        task = Task(
            description=OUTLINE_PROMPT.format(
                topic=context.topic,
                template=context.template,
                chapters=" → ".join(chapters),
                references=refs_text,
            ),
            agent=self.agent,
            expected_output="JSON 格式的论文大纲，包含章节、要点和引用文献编号",
        )
        return task.execute()
