# Deprecation Notice: Flat work/ Structure

**Status**: deprecated
**Date**: 2026-01-10
**Superseded by**: Priority-based numbered directories (ADR-010 Amendment)
**Sunset Date**: 2026-04-10 (90-day transition period)

---

## What's Deprecated

The original ADR-010 flat structure with `work/` directory:
- `work/plans-active/`
- `work/adrs-active/`
- `work/tickets-open/`
- `work/tasks-wip/`

---

## New Structure

**ADR-010 Amendment** implements priority-based numbering:
- `docs/11-plans/` (Weekly: Strategic plans, PRDs)
- `docs/12-decisions/` (Weekly: ADRs)
- `docs/13-tasks/` (Weekly: Task system, work queues)

---

## Why the Change

1. **User Preference Evolution**: During CredentialMate implementation, user explicitly preferred numbered directories
2. **Empirical Success**: CredentialMate achieved 42% directory reduction, 100% clarity
3. **Self-Documenting**: Numbers indicate priority/frequency (01-10 daily, 10-19 weekly, 20-29 monthly)
4. **Cognitive Load Reduction**: "Check 01-10 first, then 10-19" mental model

---

## Migration

All content from `work/` has been migrated to priority-based structure:
- Plans → `docs/11-plans/`
- ADRs → `docs/12-decisions/`
- Tasks → `docs/13-tasks/`

---

## Related

- ADR-010 Amendment: Priority-Based Numbering
- CredentialMate ADR-011: Documentation Organization (100% success)

---

**Sunset Date**: 2026-04-10 (old `work/` references will be removed)
