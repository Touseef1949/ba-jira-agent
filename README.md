---
title: BA Jira Agent
emoji: 🤖
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# BA Jira Agent

A LangChain ReAct agent that analyzes Jira backlogs — reasons about which tool to call, executes it, observes results, and produces structured summaries.

## Features
- 4 custom LangChain tools (load, filter, search, metrics)
- DeepSeek LLM via OpenAI-compatible API
- LangGraph ReAct orchestration
- 20 mock Jira tickets (bugs, stories, epics)
- Streamlit web UI matching BA Assistant design system
- 23 tests (unit, integration, smoke/AppTest)

## Tech Stack
- Python 3.13
- LangChain 1.3.x + LangGraph
- DeepSeek API
- Streamlit