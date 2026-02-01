---
session:
  id: "20260131-1800"
  topic: "uxpilot-gemini-design-implementation"
  type: implementation-plan
  status: in-progress
  repo: cross-repo
  phase: "Phase 0 Complete - Design System Foundation"

initiated:
  timestamp: "2026-01-31T18:00:00-08:00"
  context: "Implementation plan for UX Pilot + Gemini design workflow across AI_Orchestrator, KareMatch, and CredentialMate"

governance:
  autonomy_level: L1
  human_interventions: 0
  escalations: []
---

# UX Pilot + Gemini Design System Implementation Plan

## Executive Summary

Implement a distinctive, multi-theme design system across 3 applications using:
- **Google Gemini**: AI-generated visual assets (backgrounds, illustrations, icons)
- **UX Pilot**: UI component generation with production-ready code export
- **4 Theme Styles**: Cosmic Space, Cyberpunk, Neumorphic, Futuristic Minimalistic

### Target Applications

| Application | Current Stack | Theme Implementation |
|-------------|---------------|---------------------|
| **AI_Orchestrator** | CLI-only (Python) | NEW web dashboard with theme support |
| **KareMatch** | React + Vite + Tailwind + Radix | Theme switcher + component library |
| **CredentialMate** | Next.js 14 + Tailwind + MUI | Theme switcher + component library |

---

## Phase 0: Shared Design System Foundation

### 0.1 Create Unified Design Tokens Package

**Location**: `/Users/tmac/1_REPOS/AI_Orchestrator/packages/design-system/`

```
packages/design-system/
├── tokens/
│   ├── colors/
│   │   ├── cosmic.ts        # Galaxy purples, nebula blues, starfield whites
│   │   ├── cyberpunk.ts     # Neon pink, electric blue, dark backgrounds
│   │   ├── neumorphic.ts    # Soft grays, subtle shadows, muted accents
│   │   └── futuristic.ts    # Clean whites, accent blues, minimal blacks
│   ├── typography.ts        # Font families, sizes, weights
│   ├── spacing.ts           # Consistent spacing scale
│   ├── shadows.ts           # Theme-specific shadow definitions
│   ├── animations.ts        # Framer Motion variants per theme
│   └── index.ts             # Unified export
├── components/
│   ├── primitives/          # Headless components (Button, Card, Input)
│   └── patterns/            # Composed components (Navbar, Sidebar, Hero)
├── assets/
│   ├── backgrounds/         # Gemini-generated backgrounds
│   ├── illustrations/       # Gemini-generated illustrations
│   └── icons/               # Custom icon set
├── tailwind/
│   ├── presets/
│   │   ├── cosmic.ts        # Tailwind preset for cosmic theme
│   │   ├── cyberpunk.ts
│   │   ├── neumorphic.ts
│   │   └── futuristic.ts
│   └── plugin.ts            # Custom Tailwind plugin
├── package.json
└── README.md
```

### 0.2 Theme Color Palettes

#### Cosmic Space Theme
```typescript
// packages/design-system/tokens/colors/cosmic.ts
export const cosmic = {
  // Primary - Deep space purple
  primary: {
    50: '#f5f3ff',
    100: '#ede9fe',
    500: '#8b5cf6',
    600: '#7c3aed',
    900: '#1e1b4b',
  },
  // Secondary - Nebula blue
  secondary: {
    50: '#eff6ff',
    500: '#3b82f6',
    900: '#1e3a5f',
  },
  // Accent - Starfield gold
  accent: {
    500: '#fbbf24',
    600: '#d97706',
  },
  // Background - Deep space
  background: {
    DEFAULT: '#0a0a1a',
    card: '#12122a',
    elevated: '#1a1a3a',
  },
  // Surface glow effects
  glow: {
    purple: 'rgba(139, 92, 246, 0.3)',
    blue: 'rgba(59, 130, 246, 0.3)',
    gold: 'rgba(251, 191, 36, 0.2)',
  },
};
```

#### Cyberpunk Theme
```typescript
// packages/design-system/tokens/colors/cyberpunk.ts
export const cyberpunk = {
  // Primary - Neon pink/magenta
  primary: {
    50: '#fdf2f8',
    500: '#ec4899',
    600: '#db2777',
    900: '#500724',
  },
  // Secondary - Electric cyan
  secondary: {
    50: '#ecfeff',
    500: '#06b6d4',
    900: '#083344',
  },
  // Accent - Toxic green
  accent: {
    500: '#22c55e',
    600: '#16a34a',
  },
  // Background - Dark with subtle grid
  background: {
    DEFAULT: '#0f0f0f',
    card: '#1a1a1a',
    elevated: '#252525',
  },
  // Neon glow effects
  glow: {
    pink: 'rgba(236, 72, 153, 0.5)',
    cyan: 'rgba(6, 182, 212, 0.5)',
    green: 'rgba(34, 197, 94, 0.4)',
  },
};
```

