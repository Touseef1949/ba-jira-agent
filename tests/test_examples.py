"""Tests for guided UI examples and trace presentation helpers."""

from core.examples import GUIDED_EXAMPLES, QUICK_TOOL_EXAMPLES
from core.trace_summary import summarize_tool_calls


def test_guided_examples_use_skills_and_tools():
    assert len(GUIDED_EXAMPLES) >= 4
    for example in GUIDED_EXAMPLES:
        assert example.prompt
        assert example.skills
        assert "load_skill" in example.tools
        assert any(tool != "load_skill" for tool in example.tools)


def test_guided_examples_include_multi_skill_questions():
    assert any(len(example.skills) > 1 for example in GUIDED_EXAMPLES)


def test_quick_examples_are_tool_only_questions():
    assert len(QUICK_TOOL_EXAMPLES) >= 3
    assert all(prompt.strip() for prompt in QUICK_TOOL_EXAMPLES)


def test_summarize_tool_calls_preserves_order_and_deduplicates():
    trace = [
        {
            "role": "ai",
            "tool_calls": [
                {
                    "name": "load_skill",
                    "args": {"skill_name": "sprint-health-report"},
                },
                {"name": "filter_tickets", "args": {"field": "sprint"}},
            ],
        },
        {
            "role": "ai",
            "tool_calls": [
                {
                    "name": "load_skill",
                    "args": {"skill_name": "sprint-health-report"},
                },
                {"name": "calculate_metrics", "args": {}},
            ],
        },
    ]

    assert summarize_tool_calls(trace) == [
        {"name": "load_skill", "skill_name": "sprint-health-report"},
        {"name": "filter_tickets", "skill_name": ""},
        {"name": "calculate_metrics", "skill_name": ""},
    ]


def test_summarize_tool_calls_handles_empty_trace():
    assert summarize_tool_calls(None) == []
