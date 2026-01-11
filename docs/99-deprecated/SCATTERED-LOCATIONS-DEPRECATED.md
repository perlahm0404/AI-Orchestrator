# Deprecation Notice: Scattered Documentation Locations

**Status**: deprecated
**Date**: 2026-01-10
**Superseded by**: Priority-based consolidated structure (ADR-010 Amendment)
**Sunset Date**: 2026-04-10 (90-day transition period)

---

## What's Deprecated

Scattered documentation across multiple root-level directories:
- `governance/` → superseded by `docs/02-governance/`
- `knowledge/` → superseded by `docs/03-knowledge/`
- `AI-Team-Plans/decisions/` → superseded by `docs/12-decisions/`
- `tasks/` → superseded by `docs/13-tasks/`

---

## New Consolidated Structure

**Single Source of Truth**:
| Old Location | New Location | Priority |
|--------------|--------------|----------|
| `governance/contracts/` | `docs/02-governance/contracts/` | Daily (02) |
| `knowledge/approved/` | `docs/03-knowledge/approved/` | Daily (03) |
| `AI-Team-Plans/decisions/` | `docs/12-decisions/` | Weekly (12) |
| `tasks/queues-active/` | `docs/13-tasks/queues/` | Weekly (13) |

---

## Why the Change

1. **Zero Duplicates**: Governance in 4 locations → 1 location
2. **Visual Priority**: Numbers indicate usage frequency at a glance
3. **Agent Discoverability**: Reduced scan from 211 files to 19 organized directories
4. **Operational Alignment**: Structure matches actual usage patterns

---

## Migration Status

✅ All content migrated to priority-based structure
✅ Old directories preserved for 90-day transition
⚠️ Update any hardcoded paths in agent code

---

## Path Updates Required

**Code References**:
```python
# OLD
governance/contracts/qa-team.yaml
knowledge/approved/KO-001.md

# NEW
docs/02-governance/contracts/qa-team.yaml
docs/03-knowledge/approved/KO-001.md
```

**Documentation References**:
- CLAUDE.md: ✅ Updated
- CATALOG.md: ⚠️ Needs update
- Agent prompts: ⚠️ Check for hardcoded paths

---

## Related

- ADR-010 Amendment: Priority-Based Numbering
- CredentialMate ADR-011: Implementation reference (42% reduction)

---

**Sunset Date**: 2026-04-10 (old directories will be removed)
