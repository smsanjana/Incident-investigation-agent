# Runbook: Service Restart Assessment

## Purpose
Assess whether restarting the order-service is safe and likely to resolve the incident.

## When Restart May Help
- Connection pool is stuck/corrupted (connections leaked, not returned)
- Memory leak causing performance degradation
- Service is in an unrecoverable error state

## When Restart Will NOT Help
- Root cause is external (batch job holding DB connections)
- Pool exhaustion is caused by batch job — restart releases API connections but batch job immediately re-exhausts the pool
- Database itself is unavailable

## Pre-Restart Checks
1. Identify root cause — will restart address it?
2. Check if batch job is still running and holding pool connections
3. Assess traffic impact of restart (service will be briefly unavailable)
4. Confirm all replicas can handle restart sequentially (rolling restart)
5. Verify health check configuration

## Restart Command (REQUIRES HUMAN APPROVAL)
```
kubectl rollout restart deployment/order-service
```

## Post-Restart Verification
- Monitor error rate after restart
- Check DB connection pool returns to normal levels
- Verify all replicas pass health checks
- If errors persist after restart → root cause is NOT the application state; look externally

## Important Note
If batch job interference is the root cause, restarting the service alone will NOT resolve the issue. The batch job must also be addressed.
