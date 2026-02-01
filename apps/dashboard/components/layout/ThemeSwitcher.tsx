'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme, cn, type ThemeName } from '@ai-orchestrator/design-system';
import { Palette, Check } from 'lucide-react';

const themeConfig: Record<ThemeName, { icon: string; label: string; description: string }> = {
  cosmic: {
    icon: '🌌',
    label: 'Cosmic',
    description: 'Deep space with galaxy vibes',
  },
  cyberpunk: {
    icon: '🌆',
    label: 'Cyberpunk',
    description: 'Neon-lit urban future',
  },
  neumorphic: {
    icon: '💿',
    label: 'Neumorphic',
    description: 'Soft, tactile 3D design',
  },
  futuristic: {
    icon: '⚡',
    label: 'Futuristic',
    description: 'Clean, minimal tech',
  },
};

export function ThemeSwitcher() {
  const { theme, setTheme, availableThemes } = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-2 px-3 py-2 rounded-xl',
          'hover:bg-background-elevated transition-colors',
          isOpen && 'bg-background-elevated'
        )}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <span className="text-xl">{themeConfig[theme].icon}</span>
        <span className="text-sm font-medium hidden sm:block">
          {themeConfig[theme].label}
        </span>
        <Palette className="w-4 h-4 text-foreground-muted" />
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Dropdown */}
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className={cn(
                'absolute right-0 top-full mt-2 z-50',
                'w-64 p-2 rounded-2xl',
                'bg-background-card/95 backdrop-blur-xl',
                'border border-border shadow-lg shadow-glow/10'
              )}
            >
              <div className="px-3 py-2 mb-2">
                <h3 className="text-sm font-semibold">Choose Theme</h3>
                <p className="text-xs text-foreground-muted">
                  Select your preferred visual style
                </p>
              </div>

              <div className="space-y-1">
                {availableThemes.map((themeName) => {
                  const config = themeConfig[themeName];
                  const isActive = theme === themeName;

                  return (
                    <motion.button
                      key={themeName}
                      onClick={() => {
                        setTheme(themeName);
                        setIsOpen(false);
                      }}
                      className={cn(
                        'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl',
                        'text-left transition-all',
                        isActive
                          ? 'bg-primary-500/10 border border-primary-500/30'
                          : 'hover:bg-background-elevated'
                      )}
                      whileHover={{ x: 4 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <span className="text-2xl">{config.icon}</span>
                      <div className="flex-1">
                        <div className={cn(
                          'font-medium text-sm',
                          isActive && 'text-primary-500'
                        )}>
                          {config.label}
                        </div>
                        <div className="text-xs text-foreground-muted">
                          {config.description}
                        </div>
                      </div>
                      {isActive && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="w-5 h-5 rounded-full bg-primary-500 flex items-center justify-center"
                        >
                          <Check className="w-3 h-3 text-white" />
                        </motion.div>
                      )}
                    </motion.button>
                  );
                })}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
