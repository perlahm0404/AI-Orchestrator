# Knowledge Objects v1 - Design Specification

**Date**: 2026-01-05
**Status**: Proposed Addition to V4
**Phase**: Phase 1+ (additive, does not change Phase -1 or Phase 0)

---

## Design Principle

> **Episodic memory explains *what happened*.**
> **Knowledge Objects explain *what must never be forgotten*.**

A Knowledge Object is distilled institutional memory—the irreducible lesson extracted from resolving an issue. It transforms one-time learning into permanent, actionable knowledge.

---

## What This Does NOT Replace

| Existing Component | Purpose | Relationship to Knowledge Objects |
|-------------------|---------|-----------------------------------|
| `audit_log` | Records *what happened* during execution | Knowledge Objects *reference* audit_log entries for traceability |
| `sessions` | Tracks *episodic attempts* to resolve issues | Sessions *produce* Knowledge Objects upon success |
| `REVIEW.md` | Human UX for *reviewing a specific fix* | Knowledge Objects *extract* insights from REVIEW.md |
| `issues` | Tracks *what needs to be done* | Knowledge Objects *derive from* resolved issues |
| `hot_patterns` | Stores *recurring bug patterns* for matching | Knowledge Objects are *richer*, with prevention rules and scope |

Knowledge Objects are **additive**. They sit alongside existing components and enhance them.

---

## 1. Knowledge Object Schema (v1)

### YAML Definition

```yaml
# schema/knowledge_object.v1.yaml
knowledge_object:
  version: "1.0"

  # Identity
  id: string           # KO-{project}-{sequential}
  title: string        # Short, memorable name (max 80 chars)

  # Traceability (REQUIRED)
  derived_from:
    issue_id: integer  # FK to issues table
    session_id: uuid   # Session where resolution occurred
    resolution_status: "RESOLVED_FULL"  # Only created on full resolution

  # The Knowledge (REQUIRED)
  insight:
    what_was_learned: string      # The core lesson (1-3 sentences)
    why_it_matters: string        # Impact if ignored (1-2 sentences)
    root_cause_category: enum     # See categories below

  # Prevention (REQUIRED)
  prevention:
    rule: string                  # How to prevent recurrence
    detection_pattern: string     # Regex/glob/keyword to detect similar issues
    suggested_guardrail: string   # Optional: test or hook that could prevent this

  # Scope (REQUIRED)
  applicability:
    projects: list[string]        # ["*"] for all, or specific project names
    file_patterns: list[string]   # ["src/auth/**", "*.config.ts"]
    tech_stack: list[string]      # ["typescript", "fastapi", "postgresql"]
    tags: list[string]            # For pattern matching without embeddings

  # Lifecycle
  status: enum                    # draft | approved | superseded | archived
  created_at: timestamp
  created_by: string              # "agent:bugfix" or "human:username"
  approved_at: timestamp | null
  approved_by: string | null      # Human who approved
  superseded_by: string | null    # ID of newer Knowledge Object

  # Metrics (populated over time)
  usage:
    times_consulted: integer      # How often agents checked this
    times_prevented: integer      # Issues prevented by this knowledge
    last_consulted_at: timestamp | null

# Root cause categories
root_cause_categories:
  - null_reference           # Missing null/undefined checks
  - race_condition           # Timing/concurrency issues
  - type_mismatch            # Type system gaps
  - config_error             # Configuration mistakes
  - missing_validation       # Input validation gaps
  - state_management         # State consistency issues
  - api_contract             # API boundary issues
  - dependency_issue         # External dependency problems
  - logic_error              # Algorithmic mistakes
  - security_vulnerability   # Security-related issues
  - performance_issue        # Performance degradation
  - other                    # Uncategorized
```

### SQL Schema