#### Neumorphic Theme
```typescript
// packages/design-system/tokens/colors/neumorphic.ts
export const neumorphic = {
  // Primary - Soft blue
  primary: {
    50: '#f0f9ff',
    500: '#0ea5e9',
    600: '#0284c7',
    900: '#0c4a6e',
  },
  // Background - Soft gray
  background: {
    DEFAULT: '#e0e5ec',
    card: '#e0e5ec',
    elevated: '#e8edf4',
  },
  // Shadows - The defining feature
  shadow: {
    light: '#ffffff',
    dark: '#a3b1c6',
    insetLight: 'inset 5px 5px 10px #a3b1c6',
    insetDark: 'inset -5px -5px 10px #ffffff',
    raised: '8px 8px 16px #a3b1c6, -8px -8px 16px #ffffff',
    pressed: 'inset 4px 4px 8px #a3b1c6, inset -4px -4px 8px #ffffff',
  },
};
```

#### Futuristic Minimalistic Theme
```typescript
// packages/design-system/tokens/colors/futuristic.ts
export const futuristic = {
  // Primary - Clean blue
  primary: {
    50: '#eff6ff',
    500: '#3b82f6',
    600: '#2563eb',
    900: '#1e3a8a',
  },
  // Background - Pure whites and subtle grays
  background: {
    DEFAULT: '#ffffff',
    card: '#f8fafc',
    elevated: '#ffffff',
    dark: '#0f172a',
  },
  // Accent - Minimal gradient
  accent: {
    gradient: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
  },
  // Borders - Hairline precision
  border: {
    subtle: '#e2e8f0',
    accent: '#3b82f6',
  },
};
```

---

## Phase 1: AI_Orchestrator Web Dashboard (NEW)

### 1.1 Architecture

Create a new Next.js 14 App Router dashboard for the orchestrator.

**Location**: `/Users/tmac/1_REPOS/AI_Orchestrator/apps/dashboard/`

```
apps/dashboard/
├── app/
│   ├── layout.tsx           # Root layout with theme provider
│   ├── page.tsx             # Dashboard home
│   ├── agents/
│   │   ├── page.tsx         # Agent monitoring
│   │   └── [id]/page.tsx    # Agent detail
│   ├── tasks/
│   │   ├── page.tsx         # Task queue
│   │   └── [id]/page.tsx    # Task detail
│   ├── knowledge/
│   │   └── page.tsx         # Knowledge Objects browser
│   ├── settings/
│   │   └── page.tsx         # Theme selection + config
│   └── api/
│       └── [...slug]/       # API routes to Python backend
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   └── ThemeSwitcher.tsx
│   ├── agents/
│   │   ├── AgentCard.tsx
│   │   ├── AgentStatus.tsx
│   │   └── AgentMetrics.tsx
│   ├── tasks/
│   │   ├── TaskList.tsx
│   │   ├── TaskItem.tsx
│   │   └── TaskKanban.tsx
│   └── ui/                  # Themed components
├── lib/
│   ├── api.ts              # API client
│   ├── theme.ts            # Theme context
│   └── socket.ts           # WebSocket for real-time updates
├── package.json
├── tailwind.config.ts
└── next.config.js
```

### 1.2 Theme Implementation

