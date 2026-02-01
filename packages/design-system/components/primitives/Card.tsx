/**
 * Card Component
 *
 * Theme-aware card container with variants for each design style.
 */

'use client';

import { forwardRef, type HTMLAttributes } from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';
import { cn } from '../../lib/utils';
import { useTheme } from '../../lib/theme-context';
import { motionVariants } from '../../tokens/animations';

export interface CardProps extends HTMLMotionProps<'div'> {
  variant?: 'default' | 'elevated' | 'outlined' | 'themed';
  hoverable?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const baseStyles = 'rounded-xl overflow-hidden';

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
};

const variantStyles = {
  default: 'bg-background-card border border-border',
  elevated: 'bg-background-elevated shadow-lg',
  outlined: 'bg-transparent border-2 border-border-accent',
  themed: '', // Handled per-theme below
};

// Theme-specific styles for the 'themed' variant
const themedStyles = {
  cosmic: 'bg-background-card/50 backdrop-blur-xl border border-border-glow shadow-glow',
  cyberpunk: 'bg-background-card border border-neon-pink/30 shadow-neon-pink/20',
  neumorphic: 'bg-background shadow-neu',
  futuristic: 'bg-background-card border border-border shadow-md',
};

// Theme-specific hover styles
const hoverStyles = {
  cosmic: 'hover:shadow-cosmic hover:border-primary-500/50',
  cyberpunk: 'hover:shadow-neon-mixed hover:border-neon-cyan/50',
  neumorphic: 'hover:shadow-neu-lg',
  futuristic: 'hover:shadow-accent-lg hover:border-primary-500',
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      className,
      variant = 'default',
      hoverable = false,
      padding = 'md',
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
      <motion.div
        ref={ref}
        className={cn(
          baseStyles,
          paddingStyles[padding],
          computedVariantStyle,
          hoverable && hoverStyles[theme],
          hoverable && 'transition-all cursor-pointer',
          className
        )}
        variants={themeMotion.fadeIn}
        initial="initial"
        animate="animate"
        whileHover={hoverable ? themeMotion.hover : undefined}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

Card.displayName = 'Card';

// Sub-components
export interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {}

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col space-y-1.5 pb-4', className)}
      {...props}
    />
  )
);
CardHeader.displayName = 'CardHeader';

export interface CardTitleProps extends HTMLAttributes<HTMLHeadingElement> {}

export const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('text-xl font-semibold text-foreground', className)}
      {...props}
    />
  )
);
CardTitle.displayName = 'CardTitle';

export interface CardDescriptionProps extends HTMLAttributes<HTMLParagraphElement> {}

export const CardDescription = forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-foreground-muted', className)}
      {...props}
    />
  )
);
CardDescription.displayName = 'CardDescription';

export interface CardContentProps extends HTMLAttributes<HTMLDivElement> {}

export const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('', className)} {...props} />
  )
);
CardContent.displayName = 'CardContent';

export interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {}

export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center pt-4', className)}
      {...props}
    />
  )
);
CardFooter.displayName = 'CardFooter';

export default Card;
