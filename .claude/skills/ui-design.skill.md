# UI Design

**Command**: `/ui-design`

**Description**: Opinionated design guidance with anti-AI-slop patterns, aesthetic direction, and production-grade design systems

## What This Does

Provides **intentional, distinctive design direction** that avoids generic AI-generated aesthetics:

1. **Anti-AI-Slop Enforcement** - Rejects overused patterns that signal low-effort AI output
2. **Aesthetic Direction Selection** - Forces commitment to a bold design philosophy
3. **Typography System** - Intentional font pairing beyond default stacks
4. **Color System Generation** - Accessible, cohesive palettes with semantic meaning
5. **Dark Mode Strategy** - Proper theme architecture, not just color inversion

## Anti-AI-Slop Patterns

### What Gets Flagged

```
TYPOGRAPHY VIOLATIONS:
✗ Inter, Roboto, Arial as primary fonts (overused defaults)
✗ Single font family for everything
✗ Generic font-weight: 400/700 only
✗ Line-height: 1.5 everywhere (lazy default)

COLOR VIOLATIONS:
✗ Purple-to-blue gradients (AI signature)
✗ Generic blue (#3b82f6) as primary without justification
✗ Gray-on-white with no personality
✗ Rainbow gradients for "vibrancy"
✗ Neon accent colors without purpose

LAYOUT VIOLATIONS:
✗ Everything centered (no visual hierarchy)
✗ Uniform padding/margins (no rhythm)
✗ Cards with identical border-radius everywhere
✗ Excessive whitespace without intention
✗ Grid of identical cards as default layout

COMPONENT VIOLATIONS:
✗ Rounded-full buttons for everything
✗ Gradient backgrounds on CTAs
✗ Drop shadows with identical blur/spread
✗ Hover: scale(1.05) on everything
✗ Generic "Get Started" / "Learn More" button text
```

### What Gets Encouraged

```
TYPOGRAPHY:
✓ Display font + body font pairing (e.g., Clash Display + Satoshi)
✓ Variable fonts with optical sizing
✓ Intentional line-height per context (headings tighter, body looser)
✓ Letter-spacing adjustments for large text

COLOR:
✓ Limited palette with purpose (3-5 colors max)
✓ One dominant color, strategic accents
✓ Semantic colors tied to meaning (not decoration)
✓ Custom palette derived from brand/product

LAYOUT:
✓ Asymmetry with purpose
✓ Grid-breaking elements for emphasis
✓ Varied spacing rhythm (4px, 8px, 16px, 32px, 64px)
✓ Whitespace as design element, not filler

MOTION:
✓ Meaningful animations that guide attention
✓ Staggered reveals for lists
✓ Micro-interactions that provide feedback
✓ prefers-reduced-motion respect
```

## Aesthetic Directions

When invoked, you must **commit to a direction** before implementation:

### 1. Brutalist
```
Characteristics:
- Raw, unpolished aesthetic
- System fonts or monospace
- High contrast black/white
- Visible borders, no rounded corners
- Dense information display
- Anti-decoration

Use when:
- Developer tools
- Data-heavy dashboards
- Technical documentation
- "Honest" brand positioning
```

### 2. Neo-Corporate
```
Characteristics:
- Clean but not sterile
- Subtle gradients, refined shadows
- Professional typography (e.g., Graphik, Söhne)
- Muted accent colors
- Generous whitespace
- Subtle motion

Use when:
- B2B SaaS products
- Financial applications
- Enterprise tools
- Trust-building required
```

### 3. Playful/Friendly
```
Characteristics:
- Rounded shapes, soft corners
- Warm color palette
- Illustrated elements
- Bouncy animations
- Conversational microcopy
- Generous sizing

Use when:
- Consumer apps
- Onboarding flows
- Children's products
- Stress-reducing tools
```

### 4. Editorial/Magazine
```
Characteristics:
- Strong typography hierarchy
- Serif headlines, sans body
- Large imagery with purpose
- Column-based layouts
- Dramatic whitespace
- Refined details

Use when:
- Content platforms
- Media/publishing
- Portfolio sites
- Luxury positioning
```

### 5. Technical/Dashboard
```
Characteristics:
- Information density
- Monospace for data
- Dark mode default
- Subtle color coding
- Compact components
- Keyboard-first

Use when:
- Analytics dashboards
- Admin panels
- Developer tools
- Real-time monitoring
```

### 6. Organic/Natural
```
Characteristics:
- Earthy color palette
- Texture and grain
- Irregular shapes
- Hand-drawn elements
- Warm, muted tones
- Sustainable aesthetics

Use when:
- Wellness apps
- Sustainability products
- Food/agriculture
- Nature-connected brands
```

## Usage

```bash
# Get design direction for new project
/ui-design new --context "B2B analytics dashboard for marketing teams"

# Analyze existing design
/ui-design analyze src/components/

# Generate color system
/ui-design colors --direction neo-corporate --primary "#1a1a2e"

# Generate typography system
/ui-design typography --direction editorial

# Check for AI-slop patterns
/ui-design slop-check src/

# Generate dark mode strategy
/ui-design dark-mode --existing-tokens tailwind.config.ts
```

## Output: Design Direction Document

When starting a new project or major redesign:

```markdown
# Design Direction: [Project Name]

## Chosen Aesthetic: Neo-Corporate

### Rationale
This B2B analytics platform serves marketing directors who need to
trust the data. Neo-corporate signals professionalism while avoiding
the coldness of pure brutalist design.

## Typography System

### Font Stack
- **Headlines**: Söhne Bold (or fallback: system-ui bold)
- **Body**: Inter (yes, we're using it—but with intention)
- **Data/Code**: JetBrains Mono

### Scale (Major Third - 1.250)
| Name | Size | Weight | Line Height | Letter Spacing |
|------|------|--------|-------------|----------------|
| display-lg | 48px | 700 | 1.1 | -0.02em |
| display | 36px | 700 | 1.15 | -0.015em |
| h1 | 30px | 600 | 1.2 | -0.01em |
| h2 | 24px | 600 | 1.25 | 0 |
| h3 | 20px | 600 | 1.3 | 0 |
| body-lg | 18px | 400 | 1.6 | 0 |
| body | 16px | 400 | 1.6 | 0 |
| small | 14px | 400 | 1.5 | 0.01em |
| caption | 12px | 500 | 1.4 | 0.02em |

## Color System

### Semantic Tokens
| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| --color-surface | #ffffff | #0f0f10 | Base background |
| --color-surface-raised | #f8f9fa | #1a1a1c | Cards, modals |
| --color-surface-sunken | #f1f3f5 | #0a0a0b | Input backgrounds |
| --color-border | #e9ecef | #2a2a2e | Dividers, outlines |
| --color-text-primary | #1a1a2e | #f8f9fa | Headlines, body |
| --color-text-secondary | #6c757d | #a1a1aa | Supporting text |
| --color-text-muted | #adb5bd | #6c6c72 | Disabled, hints |
| --color-accent | #2563eb | #3b82f6 | CTAs, links |
| --color-success | #059669 | #10b981 | Positive states |
| --color-warning | #d97706 | #f59e0b | Caution states |
| --color-error | #dc2626 | #ef4444 | Error states |

### Accent Usage Rules
- Primary accent: CTA buttons, active states, links
- Never use accent for large background areas
- Accent-on-accent forbidden (use white/black text)
- Gradient only in hero sections, never on components

## Spacing System

### Scale (8px base)
| Token | Value | Usage |
|-------|-------|-------|
| --space-0 | 0 | Reset |
| --space-1 | 4px | Tight inline spacing |
| --space-2 | 8px | Icon gaps, compact padding |
| --space-3 | 12px | Button padding-y |
| --space-4 | 16px | Card padding, standard gap |
| --space-5 | 24px | Section padding |
| --space-6 | 32px | Large gaps |
| --space-8 | 48px | Section margins |
| --space-10 | 64px | Page sections |
| --space-12 | 96px | Hero spacing |

## Component Guidelines

### Buttons
- Border-radius: 6px (not rounded-full)
- Padding: 12px 20px (medium), 8px 16px (small)
- Font-weight: 500
- No gradient backgrounds
- Hover: darken 10%, no scale transform
- Focus: 2px offset ring in accent color

### Cards
- Border-radius: 8px
- Border: 1px solid var(--color-border)
- Shadow: 0 1px 3px rgba(0,0,0,0.1) (light), none (dark)
- Padding: 24px

### Inputs
- Height: 40px (medium), 32px (small)
- Border-radius: 6px
- Border: 1px solid var(--color-border)
- Focus: accent border, no shadow glow

## Motion Guidelines

### Timing
| Type | Duration | Easing |
|------|----------|--------|
| Micro (hover, focus) | 150ms | ease-out |
| Small (dropdowns) | 200ms | ease-in-out |
| Medium (modals) | 300ms | ease-out |
| Large (page transitions) | 400ms | ease-in-out |

### Principles
- Enter: fade + slight upward motion
- Exit: fade only (faster than enter)
- Stagger: 50ms between list items
- Never animate layout properties (use transform)
- Always respect prefers-reduced-motion
```

## Dark Mode Strategy

```markdown
## Dark Mode Implementation

### Approach: Semantic Tokens + CSS Variables

1. Define semantic tokens, not color values
2. Swap token values based on [data-theme="dark"]
3. Never invert colors mathematically

### Color Adjustments
| Light | Dark | Reasoning |
|-------|------|-----------|
| White bg | Not pure black | #0f0f10 reduces eye strain |
| Black text | Not pure white | #f8f9fa is softer |
| Saturated accent | Slightly desaturated | Prevents vibration |
| Subtle shadows | No shadows | Shadows invisible on dark |
| Light borders | Lighter borders | Increase contrast |

### Implementation
\`\`\`css
:root {
  --color-bg: #ffffff;
  --color-text: #1a1a2e;
}

[data-theme="dark"] {
  --color-bg: #0f0f10;
  --color-text: #f8f9fa;
}
\`\`\`

### Toggle Behavior
- Respect system preference initially
- Allow manual override
- Persist preference in localStorage
- Transition: 200ms on color properties only
```

## Autonomy

- **Auto-decides** when: Tactical styling choices within established direction
- **Must escalate** when: New aesthetic direction, breaking changes, brand decisions

## Related

- `/ui-lint` - Automated analysis and violation detection
- `/ui-scaffold` - Generate components following this direction
- `/code-review` - Full review including design adherence
