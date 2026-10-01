# Research & Existing Architecture Assessment

## Document Metadata
- **Title**: Existing Implementation Analysis & Tech Stack Evaluation
- **Specification Ref**: [Feature Specification](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md)
- **Constitution Ref**: [Project Constitution](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/constitution.md)

---

## 1. Existing Repository Evaluation

An inspection of the workspace confirms an **existing production-quality codebase**:

| Directory / File | Status | Description & Reusability Assessment |
| :--- | :--- | :--- |
| `app/main.py` | Working | FastAPI app entrypoint, lifespan event database creation, static asset & artefact file mounting. **REUSE 100%**. |
| `app/db.py` | Working | SQLite database engine configuration with `check_same_thread=False` and SQLModel session generator. **REUSE 100%**. |
| `app/models/incident.py` | Working | SQLModel DB schemas (`Incident`, `InvestigationStateDB`, `RecommendedActionDB`). **REUSE 100%**. |
| `app/models/state.py` | Working | Pydantic runtime models (`InvestigationState`, `Hypothesis`, `EvidenceItem`, `ToolCall`). **REUSE 100%**. |
| `app/agent/orchestrator.py` | Working | LiteLLM agentic loop with tool dispatching, system prompts, and rule-based deterministic fallback. **REUSE 100%**. |
| `app/agent/safety.py` | Working | Regex risk classifier (`classify_action`) & execution claim intercept (`check_execution_claim`). **REUSE 100%**. |
| `app/agent/state_manager.py` | Working | State mapping logic between SQLite DB records and Pydantic objects. **REUSE 100%**. |
| `app/agent/report_builder.py` | Working | Final structured report generator compiler. **REUSE 100%**. |
| `app/tools/` | Working | 4 controlled tools (`log_search.py`, `runbook.py`, `metadata.py`, `deployment.py`). **REUSE 100%**. |
| `app/routers/` | Working | REST routes (`incidents.py`, `investigation.py`, `evidence.py`, `report.py`, `actions.py`). **REUSE 100%**. |
| `app/static/index.html` | Working | Modern light-themed dashboard UI (Inter + JetBrains Mono fonts, flex/grid layouts, tabs). **REUSE 100%**. |
| `artefacts/` | Working | Scenarios (`INC-001`, `INC-002`), 5 JSONL log streams, 7 markdown runbooks, YAML metadata, events. **REUSE 100%**. |
| `tests/` | Working | 13 test files covering tool execution, edge cases, malformed data, timeouts, and safety. **83/83 PASSING**. |

---

## 2. Technology Choice Analysis

### 2.1 Backend Framework: FastAPI + Uvicorn
- **Rationale**: Provides automatic OpenAPI documentation (`/docs`), async request handling, dependency injection for database sessions, and static file mounting out of the box.

### 2.2 ORM & Data Layer: SQLModel + SQLite
- **Rationale**: SQLModel bridges Pydantic v2 and SQLAlchemy seamlessly, allowing identical models for API request/response validation and SQLite database persistence (`incident_agent.db`).

### 2.3 LLM Orchestration: LiteLLM
- **Rationale**: LiteLLM provides a standardized interface across OpenAI (`gpt-4o`), Google Gemini (`gemini-1.5-pro`), and Anthropic Claude (`claude-3-5-sonnet`) with unified OpenAI-style function calling (`tools` array).
- **Fallback Strategy**: If no LLM API key (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) is present, `orchestrator.py` seamlessly executes a deterministic rule-based investigation pipeline (`_run_rule_based_investigation`), enabling reliable offline testing.

### 2.4 Frontend Architecture: Vanilla HTML5 / CSS3 / JavaScript (No Build Step)
- **Rationale**: Avoids bloated Node.js build pipelines while delivering a light-theme, responsive dashboard. Interacts directly with backend REST APIs (`/incidents`, `/investigate`, `/evidence`, `/report`, `/actions`).

---

## 3. Findings & Technical Recommendations

1. **Zero Rewrite Needed**: The existing codebase already implements the required architecture cleanly and satisfies all 83 automated test cases.
2. **Utc Timezone Alignment**: Modernize `datetime.utcnow()` calls to `datetime.now(timezone.utc)` across routers and report builders to eliminate Pytest deprecation warnings.
3. **Async Enhancement Opportunity**: `POST /incidents/{id}/investigate` currently executes synchronously. While sufficient for current scenarios, future multi-turn agent runs can leverage FastAPI `BackgroundTasks`.

---

## 4. Unresolved Items / Clarifications Status

- **REMAINING UNCERTAINTIES**: None identified (`NEEDS CLARIFICATION = 0`). All specifications, state schema rules, tool definitions, and safety mechanisms are fully aligned with the Project Constitution.
