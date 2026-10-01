# Runbook: High Request Latency

## Symptoms
- p99 latency significantly above baseline (e.g., >4s vs 200ms baseline)
- WARN_DB_SLOW_ACQUIRE in application logs
- Requests timing out at upstream gateway
- Slow DB query times

## Diagnostic Checks
1. Check application logs for latency measurements
2. Check DB client logs for slow connection acquisition times
3. Check DB query durations for slow queries
4. Check CPU and memory metrics on all replicas
5. Check for GC pauses (look for GC_PAUSE events in logs)
6. Check for network issues between service and database
7. Correlate latency onset with deployment or batch job events

## Evidence to Collect
- Request duration histograms from logs
- DB connection acquisition time logs
- DB query duration logs
- Infrastructure events around latency onset time
- Replica resource utilisation

## Safe Actions
- Review latency trends in dashboards
- Check DB slow query log (read-only)
- Verify replica health and resource usage

## High-Risk Actions (Require Human Approval)
- Kill long-running DB queries
- Restart service replicas
- Change timeout configurations

## Escalation Conditions
- Latency exceeds 10x baseline for more than 5 minutes
- DB slow queries cannot be identified
- Multiple services affected
