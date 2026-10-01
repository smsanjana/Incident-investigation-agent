# Tool Definitions & Contracts

The AI Incident Investigation Agent relies on four strict read-only diagnostic tools.

---

## 1. `search_logs`
Searches application and infrastructure logs within a specified timeframe.

- **Parameters**:
  - `service` (string, required): Service name (`order-service`, `db-client`, `api-gateway`, `payment-service`, `batch-processor`).
  - `start_time` (string, required): ISO-8601 UTC timestamp.
  - `end_time` (string, required): ISO-8601 UTC timestamp.
  - `keyword` (string, optional): Filter log messages by substring (e.g., `TIMEOUT`, `503`, `POOL_EXHAUSTED`).
  - `severity` (string, optional): `INFO`, `WARN`, `ERROR`, `CRITICAL`.
  - `limit` (integer, default 50): Maximum log entries to return.

---

## 2. `get_runbook`
Retrieves standardized operational troubleshooting runbooks.

- **Parameters**:
  - `topic` (string, required): Runbook topic (`http_503`, `db_connection_pool`, `high_latency`, `deployment_regression`, `batch_job_interference`, `safe_rollback`, `service_restart`).

---

## 3. `get_service_metadata`
Retrieves configuration, dependency mappings, and operational boundaries for a service.

- **Parameters**:
  - `service_name` (string, required): Service name (`order-service`, `payment-service`, etc.).

---

## 4. `get_deployment_events`
Retrieves infrastructure deployment and job lifecycle events.

- **Parameters**:
  - `service` (string, optional): Filter by service name.
  - `event_type` (string, optional): `DEPLOYMENT`, `CONFIG_CHANGE`, `BATCH_JOB`, `RESTART`.
  - `start_time` (string, optional): Start timestamp.
  - `end_time` (string, optional): End timestamp.
