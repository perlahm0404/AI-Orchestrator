---
session:
  id: "{YYYYMMDD-HHMM}"
  topic: "{topic-kebab-case}"
  type: research | implementation | debugging | deployment | planning
  status: active | paused | complete | blocked
  repo: ai-orchestrator | karematch | credentialmate | mission-control | cross-repo

initiated:
  timestamp: "{ISO-8601}"
  context: "{What triggered this session}"

governance:
  autonomy_level: L1 | L2 | L3
  human_interventions: 0
  escalations: []
---

# Session: {Topic}

## Objective
<!-- What question are we answering? What are we trying to accomplish? -->


## Progress Log

### Phase 1: {Title}
**Status**: complete | in_progress | blocked
- {What was done}
- {What was found}

### Phase 2: {Title}
**Status**: pending
- {Planned work}


## Findings
<!-- Key discoveries, organized by importance -->


## Files Changed

| File | Change | Lines |
|------|--------|-------|
| path/to/file | description | +10/-5 |


## Issues Encountered
<!-- Problems that required troubleshooting -->


## Session Reflection (End of Session)

### What Worked Well
- {Positive patterns}

### What Could Be Improved
- {Process improvements}

### Agent Issues
- {Any agent failures, hallucinations, or unexpected behavior}

### Governance Notes
- {Policy gaps, rule improvements needed}

### Issues Log (Out of Scope)

| Issue | Priority | Notes |
|-------|----------|-------|
| {Issue description} | P1/P2/P3 | {Context for future session} |


## Next Steps
1. {Action item}
2. {Action item}
