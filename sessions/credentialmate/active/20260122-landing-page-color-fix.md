# Landing Page Brand Color Alignment Plan

**Date**: 2026-01-22
**Status**: Planning
**Target**: CredentialMate Landing Page

## Problem Assessment

The landing page colors do not match the brand colors of the logo and icon.

### Brand Colors (from logo/icon analysis)

| Element | Color | Hex |
|---------|-------|-----|
| Hexagon frame | Dark Teal | `#1D5550` - `#205854` |
| **Accent chevron** | **Lime Green** | **`#84CC16` - `#7CB342`** |
| Title "Credential" | Dark Forest Green | ~`#2E5847` |
| Title "Mate" | Medium Green | ~`#4CAF50` |

### Current Accent Color (MISMATCH)

The Tailwind config defines:
- `brand-accent`: `#D97706` (Amber/Orange)
- `gradient-accent`: Amber gradient

**This amber/orange does NOT appear anywhere in the logo.**

The logo uses **lime green** as its accent color, but the landing page uses **amber/orange** for CTAs and accents.

## Visual Evidence

| Element | Current | Should Be |
|---------|---------|-----------|
| "Start Free Trial" button | Orange `#D97706` | Lime Green `#84CC16` |
| "No credit card" text | Amber | Lime Green |
| Bell/Calendar icons | Amber | Lime Green |
| "elevated" gradient text | Amber gradient | Lime Green gradient |

## Files to Modify

### 1. `apps/frontend-web/tailwind.config.ts` (lines 61-66, 115)

Update brand accent colors:

```typescript
// BEFORE
accent: {
  DEFAULT: '#D97706', // Amber 600
  light: '#FBBF24',
  dark: '#B45309',
  foreground: '#FFFFFF',
},

// AFTER
accent: {
  DEFAULT: '#84CC16', // Lime 500 (matches logo chevron)
  light: '#A3E635',   // Lime 400
  dark: '#65A30D',    // Lime 600
  foreground: '#FFFFFF',
},
```

Update gradient (line 115):

```typescript
// BEFORE
'gradient-accent': 'linear-gradient(135deg, #F59E0B, #FCD34D)',

// AFTER
'gradient-accent': 'linear-gradient(135deg, #84CC16, #BEF264)',
```

### 2. `apps/frontend-web/src/app/page.tsx` (line 264)

Update hardcoded amber reference:

```tsx
// BEFORE (line 264)
<div className="w-14 h-14 mb-6 rounded-2xl bg-amber-50 text-amber-600 ...">

// AFTER
<div className="w-14 h-14 mb-6 rounded-2xl bg-lime-50 text-lime-600 ...">
```

### 3. `apps/frontend-web/src/styles/globals.css`

Update CSS variables for brand-accent:

```css
/* BEFORE */
--brand-accent: 38 92% 50%;  /* Amber */

/* AFTER */
--brand-accent: 84 81% 44%;  /* Lime 500 */
```

### 4. `assets/ux/design_tokens.json`

Update accent colors from amber to lime for design token consistency.

## Implementation Steps

1. Update `tailwind.config.ts` - change accent from amber to lime green
2. Update `page.tsx` - replace hardcoded amber class (line 264)
3. Update `globals.css` - update CSS variables
4. Update `design_tokens.json` - change accent palette
5. Verify all pages render correctly
6. Test in browser to confirm visual alignment with logo

## Color Reference

### Lime Green Palette (Tailwind)
- `lime-50`: `#F7FEE7`
- `lime-100`: `#ECFCCB`
- `lime-200`: `#D9F99D`
- `lime-300`: `#BEF264`
- `lime-400`: `#A3E635`
- `lime-500`: `#84CC16` ← **Primary accent**
- `lime-600`: `#65A30D`
- `lime-700`: `#4D7C0F`
- `lime-800`: `#3F6212`
- `lime-900`: `#365314`

## Expected Result

After changes, the landing page will use:
- **Dark teal** for primary backgrounds and text (already correct)
- **Lime green** for CTA buttons, accent text, and highlights (matching logo chevron)

This creates visual harmony between the logo/icon and the page design.
