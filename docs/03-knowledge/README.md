# Knowledge Object System

## Overview

The Knowledge Object (KO) system captures institutional learning from multi-iteration agent sessions, enabling agents to learn from past experiences and avoid repeating mistakes.

## How It Works

### 1. Pre-Execution Consultation

Before starting work, agents consult existing KOs:

```python
# Automatic consultation in IterationLoop
relevant_kos = _consult_knowledge(task_description)
# Agent receives relevant past learnings before execution
```

**Example**:
- Task: "Fix TypeScript type errors in drizzle-orm queries"
- Tags extracted: `['typescript', 'drizzle', 'orm', 'type']`
- KO matched: "Drizzle ORM version mismatches cause type errors"
- Agent sees this knowledge before starting work

### 2. Post-Execution Learning Capture

After successful multi-iteration fixes (≥2 iterations), the system automatically creates draft KOs:

```python
# In IterationLoop after completion
if iterations >= 2:
    _create_draft_ko(task, history, verdict)
```

**Auto-Approval**:
- High confidence KOs (PASS verdict + 2-10 iterations) are **auto-approved**
- Low confidence KOs require human review via `aibrain ko pending`

### 3. Knowledge Storage

**Directory Structure**:
```
knowledge/
├── approved/       # Auto-approved and human-approved KOs
│   ├── KO-km-001.md
│   └── KO-km-002.md
├── drafts/         # Pending human review
└── README.md       # This file
```

**File Format**: Markdown with JSON frontmatter
```yaml
---
{
  "id": "KO-km-001",
  "project": "karematch",
  "title": "Short description",
  "tags": ["typescript", "drizzle-orm"],
  ...
}
---

# Markdown content
...
```

## Tag Matching Semantics

### OR Semantics (Default)

**The KO system uses OR semantics for tag matching**, meaning ANY tag match returns the KO.

**Why OR?**
- Broad discovery: find related knowledge even if not exact match
- Avoid missing relevant learnings due to tag variations
- Users searching for knowledge want comprehensive results

**Example**:

```bash
# Search with multiple tags
aibrain ko search --tags "typescript,strict-mode" --project karematch

# Returns KOs with ANY of these tags:
# - KO-km-001: tags ["typescript", "drizzle-orm"] ✅ (typescript matches)
# - KO-km-002: tags ["typescript", "strict-mode"] ✅ (both match)
# - KO-km-003: tags ["react", "hooks"] ❌ (no match)
```

### Implementation

```python
# knowledge/service.py
def find_relevant(project, tags, file_patterns):
    for ko in all_kos:
        # Match if ANY tag matches (OR semantics)
        if any(tag in ko.tags for tag in tags):
            relevant_kos.append(ko)
```

### Future: AND Semantics (Optional)

If you need AND semantics (ALL tags must match), use:

```python
# Future enhancement
if all(tag in ko.tags for tag in tags):
    relevant_kos.append(ko)
```

## Performance

### Caching

**In-memory cache** provides 100-500x speedup for repeated queries:

```python
# First query: reads from disk (~0.4ms for 2 KOs)
kos = list_approved()

# Second query: from cache (~0.001ms) - 400x faster!
kos = list_approved()
```

**Cache invalidation**:
- Time-based: 5 minutes
- Event-based: when KO is approved/modified
- Manual: `invalidate_cache()`

**Thread-safe**: Uses `threading.Lock` for concurrent access

### Scalability Limits

| # of KOs | Performance | Recommendation |
|----------|-------------|----------------|
| 1-100 | Excellent (< 100ms) | ✅ Current implementation OK |
| 100-200 | Good (< 500ms) | ⚠️ Consider tag indexing |
| 200-500 | Slow (1-3s) | ⚠️ Requires tag index |
| 500+ | Poor (3-10s+) | ❌ Database migration needed |

**Current architecture**: Flat file + in-memory cache
**Scales to**: ~200 KOs before needing optimization

## CLI Commands

### List KOs

