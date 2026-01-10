# Implementation Plan: AI Team

**Date**: 2026-01-09
**Status**: Design Phase

---

## Overview

Build the AI Team in phases, validating each before proceeding.

---

## Phase Summary

| Phase | Focus | Duration | Deliverables |
|-------|-------|----------|--------------|
| 1 | Foundation | Week 1-2 | Unified governance, PROJECT_HQ template |
| 2 | Coordinator | Week 3-4 | Coordinator agent, auto-tracking |
| 3 | Advisors | Week 5-7 | Data/App/UI Advisors, ADR automation |
| 4 | Integration | Week 8-9 | Cross-agent workflows, testing |
| 5 | Sync | Week 10-11 | Deploy to CredentialMate, KareMatch |
| 6 | Polish | Week 12 | Documentation, refinement |

---

## Phase 1: Foundation

### Goal
Establish unified governance and single tracking document.

### Tasks

```
1.1 Create governance/unified/ structure
    - governance.yaml (master config)
    - golden-paths.yaml (protected files)
    - guardrails.yaml (safety rules)

1.2 Migrate existing contracts
    - Update qa-team.yaml
    - Update dev-team.yaml
    - Create advisor.yaml (placeholder)
    - Create coordinator.yaml (placeholder)

1.3 Create PROJECT_HQ template
    - Define all sections
    - Create update utilities
    - Test manual updates

1.4 Create decisions/ folder structure
    - ADR template
    - Numbering scheme
    - Index file
```

### Validation

- [ ] Existing agents still work with new governance
- [ ] PROJECT_HQ.md renders correctly
- [ ] Golden paths block protected files
- [ ] Guardrails catch forbidden patterns

### Dependencies
None (starting point)

---

## Phase 2: Coordinator Agent

### Goal
Build the orchestration layer that auto-manages tasks and status.

### Tasks

```
2.1 Create BaseCoordinator class
    - agents/base/base_coordinator.py
    - Task breakdown logic
    - Dependency resolution
    - Queue management

2.2 Implement auto-behaviors
    - on_adr_approved()
    - on_task_complete()
    - on_session_end()
    - on_blocked()

2.3 PROJECT_HQ auto-updates
    - Atomic update function
    - Section-specific updaters
    - Timestamp management

2.4 Work queue management
    - tasks/work_queue.json schema
    - CRUD operations
    - Priority handling

2.5 Session handoff generation
    - Template renderer
    - Auto-trigger on session end
    - Link to PROJECT_HQ

2.6 Integration with existing Builders
    - Builder notification
    - Result handling
    - BLOCKED escalation
```

### Validation

- [ ] Coordinator breaks ADR into tasks correctly
- [ ] Tasks assigned to correct Builder type
- [ ] PROJECT_HQ updates automatically
- [ ] Handoffs generated on session end
- [ ] BLOCKED verdicts surface in PROJECT_HQ

### Dependencies
- Phase 1 complete (governance, PROJECT_HQ)

---

## Phase 3: Advisor Agents

### Goal
Build dialogue-mode agents for strategic decisions.

### Tasks

```
3.1 Create BaseAdvisor class
    - agents/base/base_advisor.py
    - Options generation
    - Tradeoff analysis
    - Decision waiting
    - ADR creation

3.2 Implement Data Advisor
    - agents/data_advisor.py
    - Schema analysis
    - Migration strategy
    - Data quality rules
    - Domain knowledge sources

3.3 Implement App Advisor
    - agents/app_advisor.py
    - Architecture analysis
    - API design
    - Tech stack knowledge
    - Integration patterns

3.4 Implement UI/UX Advisor
    - agents/uiux_advisor.py
    - Component analysis
    - Flow design
    - Accessibility checks
    - Data display patterns

3.5 ADR automation
    - Template rendering
    - Auto-numbering
    - Status management
    - Linking to PROJECT_HQ

3.6 Advisor coordination
    - Multi-advisor workflows
    - Handoff between advisors
    - Dependency ordering
```

### Validation

