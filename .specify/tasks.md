# Implementation Task Breakdown: AI Incident Investigation Agent

## Document Metadata
- **Title**: Spec Kit Implementation Task Breakdown
- **Specification Ref**: [Feature Specification](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md)
- **Constitution Ref**: [Project Constitution](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/constitution.md)
- **Plan Ref**: [Technical Implementation Plan](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/plan.md)

---

## Task Matrix Overview

| Phase | Description | Tasks Count | Baseline Status |
| :--- | :--- | :---: | :--- |
| **PHASE 1** | Project foundation | 3 | Complete & Verified |
| **PHASE 2** | Data models and database | 3 | Complete & Verified |
| **PHASE 3** | Incident APIs | 3 | Complete & Verified |
| **PHASE 4** | Investigation state | 3 | Complete & Verified |
| **PHASE 5** | Investigation tools | 5 | Complete & Verified |
| **PHASE 6** | LLM/agent orchestration | 4 | Complete & Verified |
| **PHASE 7** | Evidence-based hypothesis reasoning | 4 | Complete & Verified |
| **PHASE 8** | Safety and action handling | 4 | Complete & Verified |
| **PHASE 9** | Report generation | 3 | Complete & Verified |
| **PHASE 10**| Artefacts | 3 | Complete & Verified |
| **PHASE 11**| Frontend | 3 | Complete & Verified |
| **PHASE 12**| Testing | 10 | Complete (83/83 Passing) |
| **PHASE 13**| Documentation | 3 | Complete & Verified |
| **PHASE 14**| End-to-end validation | 3 | Complete & Verified |

---

## Detailed Task Breakdown

