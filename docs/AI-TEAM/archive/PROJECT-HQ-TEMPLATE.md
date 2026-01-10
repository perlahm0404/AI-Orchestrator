# PROJECT_HQ: [Project Name]

> **Single source of truth for project status. Auto-updated by AI Team.**

**Last Updated**: [YYYY-MM-DD HH:MM]
**Updated By**: [agent-name]

---

## Current Focus

> What's being actively worked on right now.

[Auto-populated by Coordinator when task starts]

---
## Blockers (Need You)

> Items requiring your attention. Empty = no blockers.

| Task | Blocker | Details | Since |
|------|---------|---------|-------|
| | | | |

[Auto-populated when BLOCKED verdict received]

---

## Status Dashboard

> All active and recent tasks.

| Task ID | Description | Status | Agent | Updated |
|---------|-------------|--------|-------|---------|
| | | | | |

**Legend**: ⏳ Pending | 🔄 In Progress | ✅ Completed | 🚫 Blocked

[Auto-populated by Coordinator]

---

## Recent Decisions

> Architecture Decision Records from Advisor dialogues.

| ADR | Title | Advisor | Date | Status |
|-----|-------|---------|------|--------|
| | | | | |

[Auto-populated when ADR approved]

---

## Roadmap

> High-level plan, updated as decisions are made.

### Current Phase: [Phase Name]

- [ ] [Feature/milestone 1]
- [ ] [Feature/milestone 2]
- [ ] [Feature/milestone 3]

### Upcoming

- [ ] [Future item 1]
- [ ] [Future item 2]

[Auto-updated by Advisors when decisions add to roadmap]

---

## Session History

> Recent session handoffs for context.

| Session | Date | Key Accomplishments | Handoff |
|---------|------|---------------------|---------|
| | | | [link] |

[Auto-populated by Coordinator on session end]

---

## Quick Stats

| Metric | Value |
|--------|-------|
| Tasks Completed (This Week) | 0 |
| Tasks In Progress | 0 |
| Tasks Blocked | 0 |
| Decisions Made | 0 |
| Sessions | 0 |

[Auto-calculated from data above]

---

## Notes

> Persistent notes that carry across sessions.

[Manual section - add important context here]

---

<!--
SYSTEM SECTION - DO NOT EDIT MANUALLY
This section is used by the Coordinator for state management.
-->

```yaml
_system:
  version: "1.0"
  project: "[project-name]"
  created: "[timestamp]"
  last_coordinator_update: "[timestamp]"
  active_tasks: []
  pending_tasks: []
  blocked_tasks: []
```
