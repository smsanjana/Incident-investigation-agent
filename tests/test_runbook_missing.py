"""
Test: Missing runbook section handled gracefully.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["ARTEFACTS_DIR"] = os.path.join(os.path.dirname(__file__), "..", "artefacts")

from app.tools.runbook import get_runbook


class TestMissingRunbook:
    def test_unknown_topic_returns_topic_not_found(self):
        """An unknown runbook topic returns TOPIC_NOT_FOUND error."""
        result = get_runbook("unknown_nonexistent_topic")
        assert result["error"] is True
        assert result["error_code"] == "TOPIC_NOT_FOUND"
        assert "message" in result

    def test_forced_missing_returns_topic_not_found(self):
        """_force_missing=True returns TOPIC_NOT_FOUND even for valid topics."""
        result = get_runbook("http_503", _force_missing=True)
        assert result["error"] is True
        assert result["error_code"] == "TOPIC_NOT_FOUND"

    def test_missing_runbook_message_includes_available_topics(self):
        """Error message for missing runbook lists available topics."""
        result = get_runbook("completely_made_up_topic")
        assert result["error"] is True
        assert "message" in result
        # Should mention available topics
        assert "http_503" in result["message"] or "Available topics" in result["message"]

    def test_all_valid_topics_succeed(self):
        """All documented runbook topics can be retrieved successfully."""
        valid_topics = [
            "http_503", "db_connection_pool", "high_latency",
            "deployment_regression", "batch_job_interference",
            "safe_rollback", "service_restart",
        ]
        for topic in valid_topics:
            result = get_runbook(topic)
            assert result["error"] is False, f"Topic '{topic}' failed: {result.get('message')}"
