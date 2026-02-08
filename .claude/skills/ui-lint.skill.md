# UI Lint

**Command**: `/ui-lint`

**Description**: Automated UI/UX analysis with design token validation, accessibility auditing, and performance pattern detection

## What This Does

Runs comprehensive automated analysis on UI code to detect:

1. **Design Token Violations** - Raw hex colors, inline styles, non-standard spacing
2. **Accessibility Issues** - WCAG 2.1 AA/AAA compliance, ARIA, keyboard navigation
3. **Layout Problems** - Grid alignment (4/8px), responsive breakpoint consistency
4. **Performance Anti-patterns** - Missing memoization, virtualization opportunities
5. **Component Library Drift** - Deviations from established design system

## Capabilities

### Design Token Analysis
```
Detects:
- Raw hex colors (#fff, #3b82f6) instead of tokens (bg-white, text-blue-500)
- Inline styles that should use Tailwind classes
- Magic numbers for spacing (padding: 13px vs p-3)
- Non-standard font sizes outside the type scale
- Hardcoded z-index values

Severity:
- CRITICAL: Raw colors in semantic contexts (error, success, warning)
- WARNING: Inline styles that have token equivalents
- INFO: Suggestions for better token usage
```

### Accessibility Audit (WCAG 2.1)
```
Checks:
- Color contrast ratios (4.5:1 text, 3:1 large text, 3:1 UI components)
- Missing alt text on images
- Form labels not associated with inputs
- Missing ARIA labels on interactive elements
- Keyboard navigation gaps (tabindex, focus management)
- Focus indicator visibility
- Heading hierarchy (h1 → h2 → h3, no skips)
- Link text quality ("click here" → descriptive text)

Tools:
- axe-core patterns
- Pa11y rule matching
- Manual heuristics for React/Vue patterns
```

### Layout Grid Compliance
```
Validates:
- 4px/8px spacing grid adherence
- Consistent breakpoint usage (sm/md/lg/xl/2xl)
- Container max-widths
- Flex/Grid gap consistency
- Touch target sizes (44x44px minimum)
```

### Performance Pattern Detection
```
Flags:
- Large component trees without React.memo
- Lists without virtualization (>50 items)
- Inline function definitions in JSX props
- Missing useCallback/useMemo for expensive operations
- Non-lazy-loaded routes/components
- Unoptimized images (missing next/image, no srcset)
```

### Component Library Drift
```
Compares against:
- Registered component variants
- Prop type conformance
- Styling pattern consistency
- Naming convention adherence
```

## Usage

```bash
# Lint current file
/ui-lint

# Lint specific file
/ui-lint src/components/Dashboard.tsx

# Lint directory
/ui-lint src/components/

# Lint with specific checks only
/ui-lint --checks accessibility,tokens

# Lint with autofix suggestions
/ui-lint --fix

# Generate report
/ui-lint --report markdown
```

## Output Format

### Terminal (Default)
```
UI LINT REPORT
══════════════════════════════════════════════════════════

src/components/Dashboard.tsx
  ✗ [CRITICAL] Line 24: Raw hex color #ef4444 - use text-red-500
  ✗ [CRITICAL] Line 31: Missing alt text on <img>
  ⚠ [WARNING] Line 45: Inline style could use Tailwind class
  ⚠ [WARNING] Line 67: List with 120 items - consider virtualization
  ℹ [INFO] Line 89: Consider React.memo for UserCard component

Summary: 2 critical, 2 warnings, 1 info
Score: 72/100 (target: 85+)
```

### Markdown Report
```markdown
# UI Lint Report

**File**: src/components/Dashboard.tsx
**Score**: 72/100
**Status**: NEEDS WORK

## Critical Issues (2)
| Line | Issue | Suggestion |
|------|-------|------------|
| 24 | Raw hex color #ef4444 | Use `text-red-500` |
| 31 | Missing alt text | Add descriptive alt attribute |

## Warnings (2)
...

## Recommendations
1. Replace all raw colors with design tokens
2. Add virtualization for large lists
3. Wrap expensive components in React.memo
```

## Configuration

Create `.ui-lint.yaml` in project root:

```yaml
# .ui-lint.yaml
rules:
  tokens:
    severity: critical
    allow-raw-colors: false
    spacing-grid: 4  # 4px grid

  accessibility:
    severity: critical
    wcag-level: AA  # or AAA
    require-alt-text: true
    require-labels: true
    min-contrast: 4.5

  layout:
    severity: warning
    breakpoints: [sm, md, lg, xl, 2xl]
    container-max: 1280
    touch-target-min: 44

  performance:
    severity: warning
    virtualization-threshold: 50
    require-memo-above: 100  # lines

  drift:
    severity: info
    component-library: ./src/components/ui/

ignore:
  - "**/*.test.tsx"
  - "**/storybook/**"
```

## Integration with Design System

### Tailwind Config Analysis
```
Reads tailwind.config.js to:
- Extract custom color tokens
- Validate spacing scale usage
- Check breakpoint consistency
- Verify font family definitions
```

### Component Library Matching
```
If component-library path is set:
- Compares component props against definitions
- Flags variant misuse
- Suggests correct component for pattern
```

## Scoring

| Category | Weight | Max Points |
|----------|--------|------------|
| Design Tokens | 25% | 25 |
| Accessibility | 35% | 35 |
| Layout | 15% | 15 |
| Performance | 15% | 15 |
| Consistency | 10% | 10 |

**Thresholds**:
- 85+: PASS (ready for review)
- 70-84: NEEDS WORK (minor issues)
- <70: FAIL (critical issues must be fixed)

## Autofix Support

Some issues can be auto-fixed:

```bash
/ui-lint --fix
```

**Auto-fixable**:
- Raw hex colors → Tailwind tokens (if exact match exists)
- Missing key props on lists
- Simple inline styles → Tailwind classes
- Import sorting

**Manual fix required**:
- Alt text (needs human description)
- Complex accessibility issues
- Performance refactoring
- Layout restructuring

## CI/CD Integration

```yaml
# .github/workflows/ui-lint.yml
- name: UI Lint
  run: |
    aibrain ui-lint src/components/ --report json > lint-report.json
    if [ $(jq '.score' lint-report.json) -lt 85 ]; then
      exit 1
    fi
```

## Related

- `/ui-design` - Opinionated design direction guidance
- `/ui-scaffold` - Generate components from patterns
- `/code-review` - Full code review including UI aspects
- `aibrain ko search --tags ui,accessibility,tokens` - Query UI patterns
