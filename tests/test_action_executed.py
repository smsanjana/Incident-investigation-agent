"""
Test: Model claiming to have executed an action is blocked with SafetyViolationError.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agent.safety import check_execution_claim, SafetyViolationError


class TestActionExecutionBlocked:
    @pytest.mark.parametrize("violating_text", [
        "I have restarted the order-service successfully.",
        "I restarted the service and it is now healthy.",
        "I have rolled back the deployment to v2.4.0.",
        "I rolled back the deployment as requested.",
        "I have terminated all database connections.",
        "I terminated the long-running connections.",
        "I have disabled the scheduled batch job.",
        "I disabled the order-reconciliation job.",
        "Successfully restarted the order-service replicas.",
        "Successfully rolled back the deployment.",
        "The deployment has been rolled back to v2.4.0.",
        "The service has been restarted and is healthy.",
        "I have increased the pool size to 40.",
        "I increased the pool to handle more connections.",
        "I have deleted the stuck database sessions.",
        "I executed the rollback command.",
    ])
    def test_execution_claim_raises_safety_violation(self, violating_text):
        """Any text claiming an action was executed raises SafetyViolationError."""
        with pytest.raises(SafetyViolationError) as exc_info:
            check_execution_claim(violating_text)
        assert "SAFETY VIOLATION" in exc_info.value.message
        assert exc_info.value.matched_pattern is not None

    @pytest.mark.parametrize("safe_text", [
        "I recommend restarting the order-service.",
        "Consider rolling back the deployment.",
        "The runbook suggests terminating connections.",
        "A possible action is to disable the batch job.",
        "Evidence suggests a restart may help.",
        "I found log evidence of pool exhaustion.",
        "The batch job started at 02:10 and acquired 15 connections.",
    ])
    def test_safe_text_does_not_raise(self, safe_text):
        """Recommendation text (not claims of execution) does not raise."""
        # Should not raise
        check_execution_claim(safe_text)

    def test_safety_violation_error_has_matched_pattern(self):
        """SafetyViolationError includes the matched pattern that triggered it."""
        with pytest.raises(SafetyViolationError) as exc_info:
            check_execution_claim("I have restarted the production service.")
        assert exc_info.value.matched_pattern is not None
        assert isinstance(exc_info.value.matched_pattern, str)
