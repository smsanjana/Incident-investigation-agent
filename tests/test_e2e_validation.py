"""
End-to-End Validation Test Suite: Scenario 1 (INC-001) & Scenario 2 (INC-002)
"""
import pytest
import os
import sys
import json
from sqlmodel import Session

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["ARTEFACTS_DIR"] = os.path.join(os.path.dirname(__file__), "..", "artefacts")
os.environ["DATABASE_URL"] = "sqlite://"

from app.db import engine
from app.models.incident import Incident, IncidentStatus, InvestigationStateDB
from app.agent.orchestrator import run_investigation
from app.agent.state_manager import load_state, save_state
from app.agent.report_builder import build_report
from app.models.state import InvestigationState, Hypothesis, EvidenceItem, RecommendedAction


class TestEndToEndValidation:

    def test_scenario_1_sufficient_evidence_e2e(self, client):
        """Full end-to-end validation for Scenario 1 (INC-001)."""

        # 1. Load INC-001 fixture from artefacts
        inc_file = os.path.join(os.environ["ARTEFACTS_DIR"], "incidents", "INC-001.json")
        with open(inc_file, "r", encoding="utf-8") as f:
            inc_data = json.load(f)

        # 2. Incident Creation via API
        create_res = client.post("/incidents", json=inc_data)
        assert create_res.status_code == 201, f"Failed to create incident: {create_res.text}"
        created_inc = create_res.json()
        assert created_inc["incident_id"] == "INC-001"
        assert created_inc["status"] == "open"

        # 3. Incident Retrieval via API
        get_res = client.get("/incidents/INC-001")
        assert get_res.status_code == 200
        assert get_res.json()["affected_service"] == "order-service"

        # 4. Trigger Investigation via API
        inv_res = client.post("/incidents/INC-001/investigate")
        assert inv_res.status_code == 200
        inv_data = inv_res.json()
        assert inv_data["status"] == "concluded"
        assert inv_data["conclusion_type"] == "ROOT_CAUSE_IDENTIFIED"

        # 5. Fetch Evidence State & Verify Tools Invoked
        ev_res = client.get("/incidents/INC-001/evidence")
        assert ev_res.status_code == 200
        ev_data = ev_res.json()

        tools_invoked = [t["tool_name"] for t in ev_data["tools_used"]]
        assert "get_service_metadata" in tools_invoked
        assert "get_deployment_events" in tools_invoked
        assert "search_logs" in tools_invoked
        assert "get_runbook" in tools_invoked

        # 6. Verify Evidence Stored in State
        evidence_items = ev_data["evidence_items"]
        assert len(evidence_items) >= 4
        ev_sources = [e["source"] for e in evidence_items]
        assert any("get_deployment_events" in s for s in ev_sources)
        assert any("search_logs" in s for s in ev_sources)

        # 7. Verify Hypotheses Generation, Ranking & Evidence Traceability
        hypotheses = ev_data["hypotheses"]
        assert len(hypotheses) >= 2, "Multiple hypotheses must be generated"

        # Hypotheses are sorted by confidence descending
        top_h = hypotheses[0]
        assert top_h["confidence"] >= 0.85
        assert top_h["status"] == "confirmed"
        assert len(top_h["supporting_evidence_ids"]) > 0
        
        # Check for disproven / lower hypothesis with contradicting evidence
        second_h = hypotheses[1]
        assert second_h["confidence"] < top_h["confidence"]

        # 8. Fetch Final Report via API
        rpt_res = client.get("/incidents/INC-001/report")
        assert rpt_res.status_code == 200
        report = rpt_res.json()
        assert report["report_id"] == "RPT-INC-001"
        assert report["most_likely_cause"]["hypothesis_id"] == top_h["hypothesis_id"]

        # 9. Fetch Actions & Verify High-Risk Flagging
        act_res = client.get("/incidents/INC-001/actions")
        assert act_res.status_code == 200
        act_data = act_res.json()
        actions = act_data["actions"]
        assert len(actions) > 0
        
        # High-risk action requires approval
        high_risk_acts = [a for a in actions if a["requires_approval"]]
        assert len(high_risk_acts) > 0
        for a in high_risk_acts:
            assert a["requires_approval"] is True

    def test_scenario_2_insufficient_evidence_e2e(self, client):
        """Full end-to-end validation for Scenario 2 (INC-002)."""

        # 1. Load INC-002 fixture from artefacts
        inc_file = os.path.join(os.environ["ARTEFACTS_DIR"], "incidents", "INC-002.json")
        with open(inc_file, "r", encoding="utf-8") as f:
            inc_data = json.load(f)

        # 2. Incident Creation & Retrieval
        create_res = client.post("/incidents", json=inc_data)
        assert create_res.status_code == 201
        
        # 3. Trigger Investigation
        inv_res = client.post("/incidents/INC-002/investigate")
        assert inv_res.status_code == 200
        inv_data = inv_res.json()

        # Agent MUST return INSUFFICIENT_EVIDENCE
        assert inv_data["conclusion_type"] == "INSUFFICIENT_EVIDENCE"

        # 4. Fetch Evidence State
        ev_res = client.get("/incidents/INC-002/evidence")
        assert ev_res.status_code == 200
        ev_data = ev_res.json()

        # Verify multiple hypotheses remain active with similar confidence
        hypotheses = ev_data["hypotheses"]
        assert len(hypotheses) >= 2
        conf_diff = abs(hypotheses[0]["confidence"] - hypotheses[1]["confidence"])
        assert conf_diff <= 0.20, "Hypotheses should have close confidence when evidence is ambiguous"

        # Verify evidence gaps reported
        assert len(ev_data["open_questions"]) > 0, "Missing evidence gaps must be explicitly reported"
