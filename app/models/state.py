from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class EvidenceItem(BaseModel):
    evidence_id: str
    source: str  # e.g., "search_logs:db-client", "get_runbook:db_connection_pool"
    description: str
    raw_content: str  # snippet or summary
    timestamp_collected: str
    relevance: str  # how it relates to the investigation


class Hypothesis(BaseModel):
    hypothesis_id: str
    statement: str
    supporting_evidence_ids: List[str] = []
    contradicting_evidence_ids: List[str] = []
    confidence: float = Field(ge=0.0, le=1.0)  # 0 to 1
    confidence_label: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"
    additional_evidence_required: List[str] = []
    status: Literal["active", "confirmed", "ruled_out", "insufficient_evidence"] = "active"


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict
    result_summary: str
    called_at: str
    success: bool
    error_code: Optional[str] = None


class RecommendedAction(BaseModel):
    action_id: str
    description: str
    category: Literal["READ_ONLY_DIAGNOSTIC", "LOW_RISK_OPERATIONAL", "HIGH_RISK_OPERATIONAL", "DESTRUCTIVE"]
    requires_approval: bool
    rationale: str


class InvestigationState(BaseModel):
    incident_id: str
    incident_summary: str = ""
    observed_symptoms: List[str] = []
    current_hypotheses: List[Hypothesis] = []
    evidence_items: List[EvidenceItem] = []
    open_questions: List[str] = []
    tools_used: List[ToolCall] = []
    recommended_next_steps: List[str] = []
    recommended_actions: List[RecommendedAction] = []
    final_conclusion: Optional[str] = None
    conclusion_type: Optional[str] = None
    iteration_count: int = 0

    def get_evidence_by_id(self, eid: str) -> Optional[EvidenceItem]:
        return next((e for e in self.evidence_items if e.evidence_id == eid), None)

    def add_evidence(self, item: EvidenceItem):
        if not any(e.evidence_id == item.evidence_id for e in self.evidence_items):
            self.evidence_items.append(item)

    def get_hypothesis_by_id(self, hid: str) -> Optional[Hypothesis]:
        return next((h for h in self.current_hypotheses if h.hypothesis_id == hid), None)
