from app.agents.base import BaseAgent, SharedContext
from crewai import Task

COURSE_TEMPLATE = ["引言", "相关工作", "方法", "实验", "结论"]
JOURNAL_TEMPLATE = ["摘要/关键词", "引言", "方法论", "结果", "讨论", "参考文献"]

OUTLINE_PROMPT = """你是一位顶级的论文架构师。你的任务是基于文献分析结果和论文主题，设计一份逻辑严密、层次清晰、具有说服力的论文大纲。

论文主题：{topic}
论文类型：{template}
标准章节结构：{chapters}

文献分析摘要：
{references}

请按以下流程设计大纲：

## 第一步：主题解构
- 论文的核心论点是什么？
- 需要论证哪些子问题？
- 目标读者是谁？他们关心什么？

## 第二步：章节逻辑链设计
确保每一章回答一个核心问题，章节之间形成递进逻辑链：

1. **引言** — 为什么要研究这个问题？（研究背景 + 问题定义 + 贡献声明）
2. **相关工作/文献综述** — 已知什么？未知什么？（定位研究空白）
3. **方法论/方法** — 怎么做？（设计/实验/分析方法）
4. **实验/结果** — 做得怎样？（发现 + 证据）
5. **结论** — 所以呢？（总结 + 意义 + 未来方向）

## 第三步：逐章细化

严格按照以下JSON格式输出，每个章节包含：

```json
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
```

## 质量要求
- 每个章节的写作要点必须具体可执行（不是"介绍背景"这种空话，而是"从XX现象切入，引用文献[1][2]说明XX问题的紧迫性"这样的具体指令）
- ref_ids 必须引用实际存在的文献编号，且引用理由合理
- estimated_pages 总和应与论文整体篇幅一致（课程论文约8-12页，期刊论文约6-8页）
- 整体大纲的章节数量：课程论文5-6章，期刊论文6-7章

## 输出前自检
- [ ] 每章都有明确的objective
- [ ] 要点之间形成逻辑递进
- [ ] 引用文献编号有效
- [ ] 章节之间无内容重叠
- [ ] 覆盖了"引言→方法→结果→结论"的完整研究闭环

现在开始设计大纲。"""


class OutlineAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="论文架构师",
            goal="根据文献分析结果和论文模板，设计逻辑严密、具有说服力的论文大纲，并输出标准JSON格式",
            backstory="""你是一位顶级的学术论文架构师，在Nature、Science等顶刊上有丰富的审稿经验。
你的核心理念是：好的论文结构不是模板填充，而是用逻辑链条说服读者。
你擅长从混乱的研究素材中提炼出清晰的叙事线，
让每一章都推进论证，每一段都为结论服务。
你设计的论文结构经得起"挑刺"——每个章节安排都有其不可替代的理由。""",
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
            expected_output="JSON 格式的论文大纲，包含章节标题、核心目标、写作要点（可执行级别）、引用文献编号和预估页数",
        )
        return self._execute_task(task)
