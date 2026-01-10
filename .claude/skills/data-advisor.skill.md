# Data Advisor

**Command**: `/data-advisor`

**Description**: Consult the Data Advisor for schema design, migrations, and data architecture

## What This Does

Invokes the Data Advisor agent to provide expert guidance on:

1. **Schema design** - Table structure, normalization, relationships
2. **Migrations** - Database schema changes, rollback strategies
3. **Data quality** - Validation rules, constraints, integrity
4. **Query optimization** - Indexes, query patterns, performance
5. **Storage architecture** - SQL vs NoSQL, partitioning, archival

## Capabilities

- **Analyzes** existing database schema and models
- **Recommends** data structures with tradeoffs
- **Creates ADRs** for approved data decisions
- **Auto-decides** when confident (85%+) and ADR-aligned
- **Escalates** strategic decisions to you for approval

## Usage

```bash
# Invoke via @data-advisor or /data-advisor
@data-advisor How should we model certifications and expiration tracking?
@data-advisor What's the best way to handle provider credentials?
@data-advisor Should we use soft deletes or hard deletes?
```

## Autonomy

- **Can auto-decide** when:
  - Decision aligns with existing ADR (tag match)
  - Confidence >= 85%
  - Tactical domain (e.g., column naming)
  - Files touched <= 5

- **Must escalate** when:
  - Conflicts with existing ADR
  - Strategic domain (schema changes, migrations, compliance)
  - Files touched > 5
  - Confidence < 85%

## Output

- **ADR document** in `AI-Team-Plans/decisions/`
- **PROJECT_HQ update** with roadmap changes
- **Event logs** for observability

## HIPAA Extension (CredentialMate)

For HIPAA-compliant projects, the Data Advisor:
- **Always flags** PHI columns (patient health information)
- **Recommends encryption** for sensitive data
- **Includes audit logging** in schema designs
- **Validates** against HIPAA requirements

## Implementation

This skill invokes the Python-based Data Advisor agent located at:
`/Users/tmac/1_REPOS/AI_Orchestrator/agents/advisor/data_advisor.py`

The advisor:
1. Reads existing ADRs to check alignment
2. Analyzes database models and migrations
3. Scores confidence (pattern match + ADR + historical)
4. Auto-decides if all criteria met
5. Otherwise, presents 2-4 options for your decision

## Related

- `/app-advisor` - For architecture/API questions
- `/uiux-advisor` - For UI/UX questions
- `aibrain ko search --tags database,schema` - Query Knowledge Objects
