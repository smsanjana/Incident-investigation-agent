from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
import json
from datetime import datetime, timezone

from app.db import get_session
from app.models.incident import Incident, IncidentStatus, InvestigationStateDB
from app.agent.state_manager import load_state, save_state
from app.agent.orchestrator import run_investigation

router = APIRouter(prefix="/incidents", tags=["investigation"])


@router.post("/{incident_id}/investigate")
def trigger_investigation(
    incident_id: str,
    session: Session = Depends(get_session),
):
    """Trigger an agentic investigation for the incident."""
    incident = session.exec(
        select(Incident).where(Incident.incident_id == incident_id)
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    if incident.status == IncidentStatus.CONCLUDED:
        raise HTTPException(
            status_code=409, detail="Investigation already concluded. Retrieve the report."
        )

    # Update status to investigating
    incident.status = IncidentStatus.INVESTIGATING
    incident.updated_at = datetime.now(timezone.utc)
    session.commit()

    # Build incident brief for LLM
    incident_brief = {
        "incident_id": incident.incident_id,
        "title": incident.title,
        "affected_service": incident.affected_service,
        "severity": incident.severity,
        "start_time": incident.start_time,
        "detection_time": incident.detection_time,
        "customer_impact": incident.customer_impact,
        "reporter_notes": incident.reporter_notes,
        "initial_symptoms": incident.initial_symptoms,
    }

    # Load existing state (or create new)
    state = load_state(incident_id, session)

    def _save(s):
        save_state(s, session)

    # Run investigation (synchronous)
    state = run_investigation(
        incident_id=incident_id,
        incident_brief=incident_brief,
        state=state,
        save_state_fn=_save,
    )

    # Save final state
    save_state(state, session)

    # Update incident status
    incident.status = IncidentStatus.CONCLUDED
    incident.updated_at = datetime.now(timezone.utc)
    session.commit()

    return {
        "incident_id": incident_id,
        "status": "concluded",
        "conclusion_type": state.conclusion_type,
        "hypotheses_count": len(state.current_hypotheses),
        "evidence_count": len(state.evidence_items),
        "tools_used_count": len(state.tools_used),
        "message": "Investigation complete. Retrieve the report at GET /incidents/{id}/report",
    }
