#!/usr/bin/env python3
"""
BA Jira Agent — CLI entry point.
Two modes:
  1. Single query:  python3 run.py "Summarize all open bugs in Sprint 24"
  2. Interactive:   python3 run.py   (REPL loop, Ctrl+C to exit)
"""

import argparse
import sys

# agent.py handles .env loading and raises a clear error if key is missing
try:
    from agent import run_agent, agent
except RuntimeError as e:
    print(f"\n  ERROR: {e}\n")
    sys.exit(1)
except Exception as e:
    print(f"\n  ERROR loading agent: {e}\n")
    sys.exit(1)


BANNER = r"""
  ╔═══════════════════════════════════════════════════════════╗
  ║          BA Jira Agent — LangChain ReAct Agent            ║
  ║          DeepSeek LLM + 4 Tools + Mock Jira Data          ║
  ╚═══════════════════════════════════════════════════════════╝

  Tools available:
    1. load_tickets()         — Load all 20 tickets
    2. filter_tickets(f, v)   — Filter by status/priority/sprint/etc
    3. search_tickets(query)  — Keyword search in summary+description
    4. calculate_metrics(t)   — Backlog metrics & sprint velocity

  Example queries:
    "Summarize all open bugs in Sprint 24"
    "Which tickets are unassigned?"
    "What is the total story points in the backlog?"
    "Show me all Highest priority tickets"
    "Calculate sprint velocity metrics"

  Type your query and press Enter. Ctrl+C to exit.
"""


def run_single(query: str):
    """Run a single query and print the result."""
    print(f"\n  QUERY: {query}")
    print("  " + "=" * 60)
    try:
        answer = run_agent(query)
        print("\n  FINAL ANSWER:")
        print("  " + "-" * 60)
        print(f"  {answer}")
        print("  " + "-" * 60)
    except Exception as e:
        print(f"\n  ERROR: {e}")
    print()


def run_interactive():
    """Run an interactive REPL loop."""
    print(BANNER)
    while True:
        try:
            query = input("  > ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                print("\n  Goodbye!\n")
                break
            print("  " + "=" * 60)
            try:
                answer = run_agent(query)
                print("\n  FINAL ANSWER:")
                print("  " + "-" * 60)
                print(f"  {answer}")
                print("  " + "-" * 60)
            except Exception as e:
                print(f"\n  ERROR: {e}")
            print()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Goodbye!\n")
            break


def main():
    parser = argparse.ArgumentParser(
        description="BA Jira Agent — analyze mock Jira backlog with LangChain ReAct agent"
    )
    parser.add_argument(
        "query",
        nargs="*",
        help='Query string (omit for interactive mode). Example: "Summarize all open bugs in Sprint 24"',
    )
    args = parser.parse_args()

    if args.query:
        # Single query mode — join multiple args into one string
        query = " ".join(args.query)
        run_single(query)
    else:
        # Interactive REPL mode
        run_interactive()


if __name__ == "__main__":
    main()