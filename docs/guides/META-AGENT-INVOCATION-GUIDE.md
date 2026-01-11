# Meta-Agent Invocation Guide

**Version**: v6.0
**Date**: 2026-01-10
**Audience**: AI agents, humans working with AI Orchestrator

---

## Overview

This guide explains **when** and **how** to invoke each of the 3 meta-agents (Governance, PM, CMO) in the AI Orchestrator system.

---

## Quick Reference

| Agent | When to Invoke | Auto-Invoked By |
|-------|----------------|-----------------|
| **Governance** | ALWAYS (every task) | `autonomous_loop.py` |
| **PM** | Features + user-facing changes | `autonomous_loop.py` |
| **CMO** | GTM/marketing tasks | `autonomous_loop.py` |

---

## 1. Governance Agent

### When to Invoke

**ALWAYS** - Governance runs for every single task regardless of type.

### Triggers (Any of these = invoke)

- ✅ **Always** (no conditional check)
- Every task needs risk assessment before execution

### Purpose

- HIPAA compliance validation
- Risk assessment (LOW/MEDIUM/HIGH/CRITICAL)
- PHI detection (metadata flags + keywords)
- Human-in-the-loop gates for HIGH/CRITICAL risk
- Security/auth/billing/infrastructure checks

### How to Invoke

#### Method 1: Via Autonomous Loop (Automatic)

```python
# autonomous_loop.py automatically invokes Governance for ALL tasks
# No manual invocation needed - it's built into the loop
```

#### Method 2: Manual Invocation (Direct)

```python
from agents.coordinator.governance_agent import GovernanceAgent
from adapters.credentialmate import CredentialMateAdapter

# Create adapter and agent
adapter = CredentialMateAdapter()
governance_agent = GovernanceAgent(adapter)

# Prepare task data
task_data = {
    "type": "bugfix",  # or "feature", "refactor", etc.
    "files": ["src/auth/session.py"],
    "affects_user_experience": True,
    "touches_phi_code": True,  # IMPORTANT: explicit PHI flag
}

# Execute governance assessment
result = governance_agent.execute(
    task_id="BUG-CME-002",
    task_description="Fix CME hour calculation for ANCC certification",
    task_data=task_data
)

# Check decision
if result.decision == "BLOCKED":
    print(f"❌ Task blocked: {result.risk_assessment.reason}")
elif result.decision == "REQUIRES_APPROVAL":
    print(f"⚠️  Human approval needed (risk: {result.risk_assessment.risk_level})")
    # Prompt human or auto-approve in non-interactive mode
elif result.decision == "APPROVED":
    print(f"✅ Approved (risk: {result.risk_assessment.risk_level})")
```

### Decision Outcomes

| Decision | Meaning | Action |
|----------|---------|--------|
| `APPROVED` | Low risk, safe to proceed | Continue execution |
| `REQUIRES_APPROVAL` | HIGH/CRITICAL risk | Prompt human (or auto-approve in non-interactive) |
| `BLOCKED` | PHI detected in description | Stop immediately |

### Risk Levels

| Level | Triggers | Examples |
|-------|----------|----------|
| **LOW** | No high-risk indicators | Refactors, UI changes, non-sensitive code |
| **MEDIUM** | State expansion | Adding multi-state support (compliance review) |
| **HIGH** | PHI, auth, billing | PHI code, auth changes, payment processing |
| **CRITICAL** | Production infra, PHI in description | Production deploys, PHI leak detected |

---

## 2. Product Manager Agent

### When to Invoke

**CONDITIONAL** - Only when task meets ANY of these criteria:

### Triggers (Any of these = invoke)

```python
should_pm_validate = (
    task.type == "feature" OR
    task.affects_user_experience == True
)
```

- ✅ Task type is `"feature"`
- ✅ Task has `affects_user_experience: True` flag

### Purpose

- Evidence-driven feature validation
- Roadmap alignment checks
- Outcome metrics enforcement
- Block features without user evidence

### How to Invoke

#### Method 1: Via Autonomous Loop (Automatic)

```python
# autonomous_loop.py automatically checks conditions and invokes PM
# Lines 520-565 in autonomous_loop.py
```

#### Method 2: Manual Invocation (Direct)

