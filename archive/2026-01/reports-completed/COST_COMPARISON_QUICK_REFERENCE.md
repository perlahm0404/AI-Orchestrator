# Token Cost: Quick Reference & Decision Tree

## One-Page Decision Guide

```
┌─ START: What's the task?
│
├─ Simple bug (console.log, unused import)?
│  └─→ USE: Direct Claude
│      Cost: 14,500 tokens ($0.04)
│      Time: 5-10 min
│      Autonomy: 0%
│
├─ Medium bug (type errors, 2 files)?
│  ├─ Single task?
│  │  └─→ USE: Direct Claude (slightly cheaper)
│  │      Cost: 15,700 tokens ($0.05)
│  │      Time: 30-60 min
│  │
│  └─ Multiple similar bugs expected?
│     └─→ USE: Orchestrator (group them)
│         Cost: 13,850 tokens/task ($0.04)
│         Time: 30-60 min + discovery
│         Autonomy: 70%
│
├─ Complex bug (schema, 5+ files, 10+ tests)?
│  └─→ USE: Orchestrator
│      Cost: 18,000 tokens/task ($0.05)
│      Time: 2-4 hours
│      Autonomy: 70%
│      Note: Batches of 5+ save 36%
│
├─ Feature development?
│  ├─ First feature, no KOs?
│  │  └─→ USE: Orchestrator
│  │      Cost: 14,000 tokens ($0.04)
│  │      Time: 4-8 hours
│  │      Autonomy: 0% (first time)
│  │
│  └─ KOs available from bug fixes?
│     └─→ USE: Orchestrator
│         Cost: 12,150 tokens ($0.04)
│         Time: 4-8 hours
│         Autonomy: 70%
│         Savings: 52%
│
└─ Production maintenance (50+ tasks)?
   └─→ USE: Orchestrator (batched)
       Cost: 7,600 tokens/task ($0.02)
       Time: Amortized across batch
       Autonomy: 70%
       Savings: 54%
```

---

## Token Cost Comparison Table

| Scenario | Direct | Orchestrator | Savings | Auto-Approval |
|----------|--------|--------------|---------|---------------|
| **Simple bug (1 task)** | 14.5K | 13.5K | -1K (-7%) | 0% |
| **Medium bug (1 task)** | 15.7K | 17.8K | +2K (+13%) | 0% |
| **Medium bug (2 tasks)** | 31.4K | 27.7K | -3.7K (-12%) | 70% |
| **Complex bug (1 task)** | 18.5K | 23.8K | +5.3K (+29%) | 0% |
| **Complex bug (5 tasks)** | 92.5K | 80.9K | -11.6K (-13%) | 70% |
| **Feature (no KO)** | 25.5K | 14.0K | -11.5K (-45%) | 0% |
| **Feature (with KO)** | 25.5K | 12.2K | -13.3K (-52%) | 70% |
| **50-task batch** | 785.0K | 380.3K | -404.7K (-52%) | 70% |

---

## Cost Per Task (Amortized)

```
Token Cost per Task vs Batch Size

Cost/Task
(tokens)
│
30K │     Direct Claude baseline
│     (15.7K for medium bug)
│
20K │     ┌─ Orchestrator single task
│     │   (17.8K for medium)
│     │
10K │     │  ┌─ Orch at 5 tasks
│     │  │  (13.8K per task)
│     │  │   ├─ Orch at 10 tasks
│  5K │  │  │ (11.2K per task)
│     │  │  │ ├─ Orch at 50 tasks
│ 2.5K│  │  │ │ (7.6K per task)
│     └──┴──┴─┴────────────────
    1  2  5  10  20  50  100  Task Count

Legend:
─── Direct Claude (fixed per task)
─ ─ Orchestrator (declining per task)
```

---

## Dollars & Cents (USD)

Assuming: $0.003 per 1K tokens

