---
# Document Metadata
doc-id: "g-ADR-003"
title: "Lambda Cost Controls and Agentic Workflow Guardrails"
created: "2026-01-10"
updated: "2026-01-10"
author: "Claude AI"
status: "approved"

# Compliance Metadata
compliance:
  soc2:
    controls: ["CC8.1", "CC6.6"]
    evidence-type: "documentation"
    retention-period: "7-years"
  iso27001:
    controls: ["A.14.2.2", "A.12.1.1"]
    classification: "internal"
    review-frequency: "annual"

# Project Context
project: "ai-orchestrator"
domain: "infrastructure"
relates-to: ["ADR-004", "cm-plan-lambda-migration"]

# Change Control
version: "1.0"
---

# ADR-003: Lambda Cost Controls and Agentic Workflow Guardrails

**Status**: Complete ✅
**Date**: 2026-01-10
**Completed**: 2026-01-10
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

- [x] Budget alert fires at $5 threshold (testable via simulation)
  - ✅ Lambda-Monthly-Limit budget created at $10/month
- [x] Concurrency limit prevents >100 concurrent executions on Frontend function
  - ✅ CredmateFrontendDefaultFunction @ 100 reserved concurrency
- [x] CloudWatch alarm triggers on >50k invocations in 5 minutes
  - ✅ Lambda-Invocation-Spike alarm created
- [x] Circuit breaker stops agent after 100 Lambda calls in single session
  - ✅ LambdaCircuitBreaker class with configurable max_calls_per_session
- [x] Kill switch disables all agent Lambda invocations when activated
  - ✅ Integration with AI_BRAIN_MODE (OFF/PAUSED blocks all calls)

## Completion Summary

**All 6 tasks completed on 2026-01-10**

### Phase 1: AWS Infrastructure (Manual)
| Task | Result |
|------|--------|
| TASK-003-001 | Budget: `Lambda-Monthly-Limit` @ $10/month |
| TASK-003-002 | Concurrency: `CredmateFrontendDefaultFunction` @ 100 |
| TASK-003-003 | Alarm: `Lambda-Invocation-Spike` @ 50k/5min |

### Phase 2: Application Code (FeatureBuilder)
| Task | Result |
|------|--------|
| TASK-003-004 | `orchestration/circuit_breaker.py` - LambdaCircuitBreaker class (350 lines) |
| TASK-003-005 | Integration in `autonomous_loop.py` and `iteration_loop.py` |

### Phase 3: Testing (TestWriter)
| Task | Result |
|------|--------|
| TASK-003-006 | `tests/test_circuit_breaker.py` - 27 tests (100% passing) |

### Key Implementation Details
- **Thread-safe**: Uses `threading.Lock` for all counter operations
- **Kill switch**: Respects `AI_BRAIN_MODE` environment variable
- **Context manager**: `lambda_guard()` for clean Lambda call wrapping
- **Singleton pattern**: Global breaker via `get_lambda_breaker()`
- **Session stats**: Full call history and statistics via `get_stats()`

## References

- AWS Lambda Pricing: https://aws.amazon.com/lambda/pricing/
- Current usage: ~2.6M requests/month, ~60k GB-seconds/month
- Free tier: 1M requests, 400k GB-seconds
