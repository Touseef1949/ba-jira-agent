# Spec: Jira Live Connect — Mock Toggle + Jira PAT Auth

**Goal:** Add a toggle that lets end users switch between mock data (default, safe) and live Jira connection via Personal Access Token (PAT). When connected to Jira, the agent queries the user's real Jira Cloud instance instead of mock JSON.

---

## Current Architecture (Before)

```
┌─────────────────────────────────────────────────────┐
│  app.py (Streamlit UI)                              │
│  ┌─────────────┐  ┌──────────────┐                 │
│  │ Hero Card   │  │ Metric Cards │                 │
│  └─────────────┘  └──────────────┘                 │
│  ┌─────────────┐  ┌──────────────┐                 │
│  │ Query Input │  │ Results Card │                 │
│  └─────────────┘  └──────────────┘                 │
└──────────┬──────────────────────────────────────────┘
           │ run_agent_query()
           ▼
┌─────────────────────────────────────────────────────┐
│  services/agent_service.py                          │
│  ┌─────────────────────────────────────────────┐   │
│  │ validate_query() → agent.invoke() → answer  │   │
│  └─────────────────────────────────────────────┘   │
└──────────┬──────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│  agent.py (LangGraph ReAct)                         │
│  DeepSeek LLM + 4 mock tools                       │
└──────────┬──────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│  tools.py                                           │
│  load_tickets ────┐                                │
│  filter_tickets ──┤ ALL read from                   │
│  search_tickets ──┤ data/jira_export.json           │
│  calculate_metrics ┘ (mock only, hardcoded path)    │
└─────────────────────────────────────────────────────┘
```

## Proposed Architecture (After)

```
┌──────────────────────────────────────────────────────────────────┐
│  app.py (Streamlit UI)                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 🔘 Data Source Toggle: [Mock Data] ←→ [Live Jira]       │    │
│  │ (When Live: show Jira URL + PAT input fields)            │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────┐  ┌──────────────┐                              │
│  │ Hero Card   │  │ Metric Cards │                              │
│  └─────────────┘  └──────────────┘                              │
│  ┌─────────────┐  ┌──────────────┐                              │
│  │ Query Input │  │ Results Card │                              │
│  └─────────────┘  └──────────────┘                              │
└──────────┬───────────────────────────────────────────────────────┘
           │ run_agent_query(query, data_source)
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  services/agent_service.py                                       │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ validate_query() → get_agent(data_source) → answer      │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────┬───────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  agent.py                                                        │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ get_agent(data_source) → LangGraph ReAct agent       │       │
│  │   mock:    tools read from jira_export.json          │       │
│  │   jira:    tools call Jira REST API via jira_client   │       │
│  └──────────────────────────────────────────────────────┘       │
└──────────┬───────────────────────────────────────────────────────┘
           │
     ┌─────┴──────────┐
     ▼                ▼
┌──────────────┐  ┌──────────────────────┐
│ tools.py     │  │ services/            │
│ (mock path)  │  │ jira_client.py (NEW) │
│              │  │                      │
│ reads from   │  │ Jira Cloud REST API  │
│ data/jira_   │  │ v3 via PAT auth      │
│ export.json  │  │                      │
│              │  │ GET /search?jql=...  │
│              │  │ GET /issue/{key}     │
│              │  │ GET /board/{id}/     │
│              │  │   sprint             │
└──────────────┘  └──────────────────────┘
```

---

## Files to Create

### 1. `services/jira_client.py` (NEW)
Jira Cloud REST API client using PAT (Bearer token) authentication.

**Functions:**
- `validate_pat(jira_url: str, pat: str, email: str) -> dict` — test PAT against Jira API, return `{valid: bool, user: str, error: str}`
- `fetch_issues(jira_url: str, pat: str, email: str, jql: str = "", max_results: int = 100) -> list[dict]` — fetch issues via `/rest/api/3/search`
- `fetch_issue(jira_url: str, pat: str, email: str, issue_key: str) -> dict` — fetch single issue
- `map_jira_issue_to_ticket(issue: dict) -> dict` — normalize Jira API response to our internal ticket dict format

**Auth:** HTTP Header `Authorization: Basic <base64(email:pat)>` for Jira Cloud.

### 2. `services/auth_service.py` (NEW)
Secure PAT handling and validation.

**Functions:**
- `validate_jira_connection(jira_url: str, pat: str, email: str) -> dict` — validate PAT and return connection status
- `mask_pat(pat: str) -> str` — mask PAT for display (show first 4 + last 4)