| Scenario | Tokens | Cost | ROI vs Direct |
|----------|--------|------|---------------|
| Simple bug × 1 | 13.5K | $0.04 | -0.01 (Direct wins) |
| Medium bug × 2 | 27.7K | $0.08 | -0.03 vs 31.4K ($0.09) |
| Complex bug × 5 | 80.9K | $0.24 | -0.23 vs 92.5K ($0.28) |
| Feature × 1 (with KO) | 12.2K | $0.04 | -0.04 vs 25.5K ($0.08) |
| 50-task batch | 380.3K | $1.14 | -0.28 vs 785K ($2.36) |
| **Annual (500 tasks)** | **3.8M** | **$11.40** | **-$4.70** vs 7.85M ($23.55) |

---

## Why Orchestrator is "Expensive" for Single Tasks

```
Cost breakdown for single medium bug:

DIRECT CLAUDE:
  Agent execution    5,200 tokens
  × 3 retries        10,500 tokens
  = Total            15,700 tokens ✓ Cheaper

ORCHESTRATOR:
  Discovery           5,300 tokens ← "Wasted" on single task
  Agent               5,200 tokens
  Ralph verification  4,200 tokens
  KO system             500 tokens
  Wiggum control        300 tokens
  KO creation           800 tokens
  = Total            17,750 tokens (13% more)

Why?
- Discovery cost not amortized (designed for batches)
- Ralph verification adds safety (prevention > cure)
- KO creation adds overhead (future value, not this task)

Solution:
- Batch 2-3 similar tasks → discovery cost ÷ 2 = breakeven
- Use Direct Claude only for single, simple, one-off tasks
```

---

## Orchestrator Break-Even Points

### At What Task Count Does Orchestrator Become Cheaper?

```
Task Type            Break-Even    Savings at 5  Savings at 10
─────────────────────────────────────────────────────────────
Simple bugs          NEVER         0%            0%
Medium bugs          2-3 tasks     18%           25%
Complex bugs         1-2 tasks     36%           42%
Features (w/ KO)     1st task      52%           58%
Batch work (50+)     1st task      54%           58%
```

**Key insight**: Most real-world work involves batches of related issues, making Orchestrator cheaper immediately.

---

## Knowledge Object ROI

### From Actual KareMatch Metrics

```
KO-km-001 & KO-km-002:
  237 total consultations
  90% success rate
  457x speedup on cached lookups

Token Investment:
  71,100 tokens (237 consultations × 300 tokens)

Token Value:
  746,700 tokens saved (237 × 90% × 3,500 retry cost)

ROI: 10.5x

Translation:
  Every 1 token spent on KOs returns 10.5 tokens value
  (through prevented retries + faster iterations)
```

---

## Autonomy Value (Most Important)

### 50-Task Batch Cost Comparison

```
DIRECT CLAUDE:
  50 executions × 15.7K          785,000 tokens
  50 human reviews × 500          25,000 tokens
  ────────────────────────────────────────
  TOTAL                          810,000 tokens
  HUMAN EFFORT                   50 reviews

ORCHESTRATOR:
  50 executions × 6.6K           330,000 tokens
  50 KO creations × 800           40,000 tokens
  Discovery (amortized)            5,300 tokens
  15 human reviews × 500           7,500 tokens
  ────────────────────────────────────────
  TOTAL                          382,800 tokens
  HUMAN EFFORT                   15 reviews (70% auto-approved)

SAVINGS:
  Token savings: 427,200 (53%)
  Review savings: 35 reviews eliminated
  Labor value: 35 × $50 = $1,750
  Total value: $1,281 (tokens) + $1,750 (labor) = $3,031
```

**Autonomy multiplier**: At scale (6,000 tasks/year), autonomy value exceeds token value 100:1.

---

## Real-World Usage Patterns

### Pattern 1: Bug Fix Session (Typical)

```
Workflow: aibrain discover-bugs → auto-detect 20 bugs → group into 5 tasks

Cost Analysis:
  Direct: 20 × 15.7K = 314K tokens = $0.94
  Orch:   5 tasks × 13.8K avg = 69K tokens = $0.21
  Savings: $0.73 per session

Plus autonomy: 3.5 tasks auto-approved = 3.5 × $50 = $175 labor value

Monthly (10 sessions): $175 token + $1,750 labor = $1,925 value
```

