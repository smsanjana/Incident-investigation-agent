# Feature Specification: AI Incident Investigation Agent

## Document Metadata
- **Specification Title**: AI Incident Investigation Agent System Specification
- **Version**: 1.1.0 (Clarified & Audit-Refined)
- **Status**: Approved Source of Truth
- **Governance**: Complies with [Project Constitution](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/constitution.md)

---

## 1. Executive Summary & Purpose

### 1.1 Purpose
The **AI Incident Investigation Agent** is an AI-assisted operations tool designed for engineering operations, SRE, and DevOps teams. The system inspects controlled production incident artifacts—including application logs, infrastructure events, deployment records, runbooks, and service metadata—to synthesize evidence-backed investigation reports.

### 1.2 Explicit Non-Goal
**The system is NOT an autonomous remediation agent.** Under no circumstances does the application execute production commands, restart services, deploy code, pause jobs, or mutate infrastructure states. The agent is strictly read-only and advisory.

---

## 2. Problem Statement & Primary Objectives

### 2.1 Problem Statement
During production service incidents, engineering teams manually correlate disjointed telemetry across log aggregators, deployment dashboards, cloud metrics, and markdown runbooks. This manual correlation is time-consuming, cognitive-load heavy, and error-prone, often leading to incorrect root-cause diagnoses or unvalidated operational recommendations.

### 2.2 Primary Objectives
The application MUST systematically perform the following 20 core operational objectives:
1. Accept a structured incident description brief.
2. Extract initial symptoms and the target investigation time window.
3. Retrieve service metadata for the affected service and its upstream/downstream dependencies.
4. Search application logs across relevant microservice boundaries.
5. Inspect infrastructure and deployment timeline events.
6. Retrieve relevant runbook guidance sections for observed symptoms.
7. Maintain investigation state deterministically across multi-turn tool interactions.
8. Formulate multiple structured hypotheses.
9. Associate explicit supporting evidence items (`EVD-xxx`) with each hypothesis.
10. Associate explicit contradicting evidence items (`EVD-xxx`) with each hypothesis.
11. Identify missing evidence and telemetric data gaps.
12. Perform additional targeted evidence searches when required to resolve open questions.
13. Rank hypotheses by confidence score and supporting evidence count.
14. Determine the most likely root cause ONLY when empirical evidence conclusively supports it.
15. Return `INSUFFICIENT_EVIDENCE` as the conclusion type when evidence is incomplete, truncated, or contradictory.
16. Recommend safe diagnostic actions.
17. Classify all recommended actions into standardized risk categories.
18. Never execute production operations.
19. Clearly mark high-risk and destructive recommendations as requiring human approval (`requires_approval=True`).
20. Produce a complete, structured final investigation report.

---

## 3. Incident Scenarios & Controlled Artefacts

### 3.1 Primary Incident Scenario: Order Processing Intermittent Failures
The system must be validated against a customer-facing `order-service` experiencing intermittent failures.
- **Observed Symptoms**: Increased HTTP 503 response codes, elevated request latency (>2000ms), database connection timeout errors (`ERR_POOL_EXHAUSTED`).
- **Telemetry Factors**: Recent deployment (`v2.4.1`), scheduled background batch job (`order-reconciliation`) running within the incident timeframe.
- **Correlation vs. Causation**: The artefacts must contain telemetry enabling the agent to distinguish mere timeline correlation (e.g., deployment completion) from actual root cause (e.g., batch job DB pool exhaustion).

### 3.2 Evaluation Scenarios & Deterministic Differences
The system MUST be evaluated against two distinct scenarios with deterministic behavioral differences:

