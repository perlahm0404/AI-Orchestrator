# AI Orchestrator Design System

Multi-theme design system with **Cosmic**, **Cyberpunk**, **Neumorphic**, and **Futuristic** styles.

## Installation

```bash
# From the monorepo root
pnpm add @ai-orchestrator/design-system@workspace:*

# Or if published to npm
npm install @ai-orchestrator/design-system
```

## Quick Start

### 1. Add Tailwind Preset

```typescript
// tailwind.config.ts
import { cosmicPreset } from '@ai-orchestrator/design-system/tailwind';

export default {
  presets: [cosmicPreset],
  content: ['./src/**/*.{ts,tsx}'],
  // ... your config
};
```

### 2. Wrap with Theme Provider

```tsx
// app/layout.tsx or _app.tsx
import { ThemeProvider } from '@ai-orchestrator/design-system';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <ThemeProvider defaultTheme="cosmic">
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
```

### 3. Use Theme-Aware Components

```tsx
import { useTheme, cn } from '@ai-orchestrator/design-system';

function Button({ className, children, ...props }) {
  const { theme } = useTheme();

  return (
    <button
      className={cn(
        'px-4 py-2 rounded-lg transition-all',
        'bg-primary-500 text-white hover:bg-primary-600',
        'shadow-glow hover:shadow-glow-lg',
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
```

## Available Themes

| Theme | Description | Best For |
|-------|-------------|----------|
| **Cosmic** | Galaxy purples, nebula blues, starfield accents | Immersive, ethereal experiences |
| **Cyberpunk** | Neon pinks, electric cyans, dark grids | High-energy, futuristic interfaces |
| **Neumorphic** | Soft shadows, extruded 3D, tactile feel | Clean, modern, tactile UIs |
| **Futuristic** | Clean lines, minimal, precise | Professional, tech-forward apps |

## Theme Switching

```tsx
import { useTheme } from '@ai-orchestrator/design-system';

function ThemeSwitcher() {
  const { theme, setTheme, availableThemes } = useTheme();

  return (
    <select value={theme} onChange={(e) => setTheme(e.target.value)}>
      {availableThemes.map((t) => (
        <option key={t} value={t}>{t}</option>
      ))}
    </select>
  );
}
```

## Color Tokens

Each theme provides a consistent color API:

```typescript
import { cosmic, cyberpunk, neumorphic, futuristic } from '@ai-orchestrator/design-system/tokens';

// All themes have:
cosmic.primary[500]      // Primary color
cosmic.secondary[500]    // Secondary color
cosmic.accent[500]       // Accent color
cosmic.background.DEFAULT // Background
cosmic.foreground.DEFAULT // Text color
cosmic.glow.purple       // Theme-specific effects
```

## Tailwind Classes

### Cosmic Theme
```html
<div class="bg-background text-foreground">
  <button class="bg-primary-500 shadow-glow hover:shadow-cosmic">
    Cosmic Button
  </button>
</div>
```

### Cyberpunk Theme
```html
<div class="bg-background text-foreground">
  <button class="bg-neon-pink shadow-neon-pink animate-glitch">
    Cyber Button
  </button>
</div>
```

### Neumorphic Theme
```html
<div class="bg-background">
  <button class="shadow-neu hover:shadow-neu-lg active:shadow-neu-pressed">
    Soft Button
  </button>
</div>
```

### Futuristic Theme
```html
<div class="bg-background text-foreground">
  <button class="bg-gradient-primary shadow-accent hover:shadow-accent-lg">
    Modern Button
  </button>
</div>
```

## Animation Variants (Framer Motion)

```tsx
import { motion } from 'framer-motion';
import { motionVariants } from '@ai-orchestrator/design-system/tokens';

function CosmicCard({ children }) {
  return (
    <motion.div
      variants={motionVariants.cosmic.fadeIn}
      initial="initial"
      animate="animate"
      whileHover={motionVariants.cosmic.hover}
    >
      {children}
    </motion.div>
  );
}
```

## Utility Functions

```typescript
import { cn, hexWithAlpha, meetsContrastAA } from '@ai-orchestrator/design-system';

// Merge Tailwind classes intelligently
cn('bg-red-500', 'bg-blue-500') // → 'bg-blue-500'

// Add alpha to hex color
hexWithAlpha('#8b5cf6', 0.5) // → 'rgba(139, 92, 246, 0.5)'

// Check accessibility contrast
meetsContrastAA('#ffffff', '#000000') // → true
```

## Project Structure

```
packages/design-system/
├── tokens/
│   ├── colors/
│   │   ├── cosmic.ts
│   │   ├── cyberpunk.ts
│   │   ├── neumorphic.ts
│   │   └── futuristic.ts
│   ├── typography.ts
│   ├── spacing.ts
│   └── animations.ts
├── tailwind/
│   └── presets/
│       ├── cosmic.ts
│       ├── cyberpunk.ts
│       ├── neumorphic.ts
│       └── futuristic.ts
├── lib/
│   ├── utils.ts
│   └── theme-context.tsx
├── components/
│   ├── primitives/
│   └── patterns/
└── assets/
    ├── backgrounds/
    ├── illustrations/
    └── icons/
```

## Building

```bash
# Development (watch mode)
pnpm dev

# Production build
pnpm build

# Type check
pnpm type-check
```

## License

MIT
