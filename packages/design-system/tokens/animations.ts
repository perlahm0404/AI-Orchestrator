/**
 * Animation Tokens
 *
 * Framer Motion variants and CSS animations for each theme.
 */

// Duration tokens
export const duration = {
  instant: 0,
  fast: 150,
  normal: 250,
  slow: 400,
  slower: 600,
  slowest: 1000,
} as const;

// Easing curves
export const easing = {
  linear: [0, 0, 1, 1],
  easeIn: [0.4, 0, 1, 1],
  easeOut: [0, 0, 0.2, 1],
  easeInOut: [0.4, 0, 0.2, 1],
  spring: { type: 'spring', stiffness: 300, damping: 30 },
  bounce: { type: 'spring', stiffness: 400, damping: 10 },
  smooth: { type: 'spring', stiffness: 200, damping: 25 },
} as const;

// Framer Motion variants by theme
export const motionVariants = {
  cosmic: {
    // Ethereal fade with glow
    fadeIn: {
      initial: { opacity: 0, scale: 0.95 },
      animate: { opacity: 1, scale: 1 },
      exit: { opacity: 0, scale: 0.95 },
      transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] },
    },
    // Cosmic hover with glow pulse
    hover: {
      scale: 1.02,
      boxShadow: '0 0 20px rgba(139, 92, 246, 0.5), 0 0 40px rgba(139, 92, 246, 0.2)',
      transition: { duration: 0.2 },
    },
    // Float animation
    float: {
      y: [0, -8, 0],
      transition: {
        duration: 3,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
    // Glow pulse
    glowPulse: {
      boxShadow: [
        '0 0 10px rgba(139, 92, 246, 0.3)',
        '0 0 20px rgba(139, 92, 246, 0.5)',
        '0 0 10px rgba(139, 92, 246, 0.3)',
      ],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
    // Stagger children
    stagger: {
      animate: {
        transition: {
          staggerChildren: 0.1,
          delayChildren: 0.05,
        },
      },
    },
  },

  cyberpunk: {
    // Glitch effect
    glitch: {
      x: [0, -2, 2, -1, 1, 0],
      transition: { duration: 0.2 },
    },
    // Neon flicker
    flicker: {
      opacity: [1, 0.8, 1, 0.9, 1],
      transition: {
        duration: 0.15,
        repeat: Infinity,
        repeatType: 'mirror' as const,
        repeatDelay: 3,
      },
    },
    // Scan line sweep
    scanline: {
      backgroundPosition: ['0% 0%', '0% 100%'],
      transition: {
        duration: 4,
        repeat: Infinity,
        ease: 'linear',
      },
    },
    // Electric hover
    hover: {
      scale: 1.02,
      boxShadow: '0 0 15px rgba(236, 72, 153, 0.6), 0 0 30px rgba(6, 182, 212, 0.4)',
      transition: { duration: 0.15 },
    },
    // Cyberpunk fade
    fadeIn: {
      initial: { opacity: 0, x: -10, filter: 'blur(4px)' },
      animate: { opacity: 1, x: 0, filter: 'blur(0px)' },
      exit: { opacity: 0, x: 10, filter: 'blur(4px)' },
      transition: { duration: 0.2 },
    },
    // Stagger with glitch
    stagger: {
      animate: {
        transition: {
          staggerChildren: 0.05,
          delayChildren: 0.02,
        },
      },
    },
  },

  neumorphic: {
    // Soft press
    press: {
      boxShadow: 'inset 4px 4px 8px #a3b1c6, inset -4px -4px 8px #ffffff',
      scale: 0.98,
      transition: { duration: 0.1 },
    },
    // Raise on hover
    hover: {
      boxShadow: '12px 12px 24px #a3b1c6, -12px -12px 24px #ffffff',
      y: -2,
      transition: { duration: 0.2 },
    },
    // Soft fade
    fadeIn: {
      initial: { opacity: 0, y: 10 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -10 },
      transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] },
    },
    // Toggle states
    toggle: {
      on: {
        boxShadow: 'inset 4px 4px 8px #a3b1c6, inset -4px -4px 8px #ffffff',
      },
      off: {
        boxShadow: '8px 8px 16px #a3b1c6, -8px -8px 16px #ffffff',
      },
    },
    // Gentle stagger
    stagger: {
      animate: {
        transition: {
          staggerChildren: 0.08,
          delayChildren: 0.1,
        },
      },
    },
  },

  futuristic: {
    // Clean slide
    slideIn: {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -20 },
      transition: { duration: 0.25, ease: [0.4, 0, 0.2, 1] },
    },
    // Precise hover
    hover: {
      scale: 1.01,
      boxShadow: '0 8px 24px rgba(59, 130, 246, 0.15)',
      transition: { duration: 0.15, ease: [0.4, 0, 0.2, 1] },
    },
    // Minimal tap
    tap: {
      scale: 0.98,
      transition: { duration: 0.1 },
    },
    // Border accent animation
    borderAccent: {
      borderColor: ['rgba(59, 130, 246, 0.2)', 'rgba(59, 130, 246, 0.6)', 'rgba(59, 130, 246, 0.2)'],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
    // Clean stagger
    stagger: {
      animate: {
        transition: {
          staggerChildren: 0.06,
          delayChildren: 0.03,
        },
      },
    },
  },
} as const;

