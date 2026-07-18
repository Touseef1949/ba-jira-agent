# Security policy

## Reporting a vulnerability

Do not disclose suspected vulnerabilities in a public issue. Use GitHub's
private vulnerability reporting for this repository, or email
`tshaik1990@gmail.com` with the subject `BA Jira Agent security report`.

Include the affected revision, reproduction steps, impact, and suggested
mitigation. You can expect acknowledgement within seven days. Do not attach
real Jira exports, access tokens, customer tickets, or provider credentials.

## Supported versions

Only the latest tagged release and current `main` branch receive security
updates.

## AI-specific risks

See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md). The public demo uses mock data
by default. Live Jira mode crosses a separate credential and customer-data
boundary and must be configured only with an approved least-privilege account.
