/**
 * Futuristic Minimalistic Theme
 *
 * Clean, modern aesthetics with precise lines and strategic use of accent colors.
 * Designed for professional, tech-forward interfaces.
 */

export const futuristic = {
  name: 'futuristic' as const,

  // Primary - Clean blue
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
    950: '#172554',
  },

  // Secondary - Slate gray
  secondary: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
    950: '#020617',
  },

  // Accent - Vibrant violet (for key actions)
  accent: {
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
    950: '#2e1065',
  },

  // Background - Pure and clean
  background: {
    DEFAULT: '#ffffff',
    subtle: '#fafafa',
    muted: '#f5f5f5',
    card: '#ffffff',
    elevated: '#ffffff',
    overlay: 'rgba(255, 255, 255, 0.9)',
  },

  // Dark mode variant
  backgroundDark: {
    DEFAULT: '#0a0a0a',
    subtle: '#0f0f0f',
    muted: '#171717',
    card: '#141414',
    elevated: '#1a1a1a',
    overlay: 'rgba(10, 10, 10, 0.95)',
  },

  // Foreground
  foreground: {
    DEFAULT: '#0f172a',
    muted: '#475569',
    subtle: '#94a3b8',
    accent: '#3b82f6',
  },

  // Dark mode foreground
  foregroundDark: {
    DEFAULT: '#fafafa',
    muted: '#a1a1aa',
    subtle: '#71717a',
    accent: '#60a5fa',
  },

  // Border - Hairline precision
  border: {
    DEFAULT: '#e5e7eb',
    subtle: '#f3f4f6',
    accent: '#3b82f6',
    focus: '#2563eb',
  },

  // Dark mode borders
  borderDark: {
    DEFAULT: '#27272a',
    subtle: '#1f1f23',
    accent: '#3b82f6',
    focus: '#60a5fa',
  },

  // Gradients
  gradient: {
    primary: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
    subtle: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
    accent: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
    dark: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
  },

  // Shadows - Subtle and precise
  shadow: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
    accent: '0 4px 14px 0 rgba(59, 130, 246, 0.15)',
    accentLg: '0 8px 24px 0 rgba(59, 130, 246, 0.2)',
  },

  // Semantic colors
  success: {
    DEFAULT: '#22c55e',
    foreground: '#f0fdf4',
    border: '#bbf7d0',
  },
  warning: {
    DEFAULT: '#f59e0b',
    foreground: '#fffbeb',
    border: '#fde68a',
  },
  error: {
    DEFAULT: '#ef4444',
    foreground: '#fef2f2',
    border: '#fecaca',
  },
  info: {
    DEFAULT: '#3b82f6',
    foreground: '#eff6ff',
    border: '#bfdbfe',
  },

  // Animation tokens
  animation: {
    fast: '150ms',
    normal: '250ms',
    slow: '400ms',
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easingIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easingOut: 'cubic-bezier(0, 0, 0.2, 1)',
  },
} as const;

export type FuturisticTheme = typeof futuristic;
