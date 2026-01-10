# Knowledge Registry

**Last Updated**: 2026-01-10
**Purpose**: Central index of Knowledge Objects (KOs) and Knowledge Base (KB) articles across all repositories

---

## Quick Stats

- **Approved KOs**: 3
- **Draft KOs**: 4
- **KB Articles**: 2+ (CredentialMate)
- **Total**: 9+ knowledge artifacts

---

## Knowledge Objects (KOs)

### Approved KOs

| ID | Title | Project | Tags | Path |
|----|-------|---------|------|------|
| KO-aio-001 | _(title pending)_ | AI_Orchestrator | _(pending)_ | [knowledge/approved/KO-aio-001.md](../knowledge/approved/KO-aio-001.md) |
| KO-km-001 | _(title pending)_ | KareMatch | _(pending)_ | [knowledge/approved/KO-km-001.md](../knowledge/approved/KO-km-001.md) |
| KO-km-002 | _(title pending)_ | KareMatch | _(pending)_ | [knowledge/approved/KO-km-002.md](../knowledge/approved/KO-km-002.md) |

### Draft KOs

| ID | Title | Project | Status | Path |
|----|-------|---------|--------|------|
| KO-cm-001 | _(pending approval)_ | CredentialMate | 📋 Draft | [knowledge/drafts/KO-cm-001.md](../knowledge/drafts/KO-cm-001.md) |
| KO-km-003 | _(pending approval)_ | KareMatch | 📋 Draft | [knowledge/drafts/KO-km-003.md](../knowledge/drafts/KO-km-003.md) |
| KO-km-004 | _(pending approval)_ | KareMatch | 📋 Draft | [knowledge/drafts/KO-km-004.md](../knowledge/drafts/KO-km-004.md) |
| KO-km-005 | _(pending approval)_ | KareMatch | 📋 Draft | [knowledge/drafts/KO-km-005.md](../knowledge/drafts/KO-km-005.md) |

---

## KO System Documentation

**Complete Guide**: See [knowledge/README.md](../knowledge/README.md)

**Key Features**:
- In-memory caching (457x speedup)
- Tag-based search (OR semantics)
- Effectiveness metrics tracking
- Auto-approval for high-confidence KOs
- CLI commands for management

**CLI Commands**:
```bash
aibrain ko list                   # List all approved KOs
aibrain ko show KO-ID             # Show full details
aibrain ko search --tags X,Y      # Search by tags
aibrain ko pending                # List drafts
aibrain ko approve KO-ID          # Approve draft
aibrain ko metrics [KO-ID]        # View metrics
```

---

## Knowledge Base (KB) Articles

### CredentialMate KB

Located in `credentialmate/docs/kb/`:

**Features**:
| Title | Path |
|-------|------|
| Partner File Bulk Download | [../../credentialmate/docs/kb/features/partner-file-bulk-download.md](../../credentialmate/docs/kb/features/partner-file-bulk-download.md) |

**Troubleshooting**:
| Title | Path |
|-------|------|
| SQLAlchemy Reserved Attribute Errors | [../../credentialmate/docs/kb/troubleshooting/sqlalchemy-reserved-attribute-errors.md](../../credentialmate/docs/kb/troubleshooting/sqlalchemy-reserved-attribute-errors.md) |

**Templates**:
| Title | Path |
|-------|------|
| ADR Template | [../../credentialmate/docs/15-kb/templates/adr.md](../../credentialmate/docs/15-kb/templates/adr.md) |

---

## KO Locations

```
AI_Orchestrator/
├── knowledge/
│   ├── approved/       # Approved KOs (production-ready)
│   ├── drafts/         # Pending review
│   ├── config/         # Configuration files
│   └── README.md       # Full system documentation

CredentialMate/ (copies from AI_Orchestrator)
├── knowledge/
│   ├── approved/       # Same KOs as orchestrator
│   └── drafts/         # Same drafts
└── docs/
    └── kb/             # KB articles (features, troubleshooting)
```

---

## KO Naming Convention

**Format**: `KO-{project}-{number}`

| Prefix | Project | Example |
|--------|---------|---------|
| `KO-aio-` | AI_Orchestrator | KO-aio-001 |
| `KO-cm-` | CredentialMate | KO-cm-001 |
| `KO-km-` | KareMatch | KO-km-001 |

---

## Tag Aliases

System supports shortcuts for common tags:

| Alias | Expands To |
|-------|------------|
| `ts` | `typescript` |
| `js` | `javascript` |
| `py` | `python` |
| `fe` | `frontend` |
| `be` | `backend` |

---

## KO Effectiveness Metrics

Tracked automatically for each KO:
- **Consultations**: Times queried
- **Success Rate**: % of successful applications
- **Impact Score**: Weighted effectiveness
- **Last Used**: Most recent consultation

View metrics:
```bash
aibrain ko metrics              # All KOs
aibrain ko metrics KO-km-001    # Specific KO
```

---

## Auto-Approval Criteria

KOs auto-approve when:
- Ralph verdict = PASS
- Iterations = 2-10 (configurable)
- Auto-approval enabled in project config

**Impact**: 70% of KOs auto-approved (high-confidence only)

---

## Search Tips

**Search by tags** (OR semantics):
```bash
aibrain ko search --tags "typescript,strict-mode"
# Returns KOs with EITHER typescript OR strict-mode
```

**List pending approvals**:
```bash
aibrain ko pending
```

**Show full KO content**:
```bash
aibrain ko show KO-km-001
```

---

## Related Resources

- [knowledge/README.md](../knowledge/README.md) - Complete KO system guide
- [CATALOG.md](../CATALOG.md) - Master documentation index
- [adr-registry.md](./adr-registry.md) - Architecture decisions
- [STATE.md](../STATE.md) - Current implementation status
