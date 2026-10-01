# Runbook: Batch Job Interference

## Symptoms
- Service degradation coincides with scheduled batch job start time
- DB connection pool utilisation rises sharply when batch job starts
- Batch processor logs show high connection count
- API latency or errors begin after batch job acquires DB connections

## Diagnostic Checks
1. Check infrastructure events for scheduled_job_start events
2. Correlate batch job start time with DB pool utilisation rise
3. Check batch-processor logs for db_connect events and connection count
4. Check service metadata for batch job schedule and db_connections_used
5. Check service metadata known_constraints for batch/pool interaction warnings
6. Verify batch job is still running (no job_end event)
7. Calculate: batch_connections + api_connections vs pool_max

## Evidence to Collect
- Infrastructure event: scheduled_job_start timestamp
- Batch processor db_connect logs showing connection count
- DB client pool_stats showing utilisation rise correlated with batch start
- Service metadata: pool_size, batch job db_connections_used
- Known constraints from service metadata

## Causal Analysis
If: batch_job_connections + peak_api_connections > pool_max → pool exhaustion likely
For order-service: batch uses 15-16 connections, pool max is 20, API needs ~4-6 → total ~21 > 20 = exhaustion confirmed

## Safe Actions
- Review batch job logs and timing (read-only)
- Check if job has completed (look for job_end event)
- Document evidence chain

## High-Risk Actions (Require Human Approval)
- Kill or pause batch job process
- Reduce batch job connection count (config change)
- Reschedule batch job to off-peak hours
- Temporarily increase pool size

## Escalation Conditions
- Batch job cannot be safely terminated without data corruption
- Pool exhaustion persists after job completion
- Multiple batch jobs running simultaneously
