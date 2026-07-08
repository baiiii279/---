from app.agents.base import BaseAgent, SharedContext
from crewai import Task

WRITE_PROMPT = """你是学术写手。按以下要求撰写论文正文：

论文主题：{topic}
大纲参考：{outline}
可用文献：{references}

格式要求：
1. 开头：论文题目（居中），然后单独一行写「摘要」（后面不要跟内容），下一行写摘要正文200-300字，再下一行写「关键词」（后面不要跟内容），再下一行写3-5个关键词，词间空两格
2. 章节：用「第一章 引言」「第二章 相关工作」格式，每章之下用「1.1 节标题」格式分节
3. 段落：每段5-8句，段首为论点句，论点+论据+分析结构
4. 引用：用[N]、[N-M]格式，只能引用上方列出的文献，绝对禁止编造不存在的参考文献
5. 字数：摘要200-300字，引言600-800字，每章1000-1500字，结论500-700字，全文5000-7000字
6. 语言：学术正式，一般现在时，避免口语化和空泛套话

从论文题目开始直接输出正文，不要输出任何思考过程、规划或自检内容。"""


class WriteAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="学术写手",
            goal="按大纲撰写完整学术论文，以摘要开头，逻辑严谨论证充分",
            backstory="高产学术写手，擅长将研究思路转化为规范学术表达。",
        )

    def run(self, context: SharedContext) -> str:
        refs_text = "\n".join(
            f"[{i+1}] {r['title']}. {r.get('authors', '未知')}. {r.get('source', '')}"
            for i, r in enumerate(context.references)
        )
        # 明确告诉 LLM 只能引用这些文献
        ref_warning = f"\n\n可用文献共{len(context.references)}篇，编号[{1}-{len(context.references)}]，只能引用这些。"
        outline_text = str(context.outline) if isinstance(context.outline, str) else \
            "\n".join(f"- {c.get('chapter', '?')}: {c.get('objective', '')}" for c in (context.outline or []))
        task = Task(
            description=WRITE_PROMPT.format(
                topic=context.topic,
                outline=outline_text,
                references=refs_text + ref_warning,
            ),
            agent=self._get_or_create_agent(),
            expected_output="完整学术论文正文，以题目和摘要开头，包含引言、正文各章、结论和参考文献",
        )
        return self._execute_task(task)
