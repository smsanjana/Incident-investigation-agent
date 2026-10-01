import re
from typing import Dict, Any, Tuple
from app.models.incident import ActionCategory


# Keywords that indicate a high-risk or destructive action
HIGH_RISK_PATTERNS = [
    r"restart.*service",
    r"restart.*replica",
    r"restart.*pod",
    r"scale.*replica",
    r"rollback.*deployment",
    r"roll.*back",
    r"kubectl rollout",
    r"terminate.*connection",
    r"kill.*job",
    r"disable.*job",
    r"delete.*data",
    r"drop.*table",
    r"modify.*pool",
    r"change.*pool.*size",
    r"increase.*pool",
    r"scale.*down",
    r"kubectl.*delete",
]

DESTRUCTIVE_PATTERNS = [
    r"delete.*production",
    r"drop.*database",
    r"truncate.*table",
    r"remove.*data",
    r"wipe",
    r"destroy",
    r"format",
]

# Patterns that indicate the model is claiming to have EXECUTED an action
EXECUTION_CLAIM_PATTERNS = [
    r"i have restarted",
    r"i restarted",
    r"i have rolled back",
    r"i rolled back",
    r"i have terminated",
    r"i terminated",
    r"i have disabled",
    r"i disabled",
    r"i have killed",
    r"i killed",
    r"i have executed",
    r"i executed the",
    r"i have performed the rollback",
    r"successfully restarted",
    r"successfully rolled back",
    r"deployment has been rolled back",
    r"service has been restarted",
    r"i have increased the pool",
    r"i increased the pool",
    r"i have deleted",
    r"i deleted",
    r"i have modified the production",
]


class SafetyViolationError(Exception):
    """Raised when a model response claims to have executed a production action."""

    def __init__(self, message: str, matched_pattern: str):
        self.message = message
        self.matched_pattern = matched_pattern
        super().__init__(message)


def classify_action(action_text: str) -> Tuple[ActionCategory, bool]:
    """
    Classify an action description into a category and determine if it requires approval.
    Returns (category, requires_approval).
    """
    text_lower = action_text.lower()

    for pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, text_lower):
            return ActionCategory.DESTRUCTIVE, True

    for pattern in HIGH_RISK_PATTERNS:
        if re.search(pattern, text_lower):
            return ActionCategory.HIGH_RISK_OPERATIONAL, True

    # Low-risk operational patterns
    low_risk_patterns = [
        r"reschedule.*job",
        r"add replica",
        r"scale.*up",
        r"enable.*alerting",
        r"update.*runbook",
        r"adjust.*threshold",
    ]
    for pattern in low_risk_patterns:
        if re.search(pattern, text_lower):
            return ActionCategory.LOW_RISK_OPERATIONAL, False

    return ActionCategory.READ_ONLY_DIAGNOSTIC, False


def check_execution_claim(text: str) -> None:
    """
    Scan model response text for claims that a production action was executed.
    Raises SafetyViolationError if found.
    """
    text_lower = text.lower()
    for pattern in EXECUTION_CLAIM_PATTERNS:
        if re.search(pattern, text_lower):
            raise SafetyViolationError(
                f"SAFETY VIOLATION: Model response claims to have executed a production action. "
                f"This agent is an investigation assistant only and cannot execute actions. "
                f"Matched pattern: '{pattern}'",
                matched_pattern=pattern,
            )


def is_action_safe_to_recommend(category: ActionCategory) -> bool:
    """Returns True if the action can be recommended without approval."""
    return category in (
        ActionCategory.READ_ONLY_DIAGNOSTIC,
        ActionCategory.LOW_RISK_OPERATIONAL,
    )
