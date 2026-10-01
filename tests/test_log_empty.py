"""
Test: Empty log result handled gracefully.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["ARTEFACTS_DIR"] = os.path.join(os.path.dirname(__file__), "..", "artefacts")

from app.tools.log_search import search_logs


class TestEmptyLogResult:
    def test_empty_result_returns_empty_records(self):
        """Query returning no results has empty records list and EMPTY_RESULT code."""
        result = search_logs(
            service="api-gateway",
            start_time="2020-01-01T00:00:00Z",
            end_time="2020-01-01T01:00:00Z",  # no logs in this window
        )
        # Either EMPTY_RESULT or no error with empty records
        assert isinstance(result["records"], list)
        assert len(result["records"]) == 0
        assert result["total_matched"] == 0
        assert result["error_code"] == "EMPTY_RESULT"

    def test_empty_result_with_keyword_no_match(self):
        """Keyword search with no matches returns EMPTY_RESULT gracefully."""
        result = search_logs(
            service="order-service",
            start_time="2025-07-14T01:00:00Z",
            end_time="2025-07-14T03:00:00Z",
            keyword="xyzzy_nonexistent_keyword_12345",
        )
        assert isinstance(result["records"], list)
        assert len(result["records"]) == 0
        assert result["error_code"] == "EMPTY_RESULT"

    def test_empty_result_has_query_summary(self):
        """Empty result still includes a query_summary field."""
        result = search_logs(
            service="api-gateway",
            start_time="2020-01-01T00:00:00Z",
            end_time="2020-01-01T01:00:00Z",
        )
        assert "query_summary" in result
        assert isinstance(result["query_summary"], str)