// CSS keyframes for each theme
export const keyframes = {
  cosmic: {
    twinkle: {
      '0%, 100%': { opacity: '1' },
      '50%': { opacity: '0.5' },
    },
    nebulaPulse: {
      '0%, 100%': { backgroundPosition: '0% 50%' },
      '50%': { backgroundPosition: '100% 50%' },
    },
    starFloat: {
      '0%, 100%': { transform: 'translateY(0) rotate(0deg)' },
      '50%': { transform: 'translateY(-10px) rotate(5deg)' },
    },
  },

  cyberpunk: {
    glitch: {
      '0%': { transform: 'translate(0)' },
      '20%': { transform: 'translate(-2px, 2px)' },
      '40%': { transform: 'translate(-2px, -2px)' },
      '60%': { transform: 'translate(2px, 2px)' },
      '80%': { transform: 'translate(2px, -2px)' },
      '100%': { transform: 'translate(0)' },
    },
    neonPulse: {
      '0%, 100%': { boxShadow: '0 0 5px rgba(236, 72, 153, 0.5)' },
      '50%': { boxShadow: '0 0 20px rgba(236, 72, 153, 0.8), 0 0 40px rgba(6, 182, 212, 0.4)' },
    },
    scanline: {
      '0%': { transform: 'translateY(-100%)' },
      '100%': { transform: 'translateY(100%)' },
    },
  },

  neumorphic: {
    softPulse: {
      '0%, 100%': {
        boxShadow: '8px 8px 16px #a3b1c6, -8px -8px 16px #ffffff',
      },
      '50%': {
        boxShadow: '10px 10px 20px #a3b1c6, -10px -10px 20px #ffffff',
      },
    },
    breathe: {
      '0%, 100%': { transform: 'scale(1)' },
      '50%': { transform: 'scale(1.02)' },
    },
  },

  futuristic: {
    borderGlow: {
      '0%, 100%': { borderColor: 'rgba(59, 130, 246, 0.2)' },
      '50%': { borderColor: 'rgba(59, 130, 246, 0.6)' },
    },
    subtlePulse: {
      '0%, 100%': { opacity: '1' },
      '50%': { opacity: '0.8' },
    },
    slideUp: {
      '0%': { transform: 'translateY(10px)', opacity: '0' },
      '100%': { transform: 'translateY(0)', opacity: '1' },
    },
  },
} as const;

export type MotionVariants = typeof motionVariants;
export type Keyframes = typeof keyframes;
