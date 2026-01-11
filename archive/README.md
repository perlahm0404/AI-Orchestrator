# Archive Directory

This directory contains completed, superseded, and historical documentation.

## Organization

- **2026-01/** - January 2026 archived work
  - `sessions-completed/` - Completed session prompts (NEXT-SESSION-*, VERIFICATION-*, etc.)
  - `phase-guides-completed/` - Finished phase guides
  - `comparisons-historical/` - Historical comparisons (RALPH, TDD vs non-TDD)
  - `proposals-implemented/` - Implemented proposals (guardrails, governance)
  - `superseded-docs/` - Documents replaced by newer versions
  - `work-queues-large-backups/` - Compressed backup files

## Retrieval

Archived files are preserved for reference but are not part of active workflows.

### Find Archived Content

```bash
# Search by keyword
find archive/ -name "*keyword*"

# Search content
grep -r "search term" archive/

# List all archived sessions
ls archive/2026-01/sessions-completed/

# List superseded documents
ls archive/2026-01/superseded-docs/
```

## Retention Policy

- **Session artifacts**: Keep indefinitely (audit trail)
- **Superseded docs**: Keep until confirmed obsolete
- **Large backups**: Compress with gzip, keep 90 days
- **Proposals/comparisons**: Keep indefinitely (historical reference)

## Archival Process

When archiving documents:

1. **Move to appropriate subdirectory** under current month (YYYY-MM)
2. **Add archival frontmatter** if not present:
   ```yaml
   ---
   status: archived
   archived-date: YYYY-MM-DD
   archived-reason: "Superseded by [new-doc-id]" or "Completed"
   superseded-by: "new-doc-id"  # if applicable
   safe-to-delete: false  # true if purely historical with no reference value
   ---
   ```
3. **Update references** in active documentation
4. **Update CATALOG.md** to reflect archived status

## SOC2/ISO Compliance

Archived documents retain their compliance metadata for audit purposes:
- **7-year retention** for documentation evidence (SOC2 requirement)
- **Classification preserved**: internal, confidential, public
- **Audit logs**: Session artifacts preserved indefinitely

## Monthly Archive Creation

At the start of each month, create a new directory:

```bash
mkdir -p archive/YYYY-MM/{sessions-completed,phase-guides-completed,comparisons-historical,proposals-implemented,superseded-docs,work-queues-large-backups}
```

## Related Documents

- **ADR-010**: Documentation Organization & Archival Strategy
- **CATALOG.md**: Master navigation (includes archive references)
- **work/README.md**: Active work directory (contrast with archive)
