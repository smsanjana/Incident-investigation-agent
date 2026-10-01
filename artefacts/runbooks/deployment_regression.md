# Runbook: Recent Deployment Regression

## Symptoms
- Service errors begin shortly after a deployment
- New error codes not seen in previous version
- Performance degradation following deployment
- Health checks failing on new replicas

## Diagnostic Checks
1. Check deployment timestamp vs incident start time
2. Review deployment logs for any warnings or errors during deployment
3. Check application logs for new error codes introduced post-deployment
4. Compare error rate before and after deployment
5. Review deployment diff/changelog for risky changes
6. Check config warnings introduced by new version
7. Verify all replicas updated to new version

## Evidence to Collect
- Deployment event timestamp and version
- Application logs comparing pre- and post-deployment error rates
- New error codes introduced in the new version
- Deployment diff or changelog
- Config warnings from new version startup

## Key Discriminator
If errors began IMMEDIATELY after deployment completion and had NO other concurrent triggers (batch job, traffic spike), deployment regression is the likely cause.
If errors began AFTER a delay (>20 minutes) and coincide with another event (batch job, scaling), the deployment may be a red herring.

## Safe Actions
- Review deployment logs and changelog (read-only)
- Compare error rates before/after deployment
- Check if rollback is available and tested

## High-Risk Actions (Require Human Approval)
- Roll back deployment: `kubectl rollout undo deployment/order-service`
- Disable new feature flags introduced in deployment
- Modify production configuration changed in deployment

## Escalation Conditions
- Errors started immediately on deployment completion
- Rollback is not available or untested
- Multiple services affected by the deployment
