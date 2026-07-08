"""Tests for FormatAgent."""
from unittest.mock import MagicMock, patch

import pytest

from app.agents.base import SharedContext
from app.agents.format_agent import FORMAT_PROMPT, FormatAgent


class TestFormatAgent:
    """Verify FormatAgent creation, prompt, and execution path."""

    def test_instantiation(self):
        """FormatAgent can be instantiated with correct role and goal."""
        agent = FormatAgent()
        assert agent._role == "排版编辑"
        assert "格式规则" in agent._goal
        assert "GB/T 7714" in agent._backstory

    def test_run_accepts_context_and_format_rules(self):
        """run() signature accepts SharedContext and optional format_rules."""
        agent = FormatAgent()
        context = SharedContext(
            paper_id=1, topic="测试论文", content="# 测试\n\n正文内容"
        )
        # Verify the method signature is compatible
        import inspect
        sig = inspect.signature(agent.run)
        params = list(sig.parameters.keys())
        assert "context" in params
        assert "format_rules" in params
        assert sig.parameters["format_rules"].default == ""

    @patch.object(FormatAgent, "_execute_task", return_value="# 排版后正文")
    def test_run_calls_execute_task(self, mock_execute):
        """run() calls _execute_task and returns its result."""
        agent = FormatAgent()
        context = SharedContext(
            paper_id=2, topic="AI论文", content="## 引言\n\n这是正文。"
        )
        result = agent.run(context)
        assert result == "# 排版后正文"
        mock_execute.assert_called_once()

    def test_prompt_formats_with_default_rules(self):
        """FORMAT_PROMPT uses default format_rules when none provided."""
        content = "## 引言\n\n测试内容"
        formatted = FORMAT_PROMPT.format(
            content=content,
            format_rules="默认格式：宋体小四号，首行缩进2字符，行距固定值20磅",
        )
        assert content in formatted
        assert "宋体小四号" in formatted
        assert "首行缩进" in formatted

    def test_prompt_formats_with_custom_rules(self):
        """FORMAT_PROMPT uses custom format_rules when provided."""
        content = "# 标题\n\n正文"
        custom_rules = "自定义：Times New Roman 12pt，1.5倍行距"
        formatted = FORMAT_PROMPT.format(content=content, format_rules=custom_rules)
        assert content in formatted
        assert "Times New Roman" in formatted
        assert "1.5倍行距" in formatted

    @patch.object(FormatAgent, "_execute_task")
    def test_run_passes_format_rules_to_prompt(self, mock_execute):
        """run() passes format_rules into the prompt."""
        mock_execute.return_value = "# 格式化结果"
        agent = FormatAgent()
        context = SharedContext(
            paper_id=3, topic="测试", content="# 标题\n\n正文段落"
        )
        agent.run(context, format_rules="自定义格式")
        # Verify the prompt contained the custom rules
        call_args = mock_execute.call_args[0][0]
        assert "自定义格式" in call_args.description

    def test_prompt_includes_format_markers(self):
        """FORMAT_PROMPT mentions all required format markers."""
        assert "<!-- format: ref-list -->" in FORMAT_PROMPT
        assert "<!-- format: body-text -->" in FORMAT_PROMPT
        assert "<!-- format: list -->" in FORMAT_PROMPT
        assert "<!-- format: table -->" in FORMAT_PROMPT

    def test_prompt_contains_gbt_7714(self):
        """FORMAT_PROMPT references GB/T 7714 standard."""
        assert "GB/T 7714" in FORMAT_PROMPT
