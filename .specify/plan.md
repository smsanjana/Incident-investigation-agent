# Technical Implementation Plan: AI Incident Investigation Agent

## Document Metadata
- **Title**: Master Technical Implementation Plan & Architectural Blueprint
- **Specification Ref**: [Feature Specification](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md)
- **Constitution Ref**: [Project Constitution](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/constitution.md)
- **Research Ref**: [Research Document](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/research.md)

---

## 1. System Architecture Overview

The **AI Incident Investigation Agent** is designed as a decoupled, modular 13-component system adhering strictly to Python, FastAPI, LiteLLM, SQLModel, and Pytest constraints:

```
  ┌─────────────────────────────────────────────────────────────┐
  │                 11. Frontend UI Console                     │
  │            (app/static/index.html - Vanilla Web UI)         │
  └──────────────────────────────┬──────────────────────────────┘
                                 │ HTTP REST API
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                 1. API Layer (FastAPI Routers)              │
  │        (app/routers/incidents, investigate, report, etc.)   │
  └──────────────┬──────────────────────────────┬───────────────┘
                 │                              │
                 ▼                              ▼
  ┌─────────────────────────────┐    ┌──────────────────────────┐
  │ 2. Incident Management      │    │ 10. Database Persistence │
  │    (app/models/incident.py) │    │  (app/db.py + SQLModel)  │
  └──────────────┬──────────────┘    └──────────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │              3. Investigation Orchestrator                  │
  │        (app/agent/orchestrator.py - LiteLLM / Fallback)     │
  └──────────┬───────────────────────────┬──────────────────────┘
             │                           │
             ▼                           ▼
  ┌─────────────────────────────┐   ┌───────────────────────────┐
  │ 4. Investigation State Mgr  │   │ 5. Tool Layer             │
  │ (app/agent/state_manager.py)│   │ (app/tools/*.py)          │
  └──────────┬──────────────────┘   └────────────┬──────────────┘
             │                                   │
             ▼                                   ▼
  ┌─────────────────────────────┐   ┌───────────────────────────┐
  │ 6. Evidence Handling        │   │ 13. Artefact Fixtures     │
  │ 7. Hypothesis Reasoning     │   │ (artefacts/logs, etc.)    │
  │ (app/models/state.py)       │   └───────────────────────────┘
  └──────────┬──────────────────┘
             │
             ▼
  ┌─────────────────────────────┐   ┌───────────────────────────┐
  │ 8. Safety & Action Classif. │   │ 9. Report Generation      │
  │ (app/agent/safety.py)       │   │ (app/agent/report_builder)│
  └─────────────────────────────┘   └───────────────────────────┘
                                                  │
                                                  ▼
                                    ┌───────────────────────────┐
                                    │ 12. Testing Suite         │
                                    │ (tests/ - Pytest 83 tests)│
                                    └───────────────────────────┘
```

---

## 2. Detailed Component Specifications (13 Architecture Components)

### Component 1: API Layer
- **Module**: [`app/main.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/main.py) and [`app/routers/`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/routers)
- **Responsibility**: HTTP request validation, OpenAPI schema generation, static UI mounting, CORS middleware, REST routing.
- **Contracts**: Detailed in [API Contracts Document](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/contracts/api-contracts.md).

### Component 2: Incident Management
- **Module**: [`app/routers/incidents.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/routers/incidents.py) and [`app/models/incident.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/models/incident.py)
- **Responsibility**: Creation, lookup, and status lifecycle management (`open` $\rightarrow$ `investigating` $\rightarrow$ `concluded`).

### Component 3: Investigation Orchestrator
- **Module**: [`app/agent/orchestrator.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/orchestrator.py)
- **Responsibility**: Multi-turn LLM reasoning loop via LiteLLM (`completion()`). Enforces system prompt, function call dispatching, maximum iteration limits (15), and automatic rule-based fallback when LLM API keys are absent.

### Component 4: Investigation State Manager
- **Module**: [`app/agent/state_manager.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/state_manager.py)
- **Responsibility**: Load and persist `InvestigationState` to SQLite DB (`InvestigationStateDB`), serializing/deserializing hypotheses, evidence, tools used, and open questions.

### Component 5: Tool Layer
- **Module**: [`app/tools/`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/tools)
- **Responsibility**: Read-only inspection of controlled artefacts.
  - `search_logs.py`: Query JSONL log files.
  - `runbook.py`: Markdown runbook section parser.
  - `metadata.py`: YAML service metadata loader.
  - `deployment.py`: JSON infrastructure event loader.
- **Contracts**: Detailed in [Tool Contracts Document](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/contracts/tool-contracts.md).

### Component 6: Evidence Handling
- **Module**: [`app/models/state.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/models/state.py) (`EvidenceItem`)
- **Responsibility**: Structuring collected telemetry with unique IDs (`EVD-xxx`), raw content snippets, source attribution, and timestamps.

### Component 7: Hypothesis/Evidence Reasoning Engine
- **Module**: [`app/models/state.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/models/state.py) (`Hypothesis`) & `orchestrator.py`
- **Responsibility**: Associating supporting/contradicting evidence IDs, calculating confidence scores, updating status (`confirmed`, `ruled_out`, `insufficient_evidence`), and evaluating sufficiency thresholds.

### Component 8: Safety & Action Classification
- **Module**: [`app/agent/safety.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/safety.py)
- **Responsibility**: Risk classification (`classify_action`), approval flag assignment (`requires_approval=True` for high-risk/destructive actions), and model execution claim intercept (`check_execution_claim`).

### Component 9: Report Generation
- **Module**: [`app/agent/report_builder.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/agent/report_builder.py)
- **Responsibility**: Compiling structured final investigation reports containing timelines, most likely cause, alternative hypotheses, evidence reviewed, gaps, and categorized recommendations.

### Component 10: Database Persistence
- **Module**: [`app/db.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/db.py) & [`app/models/incident.py`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/models/incident.py)
- **Responsibility**: SQLModel engine initialization, SQLite database file management (`incident_agent.db`), session dependency injection (`get_session`).

### Component 11: Frontend Web UI
- **Module**: [`app/static/index.html`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/app/static/index.html)
- **Responsibility**: Light-themed, responsive single-page operations dashboard interactively connecting to REST API endpoints (`/incidents`, `/investigate`, `/evidence`, `/report`, `/actions`).

### Component 12: Testing Framework
- **Module**: [`tests/`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/tests)
- **Responsibility**: Pytest test suite containing 83 automated test cases validating tool execution, safety checks, edge cases, malformed data, timeouts, and report generation.

### Component 13: Artefact Fixtures
- **Module**: [`artefacts/`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/artefacts)
- **Responsibility**: Controlled test fixtures including incident briefs (`INC-001`, `INC-002`), microservice log files, markdown runbooks, service metadata, and infrastructure events.

---

## 3. Preservation & Reuse Strategy

As verified in the Research phase ([`research.md`](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/research.md)), all 13 core components are **already fully implemented, working, and covered by 83 passing tests**.

- **No Code Base Rewrite**: Existing working implementations are preserved 100%.
- **Deprecation Cleanup**: Modernize `datetime.utcnow()` to `datetime.now(timezone.utc)` across codebase files to eliminate Pytest warnings.

---

## 4. Remaining Uncertainty Status

- **REMAINING UNCERTAINTIES**: None (`NEEDS CLARIFICATION = 0`). All specifications, state model rules, safety controls, API payloads, and tool contracts are completely defined and validated.
