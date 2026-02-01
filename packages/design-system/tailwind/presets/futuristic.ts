/**
 * Futuristic Minimalistic Theme - Tailwind Preset
 *
 * Clean, modern aesthetics with precise lines and strategic use of accent colors.
 */

import type { Config } from 'tailwindcss';
import { futuristic } from '../../tokens/colors/futuristic';
import { typography, themeTypography } from '../../tokens/typography';
import { themeBorderRadius } from '../../tokens/spacing';
import { keyframes } from '../../tokens/animations';

export const futuristicPreset: Partial<Config> = {
  theme: {
    extend: {
      colors: {
        // Primary palette
        primary: futuristic.primary,
        secondary: futuristic.secondary,
        accent: futuristic.accent,

        // Background (light mode)
        background: futuristic.background.DEFAULT,
        'background-subtle': futuristic.background.subtle,
        'background-muted': futuristic.background.muted,
        'background-card': futuristic.background.card,
        'background-elevated': futuristic.background.elevated,

        // Dark mode backgrounds
        'background-dark': futuristic.backgroundDark.DEFAULT,
        'background-dark-subtle': futuristic.backgroundDark.subtle,
        'background-dark-muted': futuristic.backgroundDark.muted,
        'background-dark-card': futuristic.backgroundDark.card,
        'background-dark-elevated': futuristic.backgroundDark.elevated,

        // Foreground
        foreground: futuristic.foreground.DEFAULT,
        'foreground-muted': futuristic.foreground.muted,
        'foreground-subtle': futuristic.foreground.subtle,
        'foreground-accent': futuristic.foreground.accent,

        // Border
        border: futuristic.border.DEFAULT,
        'border-subtle': futuristic.border.subtle,
        'border-accent': futuristic.border.accent,
        'border-focus': futuristic.border.focus,

        // Semantic
        success: futuristic.success.DEFAULT,
        'success-foreground': futuristic.success.foreground,
        'success-border': futuristic.success.border,

        warning: futuristic.warning.DEFAULT,
        'warning-foreground': futuristic.warning.foreground,
        'warning-border': futuristic.warning.border,

        error: futuristic.error.DEFAULT,
        'error-foreground': futuristic.error.foreground,
        'error-border': futuristic.error.border,

        info: futuristic.info.DEFAULT,
        'info-foreground': futuristic.info.foreground,
        'info-border': futuristic.info.border,
      },

      fontFamily: {
        sans: typography.fontFamily.sans,
        mono: typography.fontFamily.mono,
        display: themeTypography.futuristic.display,
      },

      borderRadius: {
        DEFAULT: themeBorderRadius.futuristic.DEFAULT,
        lg: themeBorderRadius.futuristic.lg,
        xl: themeBorderRadius.futuristic.xl,
      },

      boxShadow: {
        'sm': futuristic.shadow.sm,
        'DEFAULT': futuristic.shadow.DEFAULT,
        'md': futuristic.shadow.md,
        'lg': futuristic.shadow.lg,
        'xl': futuristic.shadow.xl,
        'inner': futuristic.shadow.inner,
        'accent': futuristic.shadow.accent,
        'accent-lg': futuristic.shadow.accentLg,
      },

      backgroundImage: {
        'gradient-primary': futuristic.gradient.primary,
        'gradient-subtle': futuristic.gradient.subtle,
        'gradient-accent': futuristic.gradient.accent,
        'gradient-dark': futuristic.gradient.dark,
      },

      animation: {
        'border-glow': 'borderGlow 2s ease-in-out infinite',
        'subtle-pulse': 'subtlePulse 2s ease-in-out infinite',
        'slide-up': 'slideUp 0.3s ease-out',
      },

      keyframes: {
        borderGlow: keyframes.futuristic.borderGlow,
        subtlePulse: keyframes.futuristic.subtlePulse,
        slideUp: keyframes.futuristic.slideUp,
      },

      transitionDuration: {
        'fast': futuristic.animation.fast,
        'normal': futuristic.animation.normal,
        'slow': futuristic.animation.slow,
      },

      transitionTimingFunction: {
        'default': futuristic.animation.easing,
        'in': futuristic.animation.easingIn,
        'out': futuristic.animation.easingOut,
      },
    },
  },
};

export default futuristicPreset;
