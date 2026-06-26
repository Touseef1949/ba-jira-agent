"""
Unit tests for the 4 LangChain @tool functions.

Covers load_tickets, filter_tickets, search_tickets, and calculate_metrics.
Each tool is a LangChain StructuredTool — call via .invoke({...}).
"""

import pytest

from tools import load_tickets, filter_tickets, search_tickets, calculate_metrics


# ── load_tickets ───────────────────────────────────────────────────────────────

class TestLoadTickets:
    """Tests for the load_tickets() tool."""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_load_tickets_returns_string(self):
        """load_tickets should return a non-empty string."""
        result = load_tickets.invoke({})
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit
    def test_load_tickets_has_all_20(self, ticket_data):
        """load_tickets should contain data for all 20 tickets."""
        result = load_tickets.invoke({})
        assert "Total tickets: 20" in result
        # All 20 keys should appear in the output
        for ticket in ticket_data:
            assert ticket["key"] in result

    @pytest.mark.unit
    def test_load_tickets_contains_ticket_keys(self, ticket_data):
        """load_tickets output should contain every known ticket key."""
        result = load_tickets.invoke({})
        keys = {t["key"] for t in ticket_data}
        assert keys == {
            "BA-101", "BA-102", "BA-103", "BA-104", "BA-105",
            "BA-106", "BA-107", "BA-108", "BA-109", "BA-110",
            "BA-111", "BA-112", "BA-113", "BA-114", "BA-115",
            "BA-116", "BA-117", "BA-118", "BA-119", "BA-120",
        }
        for key in keys:
            assert key in result


# ── filter_tickets ─────────────────────────────────────────────────────────────

class TestFilterTickets:
    """Tests for the filter_tickets(field, value) tool."""

    @pytest.mark.unit
    def test_filter_tickets_by_status_open(self):
        """Filtering by status 'Open' should return open tickets."""
        result = filter_tickets.invoke({"field": "status", "value": "Open"})
        assert "Found" in result
        assert "status matches 'Open'" in result
        assert "BA-101" in result
        assert "BA-103" in result

    @pytest.mark.unit
    def test_filter_tickets_by_priority_highest(self):
        """Filtering by priority 'Highest' should return highest-priority tickets."""
        result = filter_tickets.invoke({"field": "priority", "value": "Highest"})
        assert "Found" in result
        assert "priority matches 'Highest'" in result
        assert "BA-101" in result
        assert "BA-105" in result
        assert "BA-115" in result

    @pytest.mark.unit
    def test_filter_tickets_by_type_bug(self):
        """Filtering by type 'Bug' should return only Bug tickets."""
        result = filter_tickets.invoke({"field": "type", "value": "Bug"})
        assert "Found" in result
        assert "type matches 'Bug'" in result
        assert "BA-101" in result
        assert "BA-103" in result
        # Should NOT contain Story tickets
        assert "BA-102" not in result

    @pytest.mark.unit
    def test_filter_tickets_unassigned(self):
        """Filtering by assignee 'unassigned' should return unassigned tickets."""
        result = filter_tickets.invoke({"field": "assignee", "value": "unassigned"})
        assert "Found" in result
        assert "assignee matches 'unassigned'" in result
        assert "BA-103" in result  # null assignee, Open Bug

    @pytest.mark.unit
    def test_filter_tickets_invalid_field(self):
        """Filtering by an invalid field should return an error message."""
        result = filter_tickets.invoke({"field": "colour", "value": "red"})
        assert "Error" in result
        assert "field 'colour' is not supported" in result
        assert "Valid fields" in result


# ── search_tickets ─────────────────────────────────────────────────────────────

class TestSearchTickets:
    """Tests for the search_tickets(query) tool."""

    @pytest.mark.unit
    def test_search_tickets_finds_match(self):
        """Searching for 'Slack' should return matching tickets."""
        result = search_tickets.invoke({"query": "Slack"})
        assert "Found" in result
        assert "matching 'Slack'" in result
        assert "BA-104" in result  # Slack notifications ticket

    @pytest.mark.unit
    def test_search_tickets_no_match(self):
        """Searching for a nonsense term should return no-match message."""
        result = search_tickets.invoke({"query": "xyznonexistent12345"})
        assert "No tickets found" in result
        assert "matching search query 'xyznonexistent12345'" in result


