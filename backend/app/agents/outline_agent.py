# -*- coding: utf-8 -*-
from app.agents.base import BaseAgent, SharedContext
from crewai import Task

COURSE_TEMPLATE = ["摘要/关键词", "引言", "相关工作", "方法", "实验", "结论"]
JOURNAL_TEMPLATE = ["摘要/关键词", "引言", "方法论", "结果", "讨论", "参考文献"]

OUTLINE_PROMPT = """你是一位顶级的论文架构师。你的任务是基于文献分析结果和论文主题，设计一份逻辑严密、层次清晰、具有说服力的论文大纲。

论文主题：{topic}
论文类型：{template}
标准章节结构：{chapters}

文献分析摘要：
{references}

请先不要输出大纲。按照以下思维链逐步推理，所有推理完成后再输出最终JSON。

**思考链：**

1. **理解论文核心**：先想清楚——
   - 这篇论文的核心论点是什么？一句话能说清吗？
   - 为了论证这个核心论点，需要先回答哪些子问题？
   - 目标读者是谁？他们对这个问题了解多少？

2. **构建逻辑链**：思考章节之间的递进关系——
   - 每一章应该回答哪个核心问题？
   - 章节的顺序是否构成完整的论证链条？读者读完前一章后，是否自然想知道下一章的内容？
   - 各章之间是否有内容重叠或逻辑跳跃？

3. **逐章细化思考**：对每一章，想清楚——
   - 本章的具体目标是什么？（不是宽泛的介绍背景，而是具体的论证任务）
   - 需要包含哪些关键要点才能达成这个目标？
   - 需要引用哪些文献来支撑？
   - 这一章大概需要多少篇幅？

4. **自检**：输出前问自己——
   - [ ] 整体逻辑链是否完整？（引言 方法 结果 结论）
   - [ ] 每章的objective是否具体可衡量？
   - [ ] 写作要点是否具体到写什么而非泛泛的要写什么？
   - [ ] 引用文献是否合理？编号是否存在？
   - [ ] 各章之间是否有明确边界，无内容重叠？

**重要：大纲必须包含「摘要/关键词」作为第一章**，随后才是引言和各章正文。

思考完成，现在输出大纲。**只输出纯JSON数组，不要任何markdown格式标记、不要代码块包裹、不要前后说明文字。**

输出格式（严格按此JSON结构，不要添加额外字段）：
[
  {{
    "chapter": "章节标题",
    "objective": "本章要回答的核心问题（一句话）",
    "points": [
      "写作要点1（包含具体内容说明）",
      "写作要点2",
      "写作要点3"
    ],
    "ref_ids": [1, 2],
    "estimated_pages": 2
  }}
]

质量要求：
- 每个章节的写作要点必须具体可执行
- ref_ids 必须引用实际存在的文献编号
- estimated_pages 总和应与论文整体篇幅一致（课程论文约8-12页，期刊论文约6-8页）
- 整体大纲章节数量：课程论文5-6章，期刊论文6-7章"""


class OutlineAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="论文架构师",
            goal="根据文献分析结果和论文模板，设计逻辑严密、具有说服力的论文大纲，并输出标准JSON格式",
            backstory=(
                "你是一位顶级的学术论文架构师，"
                "在Nature、Science等顶刊上有丰富的审稿经验。"
                "你的核心理念是：好的论文结构不是模板填充，"
                "而是用逻辑链条说服读者。"
                "你擅长从混乱的研究素材中提炼出清晰的叙事线，"
                "让每一章都推进论证，每一段都为结论服务。"
            ),
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
            expected_output="完整的JSON格式论文大纲，包含章节标题、核心目标、写作要点、引用文献编号和预估页数",
        )
        return self._execute_task(task)
