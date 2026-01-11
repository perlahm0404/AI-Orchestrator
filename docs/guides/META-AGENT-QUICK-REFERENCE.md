# Meta-Agent Quick Reference Card

**Version**: v6.0 | **Date**: 2026-01-10

---

## 🚦 When to Invoke Each Agent

```
┌─────────────────────────────────────────────────────────────┐
│ GOVERNANCE AGENT (ALWAYS)                                   │
├─────────────────────────────────────────────────────────────┤
│ ✅ Every single task (no conditions)                        │
│ Purpose: Risk assessment, HIPAA compliance, security        │
│ Decision: APPROVED | REQUIRES_APPROVAL | BLOCKED            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PM AGENT (CONDITIONAL)                                      │
├─────────────────────────────────────────────────────────────┤
│ Trigger: task.type == "feature" OR                          │
│          task.affects_user_experience == True               │
│ Purpose: Evidence validation, roadmap alignment             │
│ Decision: APPROVED | BLOCKED | MODIFIED                     │
│ Skip: Bugfixes, refactors, tests (no user impact)           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ CMO AGENT (CONDITIONAL)                                     │
├─────────────────────────────────────────────────────────────┤
│ Trigger: task.is_gtm_related == True                        │
│ Purpose: GTM validation, messaging alignment, ethics        │
│ Decision: APPROVED | PROPOSE_ALTERNATIVE                    │
│ Skip: Product/engineering work (90% of tasks)               │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Invocation Examples

### Python (Manual)

```python
# 1. GOVERNANCE (always)
from agents.coordinator.governance_agent import GovernanceAgent
from adapters.credentialmate import CredentialMateAdapter

adapter = CredentialMateAdapter()
gov = GovernanceAgent(adapter)

result = gov.execute(
    task_id="BUG-001",
    task_description="Fix authentication timeout",
    task_data={
        "type": "bugfix",
        "files": ["src/auth/session.py"],
        "touches_phi_code": False,
        "affects_user_experience": True,
    }
)

# Check result.decision: "APPROVED" | "REQUIRES_APPROVAL" | "BLOCKED"

# 2. PM (if feature OR user-facing)
from agents.coordinator.product_manager import ProductManagerAgent

pm = ProductManagerAgent(adapter)

result = pm.execute(
    task_id="FEAT-001",
    task_description="Add NP onboarding flow",
    task_data={
        "type": "feature",
        "files": ["src/onboarding/flow.py"],
        "affects_user_experience": True,
    }
)

# Check result.decision: "APPROVED" | "BLOCKED" | "MODIFIED"

# 3. CMO (if GTM)
from agents.coordinator.cmo_agent import CMOAgent

cmo = CMOAgent(adapter)

result = cmo.execute(
    task_id="LANDING-001",
    task_description="Create waitlist landing page",
    task_data={
        "type": "feature",
        "is_gtm_related": True,
    }
)

# Check result.decision: "APPROVED" | "PROPOSE_ALTERNATIVE"
```

### Automatic (via autonomous_loop.py)

```bash
# Meta-agents invoke automatically
python autonomous_loop.py --project credentialmate --max-iterations 100

# Conditional gates fire based on task metadata
# No manual invocation needed
```

---

## 📋 Task Data Schema

```python
task_data = {
    # Required
    "type": "feature" | "bugfix" | "refactor" | "test",
    "files": ["path/to/file.py"],

    # PM triggers
    "affects_user_experience": bool,  # User-facing change?

    # Governance triggers
    "touches_phi_code": bool,  # PHI-handling code?

    # CMO triggers
    "is_gtm_related": bool,  # Marketing/GTM task?
}
```

---

## 🎯 Decision Matrix

| Task Type | Governance | PM | CMO |
|-----------|:----------:|:--:|:---:|
| Feature (GTM) | ✅ | ✅ | ✅ |
| Feature (non-GTM) | ✅ | ✅ | ❌ |
| Bugfix (user-facing) | ✅ | ✅ | ❌ |
| Bugfix (internal) | ✅ | ❌ | ❌ |
| Refactor | ✅ | ❌ | ❌ |
| Test | ✅ | ❌ | ❌ |
| Landing Page | ✅ | ✅ | ✅ |

---

## 🚨 Common Scenarios

### ✅ Feature with Evidence (All Gates Pass)

```python
task = {
    "type": "feature",
    "affects_user_experience": True,
    "is_gtm_related": False,
    "evidence_refs": ["EVIDENCE-001"],  # ← Has evidence!
}