```python
from agents.coordinator.product_manager import ProductManagerAgent
from adapters.credentialmate import CredentialMateAdapter

# Create adapter and agent
adapter = CredentialMateAdapter()
pm_agent = ProductManagerAgent(adapter)

# Prepare task data
task_data = {
    "type": "feature",  # or "bugfix" with affects_user_experience=True
    "files": ["src/onboarding/flow.py"],
    "affects_user_experience": True,
    "touches_phi_code": False,
}

# Execute PM validation
result = pm_agent.execute(
    task_id="FEAT-ONBOARD-001",
    task_description="Add user onboarding flow for NPs",
    task_data=task_data
)

# Check decision
if result.decision == "BLOCKED":
    print(f"❌ Task blocked: {result.reason}")
    print(f"Evidence count: {result.evidence_count}")
    print("Recommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")
elif result.decision == "MODIFIED":
    print(f"📝 Task modified: {result.reason}")
    # Check if outcome metrics were added
    if result.outcome_metrics_template:
        print("Added outcome metrics template")
elif result.decision == "APPROVED":
    print(f"✅ Approved: {result.reason}")
```

### Decision Outcomes

| Decision | Meaning | Action |
|----------|---------|--------|
| `APPROVED` | Has evidence + roadmap aligned | Continue execution |
| `BLOCKED` | Missing evidence | Stop, capture evidence first |
| `MODIFIED` | Missing outcome metrics | Inject metrics template, continue |

### When PM Skips (Auto-Approves)

PM automatically approves and skips for:
- Bugfixes (unless `affects_user_experience=True`)
- Refactors
- Tests
- Code quality improvements

**Example**:
```python
# This task skips PM validation
task = {
    "type": "bugfix",
    "affects_user_experience": False,  # No user impact
    "description": "Fix typo in internal logger"
}
# PM: ⏭️ SKIPPED
```

---

## 3. CMO Agent

### When to Invoke

**CONDITIONAL** - Only when task is GTM-related:

### Triggers (Any of these = invoke)

```python
should_cmo_review = (
    task.is_gtm_related == True
)
```

- ✅ Task has `is_gtm_related: True` flag

**Keywords that trigger GTM flag** (auto-detected):
- landing page, messaging, positioning, onboarding, activation
- conversion, demo, pilot, marketing, email, webinar
- case study, roi calculator, trust, proof, testimonial

### Purpose

- GTM task validation
- Fake-door test ethics ("coming soon" messaging)
- Messaging alignment checks
- Demand evidence validation

### How to Invoke

#### Method 1: Via Autonomous Loop (Automatic)

```python
# autonomous_loop.py automatically checks is_gtm_related and invokes CMO
# Lines 567-591 in autonomous_loop.py
```

#### Method 2: Manual Invocation (Direct)

```python
from agents.coordinator.cmo_agent import CMOAgent
from adapters.credentialmate import CredentialMateAdapter

# Create adapter and agent
adapter = CredentialMateAdapter()
cmo_agent = CMOAgent(adapter)

# Prepare task data
task_data = {
    "type": "feature",
    "files": ["src/landing/waitlist.tsx"],
    "affects_user_experience": True,
    "touches_phi_code": False,
    "is_gtm_related": True,  # IMPORTANT: GTM flag
}

# Execute CMO review
result = cmo_agent.execute(
    task_id="FEAT-LANDING-003",
    task_description="Create waitlist landing page for multi-state support",
    task_data=task_data
)

# Check decision
if result.decision == "PROPOSE_ALTERNATIVE":
    print(f"⚠️  CMO proposes alternative: {result.proposed_alternative}")
    print(f"Reason: {result.reason}")
    print("Recommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")
elif result.decision == "APPROVED":
    print(f"✅ Approved: {result.reason}")
```

### Decision Outcomes