```sql
-- knowledge_objects table
CREATE TABLE knowledge_objects (
    -- Identity
    id VARCHAR(50) PRIMARY KEY,           -- KO-{project}-{seq}
    title VARCHAR(80) NOT NULL,

    -- Traceability
    issue_id INTEGER NOT NULL REFERENCES issues(id),
    session_id UUID NOT NULL,

    -- The Knowledge
    what_was_learned TEXT NOT NULL,
    why_it_matters TEXT NOT NULL,
    root_cause_category VARCHAR(30) NOT NULL,

    -- Prevention
    prevention_rule TEXT NOT NULL,
    detection_pattern TEXT,               -- Regex/glob for matching
    suggested_guardrail TEXT,             -- Optional test/hook suggestion

    -- Scope
    projects TEXT[] DEFAULT ARRAY['*'],   -- Project names or ['*']
    file_patterns TEXT[],                 -- Glob patterns
    tech_stack TEXT[],                    -- Technology tags
    tags TEXT[] NOT NULL,                 -- For pattern matching

    -- Lifecycle
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'superseded', 'archived')),
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100) NOT NULL,
    approved_at TIMESTAMP,
    approved_by VARCHAR(100),
    superseded_by VARCHAR(50) REFERENCES knowledge_objects(id),

    -- Metrics
    times_consulted INTEGER DEFAULT 0,
    times_prevented INTEGER DEFAULT 0,
    last_consulted_at TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_resolution CHECK (
        EXISTS (SELECT 1 FROM issues WHERE id = issue_id AND resolution_status = 'RESOLVED_FULL')
    )
);

-- Indexes for efficient lookup
CREATE INDEX idx_ko_status ON knowledge_objects(status) WHERE status = 'approved';
CREATE INDEX idx_ko_tags ON knowledge_objects USING GIN(tags);
CREATE INDEX idx_ko_projects ON knowledge_objects USING GIN(projects);
CREATE INDEX idx_ko_root_cause ON knowledge_objects(root_cause_category);
CREATE INDEX idx_ko_issue ON knowledge_objects(issue_id);

-- Junction table for issue-to-knowledge references
CREATE TABLE issue_knowledge_refs (
    issue_id INTEGER REFERENCES issues(id),
    knowledge_object_id VARCHAR(50) REFERENCES knowledge_objects(id),
    ref_type VARCHAR(20) CHECK (ref_type IN ('consulted', 'applied', 'derived_from')),
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (issue_id, knowledge_object_id, ref_type)
);
```

---

## 2. Creation Workflow

### When Created

A Knowledge Object is created **if and only if**:

1. An Issue reaches `resolution_status = 'RESOLVED_FULL'`
2. The resolution includes meaningful insight (not trivial typo fixes)
3. The insight has reuse potential (applies beyond this one instance)

**Cardinality**: Exactly **one** Knowledge Object per resolved Issue (or zero if not insightful).

### Step-by-Step Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                 KNOWLEDGE OBJECT CREATION WORKFLOW               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. TRIGGER                                                     │
│     └─ Issue marked RESOLVED_FULL                               │
│        └─ Agent or human signals "resolution complete"          │
│                                                                 │
│  2. EXTRACT (Agent)                                             │
│     └─ Read REVIEW.md for this issue                            │
│     └─ Read audit_log for this session                          │
│     └─ Identify:                                                │
│        ├─ Root cause (what_was_learned)                         │
│        ├─ Impact (why_it_matters)                               │
│        ├─ Prevention (how to stop recurrence)                   │
│        └─ Scope (where this applies)                            │
│                                                                 │
│  3. DRAFT (Agent)                                               │
│     └─ Generate Knowledge Object with status='draft'            │
│     └─ Assign ID: KO-{project}-{next_seq}                       │
│     └─ Write to knowledge_objects table                         │
│     └─ Generate markdown mirror                                 │
│                                                                 │
│  4. REVIEW (Human)                                              │
│     └─ Human reviews draft in Obsidian or CLI                   │
│     └─ Options:                                                 │
│        ├─ APPROVE → status='approved', approved_by=human        │
│        ├─ EDIT → modify fields, then approve                    │
│        ├─ REJECT → status='archived', no knowledge captured     │
│        └─ SKIP → remains 'draft', revisit later                 │
│                                                                 │
│  5. ACTIVATE (System)                                           │
│     └─ On approval:                                             │
│        ├─ Knowledge Object becomes queryable                    │
│        ├─ Link to issue via issue_knowledge_refs                │
│        └─ Log to audit_log: action='knowledge_object_approved'  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Extraction Prompt (for Agent)

