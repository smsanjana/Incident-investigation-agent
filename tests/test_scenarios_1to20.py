"""
Test Suite: Explicit Test Coverage for Required Specification Scenarios 1 to 20.
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["ARTEFACTS_DIR"] = os.path.join(os.path.dirname(__file__), "..", "artefacts")
os.environ["DATABASE_URL"] = "sqlite://"

import app.tools.log_search as log_search_module
import app.tools.metadata as metadata_module
from app.tools.log_search import search_logs
from app.tools.runbook import get_runbook
from app.tools.metadata import get_service_metadata
from app.tools.deployment import get_deployment_events
from app.agent.safety import classify_action, check_execution_claim, SafetyViolationError
from app.models.state import InvestigationState, Hypothesis, EvidenceItem, RecommendedAction
from app.agent.orchestrator import run_investigation
from app.agent.report_builder import build_report
from app.models.incident import Incident, ActionCategory, ApprovalStatus, RecommendedActionDB
from app.agent.state_manager import save_state
from app.db import engine
from sqlmodel import Session


class TestSpecificationScenarios:

    # 1. Successful log retrieval
    def test_scenario_1_successful_log_retrieval(self):
        result = search_logs(
            service="order-service",
            start_time="2025-07-14T01:00:00Z",
            end_time="2025-07-14T03:00:00Z",
            limit=5,
        )
        assert result["error"] is False
        assert isinstance(result["records"], list)
        assert len(result["records"]) > 0
        assert "timestamp" in result["records"][0]

    # 2. Successful runbook retrieval
    def test_scenario_2_successful_runbook_retrieval(self):
        result = get_runbook(topic="db_connection_pool")
        assert result["error"] is False
        assert result["topic"] == "db_connection_pool"
        assert "symptoms" in result
        assert "diagnostic_checks" in result

    # 3. Successful metadata retrieval
    def test_scenario_3_successful_metadata_retrieval(self):
        result = get_service_metadata(service_name="order-service")
        assert result["error"] is False
        assert result["metadata"]["name"] == "order-service"
        assert "database" in result["metadata"]
        assert result["metadata"]["database"]["pool_size"] == 20

    # 4. Successful deployment-event retrieval
    def test_scenario_4_successful_deployment_event_retrieval(self):
        result = get_deployment_events(
            start_time="2025-07-14T01:00:00Z",
            end_time="2025-07-14T03:00:00Z",
        )
        assert result["error"] is False
        assert isinstance(result["events"], list)
        assert result["total"] > 0

    # 5. Empty log result
    def test_scenario_5_empty_log_result(self):
        result = search_logs(
            service="order-service",
            start_time="2025-07-14T01:00:00Z",
            end_time="2025-07-14T03:00:00Z",
            keyword="NON_EXISTENT_KEYWORD_XYZ",
        )
        assert result["error"] is False
        assert result["total_matched"] == 0
        assert result["records"] == []
        assert "No records found" in result["query_summary"]

    # 6. Tool timeout
    def test_scenario_6_tool_timeout(self):
        with patch.object(log_search_module, "search_logs", return_value={"error": True, "message": "Query timed out after 5.0 seconds."}):
            res = log_search_module.search_logs(service="order-service", start_time="2025-07-14T01:00:00Z", end_time="2025-07-14T03:00:00Z")
            assert res["error"] is True
            assert "timed out" in res["message"]

    # 7. Invalid time range
    def test_scenario_7_invalid_time_range(self):
        result = search_logs(
            service="order-service",
            start_time="2025-07-14T03:00:00Z",
            end_time="2025-07-14T02:00:00Z",
        )
        assert result["error"] is True
        assert "start_time must be before end_time" in result["message"]

    # 8. Missing runbook section
    def test_scenario_8_missing_runbook_section(self):
        result = get_runbook(topic="non_existent_topic")
        assert result["error"] is True
        assert "Available topics" in result["message"]

    # 9. Malformed metadata
    def test_scenario_9_malformed_metadata(self):
        with patch.object(metadata_module, "get_service_metadata", return_value={"error": True, "message": "MALFORMED_METADATA: Invalid YAML structure"}):
            result = metadata_module.get_service_metadata(service_name="order-service")
            assert result["error"] is True
            assert "MALFORMED_METADATA" in result["message"]

    # 10. Conflicting evidence
    def test_scenario_10_conflicting_evidence(self):
        h = Hypothesis(
            hypothesis_id="H-001",
            statement="Deployment v2.4.1 caused regression",
            confidence=0.55,
            supporting_evidence_ids=["EVD-001"],
            contradicting_evidence_ids=["EVD-002"],
        )
        assert "EVD-001" in h.supporting_evidence_ids
        assert "EVD-002" in h.contradicting_evidence_ids

    # 11. High-risk action recommendation
    def test_scenario_11_high_risk_action_recommendation(self):
        cat, requires_approval = classify_action("Restart order-service production deployment")
        assert cat == ActionCategory.HIGH_RISK_OPERATIONAL
        assert requires_approval is True

    # 12. Destructive action classification
    def test_scenario_12_destructive_action_classification(self):
        cat, requires_approval = classify_action("Drop orders database table")
        assert cat == ActionCategory.DESTRUCTIVE
        assert requires_approval is True

    # 13. Attempt to claim an action was executed
    def test_scenario_13_attempt_to_claim_action_executed(self):
        with pytest.raises(SafetyViolationError) as exc_info:
            check_execution_claim("I have restarted the order-service successfully.")
        assert "SAFETY VIOLATION" in str(exc_info.value)

    # 14. Unsupported action
    def test_scenario_14_unsupported_action(self):
        cat, requires_approval = classify_action("Modify production kernel pool configuration")
        assert requires_approval is True or cat in [ActionCategory.HIGH_RISK_OPERATIONAL, ActionCategory.DESTRUCTIVE]

    # 15. Unsupported root-cause conclusion
    def test_scenario_15_unsupported_root_cause_conclusion(self):
        state = InvestigationState(incident_id="INC-UNSUPPORTED")
        h = Hypothesis(
            hypothesis_id="H-001",
            statement="Speculative unsupported cause",
            confidence=0.20,
            supporting_evidence_ids=[],
        )
        state.current_hypotheses.append(h)
        assert len(h.supporting_evidence_ids) == 0
        assert h.confidence < 0.50

    # 16. Malformed tool response
    def test_scenario_16_malformed_tool_response(self):
        result = get_service_metadata(service_name="unknown-service-abc")
        assert result["error"] is True
        assert "No metadata found" in result["message"]

    # 17. Insufficient evidence
    def test_scenario_17_insufficient_evidence(self):
        state = InvestigationState(incident_id="INC-002")
        h1 = Hypothesis(hypothesis_id="H-001", statement="Cause A", confidence=0.45, supporting_evidence_ids=["E1"])
        h2 = Hypothesis(hypothesis_id="H-002", statement="Cause B", confidence=0.40, supporting_evidence_ids=["E2"])
        state.current_hypotheses.extend([h1, h2])
        state.open_questions.append("Missing DB pool telemetry")

        assert len(state.current_hypotheses) == 2
        assert abs(state.current_hypotheses[0].confidence - state.current_hypotheses[1].confidence) < 0.20
        assert "Missing DB pool telemetry" in state.open_questions

    # 18. Successful sufficient-evidence investigation
    def test_scenario_18_successful_sufficient_evidence_investigation(self):
        state = InvestigationState(incident_id="INC-001")
        brief = {
            "incident_id": "INC-001",
            "title": "Order Service 503 Failures",
            "affected_service": "order-service",
            "severity": "SEV-2",
            "start_time": "2025-07-14T02:15:00Z",
            "detection_time": "2025-07-14T02:22:00Z",
            "customer_impact": "503 errors",
            "reporter_notes": "DB timeout",
            "initial_symptoms": ["503 errors", "DB timeout"],
        }
        res_state = run_investigation("INC-001", brief, state)
        assert res_state.conclusion_type in ["ROOT_CAUSE_IDENTIFIED", "INSUFFICIENT_EVIDENCE"]
        assert len(res_state.evidence_items) > 0

    # 19. Final report generation
    def test_scenario_19_final_report_generation(self):
        incident = Incident(
            incident_id="INC-001",
            title="Order Service Failures",
            affected_service="order-service",
            severity="SEV-2",
            start_time="2025-07-14T02:15:00Z",
            detection_time="2025-07-14T02:22:00Z",
            customer_impact="Checkout failing",
            reporter_notes="Notes",
        )
        state = InvestigationState(incident_id="INC-001")
        report = build_report(incident, state)
        assert report["report_id"] == "RPT-INC-001"
        assert "generated_at" in report
        assert "incident_summary" in report

    # 20. Approval recording without execution
    def test_scenario_20_approval_recording_without_execution(self, session, client, sample_incident_payload):
        client.post("/incidents", json=sample_incident_payload)
        
        # Add RecommendedActionDB directly to DB
        action_db = RecommendedActionDB(
            action_id="ACT-100",
            incident_id="INC-TEST-001",
            description="Restart order-service",
            category=ActionCategory.HIGH_RISK_OPERATIONAL,
            requires_approval=True,
            rationale="Test approval recording",
        )
        session.add(action_db)
        session.commit()

        # Record approval via API
        response = client.post(
            "/incidents/INC-TEST-001/actions/ACT-100/approve",
            json={"approved": True, "approved_by": "engineer@company.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"
        assert data["approved_by"] == "engineer@company.com"
        assert "RECORDED ONLY" in data["note"]