| Scenario Metric | Scenario 1 (`INC-001`: Sufficient Evidence) | Scenario 2 (`INC-002`: Incomplete Evidence) |
| :--- | :--- | :--- |
| **Telemetry State** | Full logs, complete events, clear runbooks | DB logs truncated at 14:10Z, job end event missing, diff unavailable |
| **Evidence Collected** | $\ge 4$ items (`EVD-001` to `EVD-004`) from 3 tool sources | 1 item (`EVD-001`) with truncated log warning |
| **Leading Hypothesis** | `H-001` (DB pool exhaustion by batch job) | `H-001` (Batch job) vs `H-002` (Deployment regression) |
| **Hypothesis Confidence** | `H-001` = 0.92 (`HIGH`), `H-002` = 0.15 (`LOW`) | `H-001` = 0.45 (`MEDIUM`), `H-002` = 0.40 (`MEDIUM`) |
| **Contradicting Evidence**| `EVD-004` (45m clean post-deploy telemetry) disproves `H-002` | Zero contradicting evidence (data gaps prevent ruling out) |
| **Conclusion Type** | `ROOT_CAUSE_IDENTIFIED` | `INSUFFICIENT_EVIDENCE` |
| **Evidence Gaps** | Empty list `[]` | 3 explicit gaps in `open_questions` and `evidence_gaps` |

### 3.3 Artefacts Requirements
The system repository MUST provide controlled test artefacts in `artefacts/`:
- **Incident Briefs**: `artefacts/incidents/INC-001.json` and `INC-002.json`.
- **Application Logs**: JSONL formatted log streams in `artefacts/logs/` for 5 services (`api-gateway`, `order-service`, `payment-service`, `db-client`, `batch-processor`).
- **Infrastructure Events**: `artefacts/infrastructure_events.json`.
- **Runbooks**: Markdown documents in `artefacts/runbooks/` for `http_503.md`, `db_connection_pool.md`, `high_latency.md`, `deployment_regression.md`, `batch_job_interference.md`, `safe_rollback.md`, `service_restart.md`.
- **Service Metadata**: `artefacts/service_metadata.yaml`.
- **Tool Contracts**: JSON Schema files in `artefacts/tool_contracts/`.
- **Facilitator Answer Key**: `facilitator/answer_key.md`.

---

## 4. System Architecture & Component Boundaries

The system consists of five distinct decoupled components:

```
  ┌─────────────────────────────────────────────────────────┐
  │                 Web UI Console Dashboard                │
  │               (FastAPI Static HTML5/CSS/JS)             │
  └────────────────────────────┬────────────────────────────┘
                               │ HTTP REST API
                               ▼
  ┌─────────────────────────────────────────────────────────┐
  │                 FastAPI Routing Tier                    │
  │        (/incidents, /investigate, /evidence, etc.)      │
  └──────────────┬───────────────────────────┬──────────────┘
                 │                           │
                 ▼                           ▼
  ┌─────────────────────────────┐   ┌───────────────────────┐
  │ Agentic Orchestration Engine│   │ SQLModel DB Store     │
  │ (LiteLLM + Rule Fallback)   │   │ (SQLite Engine)       │
  └──────────────┬──────────────┘   └───────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────────────────────────┐
  │                      Tool Suite                         │
  │ ├── search_logs         ├── get_service_metadata        │
  │ ├── get_runbook         └── get_deployment_events       │
  └────────────────────────────┬────────────────────────────┘
                               │ Reads Controlled Files
                               ▼
  ┌─────────────────────────────────────────────────────────┐
  │                 Artefacts Directory                     │
  │  (logs/*.jsonl, runbooks/*.md, metadata.yaml, etc.)     │
  └─────────────────────────────────────────────────────────┘
```

---

## 5. Investigation State Specification & Validation Rules

### 5.1 State Model Requirements
The system MUST maintain an `InvestigationState` object throughout an investigation cycle, persisted to database storage (`InvestigationStateDB`).

