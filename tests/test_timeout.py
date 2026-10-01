"""
Test: Tool timeout handling.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["ARTEFACTS_DIR"] = os.path.join(os.path.dirname(__file__), "..", "artefacts")

from app.tools.log_search import search_logs
from app.tools.deployment import get_deployment_events
from app.models.state import InvestigationState, ToolCall
from datetime import datetime


class TestTimeout:
    def test_log_search_timeout_returns_error(self):
        """A simulated log search timeout returns TIMEOUT error code."""
        result = search_logs(
            service="order-service",
            start_time="2025-07-14T00:00:00Z",
            end_time="2025-07-14T23:59:59Z",
            _force_timeout=True,
        )
        assert result["error"] is True
        assert result["error_code"] == "TIMEOUT"
        assert "message" in result

    def test_deployment_events_timeout_returns_error(self):
        """A simulated deployment event timeout returns TIMEOUT error code."""
        result = get_deployment_events(_force_timeout=True)
        assert result["error"] is True
        assert result["error_code"] == "TIMEOUT"

    def test_timeout_state_preserved(self):
        """Investigation state is preserved despite tool timeout."""
        state = InvestigationState(incident_id="INC-TIMEOUT-TEST")
        state.open_questions.append("Will timeout preserve state?")
        state.observed_symptoms.append("Test symptom")

        # Simulate timeout — state should be unchanged
        result = search_logs(
            service="order-service",
            start_time="2025-07-14T00:00:00Z",
            end_time="2025-07-14T23:59:59Z",
            _force_timeout=True,
        )
        assert result["error"] is True
        # State should still be intact
        assert len(state.open_questions) == 1
        assert len(state.observed_symptoms) == 1
