# Evidence Repository

## Purpose
Capture real-world user evidence to drive agent improvements and roadmap decisions.

## Capture Workflow
1. **Capture**: `aibrain evidence capture <type> <source>`
2. **Tag**: Add appropriate tags (state, specialty, cme/licensing)
3. **Link**: Connect to tasks/ADRs/KOs
4. **Review**: Weekly Friday review (30 min)
5. **Close**: Mark status=validated when resolved

## Types
- `bug-report`: User encountered error/incorrect behavior
- `feature-request`: User requested new capability
- `user-question`: Support question revealing gap
- `edge-case`: Unusual state/specialty combination
- `state-variation`: State-specific rule nuance

## Tags
- **States**: `ca`, `tx`, `ny`, `fl`, `pa`, ... (all 50 states)
- **Specialties**: `family-medicine`, `emergency`, `pediatrics`, `internal-medicine`, ...
- **Domains**: `cme-tracking`, `license-renewal`, `board-certification`, `continuing-education`, ...
- **Personas**: `np`, `pa`, `physician`, `do`

## Priority Levels
- `p0-blocks-user`: User cannot complete critical task
- `p1-degrades-trust`: User loses confidence in accuracy
- `p2-improvement`: Nice-to-have enhancement

## Roadmap Linking
Evidence items with `priority=p0-blocks-user` automatically trigger PM review.

## CLI Commands
```bash
# Capture new evidence
aibrain evidence capture bug-report pilot-user

# List evidence by filters
aibrain evidence list --state CA --priority p0
aibrain evidence list --tags cme-tracking
aibrain evidence list --status captured

# Link evidence to tasks
aibrain evidence link EVIDENCE-001 TASK-CME-045

# Show evidence details
aibrain evidence show EVIDENCE-001
```

## Example Evidence Files
- `EVIDENCE-001-ca-np-cme-ancc.md`: California NP with ANCC certification getting wrong CME hours
- `EVIDENCE-002-tx-pa-renewal-deadline.md`: Texas PA renewal deadline calculated incorrectly
- `EVIDENCE-003-ny-physician-compact-state.md`: New York physician reciprocity question

## Weekly Review Ritual (Fridays, 30 min)
1. Review all `status=captured` items
2. Identify patterns (3+ similar items → potential feature/bug)
3. Link to existing tasks or create new tasks
4. Update roadmap if P0 items reveal gaps
5. Mark `status=analyzed` when reviewed

## Integration with Meta-Agents
- **PM Agent**: Reads evidence for product insights, blocks tasks without evidence
- **CMO Agent**: Reads evidence for messaging/GTM insights (user objections, language)
- **Governance Agent**: Reads evidence for compliance gaps (HIPAA, state-specific risks)
