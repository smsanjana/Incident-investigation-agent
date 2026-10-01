# Project Constitution: AI Incident Investigation Agent

## Status & Governance
- **Version**: 1.0.0
- **Applies To**: AI Incident Investigation Agent
- **Enforcement**: Mandatory for all specification documents, implementation plans, code changes, tool definitions, agent prompts, and automated test suites.
- **Rule of Precedence**: In any conflict between implementation details and this Constitution, this Constitution takes absolute precedence.

---

## Non-Negotiable Core Principles

### 1. EVIDENCE FIRST
Every root-cause conclusion produced by the agent MUST be directly supported by empirical evidence collected through the supplied inspection tools (`search_logs`, `get_runbook`, `get_service_metadata`, `get_deployment_events`). 
- No root-cause conclusion may be declared based solely on assumptions, zero-evidence reasoning, or unverified reporter notes.
- Each evidence item must be tied to its authoritative tool source, raw content snippet, and timestamp.

### 2. NO FABRICATION
The agent MUST NEVER fabricate, hallucinate, synthesize, or invent:
- Log records, log entries, or log severity counts
- Infrastructure or deployment events
- Service configuration or metadata properties
- Runbook sections or operational guidance
- Timestamps, IDs, trace headers, or correlation tokens
- Evidence items or tool execution outputs
- Claims of executed production operations

### 3. UNCERTAINTY MUST BE EXPLICIT
When collected evidence is incomplete, ambiguous, missing critical sections, or evenly split between competing hypotheses:
- The system MUST return `INSUFFICIENT_EVIDENCE` as its explicit conclusion type.
- The system MUST NOT force a guess, coin-toss ranking, or unbacked single root cause.
- The final report must explicitly itemize all identified evidence gaps and missing data sources.

### 4. TRACEABLE REASONING
Every hypothesis generated and evaluated during an investigation MUST strictly maintain traceable structure:
- **Hypothesis Statement**: Clear, objective description of the potential cause.
- **Supporting Evidence**: Array of specific evidence item IDs (`EVD-xxx`) validating the hypothesis.
- **Contradicting Evidence**: Array of specific evidence item IDs (`EVD-xxx`) contradicting or disproving the hypothesis.
- **Confidence Score & Label**: Quantitative float (0.0 to 1.0) and qualitative label (`LOW`, `MEDIUM`, `HIGH`).
- **Additional Evidence Required**: Explicit list of missing telemetry or artifacts needed for further validation.

### 5. TOOL-FIRST INVESTIGATION
The agent MUST inspect relevant system artifacts using diagnostic tools BEFORE formulating or finalizing hypotheses and conclusions.
- Investigation workflow must begin with systematic telemetry gathering (metadata, deployment timeline, gateway/service logs, runbooks).
- Direct jump to final conclusions without invoking investigative tools is strictly prohibited.

### 6. SAFETY FIRST
The application is designed strictly as an **investigation assistant**, NOT an autonomous remediation agent.
- The system provides diagnostic clarity, evidence correlation, and safety-classified action recommendations.
- Under no circumstances will the system act as an autonomous remediation bot that executes changes on live infrastructure.

### 7. NO PRODUCTION EXECUTION
The agent MUST NEVER execute production operations, remediation commands, environment changes, or infrastructure mutations.
- All actions recommended by the system are advisory only.
- Any model output claiming to have executed an action (e.g., "I restarted the service", "I rolled back the deployment") MUST trigger an immediate `SafetyViolationError` and halt the investigation cycle.

### 8. HUMAN APPROVAL
High-risk operational actions and destructive actions MUST be clearly identified and marked as requiring explicit human approval (`requires_approval=True`).
- Action categories:
  1. `READ_ONLY_DIAGNOSTIC`: Log queries, runbook retrievals, status checks (Safe).
  2. `LOW_RISK_OPERATIONAL`: Rescheduling jobs, scaling read replicas (Low risk).
  3. `HIGH_RISK_OPERATIONAL`: Service restarts, deployment rollbacks, connection pool modifications (Requires Human Approval).
  4. `DESTRUCTIVE`: Data deletion, table drops, data truncation (Requires Human Approval).
- Approval API endpoints (`POST /incidents/{id}/actions/{action_id}/approve`) RECORD human authorization decisions only. They NEVER execute the underlying command.

### 9. STRUCTURED STATE
Investigation state MUST be preserved deterministically throughout the investigation lifecycle and persisted to database storage. State schema must include:
- Incident summary & observed symptoms
- Active & historical hypotheses (with supporting/contradicting evidence links)
- Accumulated evidence items with raw content snippets
- Open questions & evidence gaps
- Audit log of tool calls invoked (with arguments, execution time, and success/failure status)
- Categorized recommended actions (with risk flags and approval status)
- Final conclusion text & conclusion classification type (`ROOT_CAUSE_IDENTIFIED`, `INSUFFICIENT_EVIDENCE`, `MULTIPLE_CAUSES`, `INCONCLUSIVE`)

### 10. TESTABILITY
All critical agent behaviors, tool contracts, safety mechanisms, state transitions, and edge cases MUST be covered by comprehensive automated test suites.
- Test suites must validate: tool execution, empty query handling, timeout resiliency, malformed data handling, high-risk action flagging, safety intercept triggers on execution claims, and correct identification of `INSUFFICIENT_EVIDENCE`.

### 11. FAIL SAFELY
The system MUST handle all real-world operational failure modes gracefully and explicitly:
- **Empty log results**: Handled without error, returning zero-matched query summaries.
- **Tool timeouts**: Intercepted with standard error objects (`TIMEOUT`), preserving current state.
- **Malformed tool responses / YAML / JSON**: Caught and returned as structured errors (`MALFORMED_METADATA`).
- **Missing runbook topics**: Handled with `TOPIC_NOT_FOUND` listing available alternative topics.
- **Contradictory evidence**: Preserved in hypothesis state to lower confidence ratings naturally.

### 12. BACKWARD COMPATIBILITY
Existing, verified application functionality MUST be preserved across all iterations:
- Existing FastAPI endpoints, SQLModel schemas, tool contracts, test suites (83 passing tests), and static frontend assets must remain fully functional.
- Modifications to core interfaces must maintain backward compatibility unless explicitly dictated by project specification changes.

---

## Compliance & Audit Matrix

| Principle | Verification Method | Enforcement Layer |
| :--- | :--- | :--- |
| **Evidence First** | Pytest assertions on report output & evidence mapping | `report_builder.py` / Pytest |
| **No Fabrication** | Audit logs vs real tool output comparisons | `orchestrator.py` |
| **Explicit Uncertainty** | Scenario verification (`INC-002`) | `test_insufficient.py` |
| **Traceable Reasoning** | Schema validation on `Hypothesis` model | `state.py` Pydantic models |
| **Tool-First** | Step iteration check in orchestrator | `orchestrator.py` |
| **Safety First / No Execution** | Regex intercept check (`check_execution_claim`) | `safety.py` -> `SafetyViolationError` |
| **Human Approval** | Action classification parser (`classify_action`) | `actions.py` / `safety.py` |
| **Structured State** | SQLModel DB schema & JSON serialization | `state_manager.py` / `db.py` |
| **Testability** | Pytest suite execution | `pytest tests/ -v` |
| **Fail Safely** | Fallback & error handling tests | `test_timeout.py`, `test_malformed.py` |
| **Backward Compatibility** | Automated test suite execution | 83 passing test suite |
