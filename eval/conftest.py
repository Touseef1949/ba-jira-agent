"""
Shared fixtures for BA Jira Agent LLM evaluation suite.

Uses DeepEval 4.x with DeepSeek as the evaluator (LLM-as-Judge).
Does NOT consume DeepSeek credits during collection — only during test runs.
"""

import json
import os
from pathlib import Path

import pytest

# ── DeepSeek evaluator (created lazily to avoid imports during collection) ──────

_evaluator = None


def get_evaluator():
    """Lazy-init the DeepSeek evaluator model for DeepEval metrics."""
    global _evaluator
    if _evaluator is not None:
        return _evaluator

    from deepeval.models import DeepSeekModel

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY not set in environment. "
            "Set it before running eval tests."
        )
    _evaluator = DeepSeekModel(
        model="deepseek-v4-flash",
        api_key=api_key,
    )
    return _evaluator


# ── Agent runner ────────────────────────────────────────────────────────────────


def run_agent_query(query: str) -> dict:
    """
    Run the BA Jira Agent and return structured output.

    Returns dict with:
        answer  — final agent answer (str)
        trace   — list of message dicts from agent.invoke
        tool_outputs — concatenated tool output strings (for retrieval_context)
    """
    # Add project root to sys.path for imports
    import sys

    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from dotenv import load_dotenv

    env_path = project_root / ".env"
    load_dotenv(env_path, override=True)

    from agent import agent as _agent

    result = _agent.invoke({"messages": [{"role": "user", "content": query}]})
    messages = result.get("messages", [])

    answer = "No output returned by the agent."
    tool_outputs = []

    for msg in messages:
        # Collect tool outputs
        if hasattr(msg, "type") and msg.type == "tool":
            content = getattr(msg, "content", "")
            if content:
                tool_outputs.append(str(content))

        # Last message is the final AI answer
        if hasattr(msg, "type") and msg.type == "ai":
            content = getattr(msg, "content", "")
            if content:
                answer = str(content)

    return {
        "answer": answer,
        "trace": [
            {
                "role": getattr(m, "type", "unknown"),
                "content": str(getattr(m, "content", str(m))),
            }
            for m in messages
        ],
        "tool_outputs": tool_outputs,
        "retrieval_context": tool_outputs,  # alias for DeepEval
    }


# ── Ground-truth helpers ────────────────────────────────────────────────────────

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "jira_export.json"


@pytest.fixture(scope="session")
def ticket_data():
    """Load the 20 mock Jira tickets."""
    with open(DATA_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def ticket_map():
    """Index tickets by key for fast lookup."""
    with open(DATA_PATH, "r") as f:
        tickets = json.load(f)
    return {t["key"]: t for t in tickets}


# ── Pytest markers ──────────────────────────────────────────────────────────────


def pytest_configure(config):
    config.addinivalue_line("markers", "eval: LLM evaluation tests (calls evaluator API)")
    config.addinivalue_line("markers", "slow: evaluation tests (10-20s each)")
