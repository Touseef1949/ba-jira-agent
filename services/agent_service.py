"""
Agent invocation wrapper for BA Jira Agent.

Separates agent logic from the Streamlit UI layer. Provides functions
for running agent queries, loading tickets, and calculating metrics.
"""

import json
from pathlib import Path

from agent import agent as _agent
from services.error_logging import log_error


def run_agent_query(query: str) -> dict:
    """
    Run the LangGraph ReAct agent with a natural-language query.

    Args:
        query: Natural language query about the Jira backlog.

    Returns:
        dict with keys:
            - answer (str): The agent's final answer.
            - trace (list[dict]): Full ReAct trace with role and content
              for each message in the chain.
    """
    try:
        result = _agent.invoke({"messages": [{"role": "user", "content": query}]})
        messages = result.get("messages", [])

        answer = "No output returned by the agent."
        if messages:
            final = messages[-1]
            if hasattr(final, "content"):
                answer = final.content
            elif isinstance(final, dict):
                answer = final.get("content", answer)

        trace = []
        for msg in messages:
            entry: dict = {
                "role": getattr(msg, "type", "unknown"),
            }
            if hasattr(msg, "content"):
                entry["content"] = str(msg.content)
            else:
                entry["content"] = str(msg)

            # Capture tool call details if present
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "name": tc.get("name", "unknown"),
                        "args": tc.get("args", {}),
                    }
                    for tc in msg.tool_calls
                ]

            trace.append(entry)

        return {"answer": answer, "trace": trace}

    except Exception as e:
        log_error("agent", str(e), exc_info=True, context={"query": query})
        return {
            "answer": f"\u274c Agent error: {str(e)}",
            "trace": [{"role": "error", "content": str(e)}],
        }


def get_all_tickets() -> list[dict]:
    """
    Load all tickets from the Jira export JSON file.

    Returns:
        List of ticket dictionaries.
    """
    try:
        data_path = Path(__file__).resolve().parent.parent / "data" / "jira_export.json"
        with open(data_path, "r") as f:
            return json.load(f)
    except Exception as e:
        log_error("data", str(e), exc_info=True)
        return []


def get_metrics() -> dict:
    """
    Calculate summary metrics for the dashboard cards.

    Returns:
        dict with keys:
            - total: Total number of tickets.
            - total_sp: Total story points across all tickets.
            - unassigned: Count of tickets without an assignee.
            - open_bugs: Count of Bug-type tickets with status 'Open'.
    """
    try:
        tickets = get_all_tickets()
        return {
            "total": len(tickets),
            "total_sp": sum(t.get("story_points", 0) or 0 for t in tickets),
            "unassigned": sum(1 for t in tickets if not t.get("assignee")),
            "open_bugs": sum(
                1
                for t in tickets
                if t.get("type") == "Bug" and t.get("status") == "Open"
            ),
        }
    except Exception as e:
        log_error("metrics", str(e), exc_info=True)
        return {"total": 0, "total_sp": 0, "unassigned": 0, "open_bugs": 0}
