# Safety & Execution Controls

## Non-Negotiable Safety Principles
The AI Incident Investigation Agent is strictly an **investigation and analysis engine**, NOT an autonomous remediation bot.

1. **NO PRODUCTION OPERATION EXECUTION**: The system possesses zero execution tools or SSH/K8s write bindings.
2. **EXECUTION CLAIM DETECTOR**: Output from the LLM or agent orchestrator is audited for forbidden execution claims (*"I restarted the order-service"*, *"I executed the rollback"*). If detected, a `SafetyViolationError` is raised.
3. **MANDATORY APPROVAL FOR HIGH-RISK ACTIONS**: Actions categorized as `HIGH_RISK_OPERATIONAL` or `DESTRUCTIVE` are automatically assigned `requires_approval = True`.
4. **HUMAN APPROVAL IS RECORDED ONLY**: The endpoint `POST /incidents/{id}/actions/{id}/approve` records the authorizing engineer's identity and timestamp. It explicitly refrains from executing any underlying command.

---

## Action Classification Matrix

| Action Category | Example Actions | Requires Approval? |
| :--- | :--- | :---: |
| **`READ_ONLY_DIAGNOSTIC`** | Query logs, retrieve runbooks, check service metadata | **No** |
| **`LOW_RISK_OPERATIONAL`** | Increase log level to DEBUG | **No** |
| **`HIGH_RISK_OPERATIONAL`** | Restart service replicas, kill batch process, alter DB connection pool | **YES** |
| **`DESTRUCTIVE`** | Drop database tables, truncate records, delete production data | **YES** |
