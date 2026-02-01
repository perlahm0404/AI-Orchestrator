/**
 * Button Component
 *
 * Theme-aware button with variants for each design style.
 */

'use client';

import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';
import { cn } from '../../lib/utils';
import { useTheme } from '../../lib/theme-context';
import { motionVariants } from '../../tokens/animations';

export interface ButtonProps
  extends Omit<HTMLMotionProps<'button'>, 'children'>,
    Pick<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  variant?: 'default' | 'secondary' | 'outline' | 'ghost' | 'themed';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
}

const baseStyles = 'inline-flex items-center justify-center font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50';

const sizeStyles = {
  sm: 'h-8 px-3 text-sm rounded-md',
  md: 'h-10 px-4 text-base rounded-lg',
  lg: 'h-12 px-6 text-lg rounded-xl',
};

const variantStyles = {
  default: 'bg-primary-500 text-white hover:bg-primary-600 focus-visible:ring-primary-500',
  secondary: 'bg-secondary-500 text-white hover:bg-secondary-600 focus-visible:ring-secondary-500',
  outline: 'border-2 border-primary-500 text-primary-500 hover:bg-primary-500/10 focus-visible:ring-primary-500',
  ghost: 'hover:bg-background-elevated text-foreground focus-visible:ring-primary-500',
  themed: '', // Handled per-theme below
};

// Theme-specific styles for the 'themed' variant
const themedStyles = {
  cosmic: 'bg-primary-500 text-white shadow-glow hover:shadow-glow-lg hover:scale-[1.02]',
  cyberpunk: 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white shadow-neon-mixed hover:shadow-neon-pink',
  neumorphic: 'bg-background shadow-neu hover:shadow-neu-lg active:shadow-neu-pressed',
  futuristic: 'bg-gradient-primary text-white shadow-accent hover:shadow-accent-lg',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'default',
      size = 'md',
      loading = false,
      disabled = false,
      children,
      ...props
    },
    ref
  ) => {
    const { theme } = useTheme();
    const themeMotion = motionVariants[theme];

    const computedVariantStyle =
      variant === 'themed' ? themedStyles[theme] : variantStyles[variant];

    return (
      <motion.button
        ref={ref}
        className={cn(
          baseStyles,
          sizeStyles[size],
          computedVariantStyle,
          className
        )}
        disabled={disabled || loading}
        whileHover={themeMotion.hover}
        whileTap={{ scale: 0.98 }}
        {...props}
      >
        {loading ? (
          <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : null}
        {children}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
