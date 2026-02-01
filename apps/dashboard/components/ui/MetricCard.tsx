'use client';

import { motion } from 'framer-motion';
import { useTheme, cn } from '@ai-orchestrator/design-system';
import { TrendingUp, TrendingDown, type LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  subtitle?: string;
  variant?: 'primary' | 'success' | 'warning' | 'info';
}

const variantStyles = {
  primary: {
    icon: 'bg-primary-500/10 text-primary-500',
    glow: 'shadow-glow-sm',
  },
  success: {
    icon: 'bg-success/10 text-success',
    glow: 'shadow-[0_0_20px_rgba(34,197,94,0.2)]',
  },
  warning: {
    icon: 'bg-warning/10 text-warning',
    glow: 'shadow-[0_0_20px_rgba(245,158,11,0.2)]',
  },
  info: {
    icon: 'bg-info/10 text-info',
    glow: 'shadow-[0_0_20px_rgba(59,130,246,0.2)]',
  },
};

export function MetricCard({
  title,
  value,
  icon: Icon,
  trend,
  subtitle,
  variant = 'primary',
}: MetricCardProps) {
  const { theme } = useTheme();
  const styles = variantStyles[variant];

  return (
    <motion.div
      className={cn(
        'glass rounded-2xl p-6',
        'hover:border-primary-500/30 transition-all',
        styles.glow
      )}
      whileHover={{ y: -2, scale: 1.01 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-foreground-muted">{title}</span>
            {subtitle && (
              <span className="text-xs text-foreground-subtle px-2 py-0.5 rounded-full bg-background-elevated">
                {subtitle}
              </span>
            )}
          </div>

          <div className="flex items-baseline gap-3">
            <span className="text-4xl font-bold font-display">{value}</span>

            {trend && (
              <div
                className={cn(
                  'flex items-center gap-1 text-sm',
                  trend.isPositive ? 'text-success' : 'text-error'
                )}
              >
                {trend.isPositive ? (
                  <TrendingUp className="w-4 h-4" />
                ) : (
                  <TrendingDown className="w-4 h-4" />
                )}
                <span>{trend.isPositive ? '+' : '-'}{trend.value}</span>
              </div>
            )}
          </div>
        </div>

        <div className={cn('p-3 rounded-xl', styles.icon)}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </motion.div>
  );
}
