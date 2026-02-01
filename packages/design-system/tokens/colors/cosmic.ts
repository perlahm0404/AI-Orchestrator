/**
 * Cosmic Space Theme
 *
 * Deep space aesthetics with galaxy purples, nebula blues, and starfield accents.
 * Designed for immersive, ethereal experiences.
 */

export const cosmic = {
  name: 'cosmic' as const,

  // Primary - Deep space purple
  primary: {
    50: '#f5f3ff',
    100: '#ede9fe',
    200: '#ddd6fe',
    300: '#c4b5fd',
    400: '#a78bfa',
    500: '#8b5cf6',
    600: '#7c3aed',
    700: '#6d28d9',
    800: '#5b21b6',
    900: '#4c1d95',
    950: '#1e1b4b',
  },

  // Secondary - Nebula blue
  secondary: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a5f',
    950: '#172554',
  },

  // Accent - Starfield gold
  accent: {
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

  // Background - Deep space
  background: {
    DEFAULT: '#0a0a1a',
    subtle: '#0d0d22',
    muted: '#12122a',
    card: '#151530',
    elevated: '#1a1a3a',
    overlay: 'rgba(10, 10, 26, 0.8)',
  },

  // Foreground - Star white
  foreground: {
    DEFAULT: '#f8fafc',
    muted: '#94a3b8',
    subtle: '#64748b',
    accent: '#c4b5fd',
  },

  // Border
  border: {
    DEFAULT: 'rgba(139, 92, 246, 0.2)',
    subtle: 'rgba(139, 92, 246, 0.1)',
    accent: 'rgba(139, 92, 246, 0.4)',
    glow: 'rgba(139, 92, 246, 0.6)',
  },

  // Surface glow effects
  glow: {
    purple: 'rgba(139, 92, 246, 0.3)',
    blue: 'rgba(59, 130, 246, 0.3)',
    gold: 'rgba(251, 191, 36, 0.2)',
    white: 'rgba(248, 250, 252, 0.1)',
  },

  // Semantic colors
  success: {
    DEFAULT: '#22c55e',
    foreground: '#f0fdf4',
    glow: 'rgba(34, 197, 94, 0.3)',
  },
  warning: {
    DEFAULT: '#f59e0b',
    foreground: '#fffbeb',
    glow: 'rgba(245, 158, 11, 0.3)',
  },
  error: {
    DEFAULT: '#ef4444',
    foreground: '#fef2f2',
    glow: 'rgba(239, 68, 68, 0.3)',
  },
  info: {
    DEFAULT: '#3b82f6',
    foreground: '#eff6ff',
    glow: 'rgba(59, 130, 246, 0.3)',
  },
} as const;

export type CosmicTheme = typeof cosmic;
