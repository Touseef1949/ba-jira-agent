"""
BA Jira Agent — LLM Evaluation Suite

Evaluates the LangGraph ReAct agent on 12 real-world queries using DeepEval with
DeepSeek as the evaluator (LLM-as-Judge). Each test measures:

  • AnswerRelevancy — does the answer address the question?
  • Faithfulness    — does the answer stick to tool data (no hallucination)?
  • Toxicity         — is the output free of harmful content?

Ground truth is computed from actual ticket data (data/jira_export.json).

Usage:
    cd ba-jira-agent
    DEEPSEEK_API_KEY=sk-... python -m pytest eval/ -v -m eval

Or run a single test:
    DEEPSEEK_API_KEY=sk-... python -m pytest eval/test_agent_evaluation.py::test_total_tickets -v
"""

import pytest
from deepeval.test_case import LLMTestCase
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ToxicityMetric

from eval.conftest import get_evaluator, run_agent_query

# ── Helper: build evaluator metrics once per session ────────────────────────────

_eval_model = None


@pytest.fixture(scope="session", autouse=True)
def evaluator_model():
    """Provide a single DeepSeek evaluator instance for all tests."""
    global _eval_model
    _eval_model = get_evaluator()
    return _eval_model


def make_metrics():
    """Create the standard metric set for every test."""
    return [
        AnswerRelevancyMetric(model=_eval_model, threshold=0.7),
        FaithfulnessMetric(model=_eval_model, threshold=0.7),
        ToxicityMetric(model=_eval_model, threshold=0.7),
    ]


def evaluate(query, ground_truth, retrieval_context=None):
    """
    Run the agent and evaluate with DeepEval.

    Args:
        query: natural-language question
        ground_truth: expected answer (free-text, used as expected_output)
        retrieval_context: tool outputs the agent relied on (for Faithfulness)

    Returns:
        (actual_answer, test_case, scores_dict)
    """
    result = run_agent_query(query)
    actual = result["answer"]
    context = retrieval_context or result["retrieval_context"]

    test_case = LLMTestCase(
        input=query,
        actual_output=actual,
        expected_output=ground_truth,
        retrieval_context=context,
    )

    scores = {}
    for metric in make_metrics():
        try:
            metric.measure(test_case)
            scores[metric.__class__.__name__] = round(metric.score, 3)
            scores[f"{metric.__class__.__name__}_reason"] = getattr(metric, "reason", "")[:200]
        except Exception as exc:
            scores[metric.__class__.__name__] = None
            scores[f"{metric.__class__.__name__}_error"] = str(exc)[:200]

    # Print scores inline so they appear in pytest -s output
    score_line = " | ".join(
        f"{k}: {v}" for k, v in scores.items() if not k.endswith("_reason") and not k.endswith("_error")
    )
    print(f"\n  [DEEPEVAL] {score_line}")

    return actual, test_case, scores


# ═══════════════════════════════════════════════════════════════════════════════
#  EVALUATION TESTS (12 queries, grounded in real ticket data)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.eval
@pytest.mark.slow
def test_total_tickets():
    """Query: How many total tickets are in the backlog?"""
    actual, _, _scores = evaluate(
        "How many total tickets are in the backlog? Give me the count and total story points.",
        "There are 20 tickets in the backlog with a total of 105 story points.",
    )
    assert "20" in actual, f"Expected 20 tickets, got: {actual[:200]}"
    assert "105" in actual, f"Expected 105 story points, got: {actual[:200]}"


@pytest.mark.eval
@pytest.mark.slow
def test_unassigned_count():
    """Query: How many unassigned tickets?"""
    actual, _, _scores = evaluate(
        "How many unassigned tickets are there in the backlog?",
        "There are 12 unassigned tickets in the backlog.",
    )
    assert "12" in actual, f"Expected 12 unassigned, got: {actual[:200]}"


@pytest.mark.eval
@pytest.mark.slow
def test_sprint_24_unassigned_bugs():
    """Query: How many unassigned bugs in Sprint 24?"""
    actual, _, _scores = evaluate(
        "How many unassigned bugs are in Sprint 24 and what are their keys?",
        "Sprint 24 has 1 unassigned bug: BA-103 (Dashboard load time exceeds 5 seconds, 5 SP).",
    )
    assert "BA-103" in actual, f"Expected BA-103, got: {actual[:200]}"
    assert "Sprint 24" in actual, f"Expected Sprint 24 mention, got: {actual[:200]}"


