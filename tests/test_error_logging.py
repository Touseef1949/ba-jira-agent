"""
Unit tests for services/error_logging.py — edge cases and error paths.
"""
import json
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from services.error_logging import (
    get_latency_stats,
    get_recent_errors,
    log_error,
    log_latency,
)


# ── log_error — OSError during file write ──────────────────────────────────

@pytest.mark.unit
def test_log_error_oserror_is_silent():
    """log_error should silently ignore OSError during file write."""
    with patch("builtins.open", side_effect=OSError("disk full")):
        # Should not raise
        log_error("test", "disk error", exc_info=False)


# ── get_latency_stats — no operation filter ────────────────────────────────

@pytest.mark.unit
def test_get_latency_stats_all_operations():
    """get_latency_stats without operation filter should aggregate all samples."""
    # Clear buffer and add samples
    from services.error_logging import _latency_buffer
    _latency_buffer.clear()
    log_latency("op_a", 10.0)
    log_latency("op_b", 20.0)
    log_latency("op_a", 30.0)
    stats = get_latency_stats()  # no operation filter
    assert stats["samples"] == 3
    assert stats["p50_ms"] is not None
    assert stats["min_ms"] == 10.0
    assert stats["max_ms"] == 30.0
    assert stats["operation"] is None


# ── get_latency_stats — empty buffer ───────────────────────────────────────

@pytest.mark.unit
def test_get_latency_stats_empty_buffer():
    """get_latency_stats should return None values when buffer is empty."""
    from services.error_logging import _latency_buffer
    _latency_buffer.clear()
    stats = get_latency_stats()
    assert stats["samples"] == 0
    assert stats["p50_ms"] is None
    assert stats["min_ms"] is None
    assert stats["max_ms"] is None


# ── _percentile — empty list edge case (filtered operation with no samples) ──

@pytest.mark.unit
def test_percentile_empty_filtered_list_returns_zero():
    """_percentile should return 0.0 for empty filtered list (operation with no data)."""
    from services.error_logging import _latency_buffer
    _latency_buffer.clear()
    log_latency("op_a", 10.0)  # add sample for op_a
    # Request stats for an operation with no data
    stats = get_latency_stats(operation="nonexistent")
    assert stats["samples"] == 0
    assert stats["p50_ms"] is None


# ── _percentile — single element (hits last-element return) ─────────────────

@pytest.mark.unit
def test_percentile_single_element():
    """get_latency_stats with 1 sample should return that value for all percentiles."""
    from services.error_logging import _latency_buffer
    _latency_buffer.clear()
    log_latency("op_solo", 42.0)
    stats = get_latency_stats()
    assert stats["samples"] == 1
    assert stats["p50_ms"] == 42.0
    assert stats["p95_ms"] == 42.0
    assert stats["p99_ms"] == 42.0


# ── get_recent_errors — file read error ────────────────────────────────────

@pytest.mark.unit
def test_get_recent_errors_oserror():
    """get_recent_errors should return empty list on OSError."""
    with patch("builtins.open", side_effect=OSError("no such file")):
        result = get_recent_errors()
    assert result == []


@pytest.mark.unit
def test_get_recent_errors_json_decode_error():
    """get_recent_errors should return empty list on JSON decode error."""
    with patch("builtins.open", mock_open(read_data="not valid json\n")):
        result = get_recent_errors()
    assert result == []
