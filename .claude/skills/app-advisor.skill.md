# App Advisor

**Command**: `/app-advisor`

**Description**: Consult the App Advisor for architecture, API design, and application patterns

## What This Does

Invokes the App Advisor agent to provide expert guidance on:

1. **Architecture decisions** - System design, service patterns
2. **API design** - Endpoint structure, contracts, versioning
3. **Technology stack** - Framework selection, library choices
4. **Integration patterns** - How components communicate
5. **Security architecture** - Auth flows, encryption strategies

## Capabilities

- **Analyzes** existing codebase architecture
- **Recommends** solutions with tradeoffs explained
- **Creates ADRs** for approved architectural decisions
- **Auto-decides** when confident (85%+) and ADR-aligned
- **Escalates** strategic decisions to you for approval

## Usage

```bash
# Invoke via @app-advisor or /app-advisor
@app-advisor How should we structure the API for multi-tenancy?
@app-advisor What's the best caching strategy for this feature?
@app-advisor Should we use REST or GraphQL for the new service?
```

## Autonomy

- **Can auto-decide** when:
  - Decision aligns with existing ADR (tag match)
  - Confidence >= 85%
  - Tactical domain (e.g., code organization)
  - Files touched <= 5

- **Must escalate** when:
  - Conflicts with existing ADR
  - Strategic domain (security, external deps, schema, infra)
  - Files touched > 5
  - Confidence < 85%

## Output

- **ADR document** in `AI-Team-Plans/decisions/`
- **PROJECT_HQ update** with roadmap changes
- **Event logs** for observability

## Implementation

This skill invokes the Python-based App Advisor agent located at:
`/Users/tmac/1_REPOS/AI_Orchestrator/agents/advisor/app_advisor.py`

The advisor:
1. Reads existing ADRs to check alignment
2. Analyzes codebase patterns
3. Scores confidence (pattern match + ADR + historical)
4. Auto-decides if all criteria met
5. Otherwise, presents 2-4 options for your decision

## Related

- `/data-advisor` - For database/schema questions
- `/uiux-advisor` - For UI/UX questions
- `aibrain ko search --tags architecture` - Query Knowledge Objects