```markdown
## Extract Knowledge Object

You are extracting institutional knowledge from a resolved issue.

**Source Material:**
- REVIEW.md: {review_md_content}
- Root Cause: {task.root_cause}
- Evidence: {task.evidence}

**Extract:**

1. **What was learned?** (The irreducible insight, 1-3 sentences)
   - Not "we fixed the bug" but "null checks are missing at auth boundaries"

2. **Why does it matter?** (Impact if ignored, 1-2 sentences)
   - What would happen if we forgot this lesson?

3. **Root cause category:** (Select one)
   - null_reference, race_condition, type_mismatch, config_error,
   - missing_validation, state_management, api_contract, dependency_issue,
   - logic_error, security_vulnerability, performance_issue, other

4. **Prevention rule:** (How to prevent recurrence)
   - Concrete, actionable rule (e.g., "Always validate token before accessing claims")

5. **Detection pattern:** (How to spot similar issues)
   - Regex, glob, or keywords that would identify related code

6. **Suggested guardrail:** (Optional)
   - A test or hook that could enforce this rule

7. **Applicability:**
   - Which projects? (specific names or "*" for all)
   - Which file patterns? (globs)
   - Which tech stack? (tags)
   - General tags for matching?

**Output:** JSON matching knowledge_object.v1.yaml schema
```

---

## 3. Integration Points

### Integration with Issue Ledger

```sql
-- Issues can reference prior Knowledge Objects
ALTER TABLE issues ADD COLUMN related_knowledge TEXT[];  -- Array of KO IDs

-- When creating an issue, auto-populate related_knowledge
-- based on tag/pattern matching against approved Knowledge Objects
```

**Workflow:**
1. New issue created
2. System queries `knowledge_objects WHERE status='approved'`
3. Match by: tags overlap, file_patterns match affected_files, project match
4. Populate `issues.related_knowledge` with matching KO IDs
5. Display in issue view: "Related Knowledge: KO-karematch-001, KO-karematch-003"

### Integration with Sessions

```python
# At session start, retrieve relevant Knowledge Objects
def get_relevant_knowledge(issue_id: int) -> list[KnowledgeObject]:
    issue = db.get_issue(issue_id)

    # 1. Explicitly linked knowledge
    explicit = db.query("""
        SELECT ko.* FROM knowledge_objects ko
        WHERE ko.id = ANY(%s) AND ko.status = 'approved'
    """, [issue.related_knowledge])

    # 2. Tag-matched knowledge
    tag_matched = db.query("""
        SELECT ko.* FROM knowledge_objects ko
        WHERE ko.status = 'approved'
        AND ko.tags && %s  -- Array overlap
    """, [issue.tags])

    return dedupe(explicit + tag_matched)

# Include in agent context
def build_agent_context(session_id: uuid, issue_id: int) -> dict:
    knowledge = get_relevant_knowledge(issue_id)

    return {
        "issue": db.get_issue(issue_id),
        "prior_knowledge": [ko.to_context_block() for ko in knowledge],
        # ... other context
    }
```

### Integration with audit_log

```sql
-- Log Knowledge Object lifecycle events
INSERT INTO audit_log (action, action_type, details) VALUES
('created', 'knowledge_object', '{"ko_id": "KO-karematch-001", "issue_id": 123}'),
('approved', 'knowledge_object', '{"ko_id": "KO-karematch-001", "approved_by": "tmac"}'),
('consulted', 'knowledge_object', '{"ko_id": "KO-karematch-001", "by_session": "abc-123"}');

-- Update consultation metrics
UPDATE knowledge_objects
SET times_consulted = times_consulted + 1,
    last_consulted_at = NOW()
WHERE id = 'KO-karematch-001';
```

### Integration with REVIEW.md

Add a "Prior Knowledge" section to REVIEW.md template:

```markdown
## Prior Knowledge Consulted

The following Knowledge Objects were consulted during this fix:

| ID | Title | How Applied |
|----|-------|-------------|
| KO-karematch-001 | Null check at auth boundaries | Followed prevention rule |
| KO-karematch-003 | Token expiry edge cases | Informed test cases |

---

## Knowledge Captured

A new Knowledge Object will be created from this resolution:

**Draft ID**: KO-karematch-007
**Status**: Pending human approval

[View draft](./knowledge/drafts/KO-karematch-007.md)
```

---

## 4. Enforcement Hooks

### Pre-Action Check

Before an agent takes action on an issue, it MUST check relevant Knowledge Objects:

```python
# hooks/knowledge_check.py
def pre_action_knowledge_check(issue_id: int, proposed_action: str) -> dict:
    """
    Check if any Knowledge Object provides guidance for this action.
    Returns advisory (does not block).
    """
    knowledge = get_relevant_knowledge(issue_id)

    advisories = []
    for ko in knowledge:
        # Check if proposed action might violate a prevention rule
        if matches_detection_pattern(proposed_action, ko.detection_pattern):
            advisories.append({
                "ko_id": ko.id,
                "title": ko.title,
                "prevention_rule": ko.prevention_rule,
                "advisory": f"Prior knowledge suggests: {ko.prevention_rule}"
            })

            # Log consultation
            log_consultation(ko.id, issue_id)

    return {
        "has_relevant_knowledge": len(advisories) > 0,
        "advisories": advisories
    }
```

### Issue Creation Hook

When a new issue is created, auto-link relevant Knowledge Objects:

```python
# hooks/issue_knowledge_link.py
def on_issue_created(issue_id: int):
    """Auto-populate related_knowledge based on pattern matching."""
    issue = db.get_issue(issue_id)

    # Find matching Knowledge Objects
    matches = db.query("""
        SELECT id FROM knowledge_objects
        WHERE status = 'approved'
        AND (
            -- Tag overlap
            tags && %s
            -- OR file pattern match
            OR EXISTS (
                SELECT 1 FROM unnest(file_patterns) fp
                WHERE %s LIKE replace(replace(fp, '*', '%%'), '?', '_')
            )
            -- OR project match
            OR projects @> ARRAY[%s]
            OR projects @> ARRAY['*']
        )
    """, [issue.tags, issue.affected_files, issue.project_name])

    if matches:
        db.update_issue(issue_id, related_knowledge=[m.id for m in matches])

        log_action(
            action="linked",
            action_type="knowledge_reference",
            details={"issue_id": issue_id, "ko_ids": [m.id for m in matches]}
        )
```

### Prevention to Guardrail Pipeline

Knowledge Objects with `suggested_guardrail` can be promoted to actual guardrails:

```python
# Workflow (human-initiated, not automatic)
def promote_to_guardrail(ko_id: str):
    """
    Promote a Knowledge Object's suggested_guardrail to an actual test.
    Requires human approval and implementation.
    """
    ko = db.get_knowledge_object(ko_id)

    if not ko.suggested_guardrail:
        raise ValueError("No suggested guardrail in this Knowledge Object")

    # Generate guardrail proposal
    proposal = {
        "source_ko": ko_id,
        "guardrail_type": detect_guardrail_type(ko.suggested_guardrail),
        "implementation_suggestion": ko.suggested_guardrail,
        "file_patterns": ko.file_patterns,
        "status": "proposed"
    }

    # Create task for human to implement
    create_task(
        title=f"Implement guardrail from {ko_id}",
        description=f"Promote suggested guardrail to test:\n\n{ko.suggested_guardrail}",
        task_type="guardrail_implementation",
        metadata=proposal
    )
```

---

## 5. Storage

### Postgres (Primary)

The `knowledge_objects` table defined above is the source of truth.

### Markdown Mirror (Obsidian)

Every Knowledge Object is mirrored to markdown for human readability:

