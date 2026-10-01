"""
Test: Malformed tool responses are handled gracefully.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["ARTEFACTS_DIR"] = os.path.join(os.path.dirname(__file__), "..", "artefacts")

from app.tools.metadata import get_service_metadata
from app.tools.runbook import get_runbook


class TestMalformedToolResponse:
    def test_malformed_metadata_returns_error(self):
        """Forcing malformed metadata returns MALFORMED_METADATA error code."""
        result = get_service_metadata("order-service", _force_malformed=True)
        assert result["error"] is True
        assert result["error_code"] == "MALFORMED_METADATA"
        assert "message" in result

    def test_malformed_metadata_message_is_descriptive(self):
        """Malformed metadata error message explains what happened."""
        result = get_service_metadata("any-service", _force_malformed=True)
        assert result["error"] is True
        assert len(result["message"]) > 10  # has meaningful content

    def test_nonexistent_service_returns_service_not_found(self):
        """Requesting metadata for a non-existent service returns SERVICE_NOT_FOUND."""
        result = get_service_metadata("completely-fake-service-xyz")
        assert result["error"] is True
        assert result["error_code"] == "SERVICE_NOT_FOUND"

    def test_invalid_time_range_in_log_search(self):
        """Log search with start after end returns INVALID_TIME_RANGE."""
        from app.tools.log_search import search_logs
        result = search_logs(
            service="order-service",
            start_time="2025-07-14T03:00:00Z",  # start AFTER end
            end_time="2025-07-14T02:00:00Z",
        )
        assert result["error"] is True
        assert result["error_code"] == "INVALID_TIME_RANGE"

    def test_invalid_time_format_in_log_search(self):
        """Log search with invalid time format returns INVALID_TIME_RANGE."""
        from app.tools.log_search import search_logs
        result = search_logs(
            service="order-service",
            start_time="not-a-date",
            end_time="also-not-a-date",
        )
        assert result["error"] is True
        assert result["error_code"] == "INVALID_TIME_RANGE"

    def test_unknown_service_returns_service_not_found(self):
        """Log search for unknown service returns SERVICE_NOT_FOUND."""
        from app.tools.log_search import search_logs
        result = search_logs(
            service="unknown-service-xyz",
            start_time="2025-07-14T02:00:00Z",
            end_time="2025-07-14T03:00:00Z",
        )
        assert result["error"] is True
        assert result["error_code"] == "SERVICE_NOT_FOUND"
