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

请对以下论文进行四层深度润色：

## 第一层：术语与措辞（语言层面）
- 检查专业术语的使用是否准确一致（同一概念全文统一用词）
- 替换不恰当的直译表达和生硬的中式英语
- 纠正用词不当、搭配错误（如"提高问题"→"解决问题"）
- 统一拼写和标点符号（中英文标点不混用）

## 第二层：句式与流畅度（句子层面）
- 拆分过长的复合句（超过40字的句子考虑拆分）
- 合并过于零碎的短句，增强连贯性
- 调整语序不当的句子，使主谓宾清晰
- 消除歧义表达和指代不明
- 增加必要的过渡词和连接词

## 第三层：逻辑与论证（段落层面）
- 检查每段是否有一个明确的论点句
- 论点→论据→分析的逻辑链条是否完整
- 段落之间的过渡是否自然
- 识别并删除重复论证和冗余内容
- 识别并补充缺失的逻辑环节

## 第四层：格式与规范（全文层面）
- 保持标题层级一致性
- 保留所有引用标记 [N] 不变，确保格式统一
- 保持参考文献编号不变
- 保留所有 Markdown 格式标记（#、##、-、**等）

## 输出规范（严格遵循）
- **只输出润色后的论文正文**
- 不要添加任何前言、后记、修改说明、润色报告、修改总结等内容
- 不要以"好的"、"以下是润色后的论文"、"修改完成"等开头
- 直接从论文标题（第一章）开始输出
- 禁止在文末添加"修改说明"、"修改总结"等章节

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
