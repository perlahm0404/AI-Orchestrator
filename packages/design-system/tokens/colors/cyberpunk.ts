/**
 * Cyberpunk Theme
 *
 * Neon-drenched aesthetics with electric pinks, cyans, and dark urban grids.
 * Designed for high-energy, futuristic interfaces.
 */

export const cyberpunk = {
  name: 'cyberpunk' as const,

  // Primary - Neon pink/magenta
  primary: {
    50: '#fdf2f8',
    100: '#fce7f3',
    200: '#fbcfe8',
    300: '#f9a8d4',
    400: '#f472b6',
    500: '#ec4899',
    600: '#db2777',
    700: '#be185d',
    800: '#9d174d',
    900: '#831843',
    950: '#500724',
  },

  // Secondary - Electric cyan
  secondary: {
    50: '#ecfeff',
    100: '#cffafe',
    200: '#a5f3fc',
    300: '#67e8f9',
    400: '#22d3ee',
    500: '#06b6d4',
    600: '#0891b2',
    700: '#0e7490',
    800: '#155e75',
    900: '#164e63',
    950: '#083344',
  },

  // Accent - Toxic green
  accent: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
    950: '#052e16',
  },

  // Tertiary - Warning yellow/orange
  tertiary: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
    950: '#451a03',
  },

  // Background - Dark urban
  background: {
    DEFAULT: '#0a0a0a',
    subtle: '#0f0f0f',
    muted: '#141414',
    card: '#1a1a1a',
    elevated: '#252525',
    overlay: 'rgba(10, 10, 10, 0.9)',
  },

  // Foreground
  foreground: {
    DEFAULT: '#fafafa',
    muted: '#a1a1aa',
    subtle: '#71717a',
    accent: '#f472b6',
  },

  // Border
  border: {
    DEFAULT: 'rgba(236, 72, 153, 0.2)',
    subtle: 'rgba(236, 72, 153, 0.1)',
    accent: 'rgba(6, 182, 212, 0.4)',
    glow: 'rgba(236, 72, 153, 0.6)',
  },

  // Neon glow effects
  glow: {
    pink: 'rgba(236, 72, 153, 0.5)',
    cyan: 'rgba(6, 182, 212, 0.5)',
    green: 'rgba(34, 197, 94, 0.4)',
    yellow: 'rgba(251, 191, 36, 0.4)',
    white: 'rgba(250, 250, 250, 0.15)',
  },

  // Semantic colors
  success: {
    DEFAULT: '#22c55e',
    foreground: '#f0fdf4',
    glow: 'rgba(34, 197, 94, 0.5)',
  },
  warning: {
    DEFAULT: '#f59e0b',
    foreground: '#fffbeb',
    glow: 'rgba(245, 158, 11, 0.5)',
  },
  error: {
    DEFAULT: '#ef4444',
    foreground: '#fef2f2',
    glow: 'rgba(239, 68, 68, 0.5)',
  },
  info: {
    DEFAULT: '#06b6d4',
    foreground: '#ecfeff',
    glow: 'rgba(6, 182, 212, 0.5)',
  },

  // Special effects
  effects: {
    scanline: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 0, 0, 0.1) 2px, rgba(0, 0, 0, 0.1) 4px)',
    grid: 'linear-gradient(rgba(236, 72, 153, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(236, 72, 153, 0.03) 1px, transparent 1px)',
    noise: 'url("data:image/svg+xml,%3Csvg viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noise"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noise)" opacity="0.03"/%3E%3C/svg%3E")',
  },
} as const;

export type CyberpunkTheme = typeof cyberpunk;