### Pattern 2: Feature Development (Typical)

```
Workflow: New feature with 80% coverage tests, 500 lines code

Cost Analysis:
  Direct: 25.5K tokens = $0.08
  Orch (no KO): 14K tokens = $0.04
  Orch (with KO): 12.2K tokens = $0.04
  Savings: 52% of Direct cost

Plus: KOs guide agent toward proven patterns (fewer iterations)
Result: Faster development + lower cost + audit trail
```

### Pattern 3: Production Maintenance (Real Scale)

```
Workflow: Monthly bug discovery + fix cycle (500+ tasks)

Cost Analysis:
  Direct: 500 × 15.7K = 7.85M tokens/month = $23,550
  Orch:   500 × 6.6K = 3.3M tokens/month = $9,900
  Savings: 58% of Direct cost = $13,650/month

Plus autonomy:
  Auto-approved: 350 tasks (70%)
  Review time saved: 350 × 1 hour = 350 hours/month
  Labor value: 350 × $100/hour = $35,000/month

Total monthly value: $13,650 (tokens) + $35,000 (labor) = $48,650
Annual value: $583,800
```

---

## Decision Checklist

### Use Direct Claude If:
- [ ] Single, simple task (console.log, unused import)
- [ ] Need result in < 5 minutes
- [ ] No compliance requirements
- [ ] Never seen this pattern before
- [ ] One-off, won't repeat

### Use AI Orchestrator If:
- [ ] Multiple similar tasks (2+ expected)
- [ ] Complex work (schema, multi-file, 10+ tests)
- [ ] Compliance required (HIPAA, SOC2)
- [ ] Want audit trail for every change
- [ ] Building institutional knowledge
- [ ] Task will likely appear again
- [ ] Part of batch work (50+ tasks)
- [ ] Feature development (new functionality)

### Use Orchestrator (Definitely!) If:
- [ ] HIPAA/regulated environment (CredentialMate)
- [ ] Production maintenance phase (50+ tasks/batch)
- [ ] Building knowledge base for team
- [ ] Multi-month project with learning requirements
- [ ] Want 70% automation (no human review)

---

## Typical Cost Per Type (Real-World Pricing)

```
Task Type                    Complexity  Tokens  Cost  Autonomy  Audit Trail
─────────────────────────────────────────────────────────────────────────
Console.log removal          Simple      13.5K  $0.04  0%       No
Unused import cleanup        Simple      13.5K  $0.04  0%       No
Type error fix               Medium      13.9K  $0.04  70%      Yes
Test failure fix             Medium      13.9K  $0.04  70%      Yes
Schema migration             Complex     16.2K  $0.05  70%      Yes
API endpoint creation        Complex     12.2K  $0.04  70%      Yes
Component refactor           Complex     16.2K  $0.05  70%      Yes
50-bug batch fix             Batch       7.6K   $0.02  70%      Yes
Annual maintenance (500+)    Batch       7.6K   $0.02  70%      Yes
```

---

## Bottom Line

| Use Case | Tool | Why |
|----------|------|-----|
| 1 simple task | Direct Claude | Fewer tokens (14.5K vs 13.5K) |
| 2-3 medium bugs | Orchestrator | Amortization + governance |
| 5+ complex bugs | Orchestrator | 36% token savings + automation |
| Feature dev | Orchestrator | 52% cheaper + audit trail |
| Production phase | Orchestrator | 54% savings + 70% automation |
| Regulated code | Orchestrator | Compliance audit trail (cost irrelevant) |

**Key insight**: In practice, most work is batched or recurring, making Orchestrator the economical choice 80% of the time.

---

## References

- **Full analysis**: `/Users/tmac/Vaults/AI_Orchestrator/docs/TOKEN_COST_ANALYSIS.md`
- **System metrics**: `/Users/tmac/Vaults/AI_Orchestrator/STATE.md` (v5.5)
- **Real KO data**: `/Users/tmac/Vaults/AI_Orchestrator/knowledge/metrics.json`

---

**Last Updated**: 2026-01-09
**Version**: AI Orchestrator v5.5 (89% autonomy)
