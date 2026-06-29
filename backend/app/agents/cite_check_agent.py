from app.agents.base import BaseAgent, SharedContext
from crewai import Task

CITE_CHECK_PROMPT = """你是一位严谨的学术审计员，请检查以下论文的引用情况。

检查要求：
1. 是否每个引用标记 [N] 都有对应的参考文献
2. 引用格式是否统一
3. 是否有需要补充引用的论断

论文内容：
{content}

参考文献列表：
{references}

请输出检查报告，列出发现的问题及修正建议。"""


class CiteCheckAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="学术审计员",
            goal="检查论文引用准确性和格式规范性",
            backstory="你是一位严谨的学术审计员，专注发现引用问题。",
        )

    def run(self, context: SharedContext) -> str:
        refs_text = "\n".join(
            f"[{i+1}] {r['title']}" for i, r in enumerate(context.references)
        )
        content = context.polished_content or context.content
        task = Task(
            description=CITE_CHECK_PROMPT.format(content=content, references=refs_text),
            agent=self.agent,
            expected_output="引用检查报告，包含问题列表和修正建议",
        )
        return task.execute()
