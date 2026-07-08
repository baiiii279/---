from app.agents.base import BaseAgent, SharedContext
from crewai import Task

WRITE_PROMPT = """你是一篇学术论文。现在开始，直接输出以下结构的论文正文。

输出格式（严格按此顺序）：

# 论文题目
[摘要] 这里写摘要内容，200-300字。

[关键词] 关键词1  关键词2  关键词3

# 第一章 引言
正文内容...

## 第X节 节标题
正文内容...

# 参考文献
[1] 作者. 题名[J]. 刊名, 年.
（列出不少于10条）

---
论文主题：{topic}
大纲参考：{outline}
可用文献：{references}

规则：摘要200-300字，引言550-700字，每段5-8句。引用用[N]格式。不要输出任何思考过程、计划、自检。直接从论文题目开始。"""


class WriteAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="学术写手",
            goal="根据大纲撰写完整的学术论文正文，以摘要开头，逻辑严谨论证充分",
            backstory="你是一位学术写手，直接输出论文正文，无需任何前言后记。",
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
