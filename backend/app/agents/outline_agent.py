# -*- coding: utf-8 -*-
from app.agents.base import BaseAgent, SharedContext
from crewai import Task

COURSE_TEMPLATE = ["摘要/关键词", "引言", "相关工作", "方法", "实验", "结论"]
JOURNAL_TEMPLATE = ["摘要/关键词", "引言", "方法论", "结果", "讨论", "参考文献"]

OUTLINE_PROMPT = """你是论文架构师。基于文献分析设计论文大纲。必须包含「摘要/关键词」作为第一章。

论文主题：{topic}
论文类型：{template}
章节顺序参考：{chapters}

文献分析：
{references}

只输出纯JSON数组（不要代码块包裹）：
[
  {{"chapter": "章节名", "objective": "本章核心论证目标", "points": ["要点1", "要点2", "要点3"], "ref_ids": [1,2], "estimated_pages": 2}}
]

要求：每章3-5个可执行要点，ref_ids引用实际文献编号，总页数8-12。"""


class OutlineAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="论文架构师",
            goal="设计逻辑严密的论文大纲，输出标准JSON",
            backstory="顶刊审稿人，擅长从研究素材中构建有说服力的叙事结构。",
        )

    def run(self, context: SharedContext) -> str:
        chapters = COURSE_TEMPLATE if context.template == "course" else JOURNAL_TEMPLATE
        refs_text = "\n\n".join(
            f"[{i+1}] {r['title']}\n   摘要: {r.get('abstract', '无')[:200]}"
            for i, r in enumerate(context.references)
        )
        task = Task(
            description=OUTLINE_PROMPT.format(
                topic=context.topic,
                template="课程论文" if context.template == "course" else "期刊论文",
                chapters=" → ".join(chapters),
                references=refs_text,
            ),
            agent=self._get_or_create_agent(),
            expected_output="JSON大纲，含章节、目标、要点、引用和页数",
        )
        return self._execute_task(task)