| State Field | Type | Description | Validation Rule |
| :--- | :--- | :--- | :--- |
| `incident_id` | `str` | Unique incident identifier | Must match `INC-\d+` pattern or non-empty string. |
| `incident_summary` | `str` | High-level summary of the incident | Max 500 chars. |
| `observed_symptoms` | `List[str]` | List of extracted operational symptoms | Non-empty array after initial prompt parse. |
| `current_hypotheses` | `List[Hypothesis]` | Evaluated hypotheses | Must contain at least 2 hypotheses during multi-cause analysis. |
| `evidence_items` | `List[EvidenceItem]` | Collected evidence collection | Unique `evidence_id` (`EVD-xxx`), must include valid raw content snippet. |
| `open_questions` | `List[str]` | Unresolved questions and data gaps | Appended when tools return empty/truncated data or errors. |
| `tools_used` | `List[ToolCall]` | Audit log of tool executions | Must record tool name, args, timestamps, success status, and error codes. |
| `recommended_next_steps` | `List[str]` | Advisory next steps for operators | Non-empty array when `conclusion_type` is `INSUFFICIENT_EVIDENCE`. |
| `recommended_actions` | `List[RecommendedAction]` | Categorized recommendations | Every action MUST be classified via `classify_action()`. |
| `final_conclusion` | `Optional[str]` | Final text conclusion | Required when investigation finishes (`done=True`). |
| `conclusion_type` | `Optional[str]` | Conclusion classification | Enum: `ROOT_CAUSE_IDENTIFIED`, `INSUFFICIENT_EVIDENCE`, `MULTIPLE_CAUSES`, `INCONCLUSIVE`. |
| `iteration_count` | `int` | Count of agent loop steps | Integer between `0` and `MAX_INVESTIGATION_ITERATIONS` (default 15). |

---

## 6. Tool Contracts & Behavioral Specifications

The agent MUST interact with controlled artefacts strictly through four standardized tool functions:

### 6.1 `search_logs`
- **Required Inputs**: `service` (`str`), `start_time` (`str` ISO 8601 UTC), `end_time` (`str` ISO 8601 UTC).
- **Optional Inputs**: `severity` (`str`), `keyword` (`str`), `correlation_id` (`str`), `limit` (`int` default 50, max 100).
- **Outputs**: `error` (`bool`), `records` (`List[dict]`), `total_matched` (`int`), `truncated` (`bool`), `query_summary` (`str`).
- **Error Modes**: `INVALID_TIME_RANGE`, `SERVICE_NOT_FOUND`, `TIMEOUT`, `EMPTY_RESULT`.

### 6.2 `get_runbook`
- **Required Inputs**: `topic` (`str` enum: `http_503`, `db_connection_pool`, `high_latency`, `deployment_regression`, `batch_job_interference`, `safe_rollback`, `service_restart`).
- **Outputs**: `error` (`bool`), `topic` (`str`), `title` (`str`), `symptoms` (`List[str]`), `diagnostic_checks` (`List[str]`), `evidence_to_collect` (`List[str]`), `safe_actions` (`List[str]`), `high_risk_actions` (`List[str]`), `escalation_conditions` (`List[str]`), `raw_content` (`str`).
- **Error Modes**: `TOPIC_NOT_FOUND` (returns message listing available topics).

### 6.3 `get_service_metadata`
- **Required Inputs**: `service_name` (`str`).
- **Outputs**: `error` (`bool`), `metadata` (`dict`).
- **Error Modes**: `SERVICE_NOT_FOUND`, `MALFORMED_METADATA`.

### 6.4 `get_deployment_events`
- **Optional Inputs**: `service` (`str`), `start_time` (`str`), `end_time` (`str`), `event_type` (`str`), `limit` (`int`).
- **Outputs**: `error` (`bool`), `events` (`List[dict]`), `total` (`int`).
- **Error Modes**: `INVALID_TIME_RANGE`, `TIMEOUT`, `MALFORMED_METADATA`.

---

## 7. Evidence-Based Reasoning, Confidence & Root-Cause Rules