```typescript
// apps/dashboard/lib/theme.ts
import { cosmic, cyberpunk, neumorphic, futuristic } from '@ai-orchestrator/design-system';

export type ThemeName = 'cosmic' | 'cyberpunk' | 'neumorphic' | 'futuristic';

export const themes = {
  cosmic,
  cyberpunk,
  neumorphic,
  futuristic,
} as const;

// Theme context with persistence
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<ThemeName>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('theme') as ThemeName) || 'cosmic';
    }
    return 'cosmic';
  });

  // Apply CSS variables based on theme
  useEffect(() => {
    const root = document.documentElement;
    const colors = themes[theme];

    Object.entries(colors).forEach(([category, values]) => {
      if (typeof values === 'object') {
        Object.entries(values).forEach(([shade, color]) => {
          root.style.setProperty(`--${category}-${shade}`, color);
        });
      }
    });

    localStorage.setItem('theme', theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

### 1.3 Key Dashboard Pages

#### Agent Monitoring (Cosmic Theme Example)
```tsx
// apps/dashboard/app/agents/page.tsx
export default function AgentsPage() {
  const agents = useAgents();

  return (
    <div className="min-h-screen bg-background">
      {/* Cosmic starfield background */}
      <div className="fixed inset-0 bg-[url('/assets/starfield.svg')] opacity-20" />

      <main className="relative z-10 p-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary-500 to-secondary-500 bg-clip-text text-transparent">
          Agent Fleet
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
          {agents.map(agent => (
            <AgentCard
              key={agent.id}
              agent={agent}
              className="backdrop-blur-xl bg-background-card/50 border border-glow-purple/20 shadow-lg shadow-glow-purple/10"
            />
          ))}
        </div>
      </main>
    </div>
  );
}
```

---

## Phase 2: KareMatch Theme Integration

### 2.1 Install Design System

```bash
cd /Users/tmac/1_REPOS/karematch
pnpm add @ai-orchestrator/design-system@workspace:*
```

### 2.2 Update Tailwind Config

```typescript
// web/tailwind.config.ts
import { cosmicPreset, cyberpunkPreset, neumorphicPreset, futuristicPreset } from '@ai-orchestrator/design-system/tailwind';

export default {
  presets: [cosmicPreset], // Default theme
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      // Theme-specific extensions
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@ai-orchestrator/design-system/tailwind/plugin'),
  ],
};
```

### 2.3 Theme Switcher Component

```tsx
// web/src/components/ThemeSwitcher.tsx
import { useTheme, ThemeName } from '@ai-orchestrator/design-system';
import { motion } from 'framer-motion';

const themeIcons = {
  cosmic: '🌌',
  cyberpunk: '🌆',
  neumorphic: '💿',
  futuristic: '⚡',
};

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex gap-2 p-2 rounded-full bg-background-card">
      {(Object.keys(themeIcons) as ThemeName[]).map((t) => (
        <motion.button
          key={t}
          onClick={() => setTheme(t)}
          className={`w-10 h-10 rounded-full flex items-center justify-center ${
            theme === t ? 'bg-primary-500 shadow-lg' : 'hover:bg-background-elevated'
          }`}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          {themeIcons[t]}
        </motion.button>
      ))}
    </div>
  );
}
```

### 2.4 Component Updates

Update existing shadcn/radix components to use theme tokens:

```tsx
// web/src/components/ui/button.tsx
import { cva } from 'class-variance-authority';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md transition-all',
  {
    variants: {
      variant: {
        default: 'bg-primary-500 text-white hover:bg-primary-600 shadow-lg shadow-glow-purple/20',
        outline: 'border-2 border-primary-500 text-primary-500 hover:bg-primary-500/10',
        ghost: 'hover:bg-background-elevated',
        // Theme-adaptive cyber variant
        cyber: 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white hover:shadow-glow-pink/50 hover:shadow-lg',
        // Neumorphic variant
        soft: 'bg-background shadow-raised hover:shadow-pressed active:shadow-pressed',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4',
        lg: 'h-12 px-6 text-lg',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);
```

---

## Phase 3: CredentialMate Theme Integration

### 3.1 MUI Theme Override

CredentialMate uses MUI, so we need to create theme overrides:

```typescript
// apps/frontend-web/lib/theme/mui-themes.ts
import { createTheme, ThemeOptions } from '@mui/material/styles';
import { cosmic, cyberpunk, neumorphic, futuristic } from '@ai-orchestrator/design-system';

function createMuiTheme(tokens: typeof cosmic): ThemeOptions {
  return {
    palette: {
      mode: tokens.background.DEFAULT === '#ffffff' ? 'light' : 'dark',
      primary: {
        main: tokens.primary[500],
        light: tokens.primary[50],
        dark: tokens.primary[900],
      },
      secondary: {
        main: tokens.secondary?.[500] || tokens.primary[500],
      },
      background: {
        default: tokens.background.DEFAULT,
        paper: tokens.background.card,
      },
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: 8,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundColor: tokens.background.card,
            borderRadius: 16,
            boxShadow: tokens.shadow?.raised || '0 4px 12px rgba(0,0,0,0.1)',
          },
        },
      },
    },
  };
}