# Flow:
# 1. Governance: APPROVED (LOW risk)
# 2. PM: APPROVED (has evidence)
# 3. CMO: SKIPPED (not GTM)
# → Proceeds to execution
```

### ❌ Feature without Evidence (PM Blocks)

```python
task = {
    "type": "feature",
    "affects_user_experience": True,
    "evidence_refs": [],  # ← No evidence!
}

# Flow:
# 1. Governance: APPROVED (LOW risk)
# 2. PM: BLOCKED (no evidence)
# → STOPPED - must capture evidence first
```

### ⚠️ PHI Task (Governance Requires Approval)

```python
task = {
    "type": "bugfix",
    "touches_phi_code": True,  # ← PHI flag!
    "affects_user_experience": True,
    "evidence_refs": ["EVIDENCE-001"],
}

# Flow:
# 1. Governance: REQUIRES_APPROVAL (HIGH risk)
#    → Prompts human (or auto-approve in non-interactive)
# 2. PM: APPROVED (has evidence)
# 3. CMO: SKIPPED (not GTM)
# → Proceeds after approval
```

### ⏭️ Internal Refactor (Minimal Gates)

```python
task = {
    "type": "refactor",
    "affects_user_experience": False,
    "touches_phi_code": False,
}

# Flow:
# 1. Governance: APPROVED (LOW risk)
# 2. PM: SKIPPED (not feature, no user impact)
# 3. CMO: SKIPPED (not GTM)
# → Immediate execution (fastest path)
```

---

## 🔍 Decision Outcomes

### Governance

| Decision | Risk Level | Action |
|----------|------------|--------|
| `APPROVED` | LOW | Continue |
| `REQUIRES_APPROVAL` | HIGH/CRITICAL | Prompt human |
| `BLOCKED` | CRITICAL | Stop immediately |

### PM

| Decision | Reason | Action |
|----------|--------|--------|
| `APPROVED` | Has evidence + roadmap aligned | Continue |
| `BLOCKED` | Missing evidence | Stop, capture evidence |
| `MODIFIED` | Missing outcome metrics | Add metrics, continue |

### CMO

| Decision | Reason | Action |
|----------|--------|--------|
| `APPROVED` | Messaging aligned | Continue |
| `PROPOSE_ALTERNATIVE` | Better approach suggested | Warn, continue (doesn't block) |

---

## 📊 Efficiency Stats

| Scenario | Gates Run | Time Saved |
|----------|-----------|------------|
| Internal bugfix | 1 (Gov only) | ~2 seconds |
| User-facing bugfix | 2 (Gov + PM) | ~1 second |
| GTM feature | 3 (all) | 0 seconds |

**Impact**: 70% of tasks run 1 gate instead of 3 → 50-100 seconds saved per session

---

## 🛠️ Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| PM blocks all features | No evidence | `aibrain evidence capture` + link to task |
| Governance always needs approval | PHI flag set | Verify PHI involvement, remove flag if false positive |
| CMO never runs | Not GTM task | Set `is_gtm_related: True` if actually GTM |

---

## 📚 See Also

- **Full Guide**: `docs/guides/META-AGENT-INVOCATION-GUIDE.md`
- **ADR-011**: `AI-Team-Plans/decisions/ADR-011-meta-agent-coordination-architecture.md`
- **Completion Summary**: `AI-Team-Plans/V6.0-META-AGENT-COMPLETION-SUMMARY.md`
- **Test Examples**: `test_meta_agents.py`

---

**Version**: v6.0 | **Updated**: 2026-01-10
