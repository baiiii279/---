import re
from app.agents.base import BaseAgent, SharedContext
from crewai import Task


def _clean_polish_output(text: str) -> str:
    """清理润色输出中的引导语和修改说明，只保留论文正文"""
    text = re.sub(r'^.*?(?=#{1,3}\s)', '', text.strip(), count=1, flags=re.DOTALL)
    text = re.sub(r'#+\s*\*{0,2}润色后的论文全文\*{0,2}\s*\n*', '', text)
    text = re.sub(r'\n#+\s*\*{0,2}润色后的论文全文\*{0,2}\s*\n*', '\n', text)
    text = re.sub(r'\n---\n\s*#+\s*\*{0,2}修改说明\*{0,2}.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'\n#+\s+修改说明\s*\n.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'\n#+\s+主要修改.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'\n#+\s+修改总结.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'\n通过这些修改，.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


POLISH_PROMPT = """你是一位顶级的学术编辑，拥有20年学术论文润色经验，曾为众多SCI/SSCI期刊提供审稿和润色服务。

请先不要输出。按照以下四层递进思维链逐层处理全文，每一层处理完再进入下一层。

**思维链：**

**第1层思考 - 术语与措辞**：通读全文，逐句检查——
- 专业术语使用是否准确？同一概念全文用词是否统一？
- 有没有生硬的直译表达或中式英语？
- 用词搭配是否正确？
- 中英文标点是否混用？
→ 在脑中修正所有发现的问题

**第2层思考 - 句式与流畅度**：基于第1层的修改结果，逐句优化——
- 超过40字的复杂句是否需要拆分？
- 过于零碎的短句是否需要合并？
- 语序是否自然？主谓宾是否清晰？
- 是否存在指代不明的表达？
- 段落之间是否需要增加过渡词？
→ 在脑中完成所有句式调整

**第3层思考 - 逻辑与论证**：基于前两层的修改，逐段审查——
- 每段段首是否有一个明确的论点句？
- 论点→论据→分析的链条是否完整？
- 段落之间的过渡是否自然？
- 有没有重复论证或冗余内容可以删除？
- 有没有缺失的逻辑环节需要补充？
→ 在脑中重构所有逻辑问题

**第4层思考 - 格式与规范**：最终检查——
- 标题层级是否一致？（# → ## → ### 不乱跳级）
- 引用标记 [N] 是否全部保留且格式统一？
- Markdown 格式标记是否完整保留？

**自检**：输出前确认——
- [ ] 所有修改是否保留了作者的原意和写作风格？
- [ ] 是否消除了所有影响读者理解的障碍？
- [ ] 引用标记 [N] 是否一个都没少？
- [ ] 是否没有添加任何"修改说明"、"润色报告"等内容？

四层思考完成，现在只输出润色后的论文正文。

论文内容：
{content}"""


class PolishAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="学术编辑",
            goal="对论文进行术语、句式、逻辑、格式四层深度润色，只输出润色后的正文",
            backstory="""你是一位顶级学术编辑，在多家高影响因子期刊担任语言编辑。
你的工作哲学是：好的润色让读者感受不到编辑的存在——每一处修改都服务于更清晰的表达。
你从四个层次逐层处理：从最基础的术语拼写，到句子流畅度，到段落逻辑，再到全文格式规范。
你深知学术语言的核心是精准和清晰，而不是华丽和复杂。
你最自豪的能力是：在保持作者原意和写作风格的前提下，消除一切影响读者理解的障碍。""",
        )

    def run(self, context: SharedContext) -> str:
        task = Task(
            description=POLISH_PROMPT.format(content=context.content),
            agent=self._get_or_create_agent(),
            expected_output="""润色后的论文全文（仅正文，不含任何修改说明）。
从论文标题/第一章开始，保持原文的Markdown格式和引用标记不变。""",
        )
        result = self._execute_task(task)
        return _clean_polish_output(result)
