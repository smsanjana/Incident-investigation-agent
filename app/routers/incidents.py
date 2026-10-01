from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime, timezone

from app.db import get_session
from app.models.incident import Incident, IncidentStatus

router = APIRouter(prefix="/incidents", tags=["incidents"])


class CreateIncidentRequest(BaseModel):
    incident_id: Optional[str] = None
    title: str
    affected_service: str
    severity: str = "SEV-2"
    start_time: str
    detection_time: str
    customer_impact: str
    reporter_notes: str = ""
    initial_symptoms: List[str] = []
    tags: List[str] = []


class IncidentResponse(BaseModel):
    incident_id: str
    title: str
    affected_service: str
    severity: str
    start_time: str
    detection_time: str
    customer_impact: str
    reporter_notes: str
    status: str
    initial_symptoms: List[str]
    tags: List[str]
    created_at: str


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    request: CreateIncidentRequest,
    session: Session = Depends(get_session),
):
    """Create a new incident record."""
    # Generate incident_id if not provided
    incident_id = request.incident_id or f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Check for duplicate
    existing = session.exec(
        select(Incident).where(Incident.incident_id == incident_id)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Incident '{incident_id}' already exists.",
        )

    incident = Incident(
        incident_id=incident_id,
        title=request.title,
        affected_service=request.affected_service,
        severity=request.severity,
        start_time=request.start_time,
        detection_time=request.detection_time,
        customer_impact=request.customer_impact,
        reporter_notes=request.reporter_notes,
        initial_symptoms_json=json.dumps(request.initial_symptoms),
        tags_json=json.dumps(request.tags),
    )
    session.add(incident)
    session.commit()
    session.refresh(incident)

    return IncidentResponse(
        incident_id=incident.incident_id,
        title=incident.title,
        affected_service=incident.affected_service,
        severity=incident.severity,
        start_time=incident.start_time,
        detection_time=incident.detection_time,
        customer_impact=incident.customer_impact,
        reporter_notes=incident.reporter_notes,
        status=incident.status,
        initial_symptoms=incident.initial_symptoms,
        tags=incident.tags,
        created_at=incident.created_at.isoformat() + "Z",
    )


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    session: Session = Depends(get_session),
):
    """List all stored incidents."""
    incidents = session.exec(select(Incident).order_by(Incident.created_at.desc())).all()
    return [
        IncidentResponse(
            incident_id=inc.incident_id,
            title=inc.title,
            affected_service=inc.affected_service,
            severity=inc.severity,
            start_time=inc.start_time,
            detection_time=inc.detection_time,
            customer_impact=inc.customer_impact,
            reporter_notes=inc.reporter_notes,
            status=inc.status,
            initial_symptoms=inc.initial_symptoms,
            tags=inc.tags,
            created_at=inc.created_at.isoformat() + "Z",
        )
        for inc in incidents
    ]


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: str,
    session: Session = Depends(get_session),
):
    """Get incident details."""
    incident = session.exec(
        select(Incident).where(Incident.incident_id == incident_id)
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    return IncidentResponse(
        incident_id=incident.incident_id,
        title=incident.title,
        affected_service=incident.affected_service,
        severity=incident.severity,
        start_time=incident.start_time,
        detection_time=incident.detection_time,
        customer_impact=incident.customer_impact,
        reporter_notes=incident.reporter_notes,
        status=incident.status,
        initial_symptoms=incident.initial_symptoms,
        tags=incident.tags,
        created_at=incident.created_at.isoformat() + "Z",
    )
