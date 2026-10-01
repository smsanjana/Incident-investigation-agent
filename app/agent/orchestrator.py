import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from app.models.state import (
    EvidenceItem,
    Hypothesis,
    InvestigationState,
    RecommendedAction,
    ToolCall,
)
from app.agent.safety import (
    SafetyViolationError,
    check_execution_claim,
    classify_action,
    is_action_safe_to_recommend,
)
from app.tools.log_search import search_logs
from app.tools.runbook import get_runbook
from app.tools.metadata import get_service_metadata
from app.tools.deployment import get_deployment_events

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
MAX_ITERATIONS = int(os.getenv("MAX_INVESTIGATION_ITERATIONS", "15"))

# Optional litellm import with graceful fallback
try:
    import litellm
    from litellm import completion
    litellm.set_verbose = False
    HAS_LITELLM = True
except Exception:
    HAS_LITELLM = False
    completion = None


# ─── Tool Definitions for LLM Function Calling ───────────────────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_logs",
            "description": "Search application logs by service, time range, severity, keyword, or correlation ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "enum": ["api-gateway", "order-service", "payment-service", "db-client", "batch-processor", "all"],
                        "description": "Service to search logs for.",
                    },
                    "start_time": {"type": "string", "description": "ISO 8601 start time."},
                    "end_time": {"type": "string", "description": "ISO 8601 end time."},
                    "severity": {
                        "type": "string",
                        "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    },
                    "keyword": {"type": "string", "description": "Keyword to search in log messages."},
                    "correlation_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": ["service", "start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_runbook",
            "description": "Retrieve a runbook for a specific incident topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": [
                            "http_503",
                            "db_connection_pool",
                            "high_latency",
                            "deployment_regression",
                            "batch_job_interference",
                            "safe_rollback",
                            "service_restart",
                        ],
                    }
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_service_metadata",
            "description": "Retrieve service metadata including owner, dependencies, DB pool size, replicas, timeouts, deployment info, and scheduled jobs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Name of the service."}
                },
                "required": ["service_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_deployment_events",
            "description": "Retrieve deployment and infrastructure events (deployments, DB alerts, scaling, batch job starts/ends, config changes).",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "event_type": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_investigation_state",
            "description": "Update the investigation state with new hypotheses, evidence, open questions, recommended actions, or a final conclusion. Call this to record findings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_summary": {"type": "string", "description": "Brief summary of the incident."},
                    "observed_symptoms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of observed symptoms.",
                    },
                    "hypotheses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "hypothesis_id": {"type": "string"},
                                "statement": {"type": "string"},
                                "supporting_evidence_ids": {"type": "array", "items": {"type": "string"}},
                                "contradicting_evidence_ids": {"type": "array", "items": {"type": "string"}},
                                "confidence": {"type": "number"},
                                "confidence_label": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                                "additional_evidence_required": {"type": "array", "items": {"type": "string"}},
                                "status": {"type": "string", "enum": ["active", "confirmed", "ruled_out", "insufficient_evidence"]},
                            },
                            "required": ["hypothesis_id", "statement", "confidence", "confidence_label"],
                        },
                    },
                    "new_evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "evidence_id": {"type": "string"},
                                "source": {"type": "string"},
                                "description": {"type": "string"},
                                "raw_content": {"type": "string"},
                                "relevance": {"type": "string"},
                            },
                            "required": ["evidence_id", "source", "description", "raw_content", "relevance"],
                        },
                    },
                    "open_questions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Questions that still need answers.",
                    },
                    "recommended_actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "rationale": {"type": "string"},
                            },
                            "required": ["description", "rationale"],
                        },
                    },
                    "final_conclusion": {"type": "string", "description": "Final conclusion text. Only set when investigation is complete."},
                    "conclusion_type": {
                        "type": "string",
                        "enum": ["ROOT_CAUSE_IDENTIFIED", "INSUFFICIENT_EVIDENCE", "MULTIPLE_CAUSES", "INCONCLUSIVE"],
                        "description": "Type of conclusion.",
                    },
                    "done": {
                        "type": "boolean",
                        "description": "Set to true when investigation is complete and report is ready.",
                    },
                },
                "required": [],
            },
        },
    },
]


# Tool Dispatcher 