- [ ] Each Advisor presents 2+ options
- [ ] Tradeoffs explained in plain language
- [ ] Advisors wait for decision (don't auto-implement)
- [ ] ADRs created automatically after decision
- [ ] PROJECT_HQ roadmap updated
- [ ] Handoff to Coordinator triggers correctly

### Dependencies
- Phase 2 complete (Coordinator for handoff)

---

## Phase 4: Integration

### Goal
Full end-to-end workflow validation.

### Tasks

```
4.1 End-to-end workflow testing
    - User request → Advisor dialogue
    - Decision → ADR created
    - ADR → Coordinator breakdown
    - Tasks → Builder execution
    - Completion → Status updates

4.2 Multi-advisor scenarios
    - Feature touching data + API + UI
    - Sequential advisor handoffs
    - Linked ADRs

4.3 Error handling
    - Advisor timeout
    - Coordinator failures
    - Builder BLOCKED
    - Session interruption

4.4 Recovery scenarios
    - Resume after crash
    - Resume after BLOCKED
    - Queue corruption recovery

4.5 Performance testing
    - Large task queues
    - Many ADRs
    - Long sessions
```

### Validation

- [ ] Full workflow completes without manual intervention
- [ ] Multi-advisor features work correctly
- [ ] Errors handled gracefully
- [ ] Recovery works from any state
- [ ] Performance acceptable

### Dependencies
- Phase 3 complete (all agents)

---

## Phase 5: Project Sync

### Goal
Deploy to CredentialMate and KareMatch.

### Tasks

```
5.1 Update sync-manifest.yaml
    - Add new agents to SYNCABLE
    - Add governance/unified/ to SYNCABLE
    - Keep extensions in PROTECTED

5.2 CredentialMate deployment
    - Sync new agents
    - Create HIPAA extensions
    - Create HIPAADataAdvisor
    - Test with HIPAA guardrails

5.3 KareMatch deployment
    - Migrate from skills to agents
    - Keep domain skills as utilities
    - Create healthcare extensions
    - Test with golden paths

5.4 Project-specific PROJECT_HQ
    - credentialmate/PROJECT_HQ.md
    - karematch/PROJECT_HQ.md
    - Project-specific sections

5.5 Cross-project validation
    - Same workflow in all repos
    - Extensions work correctly
    - No governance conflicts
```

### Validation

- [ ] Agents work in CredentialMate
- [ ] HIPAA guardrails enforced
- [ ] Agents work in KareMatch
- [ ] Healthcare rules enforced
- [ ] Sync mechanism still works

### Dependencies
- Phase 4 complete (validated in AI_Orchestrator)

---

## Phase 6: Polish

### Goal
Documentation, refinement, edge cases.

### Tasks

```
6.1 Documentation
    - User guide for non-coders
    - Agent reference
    - Governance reference
    - Troubleshooting guide

6.2 Edge case handling
    - Conflicting advisor recommendations
    - Circular task dependencies
    - Long-running tasks
    - Session timeout

6.3 Metrics and monitoring
    - Task completion rates
    - Advisor decision time
    - BLOCKED frequency
    - Auto-update reliability

6.4 User experience refinement
    - Advisor dialogue flow
    - Status readability
    - Blocker clarity
    - Handoff usefulness
```

### Validation

- [ ] Documentation covers all scenarios
- [ ] Edge cases handled
- [ ] Metrics collecting
- [ ] User feedback positive

### Dependencies
- Phase 5 complete

---

## Build Order (Detailed)

### Week 1-2: Foundation

```
Day 1-2:
  - Create governance/unified/ folder
  - Write governance.yaml
  - Write golden-paths.yaml

Day 3-4:
  - Write guardrails.yaml
  - Migrate existing contracts
  - Test with existing agents

Day 5-7:
  - Create PROJECT_HQ template
  - Create decisions/ structure
  - Create ADR template

Day 8-10:
  - Integration testing
  - Fix issues
  - Document Phase 1
```

### Week 3-4: Coordinator

```
Day 1-3:
  - BaseCoordinator class
  - Task breakdown logic
  - Dependency resolution

Day 4-6:
  - Auto-behaviors implementation
  - PROJECT_HQ updaters
  - Work queue management

Day 7-10:
  - Session handoff generation
  - Builder integration
  - Testing and fixes
```

### Week 5-7: Advisors

```
Week 5:
  - BaseAdvisor class
  - ADR automation
  - Data Advisor

Week 6:
  - App Advisor
  - UI/UX Advisor

Week 7:
  - Advisor coordination
  - Multi-advisor workflows
  - Testing and fixes
```

### Week 8-9: Integration

```
Week 8:
  - End-to-end testing
  - Error handling
  - Recovery scenarios

Week 9:
  - Performance testing
  - Bug fixes
  - Documentation draft
```

### Week 10-11: Sync

```
Week 10:
  - CredentialMate deployment
  - HIPAA extensions

Week 11:
  - KareMatch deployment
  - Healthcare extensions
```

### Week 12: Polish

```
  - Final documentation
  - Edge cases
  - Metrics
  - User feedback
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Advisors too verbose | Strict plain-language guidelines, character limits |
| Coordinator misassigns | Task type detection tests, fallback to human |
| Governance conflicts | Priority rules, extensive testing |
| Sync breaks projects | Dry-run first, rollback mechanism |
| User confusion | Progressive rollout, documentation |

---

## Success Criteria

### Phase 1 Complete When:
- Governance unified
- PROJECT_HQ template working
- Existing agents unaffected

### Phase 2 Complete When:
- Coordinator auto-creates tasks from ADRs
- PROJECT_HQ updates automatically
- Handoffs generated automatically

### Phase 3 Complete When:
- All 3 Advisors present options
- ADRs created automatically
- Handoff to Coordinator works

### Phase 4 Complete When:
- Full workflow runs without manual prompts
- Errors handled gracefully
- Recovery works

### Phase 5 Complete When:
- Works in all 3 repos
- Extensions enforce correctly
- No governance conflicts

### Phase 6 Complete When:
- Documentation complete
- Metrics collecting
- User satisfied
