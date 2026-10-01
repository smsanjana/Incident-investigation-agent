# Runbook: Safe Rollback Assessment

## Purpose
Assess whether rolling back a deployment is safe and likely to resolve the incident.

## Pre-Rollback Checks
1. Confirm deployment is the likely root cause (errors started immediately after deployment)
2. Verify rollback target version is known and healthy
3. Check if database schema migrations were applied (rollback may not reverse schema changes)
4. Verify rollback capability in service metadata
5. Confirm rollback procedure with service owner
6. Check if rollback will require downtime

## Evidence Required Before Recommending Rollback
- Causal link between deployment and errors (not just temporal correlation)
- Confirmation that no concurrent events (batch jobs, traffic spikes) are the actual cause
- Rollback target version confirmed healthy
- Schema migration impact assessed

## Rollback Command (REQUIRES HUMAN APPROVAL)
```
kubectl rollout undo deployment/order-service
```

## Post-Rollback Verification
- Monitor error rate for 5 minutes post-rollback
- Confirm DB pool utilisation returns to normal
- Verify all replicas healthy on previous version
- Confirm customer-facing errors resolved

## When NOT to Rollback
- Root cause is not the deployment (e.g., batch job interference)
- Database schema changes cannot be reversed safely
- Rollback target version has known critical bugs
- Errors began >20 minutes after deployment with concurrent triggers