export const muiThemes = {
  cosmic: createTheme(createMuiTheme(cosmic)),
  cyberpunk: createTheme(createMuiTheme(cyberpunk)),
  neumorphic: createTheme(createMuiTheme(neumorphic)),
  futuristic: createTheme(createMuiTheme(futuristic)),
};
```

### 3.2 Storybook Theme Stories

```typescript
// apps/frontend-web/.storybook/preview.tsx
import { ThemeProvider } from '@mui/material';
import { muiThemes } from '../lib/theme/mui-themes';

export const decorators = [
  (Story, context) => {
    const theme = context.globals.theme || 'cosmic';
    return (
      <ThemeProvider theme={muiThemes[theme]}>
        <Story />
      </ThemeProvider>
    );
  },
];

export const globalTypes = {
  theme: {
    name: 'Theme',
    description: 'Global theme for components',
    defaultValue: 'cosmic',
    toolbar: {
      icon: 'paintbrush',
      items: ['cosmic', 'cyberpunk', 'neumorphic', 'futuristic'],
    },
  },
};
```

---

## Phase 4: Gemini Asset Generation Workflow

### 4.1 Asset Generation Scripts

```python
# packages/design-system/scripts/generate_assets.py
"""
Gemini Asset Generation Pipeline

Generates theme-specific visual assets:
- Backgrounds (SVG patterns, gradients)
- Illustrations (abstract shapes, icons)
- Hero images (marketing pages)
"""

import google.generativeai as genai
from pathlib import Path
import json

THEMES = {
    'cosmic': {
        'prompt_prefix': 'Deep space, galaxy, nebula, stars, purple and blue gradients, cosmic energy',
        'style': 'ethereal, mysterious, vast, glowing',
    },
    'cyberpunk': {
        'prompt_prefix': 'Neon lights, dark city, digital grid, holographic, pink and cyan',
        'style': 'futuristic, gritty, electric, glitch effects',
    },
    'neumorphic': {
        'prompt_prefix': 'Soft shadows, 3D extrusion, minimal, grayscale with subtle color',
        'style': 'clean, tactile, soft, rounded',
    },
    'futuristic': {
        'prompt_prefix': 'Minimal, clean lines, geometric, white space, accent blue',
        'style': 'modern, precise, elegant, tech-forward',
    },
}

def generate_background(theme: str, variant: str):
    """Generate a background pattern/image for the specified theme."""
    config = THEMES[theme]

    prompt = f"""
    Create a seamless background pattern for a web application.
    Theme: {theme}
    Style: {config['style']}
    Elements: {config['prompt_prefix']}
    Variant: {variant}

    The image should be:
    - Suitable for tiling or as a full-page background
    - Not too busy (should not distract from content)
    - High quality, modern aesthetic
    """

    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content([prompt])

    # Save to assets directory
    output_path = Path(f'packages/design-system/assets/backgrounds/{theme}/{variant}.png')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Process and save image...
    return output_path
```

### 4.2 Asset Categories

| Category | Cosmic | Cyberpunk | Neumorphic | Futuristic |
|----------|--------|-----------|------------|------------|
| **Backgrounds** | Starfield, Nebula, Galaxy | Grid, Circuit, Neon City | Soft gradient, Subtle pattern | Minimal gradient, Clean lines |
| **Icons** | Glowing, Ethereal | Neon, Glitch | Soft 3D, Rounded | Geometric, Precise |
| **Illustrations** | Space objects, Planets | Tech, Holograms | Abstract shapes | Minimal line art |
| **Hero Images** | Cosmic vista | Cityscape, Tech | Soft abstracts | Clean tech |

### 4.3 Generated Asset Structure

```
packages/design-system/assets/
├── backgrounds/
│   ├── cosmic/
│   │   ├── starfield-01.svg
│   │   ├── nebula-gradient.css
│   │   └── galaxy-pattern.png
│   ├── cyberpunk/
│   │   ├── grid-lines.svg
│   │   ├── neon-glow.css
│   │   └── circuit-pattern.png
│   ├── neumorphic/
│   │   ├── soft-gradient.css
│   │   └── subtle-texture.png
│   └── futuristic/
│       ├── minimal-gradient.css
│       └── geometric-pattern.svg
├── illustrations/
│   ├── cosmic/
│   ├── cyberpunk/
│   ├── neumorphic/
│   └── futuristic/
└── icons/
    ├── cosmic/
    ├── cyberpunk/
    ├── neumorphic/
    └── futuristic/