# ── calculate_metrics ──────────────────────────────────────────────────────────

class TestCalculateMetrics:
    """Tests for the calculate_metrics(metric_type) tool."""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_calculate_metrics_summary(self):
        """Metrics summary should show total tickets, story points, unassigned."""
        result = calculate_metrics.invoke({"metric_type": "summary"})
        assert "=== BACKLOG SUMMARY ===" in result
        assert "Total Tickets:" in result
        assert "Total Story Points:" in result
        assert "Unassigned Tickets:" in result
        assert "By Type:" in result
        # Should NOT contain other sections
        assert "=== BY PRIORITY ===" not in result
        assert "=== BY STATUS ===" not in result
        assert "=== BY SPRINT" not in result

    @pytest.mark.integration
    def test_calculate_metrics_all(self):
        """Metrics 'all' should include every section."""
        result = calculate_metrics.invoke({"metric_type": "all"})
        assert "=== BACKLOG SUMMARY ===" in result
        assert "=== BY PRIORITY ===" in result
        assert "=== BY STATUS ===" in result
        assert "=== BY SPRINT (Velocity) ===" in result

    @pytest.mark.unit
    def test_calculate_metrics_sprint(self):
        """Sprint metrics should show velocity data per sprint."""
        result = calculate_metrics.invoke({"metric_type": "sprint"})
        assert "=== BY SPRINT (Velocity) ===" in result
        assert "Sprint 24" in result
        assert "tickets" in result
        assert "story points" in result
        # Should NOT include summary section
        assert "=== BACKLOG SUMMARY ===" not in result

    @pytest.mark.unit
    def test_calculate_metrics_invalid_type(self):
        """Invalid metric_type should return an error."""
        result = calculate_metrics.invoke({"metric_type": "bogus"})
        assert "Error" in result
        assert "metric_type 'bogus' is not supported" in result
        assert "Valid types" in result


# ── Regression tests ───────────────────────────────────────────────────────────


class TestRegression:
    """Regression tests with @pytest.mark.regression marker."""

    @pytest.mark.regression
    def test_regression_load_tickets_consistent(self):
        """load_tickets should return identical output across two calls."""
        result1 = load_tickets.invoke({})
        result2 = load_tickets.invoke({})

        assert result1 == result2
        assert len(result1) > 0
        assert "Total tickets:" in result1

    @pytest.mark.regression
    def test_regression_filter_tickets_case_insensitive(self):
        """filter_tickets should be case-insensitive for the value field."""
        result_lower = filter_tickets.invoke({"field": "type", "value": "bug"})
        result_upper = filter_tickets.invoke({"field": "type", "value": "BUG"})
        result_mixed = filter_tickets.invoke({"field": "type", "value": "Bug"})

        # All three should return the same number of results
        # Note: the value display text differs (bug/BUG/Bug) so outputs aren't identical,
        # but all three should find the same tickets
        assert "Found" in result_lower
        assert "Found" in result_upper
        assert "Found" in result_mixed

    @pytest.mark.regression
    def test_regression_calculate_metrics_deterministic(self):
        """calculate_metrics('all') should be deterministic across calls."""
        result1 = calculate_metrics.invoke({"metric_type": "all"})
        result2 = calculate_metrics.invoke({"metric_type": "all"})

        assert result1 == result2
        assert "=== BACKLOG SUMMARY ===" in result1
        assert "Total Tickets:" in result1


# ── filter_tickets — no matches ─────────────────────────────────────────────

@pytest.mark.unit
def test_filter_tickets_no_match():
    """filter_tickets should return 'No tickets found' for an impossible match."""
    result = filter_tickets.invoke({"field": "assignee", "value": "ZZZZ_NONEXISTENT_PERSON_999"})
    assert "No tickets found" in result


# ── calculate_metrics — invalid metric_type ──────────────────────────────────

@pytest.mark.unit
def test_calculate_metrics_invalid_type():
    """calculate_metrics should error on unsupported metric_type."""
    result = calculate_metrics.invoke({"metric_type": "foobar"})
    assert "Error" in result
    assert "not supported" in result
