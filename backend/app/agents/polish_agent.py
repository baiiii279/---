from app.agents.base import BaseAgent, SharedContext
from crewai import Task

POLISH_PROMPT = """你是一位学术编辑，请对以下论文进行润色。

润色要求：
1. 提升学术语言流畅度
2. 检测重复表达并改写
3. 统一术语和时态
4. 改进句子结构

保留所有引用标记 [N] 不变。

论文内容：
{content}

请输出润色后的全文，并在末尾附上修改说明。"""


class PolishAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="学术编辑",
            goal="提升论文的语言质量、流畅度和学术规范性",
            backstory="你是一位严谨的学术编辑，精通学术写作规范和语言润色技巧。",
        )

    def run(self, context: SharedContext) -> str:
        task = Task(
            description=POLISH_PROMPT.format(content=context.content),
            agent=self.agent,
            expected_output="润色后的论文全文及修改说明",
        )
        return self._execute_task(task)