```
knowledge/
├── approved/
│   ├── KO-karematch-001.md
│   ├── KO-karematch-002.md
│   └── KO-credentialmate-001.md
├── drafts/
│   └── KO-karematch-007.md
└── archived/
    └── KO-karematch-000.md
```

**Markdown Template:**

```markdown
---
id: KO-karematch-001
title: Null check required at auth token boundaries
status: approved
issue_id: 123
session_id: abc-123-def-456
created_at: 2026-01-05T14:32:00Z
approved_at: 2026-01-05T15:10:00Z
approved_by: tmac
root_cause_category: null_reference
projects: ["karematch"]
file_patterns: ["src/services/auth*", "src/middleware/auth*"]
tech_stack: ["typescript", "jwt"]
tags: ["auth", "null-check", "token", "jwt"]
times_consulted: 3
times_prevented: 1
---

# KO-karematch-001: Null check required at auth token boundaries

## What Was Learned

When validating JWT tokens, the `refreshToken` parameter can be null if the token
has expired and been purged from the session store. Code that accesses token
properties without null checks will throw TypeError at runtime.

## Why It Matters

Unhandled null reference in auth flow causes 500 errors and blocks user login.
Users with expired sessions see cryptic error messages instead of being prompted
to re-authenticate.

## Prevention Rule

**Always check for null/undefined before accessing token properties at auth
boundaries.** Use early return pattern:

```typescript
if (!token) {
  return { valid: false, reason: 'token_missing' };
}
```

## Detection Pattern

```regex
token\.(claims|payload|exp|iat|sub)
```

Files: `src/services/auth*`, `src/middleware/auth*`

## Suggested Guardrail

Add ESLint rule or TypeScript strict null check for token access patterns.
Consider: `@typescript-eslint/no-unsafe-member-access` with auth file scope.

---

## Traceability

- **Derived from Issue**: [#123](../issues/123.md)
- **Resolution Session**: `abc-123-def-456`
- **REVIEW.md**: [View](../reviews/REVIEW-123.md)

## Usage Metrics

| Metric | Value |
|--------|-------|
| Times Consulted | 3 |
| Times Prevented | 1 |
| Last Consulted | 2026-01-10 |
```

### Sync Process

```python
def sync_knowledge_to_markdown(ko_id: str):
    """Sync a Knowledge Object from Postgres to markdown."""
    ko = db.get_knowledge_object(ko_id)

    # Determine directory based on status
    dir_map = {
        'approved': 'knowledge/approved',
        'draft': 'knowledge/drafts',
        'archived': 'knowledge/archived',
        'superseded': 'knowledge/archived'
    }

    directory = dir_map[ko.status]
    filepath = f"{directory}/{ko.id}.md"

    content = render_template('knowledge_object.md.j2', ko=ko)
    write_file(filepath, content)

# Trigger on any Knowledge Object change
def on_knowledge_object_changed(ko_id: str):
    sync_knowledge_to_markdown(ko_id)
```

---

## 6. Example Knowledge Object

### Real Example from Hypothetical Resolution

```yaml
id: "KO-karematch-001"
title: "Null check required at auth token boundaries"
status: "approved"

derived_from:
  issue_id: 123
  session_id: "abc-123-def-456"
  resolution_status: "RESOLVED_FULL"

insight:
  what_was_learned: |
    When validating JWT tokens, the refreshToken parameter can be null if the
    token has expired and been purged from the session store. Code that accesses
    token properties without null checks will throw TypeError at runtime.
  why_it_matters: |
    Unhandled null reference in auth flow causes 500 errors and blocks user login.
    Users with expired sessions see cryptic error messages instead of being
    prompted to re-authenticate.
  root_cause_category: "null_reference"

prevention:
  rule: |
    Always check for null/undefined before accessing token properties at auth
    boundaries. Use early return pattern: if (!token) return { valid: false }.
  detection_pattern: "token\\.(claims|payload|exp|iat|sub)"
  suggested_guardrail: |
    Add ESLint rule for token access patterns. Consider:
    @typescript-eslint/no-unsafe-member-access with auth file scope.

applicability:
  projects: ["karematch"]
  file_patterns: ["src/services/auth*", "src/middleware/auth*"]
  tech_stack: ["typescript", "jwt"]
  tags: ["auth", "null-check", "token", "jwt", "runtime-error"]

created_at: "2026-01-05T14:32:00Z"
created_by: "agent:bugfix"
approved_at: "2026-01-05T15:10:00Z"
approved_by: "tmac"

usage:
  times_consulted: 3
  times_prevented: 1
  last_consulted_at: "2026-01-10T09:15:00Z"
```

