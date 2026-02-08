# UI

**Command**: `/ui`

**Description**: Unified UI workflow - design direction → component scaffold → lint validation in one command

## What This Does

Orchestrates the complete UI development workflow for new features:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│  1. DESIGN  │ ──► │  2. SCAFFOLD │ ──► │  3. LINT    │ ──► │  OUTPUT  │
│  Direction  │     │  Components  │     │  Validate   │     │  Ready!  │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
```

**Phase 1 - Design Direction**: Establish aesthetic, colors, typography
**Phase 2 - Scaffold**: Generate components matching the design
**Phase 3 - Lint**: Validate accessibility, tokens, performance

## Usage

```bash
# Full workflow for new feature
/ui "filterable data table for user management"

# With explicit design direction
/ui "notification center" --direction neo-corporate

# With specific patterns
/ui "multi-step onboarding" --patterns form_wizard,modal_form

# Skip design phase (use existing direction)
/ui "settings panel" --skip-design

# Just design + scaffold (skip lint)
/ui "dashboard widgets" --skip-lint
```

## Workflow Phases

### Phase 1: Design Direction

**Asks**:
1. What is this feature for? (context)
2. Who is the user? (audience)
3. What aesthetic fits? (direction)

**Outputs**:
- Chosen aesthetic direction (Brutalist, Neo-Corporate, Playful, etc.)
- Color tokens for the feature
- Typography scale
- Spacing/layout guidelines

**Example Output**:
```markdown
## Design Direction: Neo-Corporate

**Context**: User management data table for B2B SaaS
**Audience**: Admin users who need efficiency over delight

**Colors**:
- Primary: slate-900 (headers, primary actions)
- Accent: blue-600 (links, selected states)
- Surface: white/slate-50 (cards, rows)
- Border: slate-200

**Typography**:
- Table headers: text-xs font-medium uppercase tracking-wide
- Table cells: text-sm
- Actions: text-sm font-medium

**Spacing**:
- Cell padding: px-4 py-3
- Row gap: border-b border-slate-100
- Section gap: space-y-6
```

### Phase 2: Component Scaffold

**Based on Phase 1**, generates:
- Component files with CVA variants
- TypeScript interfaces
- Accessibility built-in
- Storybook stories (optional)

**Pattern Selection**:
Maps your feature description to optimal patterns:

| Feature Description | Patterns Used |
|---------------------|---------------|
| "data table" | `data_table_filterable` |
| "form wizard" | `form_wizard`, `modal_form` |
| "dashboard" | `status_dashboard`, `stat_card` |
| "settings" | `settings_panel`, `toggle` |
| "notifications" | `notification_center`, `toast` |
| "navigation" | `sidebar_nav`, `breadcrumb` |
| "search" | `command_palette`, `search_autocomplete` |

### Phase 3: Lint Validation

**Runs all checks**:
- ✅ Design tokens (no raw colors)
- ✅ Accessibility (WCAG 2.1 AA)
- ✅ Performance (memo, virtualization)
- ✅ Anti-AI-slop (no generic patterns)

**Outputs score and issues**:
```
UI LINT: 92/100 ✓

✓ Design Tokens: 100/100
✓ Accessibility: 95/100
  ⚠ Line 45: Consider aria-describedby for complex table
✓ Performance: 85/100
  ⚠ Line 89: Table with 100+ rows - add virtualization
✓ Anti-Slop: 90/100
  ✓ No generic fonts
  ✓ No purple gradients
  ✓ Intentional spacing rhythm
```

## Complete Example

**Input**:
```bash
/ui "user management table with filters, bulk actions, and pagination"
```

**Phase 1 Output**:
```markdown
## Design Direction: Technical/Dashboard

For admin efficiency, using:
- Dense information display
- Monospace for IDs/emails
- Subtle row hover states
- Keyboard-first interactions

Colors: slate palette with blue-600 accent
Typography: Inter for UI, JetBrains Mono for data
```

**Phase 2 Output**:
```
Generated 6 files:

src/components/users/
├── index.ts
├── users-table.tsx        (main component)
├── users-table.types.ts   (TypeScript types)
├── table-filters.tsx      (search, status filter)
├── table-pagination.tsx   (page controls)
├── bulk-actions.tsx       (select all, delete, export)
└── users-table.stories.tsx
```

**Phase 3 Output**:
```
UI LINT: 94/100 ✓ PASS

All checks passed. Ready for review.
```

## Options

| Flag | Description |
|------|-------------|
| `--direction <name>` | Pre-select aesthetic (brutalist, neo-corporate, playful, editorial, technical, organic) |
| `--patterns <list>` | Specify scaffold patterns |
| `--skip-design` | Use existing design direction from project |
| `--skip-lint` | Skip validation phase |
| `--output <path>` | Output directory (default: inferred from feature) |
| `--no-stories` | Skip Storybook story generation |
| `--dry-run` | Show plan without generating files |

## Integration with Existing Design System

If project has established tokens:

```bash
# Reads from tailwind.config.ts
/ui "feature" --use-existing-tokens

# Reads from design-tokens.json
/ui "feature" --tokens ./design-tokens.json
```

The scaffold phase will use your existing:
- Color palette
- Typography scale
- Spacing system
- Border radius values
- Shadow definitions

## Autonomy

- **Auto-decides**: Pattern selection, component structure, file organization
- **Asks you**: Design direction (unless `--direction` specified), major layout decisions
- **Always validates**: Accessibility, token usage, performance

## Output Structure

```
src/components/{feature}/
├── index.ts                 # Barrel export
├── {feature}.tsx           # Main component
├── {feature}.types.ts      # TypeScript types
├── {sub-component}.tsx     # Sub-components
├── use-{feature}.ts        # Custom hooks (if needed)
└── {feature}.stories.tsx   # Storybook (unless --no-stories)
```

## Related Skills

- `/ui-design` - Design phase only
- `/ui-scaffold` - Scaffold phase only
- `/ui-lint` - Lint phase only
- `/code-review` - Full code review after UI complete

## Examples

```bash
# E-commerce product grid
/ui "product catalog with filters and infinite scroll" --direction playful

# Admin dashboard
/ui "analytics dashboard with KPI cards and charts" --direction technical

# User onboarding
/ui "3-step signup wizard with validation" --patterns form_wizard

# Settings page
/ui "account settings with profile, security, notifications tabs"

# Quick scaffold with existing design
/ui "delete confirmation modal" --skip-design --patterns modal_form
```
