'use client';

import { motion } from 'framer-motion';
import { useTheme, cn } from '@ai-orchestrator/design-system';
import {
  Bell,
  Search,
  User,
  Moon,
  Sun,
  Sparkles,
  Command
} from 'lucide-react';
import { ThemeSwitcher } from './ThemeSwitcher';

export function Header() {
  const { theme } = useTheme();

  return (
    <header
      className={cn(
        'fixed top-0 right-0 left-sidebar z-header',
        'h-header flex items-center justify-between px-6',
        'bg-background/80 backdrop-blur-xl',
        'border-b border-border'
      )}
    >
      {/* Search */}
      <div className="flex-1 max-w-xl">
        <motion.div
          className={cn(
            'flex items-center gap-3 px-4 py-2 rounded-xl',
            'bg-background-elevated/50 border border-border',
            'focus-within:border-primary-500/50 focus-within:shadow-glow-sm',
            'transition-all'
          )}
          whileHover={{ scale: 1.01 }}
        >
          <Search className="w-4 h-4 text-foreground-muted" />
          <input
            type="text"
            placeholder="Search agents, tasks, knowledge..."
            className={cn(
              'flex-1 bg-transparent text-sm',
              'placeholder:text-foreground-subtle',
              'focus:outline-none'
            )}
          />
          <div className="flex items-center gap-1 text-xs text-foreground-muted">
            <Command className="w-3 h-3" />
            <span>K</span>
          </div>
        </motion.div>
      </div>

      {/* Right side actions */}
      <div className="flex items-center gap-4">
        {/* Theme Switcher */}
        <ThemeSwitcher />

        {/* Notifications */}
        <motion.button
          className={cn(
            'relative p-2 rounded-xl',
            'hover:bg-background-elevated transition-colors'
          )}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Bell className="w-5 h-5 text-foreground-muted" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-primary-500 animate-pulse" />
        </motion.button>

        {/* User Menu */}
        <motion.button
          className={cn(
            'flex items-center gap-3 px-3 py-2 rounded-xl',
            'hover:bg-background-elevated transition-colors'
          )}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <div className={cn(
            'w-8 h-8 rounded-lg flex items-center justify-center',
            'bg-gradient-to-br from-primary-500 to-secondary-500',
            'shadow-glow-sm'
          )}>
            <User className="w-4 h-4 text-white" />
          </div>
          <div className="text-left hidden md:block">
            <div className="text-sm font-medium">Admin</div>
            <div className="text-xs text-foreground-muted">Operator</div>
          </div>
        </motion.button>
      </div>
    </header>
  );
}
