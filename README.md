---
title: BA Jira Agent
emoji: 🤖
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# BA Jira Agent

[Live app](https://tshaik1990-ba-jira-agent.hf.space) ·
[Case study](https://touseefshaik.com/apps/ba-jira-agent.html) ·
[Security policy](SECURITY.md) ·
[Changelog](CHANGELOG.md)

**Maturity:** public flagship, production-oriented, version 0.1.0.

BA Jira Agent helps Product Owners and delivery teams interrogate a backlog in
plain language. A LangGraph ReAct agent selects read-only Jira tools, retrieves
the relevant tickets or metrics, and returns a structured answer with a visible
reasoning trace. The public demo defaults to 20 representative mock tickets;
live Jira access is an explicit configuration.

## Product flow

1. Choose the safe mock dataset or configure an approved Jira connection.
2. Ask a backlog question such as `Which open bugs are highest priority?`.
3. Inspect the tool calls, answer, dashboard metrics, and ticket table.
4. Validate the result before using it in prioritization or delivery planning.

The [public case study](https://touseefshaik.com/apps/ba-jira-agent.html) is the
visual walkthrough.

## Architecture

```text
Streamlit UI -> query validation -> agent service -> LangGraph ReAct agent
                                              -> read-only backlog tools
Mock mode -> data/jira_export.json             -> answer + visible trace
Live mode -> Jira REST API with PAT
```

The deterministic metrics and validation layer lives in `services/`; Jira and
shared configuration in `core/`; tools in `tools.py`; deterministic tests in
`tests/`; manual model evaluation in `eval/`. See [RUNBOOK.md](RUNBOOK.md) for
deployment and incident procedures.

## Supported environment

- Python 3.13 (the Docker, CI, and supported local runtime).
- A local virtual environment and internet access for dependency installation.
- `DEEPSEEK_API_KEY` for agent queries.
- Optional Jira URL, email, and PAT for live mode; mock mode needs no Jira key.

## Reproducible quick start

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
cp .env.example .env
# add DEEPSEEK_API_KEY to .env
streamlit run app.py --server.port=8503
```

`requirements.in` declares compatible runtime dependencies. Exact runtime and
development environments are in `requirements.lock` and
`requirements-dev.lock`. `requirements.txt` makes the Docker/Hugging Face build
consume the runtime lock. Regenerate with:

```bash
uv pip compile requirements.in -o requirements.lock --python-version 3.13
uv pip compile requirements-dev.in -o requirements-dev.lock --python-version 3.13
```

## Development quality gate

```bash
python -m pip install -r requirements-dev.lock
./scripts/quality.sh
```

The command runs Ruff formatting/linting on core/service boundaries, targeted
mypy checks, compilation, deterministic tests, and the 85% coverage gate. Pull
request CI uses the same command. DeepEval is intentionally separate because it
invokes a model and can incur cost; run the manual `LLM Evaluation (DeepEval)`
workflow only with an approved key.

Safe operational checks do not call the agent:

```bash
python scripts/health_monitor.py
locust -f tests/load/locustfile.py \
  --host=https://tshaik1990-ba-jira-agent.hf.space --headless -u 10 -t 60s
```

## Versioned AI behavior

- Model: `deepseek-v4-flash` (`MODEL_ID` in `agent.py`).
- System prompt: `ba-jira-agent-system-v1` (`PROMPT_VERSION` in `agent.py`).
- Paid evaluation cases: `eval/test_agent_evaluation.py`.

Change these identifiers deliberately and record behavioral changes in the
changelog and evaluation evidence.

## Data, security, and privacy boundaries

- Tools are read-only; the agent cannot create, edit, or transition Jira issues.
- The public demo uses mock data. Live mode sends selected Jira content to the
  configured model provider.
- Use a project-scoped least-privilege PAT and never commit `.env` or real Jira
  exports.
- Treat Jira fields as untrusted input and review every generated conclusion.

See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) for controls and residual risk.

## Known limitations

- Model output can omit context or draw an incorrect conclusion.
- Live Jira behavior depends on server permissions, fields, and availability.
- The bundled mock dataset is representative, not a production-scale benchmark.
- Health/load tests prove availability only and do not measure answer quality.
- DeepEval results vary with model/provider changes and are not a deterministic
  pull-request gate.

## Release and deployment

Pull requests must pass `quality` and `security`. Stable milestones use Semantic
Versioning and [CHANGELOG.md](CHANGELOG.md). The tagged GitHub revision is then
synchronized to the Hugging Face Space and verified through the Streamlit health
endpoint and public mock-data journey.

Contributions are described in [CONTRIBUTING.md](CONTRIBUTING.md). This project
is licensed under the [MIT License](LICENSE).