| Decision | Meaning | Action |
|----------|---------|--------|
| `APPROVED` | Messaging aligned, honest | Continue execution |
| `PROPOSE_ALTERNATIVE` | Suggest better approach | Warn user, continue (doesn't block) |

### When CMO Skips (Auto-Approves)

CMO automatically approves and skips for:
- Non-GTM tasks (product/engineering work)
- Backend code changes
- Database migrations
- Test fixes

**Example**:
```python
# This task skips CMO validation
task = {
    "type": "feature",
    "is_gtm_related": False,  # Not GTM
    "description": "Add database index for faster queries"
}
# CMO: ⏭️ SKIPPED (auto-approved: not GTM-related)
```

---

## Complete Invocation Flow

### Autonomous Loop Integration (Lines 490-601 in autonomous_loop.py)

```python
# Build task_data for meta-agents
task_data = {
    "type": task.type if hasattr(task, 'type') else "bugfix",
    "files": [task.file],
    "affects_user_experience": task.affects_user_experience if hasattr(task, 'affects_user_experience') else False,
    "touches_phi_code": task.touches_phi_code if hasattr(task, 'touches_phi_code') else False,
}

# ========================================
# GATE 1: Governance (ALWAYS runs)
# ========================================
from agents.coordinator.governance_agent import GovernanceAgent
governance_agent = GovernanceAgent(adapter)
governance_result = governance_agent.execute(task.id, task.description, task_data)

# Save governance results
task.governance_risk_level = governance_result.risk_assessment.risk_level
task.governance_approved = (governance_result.decision == "APPROVED")

# Check governance decision
if governance_result.decision == "BLOCKED":
    queue.mark_blocked(task.id, f"Governance: {governance_result.risk_assessment.reason}")
    queue.save(queue_path)
    continue
elif governance_result.decision == "REQUIRES_APPROVAL":
    if not app_context.non_interactive:
        # Prompt human for approval
        approval = input(f"Task {task.id} requires approval (risk: {governance_result.risk_assessment.risk_level}). Approve? [y/N]: ")
        if approval.lower() != 'y':
            queue.mark_blocked(task.id, "Human rejected approval")
            queue.save(queue_path)
            continue
    else:
        # Auto-approve in non-interactive mode (with logging)
        logger.warning(f"⚠️  Task {task.id} auto-approved (non-interactive mode, risk: {governance_result.risk_assessment.risk_level})")

# ========================================
# GATE 2: PM (CONDITIONAL - features + user-facing)
# ========================================
should_pm_validate = (
    (hasattr(task, 'type') and task.type == "feature") or
    (hasattr(task, 'affects_user_experience') and task.affects_user_experience)
)

if should_pm_validate:
    from agents.coordinator.product_manager import ProductManagerAgent
    pm_agent = ProductManagerAgent(adapter)
    pm_result = pm_agent.execute(task.id, task.description, task_data)

    # Save PM results
    task.pm_validated = (pm_result.decision == "APPROVED")
    task.pm_feedback = pm_result.reason

    # Check PM decision
    if pm_result.decision == "BLOCKED":
        queue.mark_blocked(task.id, f"PM: {pm_result.reason}")
        queue.save(queue_path)
        continue
    elif pm_result.decision == "MODIFIED":
        # PM added outcome metrics - update task
        task.pm_outcome_metrics = pm_result.outcome_metrics_template
        logger.info(f"📝 PM modified task {task.id}: {pm_result.reason}")

# ========================================
# GATE 3: CMO (CONDITIONAL - GTM tasks only)
# ========================================
should_cmo_review = (hasattr(task, 'is_gtm_related') and task.is_gtm_related)

if should_cmo_review:
    from agents.coordinator.cmo_agent import CMOAgent
    cmo_agent = CMOAgent(adapter)
    cmo_result = cmo_agent.execute(task.id, task.description, task_data)

    # Save CMO results
    task.cmo_reviewed = True
    task.cmo_priority = cmo_result.user_value_score

    # Check CMO decision
    if cmo_result.decision == "PROPOSE_ALTERNATIVE":
        logger.warning(f"⚠️  CMO proposes alternative for {task.id}: {cmo_result.proposed_alternative}")
        # Note: CMO doesn't block, just warns

# ========================================
# All gates passed - proceed with execution
# ========================================
```

---

## Task Data Schema

When invoking meta-agents, provide this structure:

```python
task_data = {
    # Required
    "type": str,  # "feature" | "bugfix" | "refactor" | "test" | "codequality"
    "files": list[str],  # Files being modified

    # Triggers for PM
    "affects_user_experience": bool,  # Does this impact users?

    # Triggers for Governance
    "touches_phi_code": bool,  # Does this touch PHI-handling code?

    # Triggers for CMO (auto-detected from description, or explicit)
    "is_gtm_related": bool,  # Is this a GTM/marketing task?
}
```

---

## CLI Commands (Future)

**Not yet implemented** - Will be added in future versions:

```bash
# Manual governance check
aibrain governance assess TASK-ID

# Manual PM validation
aibrain pm validate TASK-ID

# Manual CMO review
aibrain cmo review TASK-ID
```

---

## Decision Matrix

| Task Type | Governance | PM | CMO | Typical Flow |
|-----------|------------|----|----|--------------|
| Feature (user-facing, GTM) | ✅ ALWAYS | ✅ YES | ✅ YES | Gov → PM → CMO → Execute |
| Feature (user-facing, non-GTM) | ✅ ALWAYS | ✅ YES | ❌ SKIP | Gov → PM → Execute |
| Feature (internal) | ✅ ALWAYS | ✅ YES | ❌ SKIP | Gov → PM → Execute |
| Bugfix (user-facing) | ✅ ALWAYS | ✅ YES | ❌ SKIP | Gov → PM → Execute |
| Bugfix (internal) | ✅ ALWAYS | ❌ SKIP | ❌ SKIP | Gov → Execute |
| Refactor | ✅ ALWAYS | ❌ SKIP | ❌ SKIP | Gov → Execute |
| Test | ✅ ALWAYS | ❌ SKIP | ❌ SKIP | Gov → Execute |
| Code Quality | ✅ ALWAYS | ❌ SKIP | ❌ SKIP | Gov → Execute |
| Landing Page | ✅ ALWAYS | ✅ YES | ✅ YES | Gov → PM → CMO → Execute |
| Migration | ✅ ALWAYS | ❌ SKIP | ❌ SKIP | Gov → Execute |

---

## Common Patterns

### Pattern 1: Feature with Evidence

```python
# Task setup
task = {
    "id": "FEAT-NP-001",
    "type": "feature",
    "description": "Add NP onboarding flow",
    "affects_user_experience": True,
    "is_gtm_related": True,
    "evidence_refs": ["EVIDENCE-001"],  # Link to evidence
}

# Expected flow:
# 1. Governance: APPROVED (LOW risk)
# 2. PM: APPROVED (has evidence + roadmap aligned)
# 3. CMO: APPROVED (messaging aligned)
# 4. Execute
```

### Pattern 2: Bugfix with PHI

```python
# Task setup
task = {
    "id": "BUG-CME-002",
    "type": "bugfix",
    "description": "Fix CME calculation",
    "affects_user_experience": True,
    "touches_phi_code": True,  # PHI flag
    "evidence_refs": ["EVIDENCE-001"],
}

# Expected flow:
# 1. Governance: REQUIRES_APPROVAL (HIGH risk - PHI)
#    → Prompt human or auto-approve
# 2. PM: APPROVED or MODIFIED (has evidence, may add metrics)
# 3. CMO: SKIPPED (not GTM)
# 4. Execute
```

### Pattern 3: Internal Refactor

```python
# Task setup
task = {
    "id": "REFACTOR-001",
    "type": "refactor",
    "description": "Extract helper function",
    "affects_user_experience": False,
    "touches_phi_code": False,
}

# Expected flow:
# 1. Governance: APPROVED (LOW risk)
# 2. PM: SKIPPED (not a feature, no user impact)
# 3. CMO: SKIPPED (not GTM)
# 4. Execute immediately (minimal overhead)
```

### Pattern 4: Landing Page (GTM)

```python
# Task setup
task = {
    "id": "FEAT-LANDING-003",
    "type": "feature",
    "description": "Create waitlist landing page for multi-state support",
    "affects_user_experience": True,
    "is_gtm_related": True,  # GTM flag
    "evidence_refs": [],  # No evidence yet
}

# Expected flow:
# 1. Governance: REQUIRES_APPROVAL (MEDIUM risk - state expansion)
#    → Prompt human or auto-approve
# 2. PM: BLOCKED (no evidence)
#    → Must capture evidence first
# 3. CMO: Not tested (PM blocked first)
# 4. BLOCKED - capture evidence before proceeding
```

---

## Troubleshooting

### "PM blocking all my features!"

**Cause**: Features lack evidence references

**Solution**:
```bash
# Capture user evidence
aibrain evidence capture

# Link to task
aibrain evidence link EVIDENCE-001 FEAT-NP-001

# Or add evidence_refs to task
task.evidence_refs = ["EVIDENCE-001"]
```

### "Governance always requires approval!"

**Cause**: Task has `touches_phi_code: True` or contains PHI keywords

**Solution**:
- If PHI is actually involved: Approval is correct (human-in-the-loop required)
- If false positive: Remove PHI keywords from description, set `touches_phi_code: False`

### "CMO isn't running!"

**Cause**: Task is not GTM-related

**Solution**:
- If task IS GTM: Set `is_gtm_related: True`
- If task is NOT GTM: This is correct behavior (CMO skips non-GTM tasks)

---

## Key Files

| File | Purpose |
|------|---------|
| `agents/coordinator/governance_agent.py` | Governance implementation |
| `agents/coordinator/product_manager.py` | PM implementation |
| `agents/coordinator/cmo_agent.py` | CMO implementation |
| `autonomous_loop.py` (lines 490-601) | Meta-agent integration |
| `tasks/work_queue.py` (lines 61-73) | Task dataclass with meta-agent fields |
| `test_meta_agents.py` | Test examples |

---

## Summary

**Governance**: ALWAYS runs (every task)
**PM**: CONDITIONAL (features + user-facing changes)
**CMO**: CONDITIONAL (GTM tasks only)

**Invocation**: Automatic via `autonomous_loop.py` OR manual via direct agent calls

**Key Principle**: Conditional gates = efficiency. Most tasks (70%+) run only 1 gate instead of 3.

---

**Version**: v6.0
**Last Updated**: 2026-01-10
**See Also**: ADR-011, V6.0-META-AGENT-COMPLETION-SUMMARY.md
