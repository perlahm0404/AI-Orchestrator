/**
 * Cyberpunk Theme - Tailwind Preset
 *
 * Neon-drenched aesthetics with electric pinks, cyans, and dark urban grids.
 */

import type { Config } from 'tailwindcss';
import { cyberpunk } from '../../tokens/colors/cyberpunk';
import { typography, themeTypography } from '../../tokens/typography';
import { themeBorderRadius } from '../../tokens/spacing';
import { keyframes } from '../../tokens/animations';

export const cyberpunkPreset: Partial<Config> = {
  theme: {
    extend: {
      colors: {
        // Primary palette
        primary: cyberpunk.primary,
        secondary: cyberpunk.secondary,
        accent: cyberpunk.accent,
        tertiary: cyberpunk.tertiary,

        // Background
        background: cyberpunk.background.DEFAULT,
        'background-subtle': cyberpunk.background.subtle,
        'background-muted': cyberpunk.background.muted,
        'background-card': cyberpunk.background.card,
        'background-elevated': cyberpunk.background.elevated,

        // Foreground
        foreground: cyberpunk.foreground.DEFAULT,
        'foreground-muted': cyberpunk.foreground.muted,
        'foreground-subtle': cyberpunk.foreground.subtle,
        'foreground-accent': cyberpunk.foreground.accent,

        // Border
        border: cyberpunk.border.DEFAULT,
        'border-subtle': cyberpunk.border.subtle,
        'border-accent': cyberpunk.border.accent,
        'border-glow': cyberpunk.border.glow,

        // Semantic
        success: cyberpunk.success.DEFAULT,
        warning: cyberpunk.warning.DEFAULT,
        error: cyberpunk.error.DEFAULT,
        info: cyberpunk.info.DEFAULT,

        // Neon colors
        'neon-pink': cyberpunk.primary[500],
        'neon-cyan': cyberpunk.secondary[500],
        'neon-green': cyberpunk.accent[500],
        'neon-yellow': cyberpunk.tertiary[500],
      },

      fontFamily: {
        sans: typography.fontFamily.sans,
        mono: themeTypography.cyberpunk.mono,
        display: themeTypography.cyberpunk.display,
      },

      borderRadius: {
        DEFAULT: themeBorderRadius.cyberpunk.DEFAULT,
        lg: themeBorderRadius.cyberpunk.lg,
        xl: themeBorderRadius.cyberpunk.xl,
      },

      boxShadow: {
        'neon-pink': `0 0 10px ${cyberpunk.glow.pink}, 0 0 20px ${cyberpunk.glow.pink}`,
        'neon-cyan': `0 0 10px ${cyberpunk.glow.cyan}, 0 0 20px ${cyberpunk.glow.cyan}`,
        'neon-green': `0 0 10px ${cyberpunk.glow.green}, 0 0 20px ${cyberpunk.glow.green}`,
        'neon-mixed': `0 0 15px ${cyberpunk.glow.pink}, 0 0 30px ${cyberpunk.glow.cyan}`,
        'glow-sm': `0 0 8px ${cyberpunk.glow.pink}`,
        'glow': `0 0 15px ${cyberpunk.glow.pink}, 0 0 30px ${cyberpunk.glow.cyan}`,
        'glow-lg': `0 0 20px ${cyberpunk.glow.pink}, 0 0 40px ${cyberpunk.glow.cyan}, 0 0 60px ${cyberpunk.glow.pink}`,
      },

      backgroundImage: {
        'cyber-gradient': `linear-gradient(135deg, ${cyberpunk.primary[900]} 0%, ${cyberpunk.background.DEFAULT} 50%, ${cyberpunk.secondary[900]} 100%)`,
        'cyber-grid': cyberpunk.effects.grid,
        'scanlines': cyberpunk.effects.scanline,
        'noise': cyberpunk.effects.noise,
        'neon-stripe': `repeating-linear-gradient(
          90deg,
          transparent,
          transparent 10px,
          ${cyberpunk.glow.pink} 10px,
          ${cyberpunk.glow.pink} 11px
        )`,
      },

      animation: {
        'glitch': 'glitch 0.3s ease-in-out infinite',
        'neon-pulse': 'neonPulse 2s ease-in-out infinite',
        'scanline': 'scanline 8s linear infinite',
        'flicker': 'flicker 0.15s ease-in-out infinite',
      },

      keyframes: {
        glitch: keyframes.cyberpunk.glitch,
        neonPulse: keyframes.cyberpunk.neonPulse,
        scanline: keyframes.cyberpunk.scanline,
        flicker: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
          '75%': { opacity: '0.9' },
        },
      },
    },
  },
};

export default cyberpunkPreset;
