import re
from app.agents.base import BaseAgent, SharedContext
from crewai import Task


def _clean_polish_output(text: str) -> str:
    """清理润色输出中的引导语和修改说明"""
    text = re.sub(r'^.*?(?=#{1,3}\s|第[一二三四五六七八九十\d]+章)', '', text.strip(), count=1, flags=re.DOTALL)
    text = re.sub(r'#+\s*\*{0,2}润色.*?\*{0,2}\s*\n*', '', text)
    text = re.sub(r'\n---\n.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'\n#+\s+修改说明\s*\n.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'\n#+\s+修改[总归].*$', '', text, flags=re.DOTALL)
    text = re.sub(r'\n通过这些修改.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


POLISH_PROMPT = """你是学术编辑。对以下论文进行润色：统一术语、优化句式流畅度、消除重复表达、修正语病。保留所有引用标记[N]不变，保留原作者语气和观点。只输出润色后的论文正文，不要添加任何修改说明或润色报告。

论文内容：
{content}"""


class PolishAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="学术编辑",
            goal="润色论文语言，提升流畅度和学术规范性，只输出润色后正文",
            backstory="顶级学术编辑，精通学术写作规范。你的信条：好的润色让读者感受不到编辑的存在。",
        )

    def run(self, context: SharedContext) -> str:
        task = Task(
            description=POLISH_PROMPT.format(content=context.content),
            agent=self._get_or_create_agent(),
            expected_output="润色后论文全文（仅正文，含引用标记，无修改说明）",
        )
        return _clean_polish_output(self._execute_task(task))
