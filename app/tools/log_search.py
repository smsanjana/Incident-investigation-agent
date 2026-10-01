import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

ARTEFACTS_DIR = os.getenv("ARTEFACTS_DIR", "./artefacts")

SERVICE_LOG_FILES = {
    "api-gateway": "api_gateway.jsonl",
    "order-service": "order_service.jsonl",
    "payment-service": "payment_service.jsonl",
    "db-client": "db_client.jsonl",
    "batch-processor": "batch_processor.jsonl",
}

SEVERITY_ORDER = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}


def search_logs(
    service: str,
    start_time: str,
    end_time: str,
    severity: Optional[str] = None,
    keyword: Optional[str] = None,
    correlation_id: Optional[str] = None,
    limit: int = 50,
    _force_timeout: bool = False,  # for testing
) -> Dict[str, Any]:
    """Search logs for a given service and filters."""

    # Simulate timeout for testing
    if _force_timeout:
        return {
            "error": True,
            "error_code": "TIMEOUT",
            "message": "Log search timed out after 30 seconds.",
        }

    # Validate time range
    try:
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    except ValueError as e:
        return {
            "error": True,
            "error_code": "INVALID_TIME_RANGE",
            "message": f"Invalid time format: {e}",
        }

    if start_dt >= end_dt:
        return {
            "error": True,
            "error_code": "INVALID_TIME_RANGE",
            "message": "start_time must be before end_time.",
        }

    # Cap limit
    limit = min(limit, 100)

    # Determine which services to search
    if service == "all":
        services_to_search = list(SERVICE_LOG_FILES.keys())
    else:
        if service not in SERVICE_LOG_FILES:
            return {
                "error": True,
                "error_code": "SERVICE_NOT_FOUND",
                "message": f"No log file found for service '{service}'.",
            }
        services_to_search = [service]

    all_records = []

    for svc in services_to_search:
        log_file = os.path.join(ARTEFACTS_DIR, "logs", SERVICE_LOG_FILES[svc])
        if not os.path.exists(log_file):
            continue

        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Time filter
                try:
                    rec_dt = datetime.fromisoformat(
                        record["timestamp"].replace("Z", "+00:00")
                    )
                except (KeyError, ValueError):
                    continue

                if not (start_dt <= rec_dt <= end_dt):
                    continue

                # Severity filter
                if severity:
                    rec_sev = record.get("severity", "INFO")
                    if SEVERITY_ORDER.get(rec_sev, 0) < SEVERITY_ORDER.get(severity, 0):
                        continue

                # Keyword filter
                if keyword:
                    message = record.get("message", "")
                    if keyword.lower() not in message.lower():
                        continue

                # Correlation ID filter
                if correlation_id:
                    req_id = record.get("request_id", "")
                    trace_id = record.get("trace_id", "")
                    if correlation_id not in (req_id or "") and correlation_id not in (
                        trace_id or ""
                    ):
                        continue

                all_records.append(record)

    # Sort by timestamp
    all_records.sort(key=lambda r: r.get("timestamp", ""))

    total_matched = len(all_records)
    truncated = total_matched > limit
    records = all_records[:limit]

    if total_matched == 0:
        return {
            "error": False,
            "error_code": "EMPTY_RESULT",
            "records": [],
            "total_matched": 0,
            "truncated": False,
            "query_summary": f"No records found for service='{service}' between {start_time} and {end_time}"
            + (f" severity>={severity}" if severity else "")
            + (f" keyword='{keyword}'" if keyword else ""),
        }

    return {
        "error": False,
        "records": records,
        "total_matched": total_matched,
        "truncated": truncated,
        "query_summary": f"Found {total_matched} records for service='{service}'"
        + (f" severity>={severity}" if severity else "")
        + (f" keyword='{keyword}'" if keyword else ""),
    }