### 7.1 Quantitative Sufficiency Criteria
Evidence is defined as **Sufficient** to confirm a root cause IF AND ONLY IF ALL of the following criteria are met:
1. **Multi-Source Requirement**: At least 2 distinct evidence items (`EVD-xxx`) collected from at least 2 independent tool sources (e.g. `search_logs` + `get_deployment_events`).
2. **Zero Unaddressed Contradictions**: Top hypothesis has 0 active, unrefuted contradicting evidence items.
3. **High Confidence Threshold**: Top hypothesis confidence score is $\ge 0.80$.
4. **Dominant Separation**: The confidence delta between the top hypothesis and any active secondary hypothesis is $\ge 0.35$.

### 7.2 Numerical Confidence Scale & Labels

| Confidence Label | Numerical Range | Criteria & Requirements |
| :--- | :--- | :--- |
| `HIGH` | `0.80` to `1.00` | Supported by $\ge 2$ independent tool sources, 0 unrefuted contradicting evidence items. |
| `MEDIUM` | `0.40` to `0.79` | Supported by 1 tool source, or open questions / minor evidence gaps remain. |
| `LOW` | `0.00` to `0.39` | 0 supporting evidence items, or active contradicting evidence present. |

### 7.3 Contradictory Evidence Impact Rule
- Each valid contradicting evidence item associated with a hypothesis MUST reduce its confidence score by at least `0.40`.
- If a hypothesis has active contradicting evidence, its status MUST NOT be set to `confirmed`. It MUST be marked `ruled_out` or `insufficient_evidence`.

### 7.4 Definition of Confirmed Root Cause
A root cause is formally **Confirmed** (`status: "confirmed"`, `conclusion_type: "ROOT_CAUSE_IDENTIFIED"`) IF AND ONLY IF:
1. The hypothesis statement describes a specific operational mechanism (e.g. DB pool exhaustion by batch job).
2. The hypothesis meets all Quantitative Sufficiency Criteria (Section 7.1).
3. All alternative hypotheses have confidence $< 0.40$ (`LOW`) or status `ruled_out`.

### 7.5 Explicit Triggers for `INSUFFICIENT_EVIDENCE`
The system MUST return `conclusion_type = "INSUFFICIENT_EVIDENCE"` whenever ANY of the following triggers occur:
1. **No High-Confidence Cause**: No hypothesis achieves confidence $\ge 0.80$.
2. **Competing Causes**: Two or more hypotheses remain active with confidence $\ge 0.40$ and confidence delta $< 0.35$.
3. **Telemetry Gaps**: Required logs are truncated, log query returns 0 records for critical window, or deployment events are missing.
4. **Single-Source Telemetry**: Total evidence items collected span $< 2$ independent tool sources.

### 7.6 Rejection of Unsupported Root-Cause Claims
If an LLM or user proposes a hypothesis without linking any valid `supporting_evidence_ids`:
- The system MUST force `confidence <= 0.15` and status `ruled_out` or `insufficient_evidence`.
- The orchestrator MUST reject setting `conclusion_type = "ROOT_CAUSE_IDENTIFIED"`.

---

## 8. Action Safety, Risk Classification & Human Approval

### 8.1 Risk Classification Pattern Rules
Actions MUST be classified using exact regex pattern matching in `classify_action()`:

```python
HIGH_RISK_PATTERNS = [
    r"restart.*service", r"restart.*pod", r"scale.*replica", r"rollback.*deployment",
    r"kill.*job", r"disable.*job", r"delete.*data", r"drop.*table", r"modify.*pool"
]
DESTRUCTIVE_PATTERNS = [
    r"delete.*production", r"drop.*database", r"truncate.*table", r"wipe", r"destroy"
]
```

