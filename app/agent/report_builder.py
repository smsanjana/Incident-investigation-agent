from datetime import datetime, timezone
from typing import Dict, Any, List
from app.models.state import InvestigationState, Hypothesis, EvidenceItem
from app.models.incident import Incident


def build_report(incident: Incident, state: InvestigationState) -> Dict[str, Any]:
    """Build a structured final investigation report."""

    # Sort hypotheses by confidence descending
    sorted_hypotheses = sorted(
        state.current_hypotheses, key=lambda h: h.confidence, reverse=True
    )

    most_likely = sorted_hypotheses[0] if sorted_hypotheses else None
    alternatives = sorted_hypotheses[1:] if len(sorted_hypotheses) > 1 else []

    # Build evidence list
    evidence_reviewed = [
        {
            "evidence_id": e.evidence_id,
            "source": e.source,
            "description": e.description,
            "relevance": e.relevance,
        }
        for e in state.evidence_items
    ]

    # Gather evidence gaps from hypotheses
    evidence_gaps = []
    for h in state.current_hypotheses:
        for gap in h.additional_evidence_required:
            if gap not in evidence_gaps:
                evidence_gaps.append(gap)
    evidence_gaps.extend(state.open_questions)

    # Classify recommended actions
    from app.agent.safety import classify_action
    diagnostic_actions = []
    remediation_actions = []
    approval_required_actions = []

    for action in state.recommended_actions:
        if action.requires_approval:
            approval_required_actions.append({
                "action_id": action.action_id,
                "description": action.description,
                "category": action.category,
                "rationale": action.rationale,
            })
        elif action.category == "READ_ONLY_DIAGNOSTIC":
            diagnostic_actions.append(action.description)
        else:
            remediation_actions.append(action.description)

    # Build timeline from tools used
    timeline = []
    for tool_call in state.tools_used:
        timeline.append({
            "time": tool_call.called_at,
            "event": f"Tool invoked: {tool_call.tool_name}",
            "summary": tool_call.result_summary,
            "success": tool_call.success,
        })

    # Add incident events to timeline
    timeline.insert(0, {"time": incident.start_time, "event": "Incident start", "summary": "Symptoms first observed."})
    timeline.insert(1, {"time": incident.detection_time, "event": "Incident detected", "summary": "Alert fired, investigation begins."})

    return {
        "report_id": f"RPT-{incident.incident_id}",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "incident_summary": {
            "incident_id": incident.incident_id,
            "title": incident.title,
            "affected_service": incident.affected_service,
            "severity": incident.severity,
            "start_time": incident.start_time,
            "detection_time": incident.detection_time,
            "customer_impact": incident.customer_impact,
        },
        "timeline": sorted(timeline, key=lambda e: e.get("time", "")),
        "most_likely_cause": {
            "hypothesis_id": most_likely.hypothesis_id if most_likely else None,
            "statement": most_likely.statement if most_likely else "No conclusion reached.",
            "confidence": most_likely.confidence if most_likely else 0.0,
            "confidence_label": most_likely.confidence_label if most_likely else "LOW",
            "supporting_evidence_count": len(most_likely.supporting_evidence_ids) if most_likely else 0,
            "contradicting_evidence_count": len(most_likely.contradicting_evidence_ids) if most_likely else 0,
            "status": most_likely.status if most_likely else "insufficient_evidence",
        } if most_likely else None,
        "alternative_hypotheses": [
            {
                "hypothesis_id": h.hypothesis_id,
                "statement": h.statement,
                "confidence": h.confidence,
                "confidence_label": h.confidence_label,
                "status": h.status,
                "supporting_evidence_count": len(h.supporting_evidence_ids),
                "contradicting_evidence_count": len(h.contradicting_evidence_ids),
            }
            for h in alternatives
        ],
        "evidence_reviewed": evidence_reviewed,
        "evidence_gaps": list(set(evidence_gaps)),
        "recommended_diagnostic_actions": diagnostic_actions,
        "recommended_remediation": remediation_actions,
        "actions_requiring_approval": approval_required_actions,
        "conclusion": {
            "type": state.conclusion_type or "INVESTIGATING",
            "text": state.final_conclusion or "Investigation in progress.",
        },
        "confidence_and_limitations": {
            "overall_confidence": most_likely.confidence if most_likely else 0.0,
            "confidence_label": most_likely.confidence_label if most_likely else "LOW",
            "limitations": [
                f"Evidence gap: {gap}" for gap in (list(set(evidence_gaps))[:5])
            ] + (
                ["Conflicting evidence present — see alternative hypotheses."]
                if alternatives else []
            ),
            "tools_invoked": len(state.tools_used),
            "evidence_items_collected": len(state.evidence_items),
            "hypotheses_evaluated": len(state.current_hypotheses),
        },
        "investigation_metadata": {
            "iterations": state.iteration_count,
            "tools_used": [t.tool_name for t in state.tools_used],
        },
    }
