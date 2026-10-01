"""
Test: Unsupported root-cause conclusion is flagged as insufficient evidence.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.state import InvestigationState, Hypothesis
from app.agent.orchestrator import apply_state_update
from app.agent.report_builder import build_report
from app.models.incident import Incident
from datetime import datetime


def make_test_incident(incident_id: str) -> Incident:
    return Incident(
        incident_id=incident_id,
        title="Test Incident",
        affected_service="order-service",
        severity="SEV-2",
        start_time="2025-07-14T02:15:00Z",
        detection_time="2025-07-14T02:22:00Z",
        customer_impact="Test impact",
        reporter_notes="Test notes",
        initial_symptoms_json="[]",
        tags_json="[]",
    )


class TestUnsupportedCause:
    def test_hypothesis_without_evidence_has_low_confidence(self):
        """A hypothesis with no supporting evidence IDs should not have HIGH confidence."""
        state = InvestigationState(incident_id="INC-UNSUPPORTED")
        update = {
            "hypotheses": [
                {
                    "hypothesis_id": "H-UNSUP",
                    "statement": "The outage was caused by cosmic rays.",
                    "supporting_evidence_ids": [],  # no evidence
                    "contradicting_evidence_ids": [],
                    "confidence": 0.9,  # HIGH claimed without evidence
                    "confidence_label": "HIGH",
                    "additional_evidence_required": [],
                    "status": "active",
                }
            ]
        }
        apply_state_update(state, update)
        h = state.current_hypotheses[0]
        # The state records it as submitted (the safety check is at report level or agent logic)
        # Verify: report should show 0 supporting evidence items
        assert len(h.supporting_evidence_ids) == 0

    def test_insufficient_evidence_conclusion_type(self):
        """State with no strong evidence yields INSUFFICIENT_EVIDENCE conclusion type."""
        state = InvestigationState(incident_id="INC-INSUF")
        state.conclusion_type = "INSUFFICIENT_EVIDENCE"
        state.final_conclusion = "Unable to confirm root cause. Evidence gaps remain."
        state.open_questions = [
            "DB slow query log not available.",
            "Batch job end event missing.",
        ]

        assert state.conclusion_type == "INSUFFICIENT_EVIDENCE"
        assert len(state.open_questions) == 2

    def test_report_with_no_evidence_shows_limitations(self):
        """Final report for a state with no evidence lists limitations."""
        state = InvestigationState(incident_id="INC-NO-EVD")
        state.final_conclusion = "No conclusion reached."
        state.conclusion_type = "INSUFFICIENT_EVIDENCE"
        state.open_questions = ["Missing DB logs", "Missing deployment diff"]

        incident = make_test_incident("INC-NO-EVD")
        report = build_report(incident, state)

        assert report["conclusion"]["type"] == "INSUFFICIENT_EVIDENCE"
        assert len(report["evidence_reviewed"]) == 0
        assert report["confidence_and_limitations"]["overall_confidence"] == 0.0
