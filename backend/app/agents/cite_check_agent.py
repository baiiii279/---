from app.agents.base import BaseAgent, SharedContext
from crewai import Task

CITE_CHECK_PROMPT = """你是引用审查员。检查以下论文的引用质量：

1. 引用缺失：正文中统计数据、他人观点是否有[N]引用标记
2. 引用准确：[N]编号是否与文献列表一一对应，有无跳号
3. 引用充分：核心论点是否有足够文献支撑，是否过度集中引用
4. 格式统一：引用标记格式是否一致

输出结构化报告：
## 引用检查报告
### 通过项
### 问题列表
| 类型 | 位置 | 描述 | 严重度 | 建议 |
### 统计
- 引用总数: N, 文献数: M
### 优化建议

严重度：高(必须修)/中(建议修)/低(可优化)

论文：
{content}

文献：
{references}"""


class CiteCheckAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="引用审查员",
            goal="检查引用完整性、准确性和格式规范，输出结构化报告",
            backstory="学术期刊引用审查员，对学术诚信有近乎偏执的坚持。",
        )

    def run(self, context: SharedContext) -> str:
        refs_text = "\n".join(
            f"[{i+1}] {r['title']}. {r.get('authors', '未知')}. {r.get('source', '')}"
            for i, r in enumerate(context.references)
        )
        content = context.polished_content or context.content
        task = Task(
            description=CITE_CHECK_PROMPT.format(content=content, references=refs_text),
            agent=self._get_or_create_agent(),
            expected_output="结构化引用检查报告，含通过项、问题列表、统计和优化建议",
        )
        return self._execute_task(task)