- If matching `DESTRUCTIVE_PATTERNS` $\rightarrow$ Category `DESTRUCTIVE`, `requires_approval = True`.
- If matching `HIGH_RISK_PATTERNS` $\rightarrow$ Category `HIGH_RISK_OPERATIONAL`, `requires_approval = True`.
- If matching low-risk patterns (reschedule job off-peak, add read replica) $\rightarrow$ Category `LOW_RISK_OPERATIONAL`, `requires_approval = False`.
- Default fallback $\rightarrow$ Category `READ_ONLY_DIAGNOSTIC`, `requires_approval = False`.

### 8.2 Safe Approval Recording (No Execution Guarantee)
`POST /incidents/{incident_id}/actions/{action_id}/approve` MUST operate strictly as follows:
1. Lookup action in `RecommendedActionDB`. If missing, query `InvestigationState` and persist record.
2. If `requires_approval == False` $\rightarrow$ Return HTTP `400 Bad Request` (`detail: "Action does not require approval"`).
3. If `approval_status != "pending"` $\rightarrow$ Return HTTP `409 Conflict` (`detail: "Action has already been approved/rejected"`).
4. Update DB fields: `approval_status` (`approved` or `rejected`), `approved_by`, `approved_at`, `rejection_reason`.
5. Return JSON payload containing `note: "IMPORTANT: This approval is RECORDED ONLY. The action must be executed manually by an authorized engineer."`
6. **NO shell execution, API call, subprocess, or cloud SDK command is ever invoked.**

---

## 9. Failure Handling & Resiliency Specifications

### 9.1 Tool Error Impact on State
- When a tool returns an error (`error: true`, e.g. `TIMEOUT`, `MALFORMED_METADATA`, `SERVICE_NOT_FOUND`), the execution MUST be logged in `state.tools_used` with `success: false` and `error_code`.
- The error string MUST be appended to `state.open_questions` (e.g., *"Tool search_logs failed: TIMEOUT — Log search timed out after 30s"*).

### 9.2 Long-Running Investigation Loop Timeout Behavior
- Max iteration limit: `MAX_INVESTIGATION_ITERATIONS = 15`.
- If `iteration_count` reaches `15` without `done = True`:
  1. Orchestrator loop MUST terminate gracefully.
  2. `state.final_conclusion` set to `"Investigation reached maximum iteration limit (15). Review evidence collected so far."`
  3. `state.conclusion_type` set to `"INCONCLUSIVE"`.
  4. Open question appended: `"Investigation reached maximum iteration limit."`

### 9.3 Malformed LLM Output Resiliency
1. **Tool Argument Parsing**: If LLM generates malformed JSON for function arguments, default to `{}` and let tool handle validation error.
2. **State Update Validation**: If LLM tool call payload for `update_investigation_state` fails Pydantic schema parsing, return error message into LLM conversation history to request correction.
3. **Execution Claim Intercept**: If LLM output text contains claims of execution (`check_execution_claim`), raise `SafetyViolationError`, halt loop immediately, set `conclusion_type = "INCONCLUSIVE"`, and record safety warning.

---

## 10. Investigation Workflow & State Transitions

```
[Incident Created] (status: open)
       │
       ▼
[POST /incidents/{id}/investigate] (status: investigating)
       │
       ├── 1. Fetch Service Metadata (get_service_metadata)
       ├── 2. Fetch Deployment & Infra Events (get_deployment_events)
       ├── 3. Query Microservice Logs (search_logs)
       ├── 4. Fetch Runbook Guidance (get_runbook)
       ├── 5. Form & Evaluate Hypotheses (update_investigation_state)
       ├── 6. Evaluate Sufficiency & Contradictions (Section 7.1)
       │      ├── Sufficient  ──> Confirm Root Cause (ROOT_CAUSE_IDENTIFIED)
       │      └── Incomplete  ──> Flag Gaps (INSUFFICIENT_EVIDENCE)
       │
       ▼
[Investigation Complete] (status: concluded)
       │
       ├── GET /incidents/{id}/report   ──> Return Structured Report
       └── POST /incidents/{id}/actions/{aid}/approve ──> Record Human Approval
```

---