```

---

## Phase 5: UX Pilot Integration Workflow

### 5.1 UX Pilot Component Generation Process

1. **Open UX Pilot** (uxpilot.ai or similar)
2. **Select theme style** (Cosmic/Cyberpunk/Neumorphic/Futuristic)
3. **Describe component** in natural language
4. **Generate design** with "Deep Design" mode
5. **Export code** (HTML/CSS/Tailwind)
6. **Convert to React** component
7. **Add to design system** package

### 5.2 Component Generation Prompts

```markdown
# UX Pilot Prompts by Theme

## Cosmic Theme Components

### Navigation Bar
"Create a navigation bar with cosmic space theme. Deep purple gradient background,
subtle star particles, glowing hover effects, transparent glass-morphism style.
Include logo area, nav links, and user avatar with cosmic glow ring."

### Dashboard Card
"Design a dashboard metric card with cosmic theme. Dark background with subtle
nebula pattern, glowing border accent, large number display with gradient text,
label below in muted purple. Add subtle hover animation that intensifies glow."

### Data Table
"Create a data table for cosmic space theme. Dark rows with alternating subtle
transparency, header row with purple gradient, hover state with cosmic glow,
column sorting indicators as small star icons."

## Cyberpunk Theme Components

### Navigation Bar
"Create a cyberpunk navigation bar. Black background with neon pink and cyan
accents, glitch effect on hover, scanline overlay, digital font. Include
hamburger menu that animates with electric effect."

### Dashboard Card
"Design a cyberpunk metric card. Dark background with circuit pattern, neon
border that pulses, holographic number display, digital readout style. Add
glitch animation on data update."

### Data Table
"Create a cyberpunk data table. Dark rows with grid line overlay, neon pink
headers, cyan accent on selection, hover state with scan line effect."

## Neumorphic Theme Components

### Navigation Bar
"Create a neumorphic navigation bar. Soft gray background with extruded shadow
effect, pressed button states, subtle rounded corners, minimal icons with
soft shadows."

### Dashboard Card
"Design a neumorphic metric card. Soft extruded effect from background,
inset number display area, subtle gradient, pill-shaped action button with
pressed state."

### Data Table
"Create a neumorphic data table. Soft raised header row, inset data cells,
subtle row shadows, gentle hover state with shadow shift."

## Futuristic Minimalistic Components

### Navigation Bar
"Create a futuristic minimal navigation bar. Pure white background, single
accent color (blue) for active state, hairline borders, clean sans-serif
font, subtle hover animations."

### Dashboard Card
"Design a minimal futuristic metric card. White background, thin border,
large clean number, minimal label, single accent color for trend indicator,
micro-animation on hover."

### Data Table
"Create a minimal futuristic data table. Clean white background, subtle
gray borders, blue accent for selection, clean typography, minimal hover
state."
```

### 5.3 Code Conversion Pipeline

```typescript
// packages/design-system/scripts/convert-uxpilot.ts
/**
 * Converts UX Pilot exported HTML/CSS to React components
 */

import { parse } from 'node-html-parser';
import { transform } from '@swc/core';

interface ConvertOptions {
  theme: 'cosmic' | 'cyberpunk' | 'neumorphic' | 'futuristic';
  componentName: string;
  htmlPath: string;
  cssPath: string;
}

async function convertToReact(options: ConvertOptions) {
  // 1. Parse HTML structure
  const html = await Bun.file(options.htmlPath).text();
  const root = parse(html);

  // 2. Extract Tailwind classes
  const classes = extractTailwindClasses(root);

  // 3. Convert to JSX
  const jsx = htmlToJsx(root);

  // 4. Generate component
  const component = `
    import { cn } from '@/lib/utils';
    import { motion } from 'framer-motion';

    export interface ${options.componentName}Props {
      className?: string;
      // Add extracted props...
    }

    export function ${options.componentName}({ className, ...props }: ${options.componentName}Props) {
      return (
        <motion.div
          className={cn('${classes}', className)}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          {...props}
        >
          ${jsx}
        </motion.div>
      );
    }
  `;

  // 5. Write to design system
  const outputPath = `packages/design-system/components/${options.theme}/${options.componentName}.tsx`;
  await Bun.write(outputPath, component);

  return outputPath;
}
```

---

## Phase 6: Implementation Roadmap

### Week 1: Foundation
- [ ] Create `packages/design-system/` structure
- [ ] Define color tokens for all 4 themes
- [ ] Create Tailwind presets
- [ ] Set up asset directories

### Week 2: AI_Orchestrator Dashboard
- [ ] Scaffold Next.js 14 app in `apps/dashboard/`
- [ ] Implement theme provider and context
- [ ] Create layout components (Sidebar, Header)
- [ ] Build theme switcher UI

### Week 3: Gemini Asset Generation
- [ ] Set up Gemini API integration
- [ ] Generate background assets for all themes
- [ ] Create icon variants
- [ ] Build illustration library

### Week 4: UX Pilot Component Library
- [ ] Generate core components per theme (Button, Card, Input, Table)
- [ ] Convert to React components
- [ ] Add to design system package
- [ ] Document in Storybook

### Week 5: KareMatch Integration
- [ ] Install design system package
- [ ] Update Tailwind config
- [ ] Add theme switcher to settings
- [ ] Update key components to use theme tokens

### Week 6: CredentialMate Integration
- [ ] Create MUI theme overrides
- [ ] Add theme provider wrapper
- [ ] Update Storybook configuration
- [ ] Migrate key pages to themed components

### Week 7: Polish & Documentation
- [ ] Cross-browser testing
- [ ] Accessibility audit (contrast ratios per theme)
- [ ] Performance optimization (lazy-load theme assets)
- [ ] Documentation and usage guides

---

## Technical Decisions

### 1. CSS Variables vs. Tailwind Classes

**Decision**: Use CSS variables at runtime, Tailwind for build-time.

```css
/* Runtime theme switching via CSS variables */
:root[data-theme="cosmic"] {
  --primary-500: #8b5cf6;
  --background: #0a0a1a;
}

