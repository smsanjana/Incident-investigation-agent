# Tool Contracts Specification

## Document Metadata
- **Title**: Investigative Diagnostic Tool Contracts & Function Schemas
- **Specification Ref**: [Feature Specification](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md)
- **Constitution Ref**: [Project Constitution](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/constitution.md)

---

## Tool Definitions

### 1. `search_logs`
- **Function Signature**: `search_logs(service: str, start_time: str, end_time: str, severity: Optional[str]=None, keyword: Optional[str]=None, correlation_id: Optional[str]=None, limit: int=50) -> Dict[str, Any]`
- **JSON Function Schema**:
  ```json
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
            "enum": ["api-gateway", "order-service", "payment-service", "db-client", "batch-processor", "all"]
          },
          "start_time": {"type": "string", "description": "ISO 8601 UTC start timestamp"},
          "end_time": {"type": "string", "description": "ISO 8601 UTC end timestamp"},
          "severity": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
          "keyword": {"type": "string"},
          "correlation_id": {"type": "string"},
          "limit": {"type": "integer", "default": 50}
        },
        "required": ["service", "start_time", "end_time"]
      }
    }
  }
  ```

---

### 2. `get_runbook`
- **Function Signature**: `get_runbook(topic: str) -> Dict[str, Any]`
- **JSON Function Schema**:
  ```json
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
              "http_503", "db_connection_pool", "high_latency",
              "deployment_regression", "batch_job_interference",
              "safe_rollback", "service_restart"
            ]
          }
        },
        "required": ["topic"]
      }
    }
  }
  ```

---

### 3. `get_service_metadata`
- **Function Signature**: `get_service_metadata(service_name: str) -> Dict[str, Any]`
- **JSON Function Schema**:
  ```json
  {
    "type": "function",
    "function": {
      "name": "get_service_metadata",
      "description": "Retrieve service metadata including owner, dependencies, DB pool size, replicas, timeouts, deployment info, and scheduled jobs.",
      "parameters": {
        "type": "object",
        "properties": {
          "service_name": {"type": "string"}
        },
        "required": ["service_name"]
      }
    }
  }
  ```

---

### 4. `get_deployment_events`
- **Function Signature**: `get_deployment_events(service: Optional[str]=None, start_time: Optional[str]=None, end_time: Optional[str]=None, event_type: Optional[str]=None, limit: int=50) -> Dict[str, Any]`
- **JSON Function Schema**:
  ```json
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
          "limit": {"type": "integer", "default": 50}
        },
        "required": []
      }
    }
  }
  ```