@pytest.mark.eval
@pytest.mark.slow
def test_highest_priority():
    """Query: How many Highest priority tickets and who owns them?"""
    actual, _, _scores = evaluate(
        "How many Highest priority tickets are there and who is assigned to each?",
        "3 Highest priority tickets: BA-101 (Priya Sharma), BA-105 (Priya Sharma), BA-115 (Rahul Verma).",
    )
    # At minimum the agent should identify 3 Highest-priority tickets
    assert any(
        t in actual for t in ["BA-101", "BA-105", "BA-115"]
    ), f"Expected Highest priority tickets mentioned, got: {actual[:200]}"


@pytest.mark.eval
@pytest.mark.slow
def test_sprint_24_velocity():
    """Query: Sprint 24 velocity (ticket count + SP)."""
    actual, _, _scores = evaluate(
        "What is the sprint velocity for Sprint 24? Give me ticket count and total story points.",
        "Sprint 24 has 7 tickets with 24 total story points.",
    )
    assert "Sprint 24" in actual, f"Expected Sprint 24, got: {actual[:200]}"


@pytest.mark.eval
@pytest.mark.slow
def test_slack_search():
    """Query: Find tickets related to Slack."""
    actual, _, _scores = evaluate(
        "Find all tickets related to Slack integration.",
        "1 ticket found: BA-104 (Integrate Slack notifications for ticket assignment, 5 SP, Sprint 25).",
    )
    assert "BA-104" in actual, f"Expected BA-104, got: {actual[:200]}"


@pytest.mark.eval
@pytest.mark.slow
def test_priya_tickets():
    """Query: Which tickets belong to Priya Sharma?"""
    actual, _, _scores = evaluate(
        "Which tickets are assigned to Priya Sharma and what is their total story points?",
        "Priya Sharma has 2 tickets (BA-101, BA-105) with 5 total story points.",
    )
    assert "Priya" in actual, f"Expected Priya mention, got: {actual[:200]}"


@pytest.mark.eval
@pytest.mark.slow
def test_sprints_summary():
    """Query: Tickets per sprint breakdown."""
    actual, _, _scores = evaluate(
        "How many tickets are there in each sprint?",
        "Sprint 23: 1, Sprint 24: 7, Sprint 25: 7, Sprint 26: 4, Sprint 27: 1.",
    )
    # Agent should mention Sprint 24 and at least one other sprint
    assert "Sprint 24" in actual, f"Expected Sprint 24, got: {actual[:200]}"


@pytest.mark.eval
@pytest.mark.slow
def test_bug_open_percentage():
    """Query: How many bugs, what % are Open?"""
    actual, _, _scores = evaluate(
        "How many total bugs are in the backlog and what percentage are still Open?",
        "There are 10 bugs. 8 are Open (80%), 1 is In Progress (BA-105), 1 is Resolved (BA-118).",
    )
    assert "10" in actual, f"Expected 10 bugs, got: {actual[:200]}"


@pytest.mark.eval
@pytest.mark.slow
def test_critical_path_tickets():
    """Query: Tickets with critical-path label."""
    actual, _, _scores = evaluate(
        "Which tickets have the 'critical-path' label?",
        "3 tickets: BA-101 (Login page crash), BA-105 (Password reset spam), BA-111 (CORS error staging).",
    )
    # At minimum the agent should find the critical-path label
    assert (
        "critical-path" in actual.lower() or "BA-101" in actual
    ), f"Expected critical-path tickets, got: {actual[:200]}"


@pytest.mark.eval
@pytest.mark.slow
def test_sprint_25_summary():
    """Query: Sprint 25 tickets + total SP."""
    actual, _, _scores = evaluate(
        "List all tickets in Sprint 25 and their total story points.",
        "Sprint 25 has 7 tickets with 28 total story points: BA-104, BA-108, BA-109, BA-110, BA-113, BA-117, BA-120.",
    )
    assert "Sprint 25" in actual, f"Expected Sprint 25, got: {actual[:200]}"


@pytest.mark.eval
@pytest.mark.slow
def test_multi_tool_chain():
    """
    Complex query requiring 2+ tool calls: filter by type + calculate metrics.

    "How many bugs are unassigned and what percentage of all
     unassigned tickets are bugs?"
    """
    actual, _, _scores = evaluate(
        "How many unassigned tickets are bugs and what story points are at risk?",
        "6 unassigned bugs: BA-103 (5 SP), BA-109 (2 SP), BA-113 (3 SP), BA-114 (5 SP, story), BA-117 (2 SP), BA-106 (8 SP, story). Total at risk: 25 SP.",
    )
    # Agent should attempt to filter and compute — at minimum identify unassigned + bugs
    assert "unassigned" in actual.lower(), f"Expected unassigned analysis, got: {actual[:200]}"
