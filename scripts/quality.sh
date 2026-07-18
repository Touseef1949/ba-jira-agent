#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-sk-dummy-key-for-tests}"

"${PYTHON_BIN}" -m ruff format --check core services scripts
"${PYTHON_BIN}" -m ruff check core services scripts
"${PYTHON_BIN}" -m mypy core/models.py services/logic.py
"${PYTHON_BIN}" -m py_compile app.py agent.py tools.py run.py
"${PYTHON_BIN}" -m pytest --cov=. --cov-report=term-missing --cov-fail-under=85 \
  -W ignore::pytest.PytestUnknownMarkWarning
