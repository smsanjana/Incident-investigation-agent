# Runbook: Investigating HTTP 503 Responses

## Symptoms
- Increased HTTP 503 (Service Unavailable) responses
- Customer-facing checkout or order APIs returning errors
- Error rate alerts firing
- Elevated request latency preceding 503s

## Diagnostic Checks
1. Check API gateway logs for 503 rate and start time
2. Check order-service logs for error events coinciding with 503s
3. Identify the upstream cause: DB timeout, memory pressure, or external dependency failure
4. Check infrastructure events for deployments or scaling events near the 503 onset
5. Check DB client logs for connection pool status
6. Verify all replicas are healthy (kubectl get pods)
7. Check for scheduled jobs running at the time of incident

## Evidence to Collect
- API gateway error rate timeline
- order-service error logs with error codes
- DB client pool utilisation logs
- Infrastructure events (deployments, scaling, DB alerts)
- Batch job execution logs and timing

## Safe Actions
- Review logs and dashboards (read-only)
- Retrieve runbooks for suspected sub-causes (DB, deployment)
- Check pod health status
- Increase replica count temporarily (low-risk)

## High-Risk Actions (Require Human Approval)
- Restart production service replicas
- Roll back deployment
- Disable scheduled batch jobs
- Modify connection pool settings in production
- Terminate active database connections

## Escalation Conditions
- 503 rate exceeds 20% for more than 5 minutes
- Root cause cannot be determined within 30 minutes
- Multiple services affected simultaneously
- Data loss or corruption suspected