```bash
# List all approved KOs
aibrain ko list

# List KOs for specific project
aibrain ko list --project karematch
```

### Search KOs

```bash
# Search by tags (OR semantics)
aibrain ko search --tags "typescript,drizzle-orm" --project karematch

# Returns all KOs with ANY of the specified tags
```

### Show KO Details

```bash
# Show full KO details
aibrain ko show KO-km-001
```

### Draft Management

```bash
# List pending drafts
aibrain ko pending

# Approve draft
aibrain ko approve KO-km-002

# Reject draft (not yet implemented)
aibrain ko reject KO-km-002
```

## Tag Extraction

Tags are automatically extracted from task descriptions using:

1. **File extensions**: `.ts` → `typescript`, `.py` → `python`
2. **Keywords**: `auth`, `drizzle`, `orm`, `test`, `migration`, etc.
3. **File paths**: `packages/api` → `packages`, `api`
4. **Filenames**: `Dashboard.tsx` → `dashboard`, `typescript`

**Example**:

```python
task = "Fix React component rendering bug in Dashboard.tsx"
# Extracts: ['bug', 'component', 'dashboard', 'fix', 'react', 'typescript']

task = "Add PostgreSQL migration for user preferences"
# Extracts: ['migration']
```

**Customization**: Edit patterns in `orchestration/ko_helpers.py:extract_tags_from_task()`

## Auto-Approval Thresholds

High-confidence KOs are auto-approved when:

1. **Ralph verdict**: PASS (successful fix)
2. **Iteration count**: 2-10 iterations
   - Too few (< 2): Trivial, no learning
   - Too many (> 10): Too complex, needs review

**Configuration**: See `orchestration/iteration_loop.py:_create_draft_ko()`

```python
should_auto_approve = (
    verdict.type.value == "PASS" and
    2 <= iterations <= 10
)
```

## Consultation Metrics

The system tracks:
- **Consultation count**: How often each KO is consulted
- **Logged to**: `knowledge/consultation_metrics.log`

**Format**:
```
2026-01-06T15:30:00,KO-km-001,consulted
2026-01-06T15:35:00,KO-km-001,consulted
2026-01-06T15:40:00,KO-km-002,consulted
```

**Future**: Effectiveness metrics (consultation → success rate)

## Integration with Wiggum

The KO system integrates with the Wiggum iteration control system:

```python
# orchestration/iteration_loop.py

class IterationLoop:
    def run(self, task_id, task_description):
        # PRE-EXECUTION (line 149)
        relevant_kos = self._consult_knowledge(task_description)

        # ... iteration loop ...

        # POST-EXECUTION (line 215)
        if self.agent.current_iteration >= 2:
            self._create_draft_ko(task_id, task_description, verdict)
```

**Flow**:
1. Agent starts task
2. System extracts tags from task description
3. System finds relevant KOs (OR matching)
4. Agent sees relevant past learnings
5. Agent executes (may iterate multiple times)
6. If iterations ≥ 2, create draft KO
7. If high confidence, auto-approve
8. Next agent benefits from this learning

## Verdict Format Support

The system supports multiple verdict formats for compatibility:

```python
# All these formats work:
"PASS"                          # String
{"status": "PASS"}             # Dict with 'status'
{"type": "FAIL"}               # Dict with 'type'
verdict_obj.type = PASS        # Object with .type
verdict_obj.status = "FAIL"    # Object with .status
```

**Normalization**: `orchestration/ko_helpers.py:_normalize_verdict()`

## Best Practices

### Creating Good KOs

**DO**:
- ✅ Write clear, concise titles (< 60 chars)
- ✅ Focus on "why" not just "what"
- ✅ Include prevention rules (how to avoid next time)
- ✅ Add specific detection patterns (regex, error messages)
- ✅ Use consistent tags (lowercase, no spaces)

