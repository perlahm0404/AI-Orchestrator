/**
 * Spacing Tokens
 *
 * Consistent spacing scale based on 4px base unit.
 */

export const spacing = {
  // Base spacing scale (px values as rem)
  px: '1px',
  0: '0',
  0.5: '0.125rem',  // 2px
  1: '0.25rem',     // 4px
  1.5: '0.375rem',  // 6px
  2: '0.5rem',      // 8px
  2.5: '0.625rem',  // 10px
  3: '0.75rem',     // 12px
  3.5: '0.875rem',  // 14px
  4: '1rem',        // 16px
  5: '1.25rem',     // 20px
  6: '1.5rem',      // 24px
  7: '1.75rem',     // 28px
  8: '2rem',        // 32px
  9: '2.25rem',     // 36px
  10: '2.5rem',     // 40px
  11: '2.75rem',    // 44px
  12: '3rem',       // 48px
  14: '3.5rem',     // 56px
  16: '4rem',       // 64px
  20: '5rem',       // 80px
  24: '6rem',       // 96px
  28: '7rem',       // 112px
  32: '8rem',       // 128px
  36: '9rem',       // 144px
  40: '10rem',      // 160px
  44: '11rem',      // 176px
  48: '12rem',      // 192px
  52: '13rem',      // 208px
  56: '14rem',      // 224px
  60: '15rem',      // 240px
  64: '16rem',      // 256px
  72: '18rem',      // 288px
  80: '20rem',      // 320px
  96: '24rem',      // 384px
} as const;

// Semantic spacing
export const semanticSpacing = {
  // Component internal spacing
  component: {
    xs: spacing[1],    // 4px - tight spacing
    sm: spacing[2],    // 8px - compact
    md: spacing[4],    // 16px - default
    lg: spacing[6],    // 24px - relaxed
    xl: spacing[8],    // 32px - spacious
  },

  // Section spacing
  section: {
    sm: spacing[8],    // 32px
    md: spacing[16],   // 64px
    lg: spacing[24],   // 96px
    xl: spacing[32],   // 128px
  },

  // Page margins
  page: {
    mobile: spacing[4],   // 16px
    tablet: spacing[8],   // 32px
    desktop: spacing[16], // 64px
  },

  // Gap sizes
  gap: {
    xs: spacing[1],    // 4px
    sm: spacing[2],    // 8px
    md: spacing[4],    // 16px
    lg: spacing[6],    // 24px
    xl: spacing[8],    // 32px
  },
} as const;

// Border radius
export const borderRadius = {
  none: '0',
  sm: '0.125rem',     // 2px
  DEFAULT: '0.25rem', // 4px
  md: '0.375rem',     // 6px
  lg: '0.5rem',       // 8px
  xl: '0.75rem',      // 12px
  '2xl': '1rem',      // 16px
  '3xl': '1.5rem',    // 24px
  full: '9999px',
} as const;

// Theme-specific border radius overrides
export const themeBorderRadius = {
  cosmic: {
    DEFAULT: '0.75rem',  // Slightly more rounded
    lg: '1rem',
    xl: '1.5rem',
  },
  cyberpunk: {
    DEFAULT: '0.125rem', // Sharp, angular
    lg: '0.25rem',
    xl: '0.5rem',
  },
  neumorphic: {
    DEFAULT: '1rem',     // Soft, rounded
    lg: '1.5rem',
    xl: '2rem',
  },
  futuristic: {
    DEFAULT: '0.5rem',   // Clean, precise
    lg: '0.75rem',
    xl: '1rem',
  },
} as const;

export type Spacing = typeof spacing;
export type BorderRadius = typeof borderRadius;
