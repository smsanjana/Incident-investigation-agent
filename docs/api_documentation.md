# API Documentation: AI Incident Investigation Agent

## Overview
The AI Incident Investigation Agent exposes a RESTful API built on FastAPI. It provides endpoints to register controlled incidents, trigger AI agent investigations, inspect collected evidence and state, record action approvals, and retrieve final structured investigation reports.

Base URL: `http://localhost:8000`

---

## Endpoint Reference

### 1. Ingest Incident
Registers a new controlled incident for investigation.

- **URL**: `POST /incidents`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "incident_id": "INC-001",
    "title": "API Gateway 503 Spike",
    "affected_service": "order-service",
    "start_time": "2025-07-14T02:15:00Z",
    "severity": "CRITICAL",
    "initial_symptoms": [
      "Increased HTTP 503 responses",
      "Elevated request latency"
    ]
  }
  ```
- **Response**: `201 Created`
  ```json
  {
    "incident_id": "INC-001",
    "affected_service": "order-service",
    "severity": "CRITICAL",
    "status": "open",
    "created_at": "2025-07-14T02:16:00Z"
  }
  ```

---

### 2. List Incidents
Retrieves all registered incidents.

- **URL**: `GET /incidents`
- **Response**: `200 OK`
  ```json
  [
    {
      "incident_id": "INC-001",
      "affected_service": "order-service",
      "severity": "CRITICAL",
      "status": "open"
    }
  ]
  ```

---

### 3. Get Incident Details
Retrieves details for a specific incident.

- **URL**: `GET /incidents/{incident_id}`
- **Response**: `200 OK` or `404 Not Found`

---

### 4. Trigger Investigation
Starts or resumes an AI-assisted investigation loop for an incident.

- **URL**: `POST /incidents/{incident_id}/investigate`
- **Response**: `200 OK`
  ```json
  {
    "incident_id": "INC-001",
    "status": "concluded",
    "conclusion_type": "ROOT_CAUSE_IDENTIFIED",
    "iterations": 4,
    "evidence_count": 4,
    "hypotheses_count": 2
  }
  ```

---

### 5. Get Evidence State
Retrieves the collected evidence items, hypotheses, tools used, and open questions.

- **URL**: `GET /incidents/{incident_id}/evidence`
- **Response**: `200 OK`
  ```json
  {
    "incident_id": "INC-001",
    "evidence_items": [...],
    "hypotheses": [...],
    "tools_used": [...],
    "open_questions": [...]
  }
  ```

---

### 6. Get Recommended Actions
Lists recommended actions generated during the investigation.

- **URL**: `GET /incidents/{incident_id}/actions`
- **Response**: `200 OK`

---

### 7. Approve Recommended Action
Records an engineer's decision to authorize a high-risk operational action without executing production commands.

- **URL**: `POST /incidents/{incident_id}/actions/{action_id}/approve`
- **Request Body**:
  ```json
  {
    "approved": true,
    "approved_by": "engineer@company.com",
    "rejection_reason": null
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "action_id": "ACT-002",
    "incident_id": "INC-001",
    "approval_status": "approved",
    "approved_by": "engineer@company.com",
    "note": "RECORDED ONLY — No production execution performed."
  }
  ```

---

### 8. Get Investigation Report
Retrieves the final structured investigation report.

- **URL**: `GET /incidents/{incident_id}/report`
- **Response**: `200 OK`

---

### 9. Health Check
Application health check endpoint.

- **URL**: `GET /health`
- **Response**: `200 OK` `{"status": "healthy"}`
