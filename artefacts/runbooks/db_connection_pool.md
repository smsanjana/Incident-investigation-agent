# Runbook: Database Connection Pool Exhaustion

## Symptoms
- DB connection timeout errors in application logs
- error_code: ERR_POOL_EXHAUSTED in db-client logs
- Pool utilisation at 100% (active == max)
- Application returning 503 due to DB unavailability
- Warnings: WARN_POOL_HIGH_UTILISATION or WARN_POOL_CRITICAL_UTILISATION

## Known Causes
1. **Batch job interference**: Scheduled batch jobs (e.g., order-reconciliation) can acquire a large number of connections from the shared pool, leaving insufficient connections for API requests.
2. **Connection leak**: Connections not being returned to the pool due to application bugs.
3. **Long-running queries**: Queries holding connections for extended periods.
4. **Traffic spike**: Sudden increase in concurrent requests exceeding pool capacity.
5. **Pool misconfiguration**: Pool size too small for current traffic levels.

## Diagnostic Checks
1. Check db-client logs for pool_stats events showing utilisation progression
2. Check batch-processor logs for job start time and connection count
3. Correlate batch job start time with pool exhaustion time
4. Check infrastructure events for DB alerts (EVT type: db_alert)
5. Verify pool_size in service metadata
6. Check if batch job schedule aligns with incident window
7. Review service metadata for known_constraints related to batch job pool usage

## Evidence to Collect
- DB client pool_stats logs showing active/idle/max counts over time
- Batch processor job_start and db_connect events
- Infrastructure DB alerts
- Service metadata pool_size and batch job db_connections_used

## Safe Actions
- Monitor pool utilisation in real-time (read-only)
- Review service metadata for known constraints
- Check batch job status (read-only query)

## High-Risk Actions (Require Human Approval)
- Terminate batch job to release connections
- Increase connection pool size in production config
- Kill long-running database sessions
- Disable scheduled job trigger
- Restart application to reset connection pool

## Escalation Conditions
- Pool exhausted for more than 10 minutes
- Batch job cannot be safely terminated
- Pool size change requires DB restart
- Customer-facing SLA breach

## Prevention
- Configure batch jobs to use a separate connection pool or run during off-peak hours
- Implement connection pool monitoring with proactive alerts
- Review pool size quarterly relative to traffic growth
