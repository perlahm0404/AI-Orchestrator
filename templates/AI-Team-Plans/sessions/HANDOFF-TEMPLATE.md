# Session Handoff: {{DATE}}-{{SEQUENCE}}

**Project**: {{PROJECT_NAME}}
**Created**: {{TIMESTAMP}}
**Created By**: Coordinator

---

## Session Summary

| Metric | Value |
|--------|-------|
| Duration | {{DURATION}} |
| Tasks Completed | {{TASKS_COMPLETED}} |
| Tasks In Progress | {{TASKS_IN_PROGRESS}} |
| Tasks Blocked | {{TASKS_BLOCKED}} |
| Iterations Total | {{ITERATIONS_TOTAL}} |
| Human Interventions | {{HUMAN_INTERVENTIONS}} |

---

## Completed This Session

| Task | Description | Agent | Iterations |
|------|-------------|-------|------------|
{{COMPLETED_TASKS}}

---

## Still In Progress

| Task | Status | Progress | Notes |
|------|--------|----------|-------|
{{IN_PROGRESS_TASKS}}

---

## Blocked (Need Human)

| Task | Blocker | Details | Since |
|------|---------|---------|-------|
{{BLOCKED_TASKS}}

---

## Next Session Should

1. {{PRIORITY_1}}
2. {{PRIORITY_2}}
3. {{PRIORITY_3}}

---

## Files Changed

| File | Changes | Agent |
|------|---------|-------|
{{FILES_CHANGED}}

---

## ADRs Referenced

{{ADRS_REFERENCED}}

---

## Events Logged

- Detailed: {{EVENTS_DETAILED}}
- Counted: {{EVENTS_COUNTED}}

---

## Notes

> Any context for next session.

{{NOTES}}

---

<!--
SYSTEM SECTION - DO NOT EDIT
Used for session continuity
-->

```yaml
_system:
  version: "3.0"
  session_id: "{{SESSION_ID}}"
  previous_session: "{{PREVIOUS_SESSION}}"
  work_queue_snapshot: "{{QUEUE_HASH}}"
  project_hq_snapshot: "{{HQ_HASH}}"
  resumable: true
```
