from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
import json

from app.db import get_session
from app.models.incident import Incident, InvestigationStateDB
from app.agent.report_builder import build_report
from app.agent.state_manager import load_state

router = APIRouter(prefix="/incidents", tags=["report"])


@router.get("/{incident_id}/report")
def get_report(
    incident_id: str,
    session: Session = Depends(get_session),
):
    """Get the structured final investigation report."""
    incident = session.exec(
        select(Incident).where(Incident.incident_id == incident_id)
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    state_db = session.exec(
        select(InvestigationStateDB).where(InvestigationStateDB.incident_id == incident_id)
    ).first()

    if not state_db:
        raise HTTPException(
            status_code=404,
            detail="No investigation state found. Run POST /incidents/{id}/investigate first.",
        )

    state = load_state(incident_id, session)
    report = build_report(incident, state)
    return report
