"""
Locust load test for BA Jira Agent.

Tests only non-LLM endpoints (health/GUI only, no agent invocation).
Run with:

    cd ba-jira-agent
    locust -f tests/load/locustfile.py --host=https://tshaik1990-ba-jira-agent.hf.space

Or for local dev:

    locust -f tests/load/locustfile.py --host=http://localhost:8503

Recommended: 10 concurrent users, 60s run time:
    locust -f tests/load/locustfile.py --host=http://localhost:8503 --headless -u 10 -t 60s
"""

from locust import HttpUser, task, between


class BAJiraAgentUser(HttpUser):
    """
    Simulates user traffic hitting the BA Jira Agent web app.

    Only tests non-LLM endpoints — no agent invocation.
    """

    # Wait 1-3 seconds between tasks (simulates real user think time)
    wait_time = between(1, 3)

    @task(3)
    def health_check(self):
        """
        GET / — verify the main page loads with HTTP 200.

        Weight 3: higher frequency since this is the main endpoint.
        """
        with self.client.get("/", timeout=30, catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Expected 200, got {resp.status_code}")

    @task(1)
    def health_check_page_content(self):
        """
        GET / — verify the page body contains 'BA Jira Agent'.

        Weight 1: lower frequency; validates content integrity.
        Performed as a separate task for cleaner failure rate stats.
        """
        with self.client.get("/", timeout=30, catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Expected 200, got {resp.status_code}")
            elif "BA Jira Agent" not in resp.text:
                resp.failure("Page does not contain 'BA Jira Agent'")
            else:
                resp.success()