:root[data-theme="cyberpunk"] {
  --primary-500: #ec4899;
  --background: #0f0f0f;
}
```

```tsx
// Tailwind references CSS variables
<button className="bg-[var(--primary-500)]">Click</button>
```

### 2. Theme Persistence

**Decision**: LocalStorage with SSR fallback.

```typescript
// Server: Read from cookie
// Client: Read from localStorage, sync to cookie
```

### 3. Animation Library

**Decision**: Framer Motion (already in both KareMatch and CredentialMate).

```typescript
// Theme-specific animation variants
const cosmicVariants = {
  hover: { scale: 1.02, boxShadow: '0 0 20px rgba(139, 92, 246, 0.5)' },
};

const cyberpunkVariants = {
  hover: { x: [0, -2, 2, 0], transition: { duration: 0.2 } }, // Glitch
};
```

### 4. Asset Delivery

**Decision**: CDN-hosted with lazy loading.

```tsx
// Lazy load theme backgrounds
const CosmicBackground = dynamic(() => import('./backgrounds/Cosmic'), {
  loading: () => <div className="bg-background" />,
});
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Theme switching performance | Medium | Medium | CSS variables + will-change hints |
| Cross-app token sync | Low | High | Single source of truth in design-system package |
| Gemini API rate limits | Medium | Low | Cache generated assets, batch generation |
| UX Pilot code quality | Medium | Medium | Manual review + conversion pipeline |
| Accessibility per theme | High | High | WCAG 2.1 AA testing per theme, contrast audits |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Theme switch latency | < 100ms |
| Lighthouse Performance | > 90 (all themes) |
| Accessibility Score | 100% WCAG 2.1 AA |
| Component coverage | 20+ themed components |
| Asset library size | 50+ Gemini-generated assets |

---

## Files to Create

| File | Purpose |
|------|---------|
| `packages/design-system/package.json` | Design system package config |
| `packages/design-system/tokens/colors/*.ts` | Theme color definitions |
| `packages/design-system/tailwind/presets/*.ts` | Tailwind presets per theme |
| `apps/dashboard/package.json` | New dashboard app config |
| `apps/dashboard/app/layout.tsx` | Root layout with theme provider |
| `apps/dashboard/lib/theme.ts` | Theme context and utilities |
| `karematch/web/tailwind.config.ts` | Updated with theme presets |
| `credentialmate/apps/frontend-web/lib/theme/mui-themes.ts` | MUI theme overrides |

---

## Next Steps

1. **Approve this plan** - Review and confirm scope
2. **Create design-system package** - Start with tokens
3. **Generate sample assets** - Test Gemini workflow
4. **Build dashboard scaffold** - Next.js app structure
5. **Integrate with KareMatch first** - Lower risk, React-native stack

---

## Session Notes

**Status**: Planning complete, awaiting approval

**Questions for Human Review**:
1. Should AI_Orchestrator dashboard be hosted separately or as part of orchestrator repo?
2. Priority order for themes (which to implement first)?
3. Should we use existing Smooth UI components or generate fresh with UX Pilot?
4. Gemini API access - do you have an API key set up?
