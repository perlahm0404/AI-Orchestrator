/**
 * Cosmic Space Theme - Tailwind Preset
 *
 * Deep space aesthetics with galaxy purples, nebula blues, and starfield accents.
 */

import type { Config } from 'tailwindcss';
import { cosmic } from '../../tokens/colors/cosmic';
import { typography, themeTypography } from '../../tokens/typography';
import { spacing, themeBorderRadius } from '../../tokens/spacing';
import { keyframes } from '../../tokens/animations';

export const cosmicPreset: Partial<Config> = {
  theme: {
    extend: {
      colors: {
        // Primary palette
        primary: cosmic.primary,
        secondary: cosmic.secondary,
        accent: cosmic.accent,

        // Background
        background: cosmic.background.DEFAULT,
        'background-subtle': cosmic.background.subtle,
        'background-muted': cosmic.background.muted,
        'background-card': cosmic.background.card,
        'background-elevated': cosmic.background.elevated,

        // Foreground
        foreground: cosmic.foreground.DEFAULT,
        'foreground-muted': cosmic.foreground.muted,
        'foreground-subtle': cosmic.foreground.subtle,
        'foreground-accent': cosmic.foreground.accent,

        // Border
        border: cosmic.border.DEFAULT,
        'border-subtle': cosmic.border.subtle,
        'border-accent': cosmic.border.accent,
        'border-glow': cosmic.border.glow,

        // Semantic
        success: cosmic.success.DEFAULT,
        warning: cosmic.warning.DEFAULT,
        error: cosmic.error.DEFAULT,
        info: cosmic.info.DEFAULT,
      },

      fontFamily: {
        sans: typography.fontFamily.sans,
        mono: typography.fontFamily.mono,
        display: themeTypography.cosmic.display,
      },

      borderRadius: {
        DEFAULT: themeBorderRadius.cosmic.DEFAULT,
        lg: themeBorderRadius.cosmic.lg,
        xl: themeBorderRadius.cosmic.xl,
      },

      boxShadow: {
        'glow-sm': `0 0 10px ${cosmic.glow.purple}`,
        'glow': `0 0 20px ${cosmic.glow.purple}`,
        'glow-lg': `0 0 30px ${cosmic.glow.purple}, 0 0 60px ${cosmic.glow.blue}`,
        'glow-accent': `0 0 20px ${cosmic.glow.gold}`,
        'cosmic': `0 0 20px ${cosmic.glow.purple}, 0 0 40px ${cosmic.glow.blue}, 0 0 60px ${cosmic.glow.purple}`,
      },

      backgroundImage: {
        'cosmic-gradient': `linear-gradient(135deg, ${cosmic.primary[900]} 0%, ${cosmic.secondary[900]} 50%, ${cosmic.primary[950]} 100%)`,
        'cosmic-radial': `radial-gradient(ellipse at center, ${cosmic.primary[900]} 0%, ${cosmic.background.DEFAULT} 70%)`,
        'nebula': `linear-gradient(45deg, ${cosmic.primary[800]}, ${cosmic.secondary[800]}, ${cosmic.primary[700]})`,
        'starfield': `radial-gradient(2px 2px at 20px 30px, white, transparent),
                      radial-gradient(2px 2px at 40px 70px, white, transparent),
                      radial-gradient(1px 1px at 90px 40px, white, transparent),
                      radial-gradient(2px 2px at 160px 120px, white, transparent)`,
      },

      animation: {
        'twinkle': 'twinkle 3s ease-in-out infinite',
        'nebula-pulse': 'nebulaPulse 8s ease-in-out infinite',
        'star-float': 'starFloat 6s ease-in-out infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },

      keyframes: {
        twinkle: keyframes.cosmic.twinkle,
        nebulaPulse: keyframes.cosmic.nebulaPulse,
        starFloat: keyframes.cosmic.starFloat,
        glowPulse: {
          '0%, 100%': { boxShadow: `0 0 10px ${cosmic.glow.purple}` },
          '50%': { boxShadow: `0 0 25px ${cosmic.glow.purple}, 0 0 50px ${cosmic.glow.blue}` },
        },
      },
    },
  },
};

export default cosmicPreset;
