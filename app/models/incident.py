from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid
import json


def generate_id():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONCLUDED = "concluded"


class ActionCategory(str, Enum):
    READ_ONLY_DIAGNOSTIC = "READ_ONLY_DIAGNOSTIC"
    LOW_RISK_OPERATIONAL = "LOW_RISK_OPERATIONAL"
    HIGH_RISK_OPERATIONAL = "HIGH_RISK_OPERATIONAL"
    DESTRUCTIVE = "DESTRUCTIVE"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ─── DB Models ────────────────────────────────────────────────────────────────

class Incident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: str = Field(index=True, unique=True)
    title: str
    affected_service: str
    severity: str
    start_time: str
    detection_time: str
    customer_impact: str
    reporter_notes: str
    status: IncidentStatus = IncidentStatus.OPEN
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # JSON-encoded fields
    initial_symptoms_json: str = Field(default="[]")
    tags_json: str = Field(default="[]")

    @property
    def initial_symptoms(self) -> List[str]:
        return json.loads(self.initial_symptoms_json)

    @property
    def tags(self) -> List[str]:
        return json.loads(self.tags_json)


class InvestigationStateDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: str = Field(index=True, unique=True)
    incident_summary: str = ""
    observed_symptoms_json: str = Field(default="[]")
    current_hypotheses_json: str = Field(default="[]")
    evidence_items_json: str = Field(default="[]")
    open_questions_json: str = Field(default="[]")
    tools_used_json: str = Field(default="[]")
    recommended_next_steps_json: str = Field(default="[]")
    final_conclusion: Optional[str] = None
    conclusion_type: Optional[str] = None  # ROOT_CAUSE_IDENTIFIED, INSUFFICIENT_EVIDENCE, etc.
    iteration_count: int = 0
    updated_at: datetime = Field(default_factory=utc_now)


class RecommendedActionDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    action_id: str = Field(default_factory=generate_id, index=True, unique=True)
    incident_id: str = Field(index=True)
    description: str
    category: ActionCategory
    requires_approval: bool
    rationale: str = ""
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
