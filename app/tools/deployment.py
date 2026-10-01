import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

ARTEFACTS_DIR = os.getenv("ARTEFACTS_DIR", "./artefacts")
EVENTS_FILE = os.path.join(ARTEFACTS_DIR, "infrastructure_events.json")


def get_deployment_events(
    service: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 50,
    _force_timeout: bool = False,
) -> Dict[str, Any]:
    """Retrieve infrastructure/deployment events with optional filters."""

    if _force_timeout:
        return {
            "error": True,
            "error_code": "TIMEOUT",
            "message": "Deployment event query timed out.",
        }

    # Validate time range
    start_dt = end_dt = None
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        except ValueError:
            return {
                "error": True,
                "error_code": "INVALID_TIME_RANGE",
                "message": f"Invalid start_time format: {start_time}",
            }
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        except ValueError:
            return {
                "error": True,
                "error_code": "INVALID_TIME_RANGE",
                "message": f"Invalid end_time format: {end_time}",
            }

    if start_dt and end_dt and start_dt >= end_dt:
        return {
            "error": True,
            "error_code": "INVALID_TIME_RANGE",
            "message": "start_time must be before end_time.",
        }

    if not os.path.exists(EVENTS_FILE):
        return {"error": False, "events": [], "total": 0}

    with open(EVENTS_FILE, "r", encoding="utf-8") as f:
        try:
            events = json.load(f)
        except json.JSONDecodeError as e:
            return {
                "error": True,
                "error_code": "MALFORMED_METADATA",
                "message": f"Infrastructure events file is malformed: {e}",
            }

    filtered = []
    for evt in events:
        # Service filter
        if service and evt.get("service", "") != service:
            continue

        # Time filter
        if start_dt or end_dt:
            try:
                evt_dt = datetime.fromisoformat(
                    evt["timestamp"].replace("Z", "+00:00")
                )
            except (KeyError, ValueError):
                continue
            if start_dt and evt_dt < start_dt:
                continue
            if end_dt and evt_dt > end_dt:
                continue

        # Event type filter
        if event_type and evt.get("event_type", "") != event_type:
            continue

        filtered.append(evt)

    limit = min(limit, 100)
    total = len(filtered)
    return {"error": False, "events": filtered[:limit], "total": total}
