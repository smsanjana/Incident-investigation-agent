import os
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

ARTEFACTS_DIR = os.getenv("ARTEFACTS_DIR", "./artefacts")

TOPIC_TO_FILE = {
    "http_503": "http_503.md",
    "db_connection_pool": "db_connection_pool.md",
    "high_latency": "high_latency.md",
    "deployment_regression": "deployment_regression.md",
    "batch_job_interference": "batch_job_interference.md",
    "safe_rollback": "safe_rollback.md",
    "service_restart": "service_restart.md",
}


def _extract_section(content: str, heading: str) -> list[str]:
    """Extract bullet list items from a markdown section."""
    pattern = rf"## {re.escape(heading)}\s*\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return []
    section_text = match.group(1).strip()
    items = []
    for line in section_text.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif line.startswith("1. ") or re.match(r"^\d+\. ", line):
            items.append(re.sub(r"^\d+\.\s+", "", line).strip())
    return items


def get_runbook(topic: str, _force_missing: bool = False) -> Dict[str, Any]:
    """Retrieve a runbook section for the given topic."""

    if _force_missing or topic not in TOPIC_TO_FILE:
        return {
            "error": True,
            "error_code": "TOPIC_NOT_FOUND",
            "message": f"No runbook found for topic '{topic}'. Available topics: {list(TOPIC_TO_FILE.keys())}",
        }

    file_path = os.path.join(ARTEFACTS_DIR, "runbooks", TOPIC_TO_FILE[topic])

    if not os.path.exists(file_path):
        return {
            "error": True,
            "error_code": "TOPIC_NOT_FOUND",
            "message": f"Runbook file not found for topic '{topic}'.",
        }

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract title
    title_match = re.match(r"# (.+)", content)
    title = title_match.group(1) if title_match else topic

    return {
        "error": False,
        "topic": topic,
        "title": title,
        "symptoms": _extract_section(content, "Symptoms"),
        "diagnostic_checks": _extract_section(content, "Diagnostic Checks"),
        "evidence_to_collect": _extract_section(content, "Evidence to Collect"),
        "safe_actions": _extract_section(content, "Safe Actions"),
        "high_risk_actions": _extract_section(content, "High-Risk Actions (Require Human Approval)"),
        "escalation_conditions": _extract_section(content, "Escalation Conditions"),
        "raw_content": content,
    }