**DON'T**:
- ❌ Create KOs for trivial changes (1 iteration fixes)
- ❌ Use overly broad tags ("code", "bug", "fix")
- ❌ Duplicate existing KOs (search first!)
- ❌ Include sensitive data (passwords, tokens, PII)

### Tag Naming Conventions

**Good tags**:
- `typescript`, `python`, `javascript` (language)
- `drizzle-orm`, `react`, `vitest` (framework/library)
- `auth`, `migration`, `api` (domain)
- `type-errors`, `null-check` (problem type)

**Bad tags**:
- `code`, `software`, `computer` (too broad)
- `thing`, `stuff`, `misc` (meaningless)
- `TypeScript`, `Type-Script` (inconsistent case/format)

### Reviewing Pending KOs

```bash
# Weekly review workflow
aibrain ko pending

# For each draft:
# 1. Read the learning carefully
# 2. Check if it's accurate and useful
# 3. Verify tags are appropriate
# 4. Approve or reject

aibrain ko approve KO-km-XXX  # if good
# OR delete draft file manually if bad
```

## Troubleshooting

### No KOs Found in Search

**Possible causes**:
1. Tags don't match (remember: OR semantics, but still need at least one match)
2. Wrong project specified
3. KO is still in drafts/ (not approved yet)

**Solution**: Try broader tag search or check `aibrain ko list`

### Cache Not Updating

**Symptom**: Approved KO doesn't appear in searches

**Solution**:
```python
from knowledge.service import invalidate_cache
invalidate_cache()
```

Or wait 5 minutes for automatic cache expiry.

### Performance Degradation

**Symptom**: `ko list` and `ko search` taking >1 second

**Cause**: Too many KOs (likely >200)

**Solution**: Implement tag indexing (see Priority 2 recommendations)

## Future Enhancements

### Priority 2 (In Progress)
- Tag index for faster searches (O(1) tag lookup)
- Consultation effectiveness metrics
- Configurable auto-approval thresholds

### Priority 3 (Planned)
- Tag aliases (`ts` → `typescript`)
- Fuzzy tag matching (typo tolerance)
- KO versioning/editing workflow
- AND semantics option for searches

## API Reference

### Core Functions

```python
# Find relevant KOs
from knowledge.service import find_relevant
kos = find_relevant(
    project="karematch",
    tags=["typescript", "orm"],
    file_patterns=["src/**/*.ts"]
)

# Create draft KO
from knowledge.service import create_draft
ko = create_draft(
    project="karematch",
    title="Always check for null",
    what_was_learned="...",
    why_it_matters="...",
    prevention_rule="...",
    tags=["null-check", "typescript"]
)

# Approve draft
from knowledge.service import approve
approve("KO-km-001")

# List approved KOs
from knowledge.service import list_approved
all_kos = list_approved()
karematch_kos = list_approved(project="karematch")

# Invalidate cache
from knowledge.service import invalidate_cache
invalidate_cache()
```

### Helper Functions

```python
# Extract tags from task
from orchestration.ko_helpers import extract_tags_from_task
tags = extract_tags_from_task("Fix auth bug in login.ts")
# Returns: ['auth', 'bug', 'fix', 'login', 'typescript']

# Format KO for display
from orchestration.ko_helpers import format_ko_for_display
print(format_ko_for_display(ko))

# Normalize verdict format
from orchestration.ko_helpers import _normalize_verdict
verdict_str = _normalize_verdict(verdict)  # Handles any format
```

## Contributing

### Adding New Tags

Edit `orchestration/ko_helpers.py:extract_tags_from_task()`:

```python
keywords = [
    'auth', 'test', 'api',  # existing
    'your-new-keyword',      # add here
]
```

### Modifying Auto-Approval Logic

Edit `orchestration/iteration_loop.py:_create_draft_ko()`:

```python
should_auto_approve = (
    verdict.type.value == "PASS" and
    2 <= iterations <= 10  # Modify these thresholds
)
```

---

**Version**: v5.1
**Last Updated**: 2026-01-06
**Status**: Production Ready ✅