## 11. REST API Specification

### 11.1 Endpoints List
- `POST /incidents`: Create incident brief.
- `GET /incidents`: List incidents.
- `GET /incidents/{incident_id}`: Get incident status.
- `POST /incidents/{incident_id}/investigate`: Trigger agentic investigation loop.
- `GET /incidents/{incident_id}/evidence`: Retrieve evidence, hypotheses, tools used, open questions.
- `GET /incidents/{incident_id}/report`: Retrieve final structured investigation report.
- `POST /incidents/{incident_id}/actions/{action_id}/approve`: Record human approval/rejection decision.

---

## 12. Final Report Structure & Evidence Reference Specification

The report returned by `GET /incidents/{incident_id}/report` MUST render evidence references explicitly:

```json
{
  "report_id": "RPT-INC-001",
  "generated_at": "2026-08-16T12:00:00Z",
  "incident_summary": {
    "incident_id": "INC-001",
    "title": "Order service 503 spikes",
    "affected_service": "order-service",
    "severity": "SEV-2",
    "start_time": "2025-07-14T02:00:00Z",
    "detection_time": "2025-07-14T02:15:00Z",
    "customer_impact": "High error rate on checkout"
  },
  "timeline": [
    {"time": "2025-07-14T02:00:00Z", "event": "Incident start", "summary": "Symptoms first observed."},
    {"time": "2025-07-14T02:15:00Z", "event": "Incident detected", "summary": "Alert fired."}
  ],
  "most_likely_cause": {
    "hypothesis_id": "H-001",
    "statement": "Batch job order-reconciliation exhausted DB pool (20 max), causing HTTP 503s.",
    "confidence": 0.92,
    "confidence_label": "HIGH",
    "supporting_evidence_count": 3,
    "contradicting_evidence_count": 0,
    "status": "confirmed"
  },
  "alternative_hypotheses": [
    {
      "hypothesis_id": "H-002",
      "statement": "Deployment order-service v2.4.1 introduced regression.",
      "confidence": 0.15,
      "confidence_label": "LOW",
      "status": "ruled_out",
      "supporting_evidence_count": 0,
      "contradicting_evidence_count": 1
    }
  ],
  "evidence_reviewed": [
    {
      "evidence_id": "EVD-001",
      "source": "get_deployment_events:batch-processor",
      "description": "Job order-reconciliation started at 02:10 UTC",
      "relevance": "Identifies batch job start time near 503 onset"
    }
  ],
  "evidence_gaps": [],
  "recommended_diagnostic_actions": ["Review gateway logs"],
  "recommended_remediation": [],
  "actions_requiring_approval": [
    {
      "action_id": "ACT-001",
      "description": "Kill or pause order-reconciliation batch job",
      "category": "HIGH_RISK_OPERATIONAL",
      "rationale": "Immediately release DB pool connections"
    }
  ],
  "conclusion": {
    "type": "ROOT_CAUSE_IDENTIFIED",
    "text": "Root cause identified: DB connection pool exhaustion caused by batch job."
  },
  "confidence_and_limitations": {
    "overall_confidence": 0.92,
    "confidence_label": "HIGH",
    "limitations": [],
    "tools_invoked": 7,
    "evidence_items_collected": 4,
    "hypotheses_evaluated": 2
  }
}
```

---

## 13. Functional Requirements

- **FR-1**: System MUST accept incident creation requests via `POST /incidents`.
- **FR-2**: System MUST automatically extract symptoms and time windows from incident briefs.
- **FR-3**: System MUST execute function calls to all 4 defined inspection tools during investigation.
- **FR-4**: System MUST maintain hypotheses with linked supporting and contradicting evidence IDs.
- **FR-5**: System MUST produce `INSUFFICIENT_EVIDENCE` conclusions when data gaps exist.
- **FR-6**: System MUST classify recommended actions into risk categories.
- **FR-7**: System MUST set `requires_approval=True` for high-risk and destructive actions.
- **FR-8**: System MUST record human approval decisions without executing operations.

