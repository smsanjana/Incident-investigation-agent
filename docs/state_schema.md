# Investigation State Schema

## Overview
The investigation state tracks collected evidence, hypotheses, tool calls, and recommended actions throughout an incident lifecycle.

---

## Pydantic Models (`app/models/state.py`)

### `EvidenceItem`
```python
class EvidenceItem(BaseModel):
    evidence_id: str             # Unique ID (e.g., EVD-001)
    source: str                  # Tool call source (e.g., search_logs:db-client)
    description: str             # Summary description
    raw_content: str             # Log snippet or raw string
    timestamp_collected: str     # ISO-8601 UTC timestamp
    relevance: str               # Diagnostic relevance
```

### `Hypothesis`
```python
class Hypothesis(BaseModel):
    hypothesis_id: str                       # Unique ID (e.g., H-001)
    statement: str                           # Candidate root-cause statement
    supporting_evidence_ids: List[str]       # Array of supporting evidence IDs
    contradicting_evidence_ids: List[str]    # Array of contradicting evidence IDs
    confidence: float                        # Score between 0.0 and 1.0
    confidence_label: Literal["LOW", "MEDIUM", "HIGH"]
    additional_evidence_required: List[str]
    status: Literal["active", "confirmed", "ruled_out", "insufficient_evidence"]
```

### `RecommendedAction`
```python
class RecommendedAction(BaseModel):
    action_id: str
    description: str
    category: Literal["READ_ONLY_DIAGNOSTIC", "LOW_RISK_OPERATIONAL", "HIGH_RISK_OPERATIONAL", "DESTRUCTIVE"]
    requires_approval: bool
    rationale: str
```

### `InvestigationState`
```python
class InvestigationState(BaseModel):
    incident_id: str
    incident_summary: str
    observed_symptoms: List[str]
    current_hypotheses: List[Hypothesis]
    evidence_items: List[EvidenceItem]
    open_questions: List[str]
    tools_used: List[ToolCall]
    recommended_next_steps: List[str]
    recommended_actions: List[RecommendedAction]
    final_conclusion: Optional[str]
    conclusion_type: Optional[str]
    iteration_count: int
```
