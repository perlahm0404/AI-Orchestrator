# Archive Directory

This directory contains code that has been removed from active use but preserved for reference and potential future restoration.

## Why Archive Instead of Delete?

Files are archived (not deleted) when they have **uncertain value**:
- Interesting concepts that may be useful later
- Code with significant implementation effort (>100 LOC)
- Experimental features not currently in use
- Components that may be needed for specific use cases

Files with **zero value** (stubs, NotImplementedError, duplicates) are deleted entirely.

---

## Archived Files

### Orchestration Components

**File**: `orchestration/monitor.py` (210 LOC)
**Archived**: 2026-01-10
**Reason**: Terminal dashboard for parallel agent execution
**Status**: Never used in production (no imports found)
**Potential Future Use**: Debugging multi-agent workflows

**File**: `orchestration/parallel_agents.py` (228 LOC)
**Archived**: 2026-01-10
**Reason**: Parallel agent orchestration via Claude Code Task tool
**Status**: Never integrated into autonomous_loop.py
**Potential Future Use**: Future parallel execution optimization

---

### Deployment Agents

**File**: `agents/deployment/rollback_agent.py` (244 LOC)
**Archived**: 2026-01-10
**Reason**: Placeholder rollback logic (not production-ready)
**Status**: Stub implementation, no real deployment integration
**Potential Future Use**: If deployment autonomy becomes priority
**Note**: migration_agent.py kept (has real validation logic)

---

### Governance Contracts

**File**: `governance/contracts/infra-team.yaml` (299 LOC)
**Archived**: 2026-01-10
**Reason**: Contract for infrastructure team (no agents implemented)
**Status**: deployment_agent.py, migration_agent.py, rollback_agent.py are stubs
**Potential Future Use**: When deployment agents are implemented

**File**: `governance/contracts/operator-team.yaml` (417 LOC)
**Archived**: 2026-01-10
**Reason**: Contract for operator team (deployment/migration/rollback)
**Status**: Related agents not implemented
**Potential Future Use**: Production deployment autonomy
**Note**: Contains detailed SQL/S3 safety rules (may inform future work)

---

## How to Restore Archived Files

If you need to restore an archived file:

```bash
# 1. Copy from archive to original location
cp archive/path/to/file.py original/path/to/file.py

# 2. Check for dependencies (imports, contracts, tests)
grep -r "filename" .

# 3. Run tests to ensure integration works
pytest tests/

# 4. Update documentation (DECISIONS.md, STATE.md)
```

---

## Deletion Criteria

Files are **permanently deleted** (not archived) when:
1. All functions raise `NotImplementedError` (pure stubs)
2. Duplicate of existing file
3. No implementation beyond boilerplate
4. Zero educational or reference value

**Examples**:
- `orchestration/checkpoint.py` - DELETED (NotImplementedError stub)
- `orchestration/session.py` - DELETED (NotImplementedError stub)
- Duplicate contract files - DELETED (keep -simple variants only)

---

## Archive Maintenance

**Review Quarterly**: Check if archived files should be:
- **Restored** (now needed for active features)
- **Permanently Deleted** (confirmed no future value)
- **Kept** (still potential future use)

**Last Review**: 2026-01-10 (Phase 1 cleanup)
**Next Review**: 2026-04-10 (Q2 2026)
