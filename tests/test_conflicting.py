"""
Test: Conflicting evidence is reflected in hypothesis fields.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.state import InvestigationState, Hypothesis, EvidenceItem
from app.agent.orchestrator import apply_state_update
from datetime import datetime, timezone


class TestConflictingEvidence:
    def test_hypothesis_records_supporting_and_contradicting(self):
        """A hypothesis can hold both supporting and contradicting evidence IDs."""
        state = InvestigationState(incident_id="INC-CONFLICT-TEST")

        # Add evidence items
        e1 = EvidenceItem(
            evidence_id="EVD-001",
            source="search_logs:db-client",
            description="Pool exhaustion at 02:14",
            raw_content="ERR_POOL_EXHAUSTED at 02:14:30Z",
            timestamp_collected=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            relevance="Supports batch job hypothesis",
        )
        e2 = EvidenceItem(
            evidence_id="EVD-002",
            source="search_logs:api-gateway",
            description="503s started 45 min after deployment",
            raw_content="503 rate 0% for 45 min post-deployment",
            timestamp_collected=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            relevance="Contradicts deployment regression hypothesis",
        )
        state.add_evidence(e1)
        state.add_evidence(e2)

        # Apply state update with hypothesis containing both supporting and contradicting evidence
        update = {
            "hypotheses": [
                {
                    "hypothesis_id": "H-001",
                    "statement": "Deployment v2.4.1 caused the 503 failures",
                    "supporting_evidence_ids": [],
                    "contradicting_evidence_ids": ["EVD-002"],
                    "confidence": 0.1,
                    "confidence_label": "LOW",
                    "additional_evidence_required": ["Check if errors started immediately post-deployment"],
                    "status": "active",
                },
                {
                    "hypothesis_id": "H-002",
                    "statement": "Batch job exhausted DB connection pool causing 503s",
                    "supporting_evidence_ids": ["EVD-001"],
                    "contradicting_evidence_ids": [],
                    "confidence": 0.85,
                    "confidence_label": "HIGH",
                    "additional_evidence_required": [],
                    "status": "active",
                },
            ]
        }
        apply_state_update(state, update)

        assert len(state.current_hypotheses) == 2
        h_deploy = next(h for h in state.current_hypotheses if h.hypothesis_id == "H-001")
        h_batch = next(h for h in state.current_hypotheses if h.hypothesis_id == "H-002")

        # Deployment hypothesis has contradicting evidence
        assert "EVD-002" in h_deploy.contradicting_evidence_ids
        assert h_deploy.confidence < 0.5

        # Batch hypothesis has supporting evidence
        assert "EVD-001" in h_batch.supporting_evidence_ids
        assert h_batch.confidence > 0.5

    def test_conflicting_evidence_both_hypotheses_preserved(self):
        """Conflicting evidence does not drop either hypothesis from state."""
        state = InvestigationState(incident_id="INC-CONFLICT-TEST-2")
        update = {
            "hypotheses": [
                {
                    "hypothesis_id": "H-A",
                    "statement": "Hypothesis A",
                    "supporting_evidence_ids": ["EVD-X"],
                    "contradicting_evidence_ids": ["EVD-Y"],
                    "confidence": 0.5,
                    "confidence_label": "MEDIUM",
                    "additional_evidence_required": [],
                    "status": "active",
                },
                {
                    "hypothesis_id": "H-B",
                    "statement": "Hypothesis B",
                    "supporting_evidence_ids": ["EVD-Y"],
                    "contradicting_evidence_ids": ["EVD-X"],
                    "confidence": 0.5,
                    "confidence_label": "MEDIUM",
                    "additional_evidence_required": [],
                    "status": "active",
                },
            ]
        }
        apply_state_update(state, update)
        assert len(state.current_hypotheses) == 2
        ids = {h.hypothesis_id for h in state.current_hypotheses}
        assert "H-A" in ids
        assert "H-B" in ids
