import json
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Session, select
from app.models.incident import InvestigationStateDB
from app.models.state import InvestigationState, EvidenceItem, Hypothesis, ToolCall, RecommendedAction


def load_state(incident_id: str, session: Session) -> InvestigationState:
    """Load investigation state from DB, or create a new one."""
    db_state = session.exec(
        select(InvestigationStateDB).where(InvestigationStateDB.incident_id == incident_id)
    ).first()

    if not db_state:
        return InvestigationState(incident_id=incident_id)

    raw_next = json.loads(db_state.recommended_next_steps_json)
    rec_actions = []
    rec_steps = []
    for item in raw_next:
        if isinstance(item, dict) and "action_id" in item:
            rec_actions.append(RecommendedAction(**item))
        elif isinstance(item, str):
            rec_steps.append(item)

    return InvestigationState(
        incident_id=incident_id,
        incident_summary=db_state.incident_summary,
        observed_symptoms=json.loads(db_state.observed_symptoms_json),
        current_hypotheses=[
            Hypothesis(**h) for h in json.loads(db_state.current_hypotheses_json)
        ],
        evidence_items=[
            EvidenceItem(**e) for e in json.loads(db_state.evidence_items_json)
        ],
        open_questions=json.loads(db_state.open_questions_json),
        tools_used=[ToolCall(**t) for t in json.loads(db_state.tools_used_json)],
        recommended_next_steps=rec_steps,
        recommended_actions=rec_actions,
        final_conclusion=db_state.final_conclusion,
        conclusion_type=db_state.conclusion_type,
        iteration_count=db_state.iteration_count,
    )


def save_state(state: InvestigationState, session: Session) -> None:
    """Persist investigation state to DB."""
    db_state = session.exec(
        select(InvestigationStateDB).where(
            InvestigationStateDB.incident_id == state.incident_id
        )
    ).first()

    if not db_state:
        db_state = InvestigationStateDB(incident_id=state.incident_id)
        session.add(db_state)

    db_state.incident_summary = state.incident_summary
    db_state.observed_symptoms_json = json.dumps(state.observed_symptoms)
    db_state.current_hypotheses_json = json.dumps(
        [h.model_dump() for h in state.current_hypotheses]
    )
    db_state.evidence_items_json = json.dumps(
        [e.model_dump() for e in state.evidence_items]
    )
    db_state.open_questions_json = json.dumps(state.open_questions)
    db_state.tools_used_json = json.dumps([t.model_dump() for t in state.tools_used])
    
    raw_actions = [a.model_dump() for a in state.recommended_actions]
    db_state.recommended_next_steps_json = json.dumps(raw_actions if raw_actions else state.recommended_next_steps)
    
    db_state.final_conclusion = state.final_conclusion
    db_state.conclusion_type = state.conclusion_type
    db_state.iteration_count = state.iteration_count
    db_state.updated_at = datetime.now(timezone.utc)

    session.commit()
