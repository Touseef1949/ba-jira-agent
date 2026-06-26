"""
BA Jira Agent — LangChain ReAct agent backed by DeepSeek API.
Uses LangChain 1.3.x / LangGraph API (create_react_agent from langgraph.prebuilt).

Exports `agent` (compiled graph), `executor` (alias), and `run_agent(query)`.
"""

import os

from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

from tools import (
    load_tickets,
    filter_tickets,
    search_tickets,
    calculate_metrics,
)

# ── Load environment ──────────────────────────────────────────────────────────
_project_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_project_dir, ".env")
load_dotenv(_env_path, override=True)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise RuntimeError(
        "DEEPSEEK_API_KEY not found. "
        "Create a .env file in the project directory with:\n"
        "  DEEPSEEK_API_KEY=your-deepseek-api-key-here"
    )

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    api_key=DEEPSEEK_API_KEY,
    temperature=0,
)

# ── Tools ─────────────────────────────────────────────────────────────────────
tools = [load_tickets, filter_tickets, search_tickets, calculate_metrics]

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a BA Assistant AI agent. You help Product Owners analyze Jira backlogs. "
    "You have tools to load tickets, filter them, search them, and calculate metrics. "
    "Always use tools to get data before answering. "
    "Provide structured, actionable summaries."
)

# ── Agent (compiled LangGraph ReAct agent) ────────────────────────────────────
# LangChain 1.3.x: create_react_agent returns a compiled StateGraph, not AgentExecutor.
# Invoke with: agent.invoke({"messages": [{"role": "user", "content": query}]})
# Result: {"messages": [...]} — last message is the final answer.
agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT,
)

# Alias for compatibility
executor = agent


# ── Public API ────────────────────────────────────────────────────────────────
def run_agent(query: str) -> str:
    """
    Run the BA Jira agent with a natural-language query.
    Returns the agent's final answer as a string.
    """
    result = agent.invoke({
        "messages": [{"role": "user", "content": query}],
    })
    messages = result.get("messages", [])
    if messages:
        final = messages[-1]
        if hasattr(final, "content"):
            return final.content
        elif isinstance(final, dict):
            return final.get("content", "No output returned by the agent.")
    return "No output returned by the agent."