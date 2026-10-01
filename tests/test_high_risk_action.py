"""
Test: High-risk action recommendations are flagged with requires_approval=True.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agent.safety import classify_action
from app.models.incident import ActionCategory
from app.models.state import InvestigationState
from app.agent.orchestrator import apply_state_update


class TestHighRiskActions:
    @pytest.mark.parametrize("action_text,expected_category", [
        ("Restart the order-service production deployment", ActionCategory.HIGH_RISK_OPERATIONAL),
        ("Rollback deployment to v2.4.0", ActionCategory.HIGH_RISK_OPERATIONAL),
        ("kubectl rollout undo deployment/order-service", ActionCategory.HIGH_RISK_OPERATIONAL),
        ("Terminate all database connections", ActionCategory.HIGH_RISK_OPERATIONAL),
        ("Kill the order-reconciliation batch job", ActionCategory.HIGH_RISK_OPERATIONAL),
        ("Disable the scheduled batch job", ActionCategory.HIGH_RISK_OPERATIONAL),
        ("Increase connection pool size from 20 to 40", ActionCategory.HIGH_RISK_OPERATIONAL),
        ("Modify pool settings in production config", ActionCategory.HIGH_RISK_OPERATIONAL),
    ])
    def test_high_risk_action_classified_correctly(self, action_text, expected_category):
        """High-risk action text is classified as HIGH_RISK_OPERATIONAL."""
        category, requires_approval = classify_action(action_text)
        assert category == expected_category
        assert requires_approval is True

    @pytest.mark.parametrize("action_text", [
        "Delete production order data",
        "Drop the orders database table",
        "Truncate the orders table",
    ])
    def test_destructive_actions_require_approval(self, action_text):
        """Destructive actions require approval."""
        category, requires_approval = classify_action(action_text)
        assert category == ActionCategory.DESTRUCTIVE
        assert requires_approval is True

    @pytest.mark.parametrize("action_text", [
        "Review API gateway logs for 503 patterns",
        "Check service metadata for pool configuration",
        "Retrieve runbook for DB connection pool",
        "Search logs for pool exhaustion errors",
    ])
    def test_read_only_actions_do_not_require_approval(self, action_text):
        """Read-only diagnostic actions do not require approval."""
        category, requires_approval = classify_action(action_text)
        assert category == ActionCategory.READ_ONLY_DIAGNOSTIC
        assert requires_approval is False

    def test_state_update_flags_high_risk_action_requires_approval(self):
        """apply_state_update correctly sets requires_approval=True for high-risk actions."""
        state = InvestigationState(incident_id="INC-HR-TEST")
        update = {
            "recommended_actions": [
                {
                    "description": "Restart the order-service production replicas to reset connection pool",
                    "rationale": "Pool may be stuck; restart will release all connections.",
                },
                {
                    "description": "Review API gateway logs for 503 error patterns",
                    "rationale": "Understand the timeline of 503s.",
                },
            ]
        }
        apply_state_update(state, update)

        assert len(state.recommended_actions) == 2
        restart_action = next(a for a in state.recommended_actions if "restart" in a.description.lower())
        review_action = next(a for a in state.recommended_actions if "review" in a.description.lower())

        assert restart_action.requires_approval is True
        assert restart_action.category == "HIGH_RISK_OPERATIONAL"
        assert review_action.requires_approval is False
        assert review_action.category == "READ_ONLY_DIAGNOSTIC"