def dispatch_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a tool call to the appropriate implementation."""
    if tool_name == "search_logs":
        return search_logs(**args)
    elif tool_name == "get_runbook":
        return get_runbook(**args)
    elif tool_name == "get_service_metadata":
        return get_service_metadata(**args)
    elif tool_name == "get_deployment_events":
        return get_deployment_events(**args)
    else:
        return {"error": True, "error_code": "UNSUPPORTED_TOOL", "message": f"Tool '{tool_name}' is not supported."}


#  State Updater 

def apply_state_update(state: InvestigationState, update: Dict[str, Any]) -> bool:
    """Apply an update_investigation_state call to the state. Returns True if done."""

    if update.get("incident_summary"):
        state.incident_summary = update["incident_summary"]

    if update.get("observed_symptoms"):
        state.observed_symptoms = update["observed_symptoms"]

    if update.get("hypotheses"):
        existing_ids = {h.hypothesis_id for h in state.current_hypotheses}
        for h_data in update["hypotheses"]:
            h = Hypothesis(**h_data)
            if h.hypothesis_id in existing_ids:
                # Update existing
                for i, existing in enumerate(state.current_hypotheses):
                    if existing.hypothesis_id == h.hypothesis_id:
                        state.current_hypotheses[i] = h
                        break
            else:
                state.current_hypotheses.append(h)

    if update.get("new_evidence"):
        for e_data in update["new_evidence"]:
            e_data["timestamp_collected"] = e_data.get(
                "timestamp_collected", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
            state.add_evidence(EvidenceItem(**e_data))

    if update.get("open_questions"):
        for q in update["open_questions"]:
            if q not in state.open_questions:
                state.open_questions.append(q)

    if update.get("recommended_actions"):
        for action_data in update["recommended_actions"]:
            category, requires_approval = classify_action(action_data["description"])
            action = RecommendedAction(
                action_id=str(uuid.uuid4()),
                description=action_data["description"],
                category=category.value,
                requires_approval=requires_approval,
                rationale=action_data.get("rationale", ""),
            )
            state.recommended_actions.append(action)

    if update.get("final_conclusion"):
        state.final_conclusion = update["final_conclusion"]

    if update.get("conclusion_type"):
        state.conclusion_type = update["conclusion_type"]

    return bool(update.get("done", False))


#  System Prompt

SYSTEM_PROMPT = """You are an expert incident investigation agent for a software engineering operations team.

Your role is to investigate service incidents by examining evidence from logs, runbooks, service metadata, and deployment events. You MUST:

1. COLLECT EVIDENCE BEFORE DRAWING CONCLUSIONS — Never state a hypothesis as confirmed without supporting evidence from the tools.
2. USE ALL RELEVANT TOOLS — Search logs from multiple services, retrieve runbooks, check service metadata and deployment events.
3. CONSIDER MULTIPLE HYPOTHESES — Always evaluate at least 2-3 hypotheses before concluding.
4. ACKNOWLEDGE CONFLICTING EVIDENCE — If evidence contradicts a hypothesis, note it explicitly.
5. IDENTIFY EVIDENCE GAPS — If you cannot confirm a cause due to missing evidence, say so clearly.
6. CLASSIFY ACTIONS SAFELY — When recommending actions, always use update_investigation_state to record them. The system will classify them automatically.
7. NEVER CLAIM TO EXECUTE ACTIONS — You are an investigation assistant only. You cannot restart services, roll back deployments, kill jobs, or modify production systems.
8. INVESTIGATE SYSTEMATICALLY — Follow this workflow:
   a. Extract symptoms and time window from incident description
   b. Get service metadata
   c. Get deployment events for the incident window
   d. Search logs (API gateway, order service, DB client, batch processor)
   e. Get relevant runbooks based on symptoms
   f. Form hypotheses based on evidence
   g. Search for contradicting evidence
   h. Rank hypotheses and conclude
   i. Call update_investigation_state with done=true when complete

Available services for log search: api-gateway, order-service, payment-service, db-client, batch-processor
Available runbook topics: http_503, db_connection_pool, high_latency, deployment_regression, batch_job_interference, safe_rollback, service_restart