### PHASE 1 — Project Foundation
#### `TASK-101`: Project Structure & Environment Verification
- **Description**: Verify Python 3.11+ environment, dependency lockfile, `.env` file parsing, and core FastAPI application lifecycle setup.
- **Source Requirement**: [Feature Spec Section 1](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#1-executive-summary--purpose), `NFR-4`
- **Affected Files**: [`requirements.txt`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/requirements.txt), [`.env.example`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.env.example), [`app/main.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/main.py)
- **Dependencies**: None
- **Acceptance Condition**: `uvicorn app.main:app` boots successfully without missing package errors.

#### `TASK-102`: CORS & Static Asset Route Mounting
- **Description**: Configure FastAPI CORS middleware and mount `/static` and `/artefacts` static file directories.
- **Source Requirement**: [Feature Spec Section 4](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#4-system-architecture--component-boundaries)
- **Affected Files**: [`app/main.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/main.py)
- **Dependencies**: `TASK-101`
- **Acceptance Condition**: `GET /` serves [`index.html`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/static/index.html) and `/health` returns `{"status": "healthy"}`.

#### `TASK-103`: Modern UTC Datetime Standardization
- **Description**: Refactor all legacy `datetime.utcnow()` references to modern timezone-aware `datetime.now(timezone.utc)` across main application modules.
- **Source Requirement**: [Constitution Principle 12](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/constitution.md#12-backward-compatibility)
- **Affected Files**: [`app/main.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/main.py), [`app/agent/report_builder.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/report_builder.py), [`app/routers/*.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/routers)
- **Dependencies**: `TASK-101`
- **Acceptance Condition**: Pytest execution emits 0 Python 3.12 datetime deprecation warnings.

---

### PHASE 2 — Data Models and Database
#### `TASK-201`: SQLModel Engine & SQLite Initialization
- **Description**: Implement database engine initialization with SQLite `check_same_thread=False` and SQLModel metadata table creation on app startup.
- **Source Requirement**: `DR-2`, [Feature Spec Section 5](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#5-investigation-state-specification--validation-rules)
- **Affected Files**: [`app/db.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/db.py)
- **Dependencies**: `TASK-101`
- **Acceptance Condition**: SQLite database file `incident_agent.db` is created with tables initialized cleanly.

#### `TASK-202`: Incident, State, and Action DB Models
- **Description**: Define SQLModel tables `Incident`, `InvestigationStateDB`, and `RecommendedActionDB` with JSON string fields for array serialization.
- **Source Requirement**: `DR-2`, [Data Model Spec Section 1](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/data-model.md#1-database-schema-sqlmodel--sqlite)
- **Affected Files**: [`app/models/incident.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/models/incident.py)
- **Dependencies**: `TASK-201`
- **Acceptance Condition**: Database schema matches table declarations and supports indexing on `incident_id` and `action_id`.

#### `TASK-203`: Runtime Pydantic State Schemas
- **Description**: Define Pydantic models for `EvidenceItem`, `Hypothesis`, `ToolCall`, `RecommendedAction`, and `InvestigationState`.
- **Source Requirement**: [Feature Spec Section 5](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#5-investigation-state-specification--validation-rules), [Data Model Spec Section 2](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/data-model.md#2-runtime-pydantic-models-appmodelsstatepy)
- **Affected Files**: [`app/models/state.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/models/state.py)
- **Dependencies**: `TASK-202`
- **Acceptance Condition**: Pydantic models serialize/deserialize JSON cleanly and validate confidence score boundaries (`0.0 <= confidence <= 1.0`).

---

### PHASE 3 — Incident APIs
#### `TASK-301`: `POST /incidents` Endpoint
- **Description**: Implement REST endpoint to ingest incident briefs, validate required fields, generate incident IDs, and persist records to DB.
- **Source Requirement**: `FR-1`, [API Contracts Section 1](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/contracts/api-contracts.md#1-post-incidents)
- **Affected Files**: [`app/routers/incidents.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/routers/incidents.py)
- **Dependencies**: `TASK-202`, `TASK-203`
- **Acceptance Condition**: `POST /incidents` returns `201 Created` with initialized status `"open"`.

#### `TASK-302`: `GET /incidents` and `GET /incidents/{incident_id}` Endpoints
- **Description**: Implement REST endpoints to list stored incidents and retrieve detailed status by ID.
- **Source Requirement**: [API Contracts Section 2](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/contracts/api-contracts.md#2-get-incidentsincident_id)
- **Affected Files**: [`app/routers/incidents.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/routers/incidents.py)
- **Dependencies**: `TASK-301`
- **Acceptance Condition**: Returns `200 OK` with incident object or `404 Not Found` for invalid IDs.

#### `TASK-303`: Duplicate Incident ID Handling
- **Description**: Add conflict check preventing duplicate incident registration under the same `incident_id`.
- **Source Requirement**: [API Contracts Section 1](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/contracts/api-contracts.md#1-post-incidents)
- **Affected Files**: [`app/routers/incidents.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/routers/incidents.py)
- **Dependencies**: `TASK-301`
- **Acceptance Condition**: Attempting to re-create an existing `incident_id` returns HTTP `409 Conflict`.

---

### PHASE 4 — Investigation State
#### `TASK-401`: State Loading & DB Deserialization
- **Description**: Implement `load_state(incident_id, session)` to query `InvestigationStateDB` and return instantiated `InvestigationState` object.
- **Source Requirement**: [Feature Spec Section 5](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#5-investigation-state-specification--validation-rules)
- **Affected Files**: [`app/agent/state_manager.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/state_manager.py)
- **Dependencies**: `TASK-202`, `TASK-203`
- **Acceptance Condition**: Correctly maps JSON string arrays in DB into Pydantic models.

#### `TASK-402`: State Persistence & Serializing
- **Description**: Implement `save_state(state, session)` to serialize Pydantic `InvestigationState` into JSON fields and commit to `InvestigationStateDB`.
- **Source Requirement**: [Constitution Principle 9](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/constitution.md#9-structured-state)
- **Affected Files**: [`app/agent/state_manager.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/state_manager.py)
- **Dependencies**: `TASK-401`
- **Acceptance Condition**: State changes during multi-turn investigation steps are safely committed to database.

#### `TASK-403`: Evidence & Hypothesis State Mutators
- **Description**: Add helper methods to `InvestigationState` for deduplicated evidence addition (`add_evidence`) and hypothesis lookups.
- **Source Requirement**: [Feature Spec Section 5](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#5-investigation-state-specification--validation-rules)
- **Affected Files**: [`app/models/state.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/models/state.py)
- **Dependencies**: `TASK-203`
- **Acceptance Condition**: Adding an existing `evidence_id` twice updates existing evidence without duplication.

---

### PHASE 5 — Investigation Tools
#### `TASK-501`: `search_logs` Tool Implementation & Tests
- **Description**: Implement log search parser over JSONL files in `artefacts/logs/` with service, time range, severity, keyword, and correlation ID filters.
- **Source Requirement**: [Feature Spec Section 6.1](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#61-search_logs)
- **Affected Files**: [`app/tools/log_search.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/tools/log_search.py), [`tests/test_tools.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_tools.py)
- **Dependencies**: `TASK-101`
- **Acceptance Condition**: Correctly returns matched records, preserves original timestamps, and enforces result limit limits.

#### `TASK-502`: Empty Log Search & Time Range Validation Tasks
- **Description**: Add explicit error handling in `search_logs` for `INVALID_TIME_RANGE` and zero-matched queries returning clean summaries.
- **Source Requirement**: [Feature Spec Section 9](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#9-failure-handling--resiliency-specification)
- **Affected Files**: [`app/tools/log_search.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/tools/log_search.py), [`tests/test_log_empty.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_log_empty.py)
- **Dependencies**: `TASK-501`
- **Acceptance Condition**: `start_time >= end_time` returns `error: true, error_code: "INVALID_TIME_RANGE"`; empty log queries return `error: false, records: []`.

#### `TASK-503`: `get_runbook` Tool & Missing Topic Tasks
- **Description**: Implement markdown section extractor for operational runbooks in `artefacts/runbooks/` and return `TOPIC_NOT_FOUND` on unknown topics.
- **Source Requirement**: [Feature Spec Section 6.2](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#62-get_runbook)
- **Affected Files**: [`app/tools/runbook.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/tools/runbook.py), [`tests/test_runbook_missing.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_runbook_missing.py)
- **Dependencies**: `TASK-101`
- **Acceptance Condition**: Parses `Symptoms`, `Diagnostic Checks`, and `Safe Actions`; missing topics return available alternative topics list.

#### `TASK-504`: `get_service_metadata` Tool & Malformed YAML Tasks
- **Description**: Implement YAML metadata reader for `service_metadata.yaml` with explicit handling for `SERVICE_NOT_FOUND` and `MALFORMED_METADATA`.
- **Source Requirement**: [Feature Spec Section 6.3](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#63-get_service_metadata)
- **Affected Files**: [`app/tools/metadata.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/tools/metadata.py), [`tests/test_malformed.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_malformed.py)
- **Dependencies**: `TASK-101`
- **Acceptance Condition**: Correctly returns database pool sizes and dependencies; corrupted YAML returns `MALFORMED_METADATA`.

#### `TASK-505`: `get_deployment_events` Tool & Timeout Tasks
- **Description**: Implement infrastructure event reader for `infrastructure_events.json` with service/time filtering and simulated timeout handling.
- **Source Requirement**: [Feature Spec Section 6.4](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#64-get_deployment_events)
- **Affected Files**: [`app/tools/deployment.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/tools/deployment.py), [`tests/test_timeout.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_timeout.py)
- **Dependencies**: `TASK-101`
- **Acceptance Condition**: Returns deployment completion events and batch job timeline records; `_force_timeout=True` returns `error_code: "TIMEOUT"`.

---

### PHASE 6 — LLM/Agent Orchestration
#### `TASK-601`: LiteLLM Integration & Tool Definition Schemas
- **Description**: Define OpenAI-compatible tool calling definitions for all 4 diagnostic tools + `update_investigation_state` in orchestrator.
- **Source Requirement**: [Tool Contracts Spec](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/contracts/tool-contracts.md)
- **Affected Files**: [`app/agent/orchestrator.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/orchestrator.py)
- **Dependencies**: `TASK-501` to `TASK-505`
- **Acceptance Condition**: `TOOL_DEFINITIONS` dictionary validates against OpenAI tool call schema specs.

#### `TASK-602`: Agent Multi-Turn Investigation Loop
- **Description**: Implement `run_investigation()` multi-turn function-calling loop with system prompt, tool dispatcher, state update application, and max iteration limit (15).
- **Source Requirement**: [Feature Spec Section 10](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#10-investigation-workflow--state-transitions)
- **Affected Files**: [`app/agent/orchestrator.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/orchestrator.py)
- **Dependencies**: `TASK-601`, `TASK-402`
- **Acceptance Condition**: Loop invokes tools sequentially, updates investigation state, and terminates when `done=True` or max iterations reached.

#### `TASK-603`: Deterministic Rule-Based Fallback Engine
- **Description**: Implement `_run_rule_based_investigation()` fallback engine to execute structured telemetry gathering when LLM API keys are unconfigured or API calls fail.
- **Source Requirement**: [Research Spec Section 2.3](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/research.md#23-llm-orchestration-litellm)
- **Affected Files**: [`app/agent/orchestrator.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/orchestrator.py)
- **Dependencies**: `TASK-602`
- **Acceptance Condition**: Agent investigation succeeds deterministically in offline environments without LLM API keys.

#### `TASK-604`: Trigger Investigation API Endpoint
- **Description**: Implement `POST /incidents/{incident_id}/investigate` router endpoint to transition incident status to `"investigating"` and run the orchestrator loop.
- **Source Requirement**: [API Contracts Section 3](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/contracts/api-contracts.md#3-post-incidentsincident_idinvestigate)
- **Affected Files**: [`app/routers/investigation.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/routers/investigation.py)
- **Dependencies**: `TASK-602`, `TASK-301`
- **Acceptance Condition**: Returns `200 OK` with `status: "concluded"`, saving final state in database.

---

### PHASE 7 — Evidence-Based Hypothesis Reasoning
#### `TASK-701`: Quantitative Sufficiency & Confidence Classifier
- **Description**: Implement rule engine enforcing Quantitative Sufficiency Criteria ($\ge 2$ tool sources, 0 unrefuted contradictions, confidence $\ge 0.80$, delta $\ge 0.35$).
- **Source Requirement**: [Feature Spec Section 7.1](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#71-quantitative-sufficiency-criteria)
- **Affected Files**: [`app/agent/orchestrator.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/orchestrator.py), [`app/models/state.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/models/state.py)
- **Dependencies**: `TASK-602`
- **Acceptance Condition**: Hypotheses failing criteria cannot be marked `confirmed`.

#### `TASK-702`: Contradictory Evidence Evaluation Tasks
- **Description**: Implement hypothesis confidence penalty ($-0.40$) when contradicting evidence IDs are linked and prevent `confirmed` status assignment.
- **Source Requirement**: [Feature Spec Section 7.3](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#73-contradictory-evidence-impact-rule)
- **Affected Files**: [`app/agent/orchestrator.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/orchestrator.py), [`tests/test_conflicting.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_conflicting.py)
- **Dependencies**: `TASK-701`
- **Acceptance Condition**: Hypothesis with contradicting evidence is demoted to `ruled_out` or lower confidence.

#### `TASK-703`: Insufficient Evidence Trigger Engine
- **Description**: Implement explicit triggers forcing `conclusion_type = "INSUFFICIENT_EVIDENCE"` when evidence gaps exist, truncated logs occur, or 2 hypotheses remain equal.
- **Source Requirement**: [Feature Spec Section 7.5](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#75-explicit-triggers-for-insufficient_evidence)
- **Affected Files**: [`app/agent/orchestrator.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/orchestrator.py), [`tests/test_insufficient.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_insufficient.py)
- **Dependencies**: `TASK-701`
- **Acceptance Condition**: Investigation of scenario `INC-002` deterministically returns `INSUFFICIENT_EVIDENCE` with open evidence gaps.

#### `TASK-704`: Unsupported Root Cause Claim Rejection
- **Description**: Enforce rule capping hypothesis confidence at $\le 0.15$ if zero supporting evidence IDs are linked.
- **Source Requirement**: [Feature Spec Section 7.6](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#76-rejection-of-unsupported-root-cause-claims)
- **Affected Files**: [`app/agent/orchestrator.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/orchestrator.py), [`tests/test_unsupported_cause.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_unsupported_cause.py)
- **Dependencies**: `TASK-701`
- **Acceptance Condition**: Asserting an evidence-free hypothesis statement sets status to `ruled_out` or `insufficient_evidence`.

---

### PHASE 8 — Safety and Action Handling
#### `TASK-801`: Action Risk Classifier (`classify_action`)
- **Description**: Implement regex pattern matcher categorizing action descriptions into `READ_ONLY_DIAGNOSTIC`, `LOW_RISK_OPERATIONAL`, `HIGH_RISK_OPERATIONAL`, or `DESTRUCTIVE`.
- **Source Requirement**: [Feature Spec Section 8.1](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#81-risk-classification-pattern-rules)
- **Affected Files**: [`app/agent/safety.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/safety.py), [`tests/test_high_risk_action.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_high_risk_action.py)
- **Dependencies**: `TASK-101`
- **Acceptance Condition**: Restart, rollback, kill job, drop table actions set `requires_approval = True`.

#### `TASK-802`: Execution Claim Intercept Guard
- **Description**: Implement `check_execution_claim(text)` regex intercept throwing `SafetyViolationError` if model text claims to have executed an operation.
- **Source Requirement**: `SR-2`, [Feature Spec Section 8.2](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#82-safe-approval-recording-no-execution-guarantee)
- **Affected Files**: [`app/agent/safety.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/safety.py), [`tests/test_action_executed.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_action_executed.py)
- **Dependencies**: `TASK-801`
- **Acceptance Condition**: Phrases like `"I have restarted the service"` raise `SafetyViolationError` and halt loop immediately.

#### `TASK-803`: Recommended Actions API Endpoint
- **Description**: Implement `GET /incidents/{incident_id}/actions` returning all recommended actions categorized with approval flags.
- **Source Requirement**: [API Contracts Section 6](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/contracts/api-contracts.md#6-post-incidentsincident_idactionsaction_idapprove)
- **Affected Files**: [`app/routers/actions.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/routers/actions.py)
- **Dependencies**: `TASK-801`
- **Acceptance Condition**: Returns total action count and `approval_required_count`.

#### `TASK-804`: Safe Human Approval Endpoint (No Execution)
- **Description**: Implement `POST /incidents/{incident_id}/actions/{action_id}/approve` to record human approval decisions in `RecommendedActionDB` without executing commands.
- **Source Requirement**: `FR-8`, [Feature Spec Section 8.2](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#82-safe-approval-recording-no-execution-guarantee)
- **Affected Files**: [`app/routers/actions.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/routers/actions.py)
- **Dependencies**: `TASK-803`
- **Acceptance Condition**: Updates `approval_status` (`approved`/`rejected`), returns explicit disclaimer note, and executes zero shell commands.

---

### PHASE 9 — Report Generation
#### `TASK-901`: Final Report Builder Compiler
- **Description**: Implement `build_report(incident, state)` compiling structured report dictionary with timeline, primary cause, evidence reviewed, gaps, and recommendations.
- **Source Requirement**: [Feature Spec Section 12](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#12-final-report-structure-specification)
- **Affected Files**: [`app/agent/report_builder.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/report_builder.py)
- **Dependencies**: `TASK-701`, `TASK-801`
- **Acceptance Condition**: Generates valid report dictionary adhering to Section 12 schema specs.

#### `TASK-902`: `GET /incidents/{incident_id}/report` Endpoint
- **Description**: Implement REST route returning compiled final report document for concluded incidents.
- **Source Requirement**: [API Contracts Section 5](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/contracts/api-contracts.md#5-get-incidentsincident_idreport)
- **Affected Files**: [`app/routers/report.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/routers/report.py)
- **Dependencies**: `TASK-901`
- **Acceptance Condition**: Returns `200 OK` with JSON report payload or `404` if investigation not yet run.

#### `TASK-903`: `GET /incidents/{incident_id}/evidence` Endpoint
- **Description**: Implement REST route returning raw evidence items, hypotheses, tools used audit log, and open questions.
- **Source Requirement**: [API Contracts Section 4](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/contracts/api-contracts.md#4-get-incidentsincident_idevidence)
- **Affected Files**: [`app/routers/evidence.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/routers/evidence.py)
- **Dependencies**: `TASK-401`
- **Acceptance Condition**: Returns `200 OK` with complete evidence breakdown.

---

### PHASE 10 — Artefacts
#### `TASK-1001`: Incident Scenario Brief Fixtures (`INC-001` & `INC-002`)
- **Description**: Create controlled JSON incident briefs `INC-001.json` (sufficient evidence) and `INC-002.json` (incomplete evidence).
- **Source Requirement**: [Feature Spec Section 3.2](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#32-evaluation-scenarios--deterministic-differences)
- **Affected Files**: [`artefacts/incidents/INC-001.json`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/artefacts/incidents/INC-001.json), [`artefacts/incidents/INC-002.json`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/artefacts/incidents/INC-002.json)
- **Dependencies**: None
- **Acceptance Condition**: Valid JSON briefs representing `order-service` 503 failures.

#### `TASK-1002`: Microservice JSONL Telemetry Logs Fixtures
- **Description**: Provide JSONL log files for `api-gateway`, `order-service`, `payment-service`, `db-client`, and `batch-processor`.
- **Source Requirement**: `DR-1`, [Feature Spec Section 3.3](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#33-artefacts-requirements)
- **Affected Files**: [`artefacts/logs/*.jsonl`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/artefacts/logs)
- **Dependencies**: None
- **Acceptance Condition**: Contains valid ISO UTC timestamps, routine logs, misleading signals, and pool exhaustion errors.

#### `TASK-1003`: Runbooks, Metadata, and Infrastructure Event Fixtures
- **Description**: Provide 7 Markdown runbooks, `service_metadata.yaml`, `infrastructure_events.json`, and JSON Schema tool contracts.
- **Source Requirement**: [Feature Spec Section 3.3](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#33-artefacts-requirements)
- **Affected Files**: [`artefacts/runbooks/*.md`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/artefacts/runbooks), [`artefacts/service_metadata.yaml`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/artefacts/service_metadata.yaml), [`artefacts/infrastructure_events.json`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/artefacts/infrastructure_events.json)
- **Dependencies**: None
- **Acceptance Condition**: Formatted cleanly and parseable by respective tool readers.

---

### PHASE 11 — Frontend
#### `TASK-1101`: Single-Page Dashboard Layout & Styling
- **Description**: Build responsive HTML5 layout with top navbar, brand icon, CSS tokens, and navigation tabs (Overview, Evidence, Report, Actions, Log Viewer).
- **Source Requirement**: [Feature Spec Section 4](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#4-system-architecture--component-boundaries)
- **Affected Files**: [`app/static/index.html`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/static/index.html)
- **Dependencies**: `TASK-102`
- **Acceptance Condition**: Light-themed console renders cleanly in modern browsers.

#### `TASK-1102`: REST API Integration & Data Binding
- **Description**: Implement Vanilla JS fetch handlers linking UI buttons to backend REST endpoints (`/incidents`, `/investigate`, `/evidence`, `/report`, `/actions`).
- **Source Requirement**: [Plan Spec Component 11](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/plan.md#component-11-frontend-web-ui)
- **Affected Files**: [`app/static/index.html`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/static/index.html)
- **Dependencies**: `TASK-1101`, `TASK-301` to `TASK-902`
- **Acceptance Condition**: Clicking "Trigger Investigation" calls backend API and updates UI with real response data.

#### `TASK-1103`: Action Approval Modal & Interactive Log Viewer
- **Description**: Add UI approval buttons for high-risk actions calling `/approve` endpoint and interactive log search filter form.
- **Source Requirement**: [Feature Spec Section 8.2](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#82-safe-approval-recording-no-execution-guarantee)
- **Affected Files**: [`app/static/index.html`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/static/index.html)
- **Dependencies**: `TASK-1102`, `TASK-804`
- **Acceptance Condition**: Approving an action records approval decision in real-time without fake simulated execution claims.

---

### PHASE 12 — Testing
#### `TASK-1201`: Tool Retrieval Test Suite (`test_tools.py`)
- **Description**: Verify response correctness for all 4 diagnostic tools (`search_logs`, `get_runbook`, `get_service_metadata`, `get_deployment_events`).
- **Source Requirement**: [Testing Spec Case 1](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#17-testing-requirements)
- **Affected Files**: [`tests/test_tools.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_tools.py)
- **Dependencies**: `TASK-501` to `TASK-505`
- **Acceptance Condition**: Test suite passes cleanly (`pytest tests/test_tools.py -v`).

#### `TASK-1202`: Empty Log Result Test Suite (`test_log_empty.py`)
- **Description**: Verify log search behavior when zero records match query filters.
- **Source Requirement**: [Testing Spec Case 2](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#17-testing-requirements)
- **Affected Files**: [`tests/test_log_empty.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_log_empty.py)
- **Dependencies**: `TASK-502`
- **Acceptance Condition**: Test suite passes cleanly.

#### `TASK-1203`: Tool Timeout Test Suite (`test_timeout.py`)
- **Description**: Verify system resiliency when log or deployment queries time out.
- **Source Requirement**: [Testing Spec Case 3](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#17-testing-requirements)
- **Affected Files**: [`tests/test_timeout.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_timeout.py)
- **Dependencies**: `TASK-505`
- **Acceptance Condition**: Test suite passes cleanly.

#### `TASK-1204`: Conflicting Evidence Test Suite (`test_conflicting.py`)
- **Description**: Verify confidence score reduction when opposing evidence items are present.
- **Source Requirement**: [Testing Spec Case 4](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#17-testing-requirements)
- **Affected Files**: [`tests/test_conflicting.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_conflicting.py)
- **Dependencies**: `TASK-702`
- **Acceptance Condition**: Test suite passes cleanly.

#### `TASK-1205`: Missing Runbook Section Test Suite (`test_runbook_missing.py`)
- **Description**: Verify `TOPIC_NOT_FOUND` behavior for unknown runbook requests.
- **Source Requirement**: [Testing Spec Case 5](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#17-testing-requirements)
- **Affected Files**: [`tests/test_runbook_missing.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_runbook_missing.py)
- **Dependencies**: `TASK-503`
- **Acceptance Condition**: Test suite passes cleanly.

#### `TASK-1206`: High-Risk Action Flagging Test Suite (`test_high_risk_action.py`)
- **Description**: Verify risk classification and `requires_approval=True` for high-risk recommendations.
- **Source Requirement**: [Testing Spec Case 6](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#17-testing-requirements)
- **Affected Files**: [`tests/test_high_risk_action.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_high_risk_action.py)
- **Dependencies**: `TASK-801`
- **Acceptance Condition**: Test suite passes cleanly.

#### `TASK-1207`: Fake Execution Claim Intercept Test Suite (`test_action_executed.py`)
- **Description**: Verify `SafetyViolationError` trigger when model claims action execution.
- **Source Requirement**: [Testing Spec Case 7](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#17-testing-requirements)
- **Affected Files**: [`tests/test_action_executed.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_action_executed.py)
- **Dependencies**: `TASK-802`
- **Acceptance Condition**: Test suite passes cleanly.

#### `TASK-1208`: Unsupported Root Cause Test Suite (`test_unsupported_cause.py`)
- **Description**: Verify low confidence assignment for unbacked hypothesis statements.
- **Source Requirement**: [Testing Spec Case 8](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#17-testing-requirements)
- **Affected Files**: [`tests/test_unsupported_cause.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_unsupported_cause.py)
- **Dependencies**: `TASK-704`
- **Acceptance Condition**: Test suite passes cleanly.

#### `TASK-1209`: Malformed Tool Response Test Suite (`test_malformed.py`)
- **Description**: Verify handling of invalid YAML/JSON/time range formats.
- **Source Requirement**: [Testing Spec Case 9](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#17-testing-requirements)
- **Affected Files**: [`tests/test_malformed.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_malformed.py)
- **Dependencies**: `TASK-504`
- **Acceptance Condition**: Test suite passes cleanly.

#### `TASK-1210`: Insufficient Evidence Test Suite (`test_insufficient.py`)
- **Description**: Verify `INSUFFICIENT_EVIDENCE` outcome for incomplete scenario `INC-002`.
- **Source Requirement**: [Testing Spec Case 10](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#17-testing-requirements)
- **Affected Files**: [`tests/test_insufficient.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests/test_insufficient.py)
- **Dependencies**: `TASK-703`
- **Acceptance Condition**: Test suite passes cleanly (**All 83 test cases across suites passing**).

---

### PHASE 13 — Documentation
#### `TASK-1301`: Agent Workflow Documentation (`docs/agent_workflow.md`)
- **Description**: Document investigation loop, safety intercepts, and state lifecycles with Mermaid diagrams.
- **Source Requirement**: [Feature Spec Deliverables](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#181-required-deliverables)
- **Affected Files**: [`docs/agent_workflow.md`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/docs/agent_workflow.md)
- **Dependencies**: `TASK-602`
- **Acceptance Condition**: File renders valid Mermaid diagrams for workflow and state transitions.

#### `TASK-1302`: API & Safety Documentation (`docs/api_documentation.md`, `docs/safety_controls.md`)
- **Description**: Document API REST endpoints, request/response examples, risk categories, and human approval controls.
- **Source Requirement**: [Feature Spec Deliverables](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#181-required-deliverables)
- **Affected Files**: [`docs/api_documentation.md`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/docs/api_documentation.md), [`docs/safety_controls.md`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/docs/safety_controls.md)
- **Dependencies**: `TASK-301`, `TASK-804`
- **Acceptance Condition**: Contains complete documentation of safety rules and REST interfaces.

#### `TASK-1303`: State Schema & Tool Definitions Documentation (`docs/state_schema.md`, `docs/tool_definitions.md`)
- **Description**: Document Pydantic state model attributes, validation rules, and tool function schemas.
- **Source Requirement**: [Feature Spec Deliverables](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#181-required-deliverables)
- **Affected Files**: [`docs/state_schema.md`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/docs/state_schema.md), [`docs/tool_definitions.md`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/docs/tool_definitions.md)
- **Dependencies**: `TASK-203`, `TASK-501`
- **Acceptance Condition**: Documents match runtime models and tool definitions.

---

### PHASE 14 — End-to-End Validation
#### `TASK-1401`: Scenario 1 (`INC-001`) End-to-End Validation
- **Description**: Execute complete investigation pipeline for `INC-001` and verify root cause `ROOT_CAUSE_IDENTIFIED` against facilitator answer key (`facilitator/answer_key.md`).
- **Source Requirement**: [Feature Spec Section 3.2](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#32-evaluation-scenarios--deterministic-differences)
- **Affected Files**: [`app/agent/orchestrator.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/orchestrator.py), [`facilitator/answer_key.md`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/facilitator/answer_key.md)
- **Dependencies**: `TASK-602`, `TASK-902`
- **Acceptance Condition**: Correctly identifies DB pool exhaustion caused by batch job as root cause.

#### `TASK-1402`: Scenario 2 (`INC-002`) End-to-End Validation
- **Description**: Execute complete investigation pipeline for `INC-002` and verify conclusion type `INSUFFICIENT_EVIDENCE` with explicit data gaps.
- **Source Requirement**: [Feature Spec Section 3.2](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#32-evaluation-scenarios--deterministic-differences)
- **Affected Files**: [`app/agent/orchestrator.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/orchestrator.py)
- **Dependencies**: `TASK-1401`
- **Acceptance Condition**: Returns `INSUFFICIENT_EVIDENCE` with active hypotheses `H-001` and `H-002`.

#### `TASK-1403`: Final Acceptance Criteria Audit
- **Description**: Execute full test suite (`python -m pytest tests/ -v`), inspect web UI console, and verify all 10 acceptance criteria checkboxes.
- **Source Requirement**: [Feature Spec Section 18.2](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#182-final-acceptance-criteria)
- **Affected Files**: All repository files
- **Dependencies**: `TASK-101` to `TASK-1402`
- **Acceptance Condition**: All 83 automated test cases pass cleanly, and all acceptance criteria are verified.
