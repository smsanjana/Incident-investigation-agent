"""
Test: Successful retrieval from all three tool types.
Covers: search_logs, get_runbook, get_service_metadata, get_deployment_events
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["ARTEFACTS_DIR"] = os.path.join(os.path.dirname(__file__), "..", "artefacts")

from app.tools.log_search import search_logs
from app.tools.runbook import get_runbook
from app.tools.metadata import get_service_metadata
from app.tools.deployment import get_deployment_events


class TestSearchLogs:
    def test_search_logs_returns_records(self):
        """search_logs returns records for a valid service and time range."""
        result = search_logs(
            service="api-gateway",
            start_time="2025-07-14T02:00:00Z",
            end_time="2025-07-14T02:30:00Z",
        )
        assert result["error"] is False
        assert isinstance(result["records"], list)
        assert result["total_matched"] > 0
        assert "query_summary" in result

    def test_search_logs_preserves_timestamps(self):
        """All returned records have timestamps within the requested range."""
        result = search_logs(
            service="order-service",
            start_time="2025-07-14T02:00:00Z",
            end_time="2025-07-14T02:30:00Z",
        )
        assert result["error"] is False
        from datetime import datetime, timezone
        start = datetime.fromisoformat("2025-07-14T02:00:00+00:00")
        end = datetime.fromisoformat("2025-07-14T02:30:00+00:00")
        for record in result["records"]:
            ts = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
            assert start <= ts <= end, f"Timestamp {ts} out of range"

    def test_search_logs_severity_filter(self):
        """Severity filter returns only records at or above the specified level."""
        result = search_logs(
            service="order-service",
            start_time="2025-07-14T01:00:00Z",
            end_time="2025-07-14T03:00:00Z",
            severity="ERROR",
        )
        assert result["error"] is False
        for record in result["records"]:
            assert record["severity"] in ("ERROR", "CRITICAL")

    def test_search_logs_keyword_filter(self):
        """Keyword filter returns only records containing the keyword."""
        result = search_logs(
            service="db-client",
            start_time="2025-07-14T01:00:00Z",
            end_time="2025-07-14T03:00:00Z",
            keyword="exhausted",
        )
        assert result["error"] is False
        for record in result["records"]:
            assert "exhausted" in record["message"].lower()

    def test_search_logs_limit_respected(self):
        """Result count does not exceed the specified limit."""
        result = search_logs(
            service="all",
            start_time="2025-07-14T01:00:00Z",
            end_time="2025-07-14T03:00:00Z",
            limit=5,
        )
        assert result["error"] is False
        assert len(result["records"]) <= 5


class TestGetRunbook:
    def test_get_runbook_http_503(self):
        """get_runbook returns a valid runbook for http_503 topic."""
        result = get_runbook("http_503")
        assert result["error"] is False
        assert result["topic"] == "http_503"
        assert isinstance(result["symptoms"], list)
        assert len(result["symptoms"]) > 0
        assert isinstance(result["high_risk_actions"], list)
        assert len(result["high_risk_actions"]) > 0
        assert "raw_content" in result

    def test_get_runbook_db_connection_pool(self):
        """get_runbook returns a valid runbook for db_connection_pool topic."""
        result = get_runbook("db_connection_pool")
        assert result["error"] is False
        assert result["topic"] == "db_connection_pool"
        assert isinstance(result["diagnostic_checks"], list)
        assert isinstance(result["evidence_to_collect"], list)

    def test_get_runbook_all_sections_present(self):
        """All required runbook sections are present."""
        result = get_runbook("batch_job_interference")
        assert result["error"] is False
        for field in ["symptoms", "diagnostic_checks", "evidence_to_collect",
                      "safe_actions", "high_risk_actions", "escalation_conditions"]:
            assert field in result, f"Missing field: {field}"


class TestGetServiceMetadata:
    def test_get_service_metadata_order_service(self):
        """get_service_metadata returns full metadata for order-service."""
        result = get_service_metadata("order-service")
        assert result["error"] is False
        meta = result["metadata"]
        assert meta["name"] == "order-service"
        assert "database" in meta
        assert "scheduled_jobs" in meta
        assert "known_constraints" in meta
        assert meta["database"]["pool_size"] == 20

    def test_get_service_metadata_has_deployment_info(self):
        """Metadata contains deployment timestamp and version."""
        result = get_service_metadata("order-service")
        assert result["error"] is False
        meta = result["metadata"]
        assert "current_version" in meta
        assert "deployment_timestamp" in meta


class TestGetDeploymentEvents:
    def test_get_deployment_events_returns_events(self):
        """get_deployment_events returns events for a time range."""
        result = get_deployment_events(
            start_time="2025-07-14T01:00:00Z",
            end_time="2025-07-14T03:00:00Z",
        )
        assert result["error"] is False
        assert isinstance(result["events"], list)
        assert result["total"] > 0

    def test_get_deployment_events_event_type_filter(self):
        """Event type filter returns only matching event types."""
        result = get_deployment_events(
            event_type="db_alert",
            start_time="2025-07-14T01:00:00Z",
            end_time="2025-07-14T03:00:00Z",
        )
        assert result["error"] is False
        for evt in result["events"]:
            assert evt["event_type"] == "db_alert"
