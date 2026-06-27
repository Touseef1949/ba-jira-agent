"""
Agent invocation wrapper for BA Jira Agent.

Separates agent logic from the Streamlit UI layer. Provides functions
for running agent queries, loading tickets, and calculating metrics.
"""

import json
import time
from pathlib import Path

from agent import agent as _agent
from core.jira_config import DEFAULT_JQL, JIRA_MAX_RESULTS
from core.models import AgentResult, DashboardMetrics
from services.error_logging import log_error, log_latency
from services.logic import compute_metrics, validate_query


def run_agent_query(query: str, data_source: str = "mock", jira_config: dict | None = None) -> dict:
    """
    Run the LangGraph ReAct agent with a natural-language query.

    Args:
        query: Natural language query about the Jira backlog.
        data_source: "mock" for JSON data or "jira" for live Jira.
        jira_config: Jira connection configuration for live Jira mode.

    Returns:
        dict with keys:
            - answer (str): The agent's final answer.
            - trace (list[dict]): Full ReAct trace with role and content
              for each message in the chain.
    """
    # Validate the query before calling the agent
    valid, reason = validate_query(query)
    if not valid:
        return {
            "answer": f"\u274c Invalid query: {reason}",
            "trace": [{"role": "error", "content": reason}],
        }

    start = time.monotonic()
    try:
        active_agent = _agent
        if (data_source or "mock").lower() != "mock" or jira_config is not None:
            from agent import get_agent

            active_agent = get_agent(data_source=data_source, jira_config=jira_config)

        result = active_agent.invoke({"messages": [{"role": "user", "content": query}]})
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        log_latency("run_agent_query", latency_ms)

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

        # Build the AgentResult for internal use; return dict for backward compat
        agent_result = AgentResult(answer=answer, trace=trace)
        return {"answer": agent_result.answer, "trace": agent_result.trace}

    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        log_error(
            "agent",
            str(e),
            exc_info=True,
            context={"query": query},
            latency_ms=latency_ms,
        )
        return {
            "answer": f"\u274c Agent error: {str(e)}",
            "trace": [{"role": "error", "content": str(e)}],
        }


def get_all_tickets(data_source: str = "mock", jira_config: dict | None = None) -> list[dict]:
    """
    Load all normalized tickets from mock JSON or live Jira.

    Returns:
        List of ticket dictionaries.
    """
    try:
        if (data_source or "mock").lower() == "jira":
            if not jira_config:
                return []
            from services import jira_client

            issues = jira_client.fetch_issues(
                jira_config.get("jira_url", ""),
                jira_config.get("pat", ""),
                jira_config.get("email", ""),
                jql=jira_config.get("jql", DEFAULT_JQL),
                max_results=jira_config.get("max_results", JIRA_MAX_RESULTS),
                start_at=jira_config.get("start_at", 0),
            )
            return [jira_client.map_jira_issue_to_ticket(issue) for issue in issues]

        data_path = Path(__file__).resolve().parent.parent / "data" / "jira_export.json"
        with open(data_path, "r") as f:
            return json.load(f)
    except Exception as e:
        log_error("data", str(e), exc_info=True)
        return []


def get_metrics(data_source: str = "mock", jira_config: dict | None = None) -> dict:
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
        tickets = get_all_tickets(data_source=data_source, jira_config=jira_config)
        metrics: DashboardMetrics = compute_metrics(tickets)
        return {
            "total": metrics.total,
            "total_sp": metrics.total_sp,
            "unassigned": metrics.unassigned,
            "open_bugs": metrics.open_bugs,
        }
    except Exception as e:
        log_error("metrics", str(e), exc_info=True)
        return {"total": 0, "total_sp": 0, "unassigned": 0, "open_bugs": 0}
