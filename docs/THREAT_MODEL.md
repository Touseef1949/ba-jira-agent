# AI threat model

## Protected assets

- Jira tickets, backlog metrics, search results, and agent traces
- Jira URL, account email, personal access token, and DeepSeek key
- system prompt, model identifier, evaluation cases, logs, and deployment state

## Trust boundaries

User queries and Jira fields are untrusted text. Mock JSON or Jira API data is
passed through deterministic tools before selected content is provided to the
model. The model response and trace return to the Streamlit UI. Jira, DeepSeek,
and Hugging Face are external services with separate access and retention rules.

## Principal threats and controls

| Threat | Control |
| --- | --- |
| Prompt injection in a query or Jira field | Query guard, tool-first system prompt, bounded tools, no model access to secrets, and human review. |
| Jira credential or ticket disclosure | Environment secrets, git ignores, push protection, Gitleaks, masked display, and mock mode as the public default. |
| Cross-project or over-privileged Jira access | Explicit Jira configuration, least-privilege PAT, and project-scoped server permissions. |
| Incorrect backlog conclusions | Tool-grounded metrics and ticket retrieval, visible trace, deterministic tests, and no autonomous Jira writes. |
| Cost or denial-of-wallet abuse | Explicit user invocation, input limits, provider monitoring, and non-LLM health/load checks. |
| Dependency or workflow compromise | Exact locks, Dependabot, immutable action pins, and read-only workflow permissions. |

## Privacy boundary

Do not use live mode with tickets containing regulated or customer-sensitive
data unless both the Jira and model-provider flows are approved. The agent is
read-only: it analyzes backlog data and does not create, edit, or transition
Jira issues.

## Residual risk

The model can omit context, infer incorrectly, or be influenced by adversarial
ticket text. Outputs support backlog analysis; they do not replace Product
Owner judgement, security review, or delivery decisions.
