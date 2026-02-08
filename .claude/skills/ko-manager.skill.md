# Knowledge Object Manager

**Command**: `/ko`

**Description**: Manage Knowledge Objects - create, search, approve, and track institutional learning

## What This Does

Provides a unified interface for Knowledge Object operations:

1. **Create** - Draft new KOs from learnings
2. **Search** - Query approved KOs by tags, content
3. **Approve** - Review and approve pending KOs
4. **Metrics** - Track KO effectiveness and usage
5. **Sync** - Sync KOs with MCP Memory knowledge graph

## Capabilities

- **Creates** structured KOs with proper metadata
- **Searches** with caching (457x speedup)
- **Auto-approves** high-confidence KOs (70% threshold)
- **Tracks** consultation and success rates
- **Syncs** with Memory MCP for cross-session persistence

## Usage

```bash
# List all approved KOs
/ko list

# Search by tags (OR semantics)
/ko search --tags typescript,testing

# Search by content
/ko search "error handling patterns"

# Show pending drafts
/ko pending

# Approve a pending KO
/ko approve KO-draft-2024-001

# Show KO metrics
/ko metrics

# Create new KO from current session
/ko create --title "React 19 Server Components Pattern"

# Sync with Memory MCP
/ko sync
```

## Knowledge Object Structure

```yaml
id: KO-{project}-{number}
title: Descriptive title
category: Pattern | Bug Fix | Architecture | Best Practice
tags: [relevant, searchable, terms]
source: Session-ID or PR-URL
confidence: 0.0-1.0
effectiveness:
  consultations: 0
  successes: 0
content: |
  ## Problem
  What issue this addresses

  ## Solution
  The learned pattern or fix

  ## Evidence
  Tests, metrics, or verification
```

## Auto-Approval Criteria

KOs are auto-approved when:
- Confidence >= 0.85
- Source is verified (PR merged, tests passing)
- No conflicting existing KOs
- Category is tactical (not strategic)

Strategic KOs always require human review:
- Architecture decisions
- Security patterns
- Compliance-related
- Cross-project standards

## Memory MCP Integration

The `/ko sync` command:
1. Reads all approved KOs
2. Creates entities in Memory knowledge graph
3. Establishes relations (KO → applies_to → project)
4. Adds observations from content

This enables:
- Cross-session KO retrieval
- Pattern relationship discovery
- Usage tracking via graph queries

## Output

- **KO documents** in `knowledge/approved/` or `knowledge/drafts/`
- **Memory graph updates** in `.aibrain/memory/knowledge-graph.jsonl`
- **Metrics reports** showing effectiveness

## Storage

| Path | Content |
|------|---------|
| `knowledge/approved/` | Approved KOs (committed) |
| `knowledge/drafts/` | Pending review (git-ignored) |
| `.aibrain/memory/` | Knowledge graph (session-specific) |

## Related

- `aibrain ko` - CLI equivalent
- `docs/03-knowledge/README.md` - Full KO documentation
- Memory MCP - Cross-session persistence