### 3. `core/jira_config.py` (NEW)
Jira-related configuration constants.
- `JIRA_API_VERSION = "3"`
- `JIRA_MAX_RESULTS = 100`
- `JIRA_REQUIRED_SCOPES = [...]`

---

## Files to Modify

### 4. `tools.py`
Each tool needs to accept an optional `data_source` parameter or be wrapped in a factory:
- `create_tools(data_source: str, jira_client=None) -> list` — factory that returns tools reading from the appropriate source

When `data_source="mock"`: tools read from `data/jira_export.json` (current behavior)
When `data_source="jira"`: tools call `jira_client.fetch_issues()` etc.

### 5. `agent.py`
- Add `get_agent(data_source: str = "mock", jira_config: dict | None = None) -> CompiledStateGraph`
- Factory that creates agent with either mock tools or Jira tools
- Keep backward compatibility: `agent = get_agent()` defaults to mock

### 6. `core/config.py`
- Add `JIRA_URL = os.getenv("JIRA_URL", "")`
- Add `JIRA_PAT = os.getenv("JIRA_PAT", "")`
- Add `JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")`

### 7. `services/agent_service.py`
- `run_agent_query(query, data_source="mock", jira_config=None)` — accepts data source
- `get_all_tickets(data_source="mock", jira_config=None)` — routes to mock or Jira
- `get_metrics(data_source="mock", jira_config=None)` — routes to mock or Jira

### 8. `app.py`
- Add **Data Source section** in sidebar (or below hero):
  - `st.toggle("Use Live Jira")` (default OFF → mock data)
  - When ON: show `st.text_input("Jira URL")` (e.g., `https://your-domain.atlassian.net`)
  - When ON: show `st.text_input("Email")`
  - When ON: show `st.text_input("API Token", type="password")`
  - "Test Connection" button → calls `validate_jira_connection()`
  - Connection status badge (✅ Connected / ❌ Failed / ⏳ Not tested)
- Store connection state in `st.session_state.jira_config`
- Pass data source to `run_agent_query()`, `get_all_tickets()`, `get_metrics()`

---

## Testing Checklist

### Unit Tests (new files)
- [ ] `tests/test_jira_client.py`
  - `test_map_jira_issue_to_ticket` — standard issue, issue with null fields, epic, subtask
  - `test_validate_pat_success` — mock 200 response
  - `test_validate_pat_unauthorized` — mock 401
  - `test_validate_pat_network_error` — mock connection error
  - `test_fetch_issues_empty` — no results
  - `test_fetch_issues_with_results` — normal response
  - `test_fetch_issues_jql_filter` — JQL parameter passed correctly
  - `test_map_jira_issue_missing_fields` — handles null/absent fields

- [ ] `tests/test_auth_service.py`
  - `test_validate_jira_connection_success`
  - `test_validate_jira_connection_invalid_pat`
  - `test_validate_jira_connection_bad_url`
  - `test_mask_pat_standard`
  - `test_mask_pat_short`
  - `test_mask_pat_empty`

### Integration Tests
- [ ] `tests/test_tools_jira_mode.py`
  - `test_load_tickets_jira_mode` — calls jira_client, not JSON
  - `test_filter_tickets_jira_mode` — JQL filtering
  - `test_search_tickets_jira_mode` — text search via Jira API
  - `test_calculate_metrics_jira_mode` — aggregates Jira results

### AppTests (end-to-end)
- [ ] `tests/test_app_jira_toggle.py`
  - `test_toggle_defaults_to_mock` — toggle is OFF on first load
  - `test_toggle_switches_to_jira_mode` — flipping toggle shows PAT fields
  - `test_jira_fields_hidden_in_mock_mode` — PAT fields not shown when toggle OFF
  - `test_test_connection_success` — green badge shown
  - `test_test_connection_failure` — red error shown
  - `test_metrics_load_from_mock_when_toggle_off`
  - `test_metrics_load_from_jira_when_toggle_on` — mock jira_client

---

## Constraints
- **Default = mock data**. Live Jira is opt-in per session.
- **PAT never persisted to disk**. `st.session_state` only. Clears on browser refresh.
- **No breaking changes to existing API**. `agent.py` and `agent_service.py` exports remain backward compatible.
- **Preserve all existing tests**. Current 62 tests must continue passing.
- **Security**: PAT is masked in all logs and UI displays (show first 4 + last 4 chars).
- **Jira Cloud only** (not Server/Data Center). Uses REST API v3 with Basic auth (email:PAT).
