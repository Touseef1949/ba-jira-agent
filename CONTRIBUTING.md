# Contributing

1. Create a focused branch from `main`.
2. Use Python 3.13 and install `requirements-dev.lock`.
3. Add deterministic tests for observable behavior.
4. Run `./scripts/quality.sh`.
5. Open a pull request using the repository template.

Never commit real Jira exports, credentials, customer ticket text, or generated
logs. Pull-request CI must remain deterministic. DeepEval is a separate manual
workflow because it uses a model and can incur cost.