---

## 7. Agent Read/Write Rules

### Read Rules

| Agent | Can Read | Conditions |
|-------|----------|------------|
| BugFix | Yes | Approved KOs matching issue tags/files |
| CodeQuality | Yes | Approved KOs matching file patterns |
| Refactor | Yes | Approved KOs matching affected scope |
| All Agents | No | Draft KOs (human-only until approved) |

### Write Rules

| Agent | Can Write | Conditions |
|-------|-----------|------------|
| BugFix | Create Draft | Only on RESOLVED_FULL, exactly one per issue |
| CodeQuality | No | Does not resolve issues |
| Refactor | No | Does not resolve issues |
| Human | Approve/Edit/Archive | Full control over all KOs |

### Enforcement

```python
class KnowledgeObjectPermissions:
    @staticmethod
    def can_read(agent_type: str, ko: KnowledgeObject) -> bool:
        if ko.status != 'approved':
            return False  # Only humans see drafts
        return True

    @staticmethod
    def can_create(agent_type: str, issue: Issue) -> bool:
        if agent_type != 'bugfix':
            return False
        if issue.resolution_status != 'RESOLVED_FULL':
            return False
        if db.exists_ko_for_issue(issue.id):
            return False  # One per issue
        return True

    @staticmethod
    def can_approve(actor_type: str) -> bool:
        return actor_type == 'human'
```

---

## 8. What This Does NOT Do

| Capability | Status | Rationale |
|------------|--------|-----------|
| Vector embeddings for semantic search | NOT INCLUDED | Heavyweight; use tag matching for v1 |
| Automatic guardrail generation | NOT INCLUDED | Suggests only; human implements |
| Cross-project knowledge sharing | LIMITED | Projects opt-in via `projects: ["*"]` |
| Knowledge Object editing by agents | NOT INCLUDED | Human-only after creation |
| Automatic issue blocking | NOT INCLUDED | Advisory only; agents informed, not blocked |
| Replace audit_log | NOT INCLUDED | Complements, does not replace |
| Replace REVIEW.md | NOT INCLUDED | Extracts from, does not replace |

---

## 9. Phase Integration

| Phase | Knowledge Object Activity |
|-------|---------------------------|
| Phase -1 | None (manual workflow validation only) |
| Phase 0 | None (governance foundation) |
| Phase 1 | **First Knowledge Objects created** from BugFix resolutions |
| Phase 2 | Knowledge linked to intake/triage |
| Phase 3 | Knowledge informs hot_patterns (merge or complement) |
| Phase 4 | Cross-project knowledge dashboard |

**No changes to Phase -1 or Phase 0 scope.**

---

## 10. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Knowledge Objects per resolved issue | 0.3 - 0.7 | Not every fix is insightful |
| Human approval rate | > 80% | Drafts should be high quality |
| Times consulted (avg per KO) | > 2 | Knowledge is being used |
| Times prevented (total) | > 0 | Knowledge prevents recurrence |
| Time to approve | < 5 minutes | Low friction for humans |

---

## Summary

Knowledge Objects are the **durable semantic memory** layer that sits above episodic execution data. They capture:

- **What was learned** (insight)
- **Why it matters** (impact)
- **How to prevent recurrence** (prevention rule)
- **Where it applies** (scope)
- **Where it came from** (traceability)

They are:
- Created **only** on RESOLVED_FULL
- **One** per resolved issue (or zero)
- **Human-approved** (L1/L2 compatible)
- **Advisory** (inform, don't block)
- **Additive** (complement existing components)

This is the beginning of institutional memory for AI Brain.