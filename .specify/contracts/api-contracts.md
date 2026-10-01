# REST API Contracts Specification

## Document Metadata
- **Title**: API Endpoints, Payloads, and Response Contracts
- **Specification Ref**: [Feature Specification](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md)
- **Constitution Ref**: [Project Constitution](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/constitution.md)

---

## Endpoints

### 1. `POST /incidents`
- **Description**: Create a new incident brief.
- **Request Body**:
  ```json
  {
    "incident_id": "INC-001",
    "title": "Order service HTTP 503 spikes",
    "affected_service": "order-service",
    "severity": "SEV-2",
    "start_time": "2025-07-14T02:00:00Z",
    "detection_time": "2025-07-14T02:15:00Z",
    "customer_impact": "High error rate on checkout page",
    "reporter_notes": "Intermittent failures started after scheduled maintenance window",
    "initial_symptoms": ["HTTP 503", "DB Connection Timeout"],
    "tags": ["production", "checkout"]
  }
  ```
- **Response**: `201 Created`
  ```json
  {
    "incident_id": "INC-001",
    "title": "Order service HTTP 503 spikes",
    "affected_service": "order-service",
    "severity": "SEV-2",
    "start_time": "2025-07-14T02:00:00Z",
    "detection_time": "2025-07-14T02:15:00Z",
    "customer_impact": "High error rate on checkout page",
    "reporter_notes": "Intermittent failures started after scheduled maintenance window",
    "status": "open",
    "initial_symptoms": ["HTTP 503", "DB Connection Timeout"],
    "tags": ["production", "checkout"],
    "created_at": "2026-08-16T12:00:00Z"
  }
  ```

---

### 2. `GET /incidents`
- **Description**: List all stored incidents ordered by creation time descending.
- **Response**: `200 OK`
  ```json
  [
    {
      "incident_id": "INC-001",
      "title": "Order service HTTP 503 spikes",
      "affected_service": "order-service",
      "severity": "SEV-2",
      "start_time": "2025-07-14T02:00:00Z",
      "detection_time": "2025-07-14T02:15:00Z",
      "customer_impact": "High error rate on checkout page",
      "reporter_notes": "Intermittent failures started after scheduled maintenance window",
      "status": "open",
      "initial_symptoms": ["HTTP 503", "DB Connection Timeout"],
      "tags": ["production", "checkout"],
      "created_at": "2026-08-16T12:00:00Z"
    }
  ]
  ```

---

### 3. `GET /incidents/{incident_id}`
- **Description**: Fetch incident details and current status by ID.
- **Response**: `200 OK` (Single `IncidentResponse` object) or `404 Not Found`.

---

### 4. `POST /incidents/{incident_id}/investigate`
- **Description**: Trigger agentic investigation loop.
- **Response**: `200 OK`
  ```json
  {
    "incident_id": "INC-001",
    "status": "concluded",
    "conclusion_type": "ROOT_CAUSE_IDENTIFIED",
    "hypotheses_count": 2,
    "evidence_count": 4,
    "tools_used_count": 7,
    "message": "Investigation complete. Retrieve the report at GET /incidents/{id}/report"
  }
  ```

---

### 5. `GET /incidents/{incident_id}/evidence`
- **Description**: Retrieve all raw collected evidence items, hypotheses, tools log, and open questions.
- **Response**: `200 OK`
  ```json
  {
    "incident_id": "INC-001",
    "evidence_items": [
      {
        "evidence_id": "EVD-001",
        "source": "get_deployment_events:batch-processor",
        "description": "Scheduled job order-reconciliation started at 02:10 UTC",
        "raw_content": "job_name: order-reconciliation, schedule: 0 2 * * *",
        "timestamp_collected": "2026-08-16T12:00:00Z",
        "relevance": "Identifies batch job start time near 503 onset"
      }
    ],
    "evidence_count": 1,
    "hypotheses": [],
    "hypotheses_count": 0,
    "tools_used": [],
    "tools_used_count": 0,
    "open_questions": []
  }
  ```

---

### 6. `GET /incidents/{incident_id}/report`
- **Description**: Retrieve final structured investigation report document.
- **Response**: `200 OK` (Schema specified in [Feature Spec Section 12](file:///C:/Users/sanjana.smarigoudar/.gemini/antigravity/scratch/incident-agent/.specify/spec.md#12-final-report-structure-specification)).

---

### 7. `POST /incidents/{incident_id}/actions/{action_id}/approve`
- **Description**: Record human approval/rejection decision.
- **Request Body**:
  ```json
  {
    "approved": true,
    "approved_by": "lead-sre@company.com",
    "rejection_reason": null
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "action_id": "act-12345",
    "incident_id": "INC-001",
    "description": "Kill or pause the order-reconciliation batch job process",
    "category": "HIGH_RISK_OPERATIONAL",
    "approval_status": "approved",
    "approved_by": "lead-sre@company.com",
    "approved_at": "2026-08-16T12:01:00Z",
    "rejection_reason": null,
    "note": "IMPORTANT: This approval is RECORDED ONLY. The action must be executed manually by an authorized engineer."
  }
  ```
