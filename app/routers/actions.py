from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from app.db import get_session
from app.models.incident import RecommendedActionDB, ApprovalStatus, Incident
from app.agent.state_manager import load_state

router = APIRouter(prefix="/incidents", tags=["actions"])


class ApprovalRequest(BaseModel):
    approved: bool
    approved_by: str
    rejection_reason: Optional[str] = None


@router.get("/{incident_id}/actions")
def list_actions(
    incident_id: str,
    session: Session = Depends(get_session),
):
    """List all recommended actions for an incident."""
    incident = session.exec(
        select(Incident).where(Incident.incident_id == incident_id)
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    state = load_state(incident_id, session)
    return {
        "incident_id": incident_id,
        "actions": [a.model_dump() for a in state.recommended_actions],
        "total": len(state.recommended_actions),
        "approval_required_count": sum(1 for a in state.recommended_actions if a.requires_approval),
    }


@router.post("/{incident_id}/actions/{action_id}/approve")
def approve_action(
    incident_id: str,
    action_id: str,
    request: ApprovalRequest,
    session: Session = Depends(get_session),
):
    """
    Record an approval decision for a high-risk action.
    This endpoint RECORDS the decision only — it does NOT execute the action.
    """
    incident = session.exec(
        select(Incident).where(Incident.incident_id == incident_id)
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    # Check if action exists in DB
    action_db = session.exec(
        select(RecommendedActionDB).where(
            RecommendedActionDB.action_id == action_id,
            RecommendedActionDB.incident_id == incident_id,
        )
    ).first()

    # If not in DB, look it up from state and persist it
    if not action_db:
        state = load_state(incident_id, session)
        matching = next((a for a in state.recommended_actions if a.action_id == action_id), None)
        if not matching:
            raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found for incident '{incident_id}'.")

        action_db = RecommendedActionDB(
            action_id=action_id,
            incident_id=incident_id,
            description=matching.description,
            category=matching.category,
            requires_approval=matching.requires_approval,
            rationale=matching.rationale,
        )
        session.add(action_db)

    if not action_db.requires_approval:
        raise HTTPException(
            status_code=400,
            detail=f"Action '{action_id}' does not require approval (category: {action_db.category}).",
        )

    if action_db.approval_status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Action '{action_id}' has already been {action_db.approval_status}.",
        )

    # Record decision
    action_db.approval_status = ApprovalStatus.APPROVED if request.approved else ApprovalStatus.REJECTED
    action_db.approved_by = request.approved_by
    action_db.approved_at = datetime.now(timezone.utc)
    if not request.approved:
        action_db.rejection_reason = request.rejection_reason

    session.commit()
    session.refresh(action_db)

    return {
        "action_id": action_id,
        "incident_id": incident_id,
        "description": action_db.description,
        "category": action_db.category,
        "approval_status": action_db.approval_status,
        "approved_by": action_db.approved_by,
        "approved_at": action_db.approved_at.isoformat() + "Z" if action_db.approved_at else None,
        "rejection_reason": action_db.rejection_reason,
        "note": "IMPORTANT: This approval is RECORDED ONLY. The action must be executed manually by an authorized engineer.",
    }
