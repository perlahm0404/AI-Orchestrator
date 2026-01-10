# ADR-{{NUMBER}}: {{TITLE}}

**Date**: {{DATE}}
**Status**: draft | approved | superseded
**Advisor**: data-advisor | app-advisor | uiux-advisor
**Deciders**: {{HUMAN_NAME}}

---

## Tags

```yaml
tags: [{{TAGS}}]
applies_to:
  - "{{FILE_PATTERN_1}}"
  - "{{FILE_PATTERN_2}}"
domains: [{{DOMAINS}}]
```

---

## Context

> What prompted this decision? What problem are we solving?

{{CONTEXT}}

---

## Decision

> What was decided? State it clearly and concisely.

{{DECISION}}

---

## Options Considered

### Option A: {{OPTION_A_NAME}}

**Approach**: {{OPTION_A_DESCRIPTION}}

**Tradeoffs**:
- Pro: {{OPTION_A_PRO}}
- Con: {{OPTION_A_CON}}

**Best for**: {{OPTION_A_USE_CASE}}

### Option B: {{OPTION_B_NAME}}

**Approach**: {{OPTION_B_DESCRIPTION}}

**Tradeoffs**:
- Pro: {{OPTION_B_PRO}}
- Con: {{OPTION_B_CON}}

**Best for**: {{OPTION_B_USE_CASE}}

{{ADDITIONAL_OPTIONS}}

---

## Rationale

> Why was this option chosen? Capture the human's reasoning.

{{RATIONALE}}

---

## Implementation Notes

> Technical details for Coordinator to break into tasks.

### Schema Changes
{{SCHEMA_CHANGES}}

### API Changes
{{API_CHANGES}}

### UI Changes
{{UI_CHANGES}}

### Estimated Scope
- Files to modify: {{ESTIMATED_FILES}}
- Complexity: Low | Medium | High
- Dependencies: {{DEPENDENCIES}}

---

## Consequences

### Enables
- {{CONSEQUENCE_ENABLES_1}}
- {{CONSEQUENCE_ENABLES_2}}

### Constrains
- {{CONSEQUENCE_CONSTRAINS_1}}
- {{CONSEQUENCE_CONSTRAINS_2}}

---

## Related ADRs

- {{RELATED_ADR_1}}
- {{RELATED_ADR_2}}

---

<!--
SYSTEM SECTION - DO NOT EDIT
-->

```yaml
_system:
  created_by: "{{ADVISOR_NAME}}"
  created_at: "{{CREATED_TIMESTAMP}}"
  approved_at: "{{APPROVED_TIMESTAMP}}"
  approved_by: "{{APPROVER}}"
  confidence: {{CONFIDENCE}}
  auto_decided: {{AUTO_DECIDED}}
  escalation_reason: "{{ESCALATION_REASON}}"
```