---

## 14. Non-Functional Requirements

- **NFR-1 (Performance)**: Rule-based fallback investigation loop must finish execution in under 2.0 seconds.
- **NFR-2 (Reliability)**: The test suite must pass 100% of defined automated test cases.
- **NFR-3 (Maintainability)**: Codebase must adhere to PEP 8 standards with full type annotations.
- **NFR-4 (Security & Privacy)**: API keys and sensitive tokens must be loaded exclusively via environment variables (`.env`).

---

## 15. Safety & Security Requirements

- **SR-1 (Read-Only Guarantee)**: The system MUST NOT possess execution capabilities or integrations to modify production infrastructure.
- **SR-2 (Execution Intercept)**: `check_execution_claim()` MUST scan model responses and raise `SafetyViolationError` if execution is claimed.
- **SR-3 (Approval Audit)**: Human approval decisions MUST be immutably recorded with timestamp and author identity.

---

## 16. Data Requirements

- **DR-1**: Telemetry data in `artefacts/logs/` must use JSONL format with valid ISO 8601 timestamps.
- **DR-2**: Database persistence must use SQLite with SQLModel schemas for `Incident`, `InvestigationStateDB`, and `RecommendedActionDB`.

---

## 17. Testing Requirements

The project test suite in `tests/` MUST contain automated tests covering all 10 mandatory scenario categories:

1. **Tool Retrieval**: `test_tools.py` verifying `search_logs`, `get_runbook`, `get_service_metadata`, `get_deployment_events`.
2. **Empty Log Handling**: `test_log_empty.py` verifying query execution with 0 results.
3. **Tool Timeout Resiliency**: `test_timeout.py` verifying tool timeout error capture.
4. **Conflicting Evidence Evaluation**: `test_conflicting.py` verifying hypotheses handling opposing evidence.
5. **Missing Runbook Handling**: `test_runbook_missing.py` verifying `TOPIC_NOT_FOUND` error responses.
6. **High-Risk Action Flagging**: `test_high_risk_action.py` verifying risk classification and `requires_approval=True`.
7. **Execution Claim Intercept**: `test_action_executed.py` verifying `SafetyViolationError` triggers.
8. **Unsupported Root Cause Handling**: `test_unsupported_cause.py` verifying low confidence on unsupported statements.
9. **Malformed Tool Response Resiliency**: `test_malformed.py` verifying handling of invalid YAML/JSON/time formats.
10. **Insufficient Evidence Handling**: `test_insufficient.py` verifying `INSUFFICIENT_EVIDENCE` for incomplete scenarios (`INC-002`).

*Acceptance Threshold*: **At least 8 automated tests MUST pass (current baseline: 83/83 passing).**

---

## 18. Deliverables & Acceptance Criteria

### 18.1 Required Deliverables
1. Source Code (`app/` package).
2. Readme & Documentation (`README.md`, `docs/`).
3. Artefacts Suite (`artefacts/`).
4. Facilitator Answer Key (`facilitator/answer_key.md`).
5. Automated Pytest Test Suite (`tests/`).

### 18.2 Final Acceptance Criteria
The project is complete ONLY when:
- [x] Incident briefs can be created via REST API.
- [x] Agent triggers multi-step tool investigations.
- [x] All 4 diagnostic tools execute cleanly.
- [x] Evidence is explicitly recorded in `InvestigationState`.
- [x] Root-cause conclusions directly cite empirical evidence item IDs.
- [x] Conflicting evidence is recorded and deprioritizes invalidated hypotheses.
- [x] High-risk actions set `requires_approval=True` and are never executed by the system.
- [x] `POST /incidents/{id}/actions/{aid}/approve` records approval decisions without executing commands.
- [x] Structured final report is generated adhering to section requirements.
- [x] All 83 automated test cases pass cleanly.
