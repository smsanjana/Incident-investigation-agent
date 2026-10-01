from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import json

from app.db import get_session
from app.models.incident import Incident, InvestigationStateDB
from app.models.state import EvidenceItem, Hypothesis, ToolCall

router = APIRouter(prefix="/incidents", tags=["evidence"])


@router.get("/{incident_id}/evidence")
def get_evidence(
    incident_id: str,
    session: Session = Depends(get_session),
):
    """Get all collected evidence for an incident."""
    incident = session.exec(
        select(Incident).where(Incident.incident_id == incident_id)
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    state_db = session.exec(
        select(InvestigationStateDB).where(InvestigationStateDB.incident_id == incident_id)
    ).first()

    if not state_db:
        return {
            "incident_id": incident_id,
            "evidence_items": [],
            "hypotheses": [],
            "tools_used": [],
            "open_questions": [],
            "message": "No investigation has been run yet.",
        }

    evidence_items = json.loads(state_db.evidence_items_json)
    hypotheses = json.loads(state_db.current_hypotheses_json)
    tools_used = json.loads(state_db.tools_used_json)
    open_questions = json.loads(state_db.open_questions_json)

    return {
        "incident_id": incident_id,
        "evidence_items": evidence_items,
        "evidence_count": len(evidence_items),
        "hypotheses": hypotheses,
        "hypotheses_count": len(hypotheses),
        "tools_used": tools_used,
        "tools_used_count": len(tools_used),
        "open_questions": open_questions,
    }
