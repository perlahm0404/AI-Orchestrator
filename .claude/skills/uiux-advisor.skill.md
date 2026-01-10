# UI/UX Advisor

**Command**: `/uiux-advisor`

**Description**: Consult the UI/UX Advisor for user experience, interfaces, and interaction design

## What This Does

Invokes the UI/UX Advisor agent to provide expert guidance on:

1. **User flow design** - Journey mapping, task flows, navigation
2. **Component architecture** - Reusable components, composition patterns
3. **Data display** - Tables, cards, forms, visualization
4. **Accessibility** - WCAG compliance, keyboard nav, screen readers
5. **Responsive design** - Mobile-first, breakpoints, adaptive layouts

## Capabilities

- **Analyzes** existing UI components and flows
- **Recommends** UX patterns with usability justification
- **Creates ADRs** for approved UI/UX decisions
- **Auto-decides** when confident (85%+) and ADR-aligned
- **Escalates** strategic decisions to you for approval

## Usage

```bash
# Invoke via @uiux-advisor or /uiux-advisor
@uiux-advisor How should we display the provider dashboard?
@uiux-advisor What's the best flow for certification upload?
@uiux-advisor Should we use a modal or inline form for editing?
```

## Autonomy

- **Can auto-decide** when:
  - Decision aligns with existing ADR (tag match)
  - Confidence >= 85%
  - Tactical domain (e.g., component naming, layout)
  - Files touched <= 5

- **Must escalate** when:
  - Conflicts with existing ADR
  - Strategic domain (new user flows, breaking UX changes)
  - Files touched > 5
  - Confidence < 85%

## Output

- **ADR document** in `AI-Team-Plans/decisions/`
- **PROJECT_HQ update** with roadmap changes
- **Event logs** for observability

## Accessibility First

The UI/UX Advisor always considers:
- **Keyboard navigation** - All interactions keyboard-accessible
- **Screen readers** - Semantic HTML, ARIA labels
- **Color contrast** - WCAG AA/AAA compliance
- **Focus indicators** - Clear visual focus states
- **Responsive behavior** - Mobile, tablet, desktop

## Implementation

This skill invokes the Python-based UI/UX Advisor agent located at:
`/Users/tmac/1_REPOS/AI_Orchestrator/agents/advisor/uiux_advisor.py`

The advisor:
1. Reads existing ADRs to check alignment
2. Analyzes UI components and flows
3. Scores confidence (pattern match + ADR + historical)
4. Auto-decides if all criteria met
5. Otherwise, presents 2-4 options for your decision

## Related

- `/app-advisor` - For architecture/API questions
- `/data-advisor` - For database/schema questions
- `aibrain ko search --tags ui,ux,accessibility` - Query Knowledge Objects
