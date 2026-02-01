/**
 * Neumorphic Theme - Tailwind Preset
 *
 * Soft, extruded 3D aesthetics with subtle shadows and tactile feel.
 */

import type { Config } from 'tailwindcss';
import { neumorphic } from '../../tokens/colors/neumorphic';
import { typography, themeTypography } from '../../tokens/typography';
import { themeBorderRadius } from '../../tokens/spacing';
import { keyframes } from '../../tokens/animations';

export const neumorphicPreset: Partial<Config> = {
  theme: {
    extend: {
      colors: {
        // Primary palette
        primary: neumorphic.primary,
        secondary: neumorphic.secondary,
        accent: neumorphic.accent,

        // Background (light mode)
        background: neumorphic.background.DEFAULT,
        'background-subtle': neumorphic.background.subtle,
        'background-muted': neumorphic.background.muted,
        'background-card': neumorphic.background.card,
        'background-elevated': neumorphic.background.elevated,

        // Foreground
        foreground: neumorphic.foreground.DEFAULT,
        'foreground-muted': neumorphic.foreground.muted,
        'foreground-subtle': neumorphic.foreground.subtle,
        'foreground-accent': neumorphic.foreground.accent,

        // Border
        border: neumorphic.border.DEFAULT,
        'border-subtle': neumorphic.border.subtle,
        'border-accent': neumorphic.border.accent,

        // Shadow colors
        'shadow-light': neumorphic.shadow.light,
        'shadow-dark': neumorphic.shadow.dark,

        // Semantic
        success: neumorphic.success.DEFAULT,
        warning: neumorphic.warning.DEFAULT,
        error: neumorphic.error.DEFAULT,
        info: neumorphic.info.DEFAULT,
      },

      fontFamily: {
        sans: typography.fontFamily.sans,
        mono: typography.fontFamily.mono,
        display: themeTypography.neumorphic.display,
      },

      borderRadius: {
        DEFAULT: themeBorderRadius.neumorphic.DEFAULT,
        lg: themeBorderRadius.neumorphic.lg,
        xl: themeBorderRadius.neumorphic.xl,
      },

      boxShadow: {
        // Raised effects (default state)
        'neu': neumorphic.shadow.raised,
        'neu-sm': neumorphic.shadow.raisedSm,
        'neu-lg': neumorphic.shadow.raisedLg,

        // Pressed effects (active/clicked state)
        'neu-pressed': neumorphic.shadow.pressed,
        'neu-pressed-sm': neumorphic.shadow.pressedSm,
        'neu-pressed-lg': neumorphic.shadow.pressedLg,

        // Flat effect
        'neu-flat': neumorphic.shadow.flat,

        // Concave (for inputs)
        'neu-concave': neumorphic.shadow.concave,

        // Convex (for buttons)
        'neu-convex': neumorphic.shadow.convex,

        // Semantic shadows
        'neu-success': neumorphic.success.shadow,
        'neu-warning': neumorphic.warning.shadow,
        'neu-error': neumorphic.error.shadow,
        'neu-info': neumorphic.info.shadow,
      },

      backgroundImage: {
        'neu-gradient': `linear-gradient(145deg, ${neumorphic.background.elevated}, ${neumorphic.background.muted})`,
        'neu-subtle': `linear-gradient(145deg, ${neumorphic.background.subtle}, ${neumorphic.background.DEFAULT})`,
      },

      animation: {
        'soft-pulse': 'softPulse 3s ease-in-out infinite',
        'breathe': 'breathe 4s ease-in-out infinite',
      },

      keyframes: {
        softPulse: keyframes.neumorphic.softPulse,
        breathe: keyframes.neumorphic.breathe,
      },
    },
  },
};

export default neumorphicPreset;
