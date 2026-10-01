"""
Test: Investigation with insufficient evidence yields appropriate conclusion.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.state import InvestigationState, Hypothesis, EvidenceItem
from app.agent.orchestrator import apply_state_update
from app.agent.report_builder import build_report
from app.models.incident import Incident
from datetime import datetime


def make_incident(iid: str) -> Incident:
    return Incident(
        incident_id=iid,
        title="Insufficient Evidence Incident",
        affected_service="order-service",
        severity="SEV-3",
        start_time="2025-07-21T14:05:00Z",
        detection_time="2025-07-21T14:18:00Z",
        customer_impact="6% failures",
        reporter_notes="Incomplete logs",
        initial_symptoms_json="[]",
        tags_json="[]",
    )


class TestInsufficientEvidence:
    def test_state_with_two_equal_hypotheses_is_insufficient(self):
        """Two hypotheses with equal confidence and missing evidence = INSUFFICIENT_EVIDENCE."""
        state = InvestigationState(incident_id="INC-002")
        update = {
            "incident_summary": "Order service 503s. DB truncated logs. Deployment and batch job both in window.",
            "hypotheses": [
                {
                    "hypothesis_id": "H-BATCH",
                    "statement": "Batch job (order-export) exhausted the DB connection pool.",
                    "supporting_evidence_ids": ["EVD-BATCH-START"],
                    "contradicting_evidence_ids": [],
                    "confidence": 0.45,
                    "confidence_label": "MEDIUM",
                    "additional_evidence_required": [
                        "Full DB client logs showing pool exhaustion",
                        "Batch job end event to confirm duration",
                    ],
                    "status": "active",
                },
                {
                    "hypothesis_id": "H-DEPLOY",
                    "statement": "Deployment v2.4.2 introduced a slow query causing timeouts.",
                    "supporting_evidence_ids": [],
                    "contradicting_evidence_ids": [],
                    "confidence": 0.4,
                    "confidence_label": "MEDIUM",
                    "additional_evidence_required": [
                        "Deployment diff for v2.4.2",
                        "DB slow query log",
                    ],
                    "status": "active",
                },
            ],
            "open_questions": [
                "Are DB client logs complete or truncated?",
                "Did batch job run to completion or is it still running?",
                "What changed in v2.4.2 deployment?",
            ],
            "final_conclusion": "Insufficient evidence to confirm root cause. Two plausible hypotheses remain open.",
            "conclusion_type": "INSUFFICIENT_EVIDENCE",
            "done": True,
        }
        done = apply_state_update(state, update)
        assert done is True
        assert state.conclusion_type == "INSUFFICIENT_EVIDENCE"
        assert len(state.current_hypotheses) == 2
        assert len(state.open_questions) == 3

    def test_insufficient_evidence_report_lists_gaps(self):
        """Report for INC-002 style investigation lists evidence gaps."""
        state = InvestigationState(incident_id="INC-002")
        state.conclusion_type = "INSUFFICIENT_EVIDENCE"
        state.final_conclusion = "Cannot confirm root cause. DB logs incomplete."
        state.open_questions = ["DB logs truncated", "Batch job end event missing"]

        h = Hypothesis(
            hypothesis_id="H-BATCH",
            statement="Batch job caused pool exhaustion",
            supporting_evidence_ids=["EVD-001"],
            contradicting_evidence_ids=[],
            confidence=0.45,
            confidence_label="MEDIUM",
            additional_evidence_required=["Full DB pool logs"],
            status="insufficient_evidence",
        )
        state.current_hypotheses.append(h)

        incident = make_incident("INC-002")
        report = build_report(incident, state)

        assert report["conclusion"]["type"] == "INSUFFICIENT_EVIDENCE"
        assert len(report["evidence_gaps"]) > 0
        assert report["confidence_and_limitations"]["overall_confidence"] < 0.9

    def test_insufficient_evidence_recommends_follow_up_actions(self):
        """When evidence is insufficient, recommended_next_steps are populated."""
        state = InvestigationState(incident_id="INC-002")
        state.conclusion_type = "INSUFFICIENT_EVIDENCE"
        state.recommended_next_steps = [
            "Retrieve full DB slow-query log from DBA",
            "Confirm batch job completion time from scheduler",
            "Obtain deployment diff for v2.4.2 from CI/CD",
        ]
        assert len(state.recommended_next_steps) == 3
