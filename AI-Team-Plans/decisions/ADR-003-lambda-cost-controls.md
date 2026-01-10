# ADR-003: Lambda Cost Controls and Agentic Workflow Guardrails

**Status**: Approved
**Date**: 2026-01-10
**Advisor**: app-advisor
**Domain**: infrastructure, cost-management, agentic-systems

---

## Context

AWS Lambda usage has grown significantly:
- **2.6M invocations/month** (up from near-zero pre-Dec 21)
- **~$50/month forecast** (currently within free tier)
- Primary driver: CredmateFrontendDefaultFunction (652k invocations/week)

As we build autonomous AI agents that may invoke Lambda functions, we need guardrails to prevent:
1. **Runaway costs** from infinite loops or misconfigured agents
2. **Resource exhaustion** from concurrent execution spikes
3. **Silent failures** that go unnoticed until billing

## Decision

Implement a **three-layer defense** for Lambda cost control:

### Layer 1: AWS-Level Controls
- **Budget alerts** at $5, $10, $25 thresholds
- **Concurrency limits** per function (prevent single function from consuming all capacity)
- **CloudWatch alarms** on invocation spikes

### Layer 2: Application-Level Circuit Breakers
- **Per-session call limits** in agent code
- **Exponential backoff** on repeated failures
- **Kill switch** integration with AI Orchestrator

### Layer 3: Observability
- **Cost attribution tags** on all Lambda functions
- **Weekly cost reports** via CloudWatch
- **Anomaly detection** for invocation patterns

## Implementation Notes

### AWS Changes
Files to modify: 3 (Terraform/CloudFormation)

1. Create AWS Budget for Lambda
2. Set reserved concurrency on high-volume functions
3. Create CloudWatch alarm for invocation spikes

### Agent Code Changes
Files to modify: 2

1. Add `LambdaCircuitBreaker` class to orchestration
2. Integrate with existing kill-switch mechanism

### No Schema Changes
No database migrations required.

### No API Changes
No endpoint modifications.

## Consequences

**Positive:**
- Prevents unexpected cost spikes
- Provides visibility into Lambda usage
- Safe guardrails for agentic workflows

**Negative:**
- Concurrency limits may throttle legitimate traffic during spikes
- Circuit breakers add latency (negligible)

**Mitigations:**
- Set concurrency limits with 50% headroom above peak usage
- Circuit breaker only activates after configurable threshold

## Tags

```yaml
tags: [infrastructure, lambda, cost-control, agentic, guardrails]
domains: [infrastructure, cost-management]
applies_to:
  - 'orchestration/*.py'
  - 'terraform/*.tf'
  - 'governance/*.yaml'
```

## Tasks Generated

| ID | Title | Type | Priority | Agent |
|----|-------|------|----------|-------|
| TASK-003-001 | Create AWS Budget for Lambda | infrastructure | P1 | manual |
| TASK-003-002 | Set Lambda concurrency limits | infrastructure | P1 | manual |
| TASK-003-003 | Create CloudWatch invocation alarm | infrastructure | P2 | manual |
| TASK-003-004 | Implement LambdaCircuitBreaker class | feature | P1 | FeatureBuilder |
| TASK-003-005 | Add circuit breaker to agent orchestration | feature | P2 | FeatureBuilder |
| TASK-003-006 | Write tests for circuit breaker | test | P3 | TestWriter |

## Acceptance Criteria

- [ ] Budget alert fires at $5 threshold (testable via simulation)
- [ ] Concurrency limit prevents >100 concurrent executions on Frontend function
- [ ] CloudWatch alarm triggers on >50k invocations in 5 minutes
- [ ] Circuit breaker stops agent after 100 Lambda calls in single session
- [ ] Kill switch disables all agent Lambda invocations when activated

## References

- AWS Lambda Pricing: https://aws.amazon.com/lambda/pricing/
- Current usage: ~2.6M requests/month, ~60k GB-seconds/month
- Free tier: 1M requests, 400k GB-seconds
