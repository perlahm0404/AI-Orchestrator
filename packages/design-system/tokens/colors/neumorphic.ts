/**
 * Neumorphic Theme
 *
 * Soft, extruded 3D aesthetics with subtle shadows and tactile feel.
 * Designed for clean, modern interfaces with depth.
 */

export const neumorphic = {
  name: 'neumorphic' as const,

  // Primary - Soft blue
  primary: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
    950: '#082f49',
  },

  // Secondary - Soft purple
  secondary: {
    50: '#faf5ff',
    100: '#f3e8ff',
    200: '#e9d5ff',
    300: '#d8b4fe',
    400: '#c084fc',
    500: '#a855f7',
    600: '#9333ea',
    700: '#7e22ce',
    800: '#6b21a8',
    900: '#581c87',
    950: '#3b0764',
  },

  // Accent - Soft coral
  accent: {
    50: '#fff1f2',
    100: '#ffe4e6',
    200: '#fecdd3',
    300: '#fda4af',
    400: '#fb7185',
    500: '#f43f5e',
    600: '#e11d48',
    700: '#be123c',
    800: '#9f1239',
    900: '#881337',
    950: '#4c0519',
  },

  // Background - Soft gray (the canvas for neumorphic shadows)
  background: {
    DEFAULT: '#e0e5ec',
    subtle: '#e4e9f0',
    muted: '#d8dde4',
    card: '#e0e5ec',
    elevated: '#e8edf4',
    overlay: 'rgba(224, 229, 236, 0.95)',
  },

  // Dark mode variant
  backgroundDark: {
    DEFAULT: '#2d3748',
    subtle: '#323d4d',
    muted: '#283141',
    card: '#2d3748',
    elevated: '#374151',
    overlay: 'rgba(45, 55, 72, 0.95)',
  },

  // Foreground
  foreground: {
    DEFAULT: '#1e293b',
    muted: '#475569',
    subtle: '#64748b',
    accent: '#0ea5e9',
  },

  // Border
  border: {
    DEFAULT: 'rgba(163, 177, 198, 0.3)',
    subtle: 'rgba(163, 177, 198, 0.15)',
    accent: 'rgba(14, 165, 233, 0.4)',
  },

  // The defining feature: shadow system
  shadow: {
    // Light source colors
    light: '#ffffff',
    dark: '#a3b1c6',

    // Pre-computed shadow values
    raised: '8px 8px 16px #a3b1c6, -8px -8px 16px #ffffff',
    raisedSm: '4px 4px 8px #a3b1c6, -4px -4px 8px #ffffff',
    raisedLg: '12px 12px 24px #a3b1c6, -12px -12px 24px #ffffff',

    pressed: 'inset 4px 4px 8px #a3b1c6, inset -4px -4px 8px #ffffff',
    pressedSm: 'inset 2px 2px 4px #a3b1c6, inset -2px -2px 4px #ffffff',
    pressedLg: 'inset 6px 6px 12px #a3b1c6, inset -6px -6px 12px #ffffff',

    // Flat (subtle)
    flat: '2px 2px 4px #a3b1c6, -2px -2px 4px #ffffff',

    // Concave (for inputs)
    concave: 'inset 2px 2px 5px #a3b1c6, inset -2px -2px 5px #ffffff',

    // Convex (for buttons)
    convex: '3px 3px 6px #a3b1c6, -3px -3px 6px #ffffff, inset 1px 1px 2px #ffffff, inset -1px -1px 2px #a3b1c6',
  },

  // Dark mode shadows
  shadowDark: {
    light: '#3d4a5c',
    dark: '#1f2937',

    raised: '8px 8px 16px #1f2937, -8px -8px 16px #3d4a5c',
    pressed: 'inset 4px 4px 8px #1f2937, inset -4px -4px 8px #3d4a5c',
    flat: '2px 2px 4px #1f2937, -2px -2px 4px #3d4a5c',
    concave: 'inset 2px 2px 5px #1f2937, inset -2px -2px 5px #3d4a5c',
    convex: '3px 3px 6px #1f2937, -3px -3px 6px #3d4a5c, inset 1px 1px 2px #3d4a5c, inset -1px -1px 2px #1f2937',
  },

  // Semantic colors (softer versions)
  success: {
    DEFAULT: '#10b981',
    foreground: '#ecfdf5',
    shadow: '4px 4px 8px #a3b1c6, -4px -4px 8px #ffffff, 0 0 8px rgba(16, 185, 129, 0.3)',
  },
  warning: {
    DEFAULT: '#f59e0b',
    foreground: '#fffbeb',
    shadow: '4px 4px 8px #a3b1c6, -4px -4px 8px #ffffff, 0 0 8px rgba(245, 158, 11, 0.3)',
  },
  error: {
    DEFAULT: '#ef4444',
    foreground: '#fef2f2',
    shadow: '4px 4px 8px #a3b1c6, -4px -4px 8px #ffffff, 0 0 8px rgba(239, 68, 68, 0.3)',
  },
  info: {
    DEFAULT: '#0ea5e9',
    foreground: '#f0f9ff',
    shadow: '4px 4px 8px #a3b1c6, -4px -4px 8px #ffffff, 0 0 8px rgba(14, 165, 233, 0.3)',
  },
} as const;

export type NeumorphicTheme = typeof neumorphic;