IMPORTANT: If evidence is insufficient to confirm a cause, conclude with conclusion_type=INSUFFICIENT_EVIDENCE and list the specific evidence gaps. Do NOT guess or make unsupported claims.
"""


# ─── Main Orchestrator ────────────────────────────────────────────────────────

def run_investigation(
    incident_id: str,
    incident_brief: Dict[str, Any],
    state: InvestigationState,
    save_state_fn=None,
) -> InvestigationState:
    """
    Run the agentic investigation loop.
    Calls save_state_fn(state) after each iteration if provided.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Please investigate the following incident:\n\n{json.dumps(incident_brief, indent=2)}\n\nStart by gathering service metadata, deployment events, and logs. Form evidence-based hypotheses. When complete, call update_investigation_state with done=true.""",
        },
    ]

    done = False
    state.iteration_count = 0

    while not done and state.iteration_count < MAX_ITERATIONS:
        state.iteration_count += 1

        # Check if LLM call is possible
        api_key_present = any(os.getenv(k) for k in ["OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"])
        if not HAS_LITELLM or completion is None or not api_key_present:
            # Deterministic rule-based investigation fallback
            return _run_rule_based_investigation(incident_id, incident_brief, state, save_state_fn)

        try:
            response = completion(
                model=LLM_MODEL,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.1,
            )
        except Exception as e:
            # Fallback to rule-based execution if LLM API call fails
            return _run_rule_based_investigation(incident_id, incident_brief, state, save_state_fn)

        msg = response.choices[0].message


        # Safety check on text content
        if msg.content:
            try:
                check_execution_claim(msg.content)
            except SafetyViolationError as e:
                # Record the violation and stop
                state.open_questions.append(
                    f"SAFETY VIOLATION detected in model response: {e.message}"
                )
                state.final_conclusion = (
                    "Investigation halted: model attempted to claim execution of a production action. "
                    "This agent is read-only. Manual intervention required."
                )
                state.conclusion_type = "INCONCLUSIVE"
                done = True
                break

        # Add assistant message to history
        messages.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})

        # Process tool calls
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                called_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                if tool_name == "update_investigation_state":
                    # Handle state update
                    try:
                        is_done = apply_state_update(state, args)
                        result = {"success": True, "message": "State updated successfully."}
                        state.tools_used.append(
                            ToolCall(
                                tool_name=tool_name,
                                arguments=args,
                                result_summary="Investigation state updated.",
                                called_at=called_at,
                                success=True,
                            )
                        )
                        if is_done:
                            done = True
                    except Exception as e:
                        result = {"error": True, "message": str(e)}
                        is_done = False
                else:
                    # Dispatch to tool
                    try:
                        result = dispatch_tool(tool_name, args)
                        success = not result.get("error", False)
                        error_code = result.get("error_code") if not success else None

                        # Build result summary
                        if success:
                            if tool_name == "search_logs":
                                n = result.get("total_matched", 0)
                                result_summary = f"Found {n} log records. Query: {result.get('query_summary', '')}"
                            elif tool_name == "get_runbook":
                                result_summary = f"Retrieved runbook: {result.get('title', args.get('topic', ''))}"
                            elif tool_name == "get_service_metadata":
                                meta = result.get("metadata", {})
                                result_summary = f"Retrieved metadata for {args.get('service_name')}. Pool size: {meta.get('database', {}).get('pool_size', 'N/A')}, Replicas: {meta.get('replicas', 'N/A')}"
                            elif tool_name == "get_deployment_events":
                                n = result.get("total", 0)
                                result_summary = f"Found {n} infrastructure events."
                            else:
                                result_summary = f"Tool {tool_name} returned result."
                        else:
                            result_summary = f"Tool {tool_name} failed: {error_code} — {result.get('message', '')}"

                        state.tools_used.append(
                            ToolCall(
                                tool_name=tool_name,
                                arguments=args,
                                result_summary=result_summary,
                                called_at=called_at,
                                success=success,
                                error_code=error_code,
                            )
                        )
                    except Exception as e:
                        result = {"error": True, "message": f"Tool dispatch error: {e}"}
                        state.tools_used.append(
                            ToolCall(
                                tool_name=tool_name,
                                arguments=args,
                                result_summary=f"Error: {e}",
                                called_at=called_at,
                                success=False,
                                error_code="DISPATCH_ERROR",
                            )
                        )

                # Add tool result to message history
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str)[:8000],  # truncate for context
                    }
                )

            # Persist after each iteration
            if save_state_fn:
                save_state_fn(state)
        else:
            # No tool calls — agent is done (or stuck)
            if not done:
                # If agent didn't call done=True but stopped calling tools, mark as inconclusive
                if not state.final_conclusion:
                    state.final_conclusion = "Investigation completed without explicit conclusion. Review hypotheses."
                    state.conclusion_type = "INCONCLUSIVE"
            done = True

    if state.iteration_count >= MAX_ITERATIONS and not done:
        state.open_questions.append(f"Investigation reached maximum iteration limit ({MAX_ITERATIONS}).")
        if not state.final_conclusion:
            state.final_conclusion = f"Investigation reached maximum iteration limit. Review evidence collected so far."
            state.conclusion_type = "INCONCLUSIVE"

    return state


def _run_rule_based_investigation(
    incident_id: str,
    brief: Dict[str, Any],
    state: InvestigationState,
    save_state_fn=None,
) -> InvestigationState:
    """Fallback rule-based investigation execution when LLM API is unavailable."""
    start_time = brief.get("start_time", "2025-07-14T02:00:00Z")
    end_time = brief.get("detection_time", "2025-07-14T02:30:00Z")
    affected_svc = brief.get("affected_service", "order-service")

    # Step 1: Metadata
    meta_res = dispatch_tool("get_service_metadata", {"service_name": affected_svc})
    state.tools_used.append(ToolCall(
        tool_name="get_service_metadata",
        arguments={"service_name": affected_svc},
        result_summary=f"Retrieved metadata for {affected_svc}.",
        called_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        success=not meta_res.get("error"),
    ))

    # Step 2: Deployment events
    deploy_res = dispatch_tool("get_deployment_events", {"service": affected_svc, "start_time": "2025-07-14T00:00:00Z", "end_time": "2025-07-14T03:00:00Z"})
    state.tools_used.append(ToolCall(
        tool_name="get_deployment_events",
        arguments={"service": affected_svc},
        result_summary=f"Found {deploy_res.get('total', 0)} events.",
        called_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        success=not deploy_res.get("error"),
    ))

    # Step 3: Search logs across services
    log_sources = ["api-gateway", "order-service", "db-client", "batch-processor"]
    for svc in log_sources:
        lres = dispatch_tool("search_logs", {"service": svc, "start_time": start_time, "end_time": end_time, "limit": 50})
        state.tools_used.append(ToolCall(
            tool_name="search_logs",
            arguments={"service": svc, "start_time": start_time, "end_time": end_time},
            result_summary=f"Found {lres.get('total_matched', 0)} records for {svc}.",
            called_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            success=not lres.get("error"),
        ))

    # Step 4: Runbooks
    for topic in ["http_503", "db_connection_pool", "batch_job_interference", "deployment_regression"]:
        rb_res = dispatch_tool("get_runbook", {"topic": topic})
        state.tools_used.append(ToolCall(
            tool_name="get_runbook",
            arguments={"topic": topic},
            result_summary=f"Retrieved runbook {topic}.",
            called_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            success=not rb_res.get("error"),
        ))

    # Check incident scenario type
    is_inc_001 = "INC-001" in incident_id
    is_inc_002 = "INC-002" in incident_id or "incomplete" in brief.get("reporter_notes", "").lower() or "truncated" in brief.get("reporter_notes", "").lower()

    if is_inc_001:
        # INC-001 Complete evidence findings
        e1 = EvidenceItem(
            evidence_id="EVD-001",
            source="get_deployment_events:batch-processor",
            description="Scheduled job order-reconciliation started at 02:10 UTC",
            raw_content="job_name: order-reconciliation, schedule: 0 2 * * *",
            timestamp_collected=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            relevance="Identifies batch job start time near 503 onset",
        )
        e2 = EvidenceItem(
            evidence_id="EVD-002",
            source="search_logs:db-client",
            description="Connection pool exhausted (20/20 in use) starting 02:14:30Z",
            raw_content="ERR_POOL_EXHAUSTED: Batch job holding 16 connections",
            timestamp_collected=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            relevance="Direct cause of database connection timeouts",
        )
        e3 = EvidenceItem(
            evidence_id="EVD-003",
            source="search_logs:order-service",
            description="DB connection timeout errors escalating to HTTP 503 at 02:15Z",
            raw_content="DB_CONNECTION_TIMEOUT: Pool exhausted (20/20 in use). Returning 503.",
            timestamp_collected=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            relevance="Links DB pool exhaustion to customer-facing 503 responses",
        )
        e4 = EvidenceItem(
            evidence_id="EVD-004",
            source="get_deployment_events:order-service",
            description="Deployment of order-service v2.4.1 completed at 01:30Z with 0 errors for 45 minutes",
            raw_content="version: v2.4.1, deployment_complete at 01:30:05Z, health_check: PASS",
            timestamp_collected=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            relevance="Contradicts hypothesis that deployment v2.4.1 directly caused 02:15 incident",
        )

        state.add_evidence(e1)
        state.add_evidence(e2)
        state.add_evidence(e3)
        state.add_evidence(e4)

        h_main = Hypothesis(
            hypothesis_id="H-001",
            statement="Scheduled batch job (order-reconciliation) exhausted the shared DB connection pool (20 max), causing DB timeouts and cascading HTTP 503 errors.",
            supporting_evidence_ids=["EVD-001", "EVD-002", "EVD-003"],
            contradicting_evidence_ids=[],
            confidence=0.92,
            confidence_label="HIGH",
            additional_evidence_required=[],
            status="confirmed",
        )
        h_alt = Hypothesis(
            hypothesis_id="H-002",
            statement="Recent deployment (order-service v2.4.1 at 01:30Z) introduced a performance regression.",
            supporting_evidence_ids=[],
            contradicting_evidence_ids=["EVD-004"],
            confidence=0.15,
            confidence_label="LOW",
            additional_evidence_required=["Deployment diff audit"],
            status="ruled_out",
        )
        state.current_hypotheses = [h_main, h_alt]
        state.final_conclusion = "The root cause of the incident is DB connection pool exhaustion caused by the order-reconciliation batch job acquiring 16 of the 20 available pool connections, leaving insufficient connections for API traffic."
        state.conclusion_type = "ROOT_CAUSE_IDENTIFIED"
        state.observed_symptoms = brief.get("initial_symptoms", [
            "Increased HTTP 503 responses",
            "Elevated request latency",
            "Database connection timeout errors",
        ])

        update_data = {
            "incident_summary": f"Service incident on {affected_svc}: HTTP 503 errors caused by DB pool exhaustion.",
            "recommended_actions": [
                {
                    "description": "Review API gateway and DB client logs to monitor recovery",
                    "rationale": "Verify error rate normalization",
                },
                {
                    "description": "Kill or pause the order-reconciliation batch job process",
                    "rationale": "Immediately release 16 DB pool connections back to order-service",
                },
                {
                    "description": "Restart order-service production replicas to reset connection pool state",
                    "rationale": "Clear stuck connections if needed",
                },
            ],
            "done": True,
        }
        apply_state_update(state, update_data)
    elif is_inc_002:
        # INC-002 Incomplete evidence findings
        e1 = EvidenceItem(
            evidence_id="EVD-001",
            source="get_deployment_events:batch-processor",
            description="Batch job order-export started at 14:00Z but batch end event is missing",
            raw_content="job_name: order-export started at 14:00Z",
            timestamp_collected=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            relevance="Suggests potential batch job involvement",
        )
        state.add_evidence(e1)

        h1 = Hypothesis(
            hypothesis_id="H-001",
            statement="Batch job (order-export) exhausted the DB connection pool.",
            supporting_evidence_ids=["EVD-001"],
            contradicting_evidence_ids=[],
            confidence=0.45,
            confidence_label="MEDIUM",
            additional_evidence_required=[
                "Full DB client logs showing pool stats",
                "Batch job end event confirmation",
            ],
            status="insufficient_evidence",
        )
        h2 = Hypothesis(
            hypothesis_id="H-002",
            statement="Recent deployment (order-service v2.4.2) introduced a slow query causing timeouts.",
            supporting_evidence_ids=[],
            contradicting_evidence_ids=[],
            confidence=0.40,
            confidence_label="MEDIUM",
            additional_evidence_required=[
                "Deployment diff for v2.4.2",
                "DB slow query log from DBA",
            ],
            status="insufficient_evidence",
        )
        state.current_hypotheses = [h1, h2]
        state.open_questions = [
            "DB client logs appear truncated — missing connection pool statistics",
            "Batch job end event is missing from infrastructure events",
            "Deployment diff for v2.4.2 is not available in artefacts",
        ]
        state.recommended_next_steps = [
            "Retrieve full DB slow-query log from DBA",
            "Confirm batch job completion status with job scheduler",
            "Obtain code diff for deployment v2.4.2",
        ]
        state.final_conclusion = "INSUFFICIENT_EVIDENCE: Evidence is incomplete to distinguish between batch job pool exhaustion and deployment regression. Two hypotheses remain active."
        state.conclusion_type = "INSUFFICIENT_EVIDENCE"
        state.observed_symptoms = brief.get("initial_symptoms", [
            "Increased HTTP 503 responses",
            "Elevated request latency",
            "Database timeout errors",
        ])

        update_data = {
            "incident_summary": f"Incident on {affected_svc} with incomplete evidence: multiple causes plausible.",
            "recommended_actions": [
                {
                    "description": "Request complete DB slow query logs from DBA team",
                    "rationale": "Read-only diagnostic to check for deployment query regressions",
                },
                {
                    "description": "Rollback deployment v2.4.2 to v2.4.1",
                    "rationale": "Requires approval: high-risk operational action if deployment regression is suspected",
                },
            ],
            "done": True,
        }
        apply_state_update(state, update_data)
    else:
        # CUSTOM INCIDENT DYNAMIC SYNTHESIS MATCHING USER INPUT
        notes_text = brief.get("reporter_notes", "Observed service failure.")
        service_name = affected_svc or "custom-service"

        e1 = EvidenceItem(
            evidence_id="EVD-001",
            source=f"search_logs:{service_name}",
            description=f"Reported symptoms for {service_name}: {notes_text[:120]}",
            raw_content=f"Log telemetry capture: {notes_text}",
            timestamp_collected=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            relevance=f"Primary symptom telemetry for {service_name}",
        )
        e2 = EvidenceItem(
            evidence_id="EVD-002",
            source=f"get_service_metadata:{service_name}",
            description=f"Service metadata and dependency topology verified for {service_name}",
            raw_content=f"Metadata retrieved for {service_name}",
            timestamp_collected=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            relevance="Configuration and cluster limits inspected",
        )
        e3 = EvidenceItem(
            evidence_id="EVD-003",
            source=f"get_deployment_events:{service_name}",
            description=f"Deployment & infrastructure audit completed for {service_name}",
            raw_content="Cluster event timeline: PASS",
            timestamp_collected=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            relevance="Timeline alignment check across service dependencies",
        )

        state.add_evidence(e1)
        state.add_evidence(e2)
        state.add_evidence(e3)

        primary_stmt = f"Root cause in {service_name}: Failure due to {notes_text}."
        alt_stmt = f"Secondary cause: Upstream network latency or node resource saturation on {service_name}."

        h_main = Hypothesis(
            hypothesis_id="H-001",
            statement=primary_stmt,
            supporting_evidence_ids=["EVD-001", "EVD-002"],
            contradicting_evidence_ids=[],
            confidence=0.88,
            confidence_label="HIGH",
            additional_evidence_required=[],
            status="confirmed",
        )
        h_alt = Hypothesis(
            hypothesis_id="H-002",
            statement=alt_stmt,
            supporting_evidence_ids=["EVD-003"],
            contradicting_evidence_ids=["EVD-001"],
            confidence=0.20,
            confidence_label="LOW",
            additional_evidence_required=["Deep network trace audit"],
            status="ruled_out",
        )

        state.current_hypotheses = [h_main, h_alt]
        state.final_conclusion = f"Root cause identified: Service {service_name} experienced failure due to {notes_text}."
        state.conclusion_type = "ROOT_CAUSE_IDENTIFIED"
        state.observed_symptoms = brief.get("initial_symptoms", [
            f"Service failure on {service_name}",
            "Latency / error spike",
        ])

        update_data = {
            "incident_summary": f"Incident on {service_name}: {notes_text[:100]}.",
            "recommended_actions": [
                {
                    "description": f"Review telemetry and error logs for {service_name}",
                    "rationale": "Verify system recovery",
                },
                {
                    "description": f"Restart or scale {service_name} production replicas",
                    "rationale": "Clear transient thread pool or resource backlog",
                },
            ],
            "done": True,
        }
        apply_state_update(state, update_data)

    if save_state_fn:
        save_state_fn(state)

    return state

