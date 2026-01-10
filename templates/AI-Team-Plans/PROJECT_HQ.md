# PROJECT_HQ: {{PROJECT_NAME}}

> **Single source of truth for project status. Auto-updated by Coordinator.**

**Last Updated**: {{TIMESTAMP}}
**Updated By**: {{AGENT_NAME}}

---

## Current Focus

> What's being actively worked on right now.

{{CURRENT_FOCUS}}

---

## Blockers (Need You)

> Items requiring your attention. Empty = no blockers.

| Task | Blocker | Details | Since |
|------|---------|---------|-------|
{{BLOCKERS}}

---

## Status Dashboard

> All active and recent tasks.

| Task ID | Description | Status | Agent | Updated |
|---------|-------------|--------|-------|---------|
{{TASKS}}

**Legend**: ⏳ Pending | 🔄 In Progress | ✅ Completed | 🚫 Blocked

---

## Recent Decisions

> Architecture Decision Records from Advisor dialogues.

| ADR | Title | Advisor | Date | Status |
|-----|-------|---------|------|--------|
{{DECISIONS}}

---

## Roadmap

> High-level plan, updated as decisions are made.

### Current Phase: {{CURRENT_PHASE}}

{{ROADMAP_ITEMS}}

### Upcoming

{{UPCOMING_ITEMS}}

---

## Session History

> Recent session handoffs for context.

| Session | Date | Key Accomplishments | Handoff |
|---------|------|---------------------|---------|
{{SESSIONS}}

---

## Quick Stats

| Metric | Value |
|--------|-------|
| Tasks Completed (This Week) | {{TASKS_COMPLETED}} |
| Tasks In Progress | {{TASKS_IN_PROGRESS}} |
| Tasks Blocked | {{TASKS_BLOCKED}} |
| Decisions Made | {{DECISIONS_MADE}} |
| Sessions | {{SESSION_COUNT}} |

---

## Notes

> Persistent notes that carry across sessions.

{{NOTES}}

---

<!--
SYSTEM SECTION - DO NOT EDIT MANUALLY
This section is used by the Coordinator for state management.
-->

```yaml
_system:
  version: "3.0"
  project: "{{PROJECT_ID}}"
  created: "{{CREATED_TIMESTAMP}}"
  last_coordinator_update: "{{LAST_UPDATE}}"
  current_phase: {{PHASE_NUMBER}}
  active_tasks: []
  pending_tasks: []
  blocked_tasks: []
```
