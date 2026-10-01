# Data Model Specification: AI Incident Investigation Agent

## Document Metadata
- **Title**: Database Schema & Runtime State Models
- **Specification Ref**: [Feature Specification](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md)
- **Constitution Ref**: [Project Constitution](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/constitution.md)

---

## 1. Database Schema (SQLModel / SQLite)

The application uses SQLite (`incident_agent.db`) managed via SQLModel tables defined in [`app/models/incident.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/models/incident.py).

```
 ┌───────────────────────────────────┐        ┌───────────────────────────────────┐
 │             Incident              │        │      InvestigationStateDB         │
 ├───────────────────────────────────┤        ├───────────────────────────────────┤
 │ id: int (PK)                      │        │ id: int (PK)                      │
 │ incident_id: str (Index, Unique)  │───────>│ incident_id: str (Index, Unique)  │
 │ title: str                        │        │ incident_summary: str             │
 │ affected_service: str             │        │ observed_symptoms_json: str       │
 │ severity: str                     │        │ current_hypotheses_json: str      │
 │ start_time: str                   │        │ evidence_items_json: str          │
 │ detection_time: str               │        │ open_questions_json: str          │
 │ customer_impact: str              │        │ tools_used_json: str              │
 │ reporter_notes: str               │        │ recommended_next_steps_json: str  │
 │ status: IncidentStatus (Enum)     │        │ final_conclusion: Optional[str]   │
 │ created_at: datetime              │        │ conclusion_type: Optional[str]    │
 │ updated_at: datetime              │        │ iteration_count: int              │
 │ initial_symptoms_json: str        │        │ updated_at: datetime              │
 │ tags_json: str                    │        └───────────────────────────────────┘
 └───────────────────────────────────┘
                  │
                  │                           ┌───────────────────────────────────┐
                  │                           │       RecommendedActionDB         │
                  │                           ├───────────────────────────────────┤
                  │                           │ id: int (PK)                      │
                  └──────────────────────────>│ action_id: str (Index, Unique)    │
                                              │ incident_id: str (Index)          │
                                              │ description: str                  │
                                              │ category: ActionCategory (Enum)   │
                                              │ requires_approval: bool           │
                                              │ rationale: str                    │
                                              │ approval_status: ApprovalStatus   │
                                              │ approved_by: Optional[str]        │
                                              │ approved_at: Optional[datetime]   │
                                              │ rejection_reason: Optional[str]   │
                                              │ created_at: datetime              │
                                              └───────────────────────────────────┘
```

### 1.1 `Incident` Table
- **Primary Key**: `id` (`Optional[int]`)
- **Index/Unique**: `incident_id` (`str`, e.g. `"INC-001"`)
- **Attributes**: `title`, `affected_service`, `severity` (`SEV-1`, `SEV-2`, `SEV-3`), `start_time`, `detection_time`, `customer_impact`, `reporter_notes`, `status` (`open`, `investigating`, `concluded`), `created_at`, `updated_at`.
- **JSON Encoded Storage**: `initial_symptoms_json` (`List[str]`), `tags_json` (`List[str]`).

### 1.2 `InvestigationStateDB` Table
- **Primary Key**: `id` (`Optional[int]`)
- **Index/Unique**: `incident_id` (`str`)
- **Attributes**: `incident_summary`, `final_conclusion`, `conclusion_type` (`ROOT_CAUSE_IDENTIFIED`, `INSUFFICIENT_EVIDENCE`, `MULTIPLE_CAUSES`, `INCONCLUSIVE`), `iteration_count`, `updated_at`.
- **JSON Encoded Storage**: `observed_symptoms_json`, `current_hypotheses_json`, `evidence_items_json`, `open_questions_json`, `tools_used_json`, `recommended_next_steps_json`.

### 1.3 `RecommendedActionDB` Table
- **Primary Key**: `id` (`Optional[int]`)
- **Index/Unique**: `action_id` (`str` UUID)
- **Index**: `incident_id` (`str`)
- **Attributes**: `description`, `category` (`READ_ONLY_DIAGNOSTIC`, `LOW_RISK_OPERATIONAL`, `HIGH_RISK_OPERATIONAL`, `DESTRUCTIVE`), `requires_approval` (`bool`), `rationale`, `approval_status` (`pending`, `approved`, `rejected`), `approved_by`, `approved_at`, `rejection_reason`, `created_at`.

---

## 2. Runtime Pydantic Models (`app/models/state.py`)

These objects govern agentic loop state transitions and JSON API payloads:

### 2.1 `EvidenceItem`
```python
class EvidenceItem(BaseModel):
    evidence_id: str             # e.g., "EVD-001"
    source: str                  # e.g., "search_logs:db-client"
    description: str             # Human readable finding
    raw_content: str             # Log snippet or YAML property
    timestamp_collected: str     # ISO UTC timestamp
    relevance: str               # Strategic explanation of evidence link
```

### 2.2 `Hypothesis`
```python
class Hypothesis(BaseModel):
    hypothesis_id: str           # e.g., "H-001"
    statement: str               # Candidate root cause mechanism
    supporting_evidence_ids: List[str] = []   # Array of EVD-xxx strings
    contradicting_evidence_ids: List[str] = [] # Array of EVD-xxx strings
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_label: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"
    additional_evidence_required: List[str] = []
    status: Literal["active", "confirmed", "ruled_out", "insufficient_evidence"] = "active"
```

### 2.3 `ToolCall`
```python
class ToolCall(BaseModel):
    tool_name: str
    arguments: dict
    result_summary: str
    called_at: str
    success: bool
    error_code: Optional[str] = None
```

### 2.4 `RecommendedAction`
```python
class RecommendedAction(BaseModel):
    action_id: str
    description: str
    category: Literal["READ_ONLY_DIAGNOSTIC", "LOW_RISK_OPERATIONAL", "HIGH_RISK_OPERATIONAL", "DESTRUCTIVE"]
    requires_approval: bool
    rationale: str
```

### 2.5 `InvestigationState`
```python
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
```
