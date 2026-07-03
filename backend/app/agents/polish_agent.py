import re
from app.agents.base import BaseAgent, SharedContext
from crewai import Task


def _clean_polish_output(text: str) -> str:
    """清理润色输出中的引导语和修改说明，只保留论文正文"""
    # 去掉开头的引导语（如"好的，以下是为您润色后的论文全文及修改说明"）
    text = re.sub(
        r'^.*?(?=#{1,3}\s)',
        '',
        text.strip(),
        count=1,
        flags=re.DOTALL,
    )
    # 去掉 "润色后的论文全文" 等中间标记
    text = re.sub(r'#+\s*\*{0,2}润色后的论文全文\*{0,2}\s*\n*', '', text)
    text = re.sub(r'\n#+\s*\*{0,2}润色后的论文全文\*{0,2}\s*\n*', '\n', text)
    # 去掉末尾的修改说明（从 "---" 分隔线后的内容，或 "修改说明" 段落开始）
    text = re.sub(
        r'\n---\n\s*#+\s*\*{0,2}修改说明\*{0,2}.*$',
        '',
        text,
        flags=re.DOTALL,
    )
    # 也匹配末尾 "## 修改说明" 或 "### 修改说明"（不带分隔线的情况）
    text = re.sub(
        r'\n#+\s+修改说明\s*\n.*$',
        '',
        text,
        flags=re.DOTALL,
    )
    # 去掉末尾的"通过这些修改，论文的学术表达..."等总结语
    text = re.sub(
        r'\n通过这些修改，.*$',
        '',
        text,
        flags=re.DOTALL,
    )
    # 去掉多余的空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

POLISH_PROMPT = """你是一位学术编辑，请对以下论文进行润色。

润色要求：
1. 提升学术语言流畅度
2. 检测重复表达并改写
3. 统一术语和时态
4. 改进句子结构

严格遵循以下输出规范：
- 保留所有引用标记 [N] 不变
- 只输出润色后的论文正文，不要添加任何前言、后记、修改说明、润色报告等内容
- 不要添加"好的"、"以下是润色后的论文"等引导语
- 直接从论文标题开始输出

论文内容：
{content}"""


class PolishAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="学术编辑",
            goal="提升论文的语言质量、流畅度和学术规范性，只输出润色后的论文正文",
            backstory="你是一位严谨的学术编辑，精通学术写作规范和语言润色技巧。你只输出润色后的论文正文，绝不添加任何修改说明或润色报告。",
        )

    def run(self, context: SharedContext) -> str:
        task = Task(
            description=POLISH_PROMPT.format(content=context.content),
            agent=self._get_or_create_agent(),
            expected_output="润色后的论文全文（不包含任何修改说明或润色报告，直接从论文标题开始）",
        )
        result = self._execute_task(task)
        # 清理可能的引导语和修改说明
        return _clean_polish_output(result)
