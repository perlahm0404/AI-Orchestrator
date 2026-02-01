'use client';

import { motion } from 'framer-motion';
import { useTheme, cn, type ThemeName } from '@ai-orchestrator/design-system';
import {
  Settings,
  Palette,
  Bell,
  Shield,
  Database,
  Zap,
  Check
} from 'lucide-react';

const themeConfig: Record<ThemeName, { icon: string; label: string; colors: string[] }> = {
  cosmic: {
    icon: '🌌',
    label: 'Cosmic Space',
    colors: ['#8b5cf6', '#3b82f6', '#0a0a1a'],
  },
  cyberpunk: {
    icon: '🌆',
    label: 'Cyberpunk',
    colors: ['#ec4899', '#06b6d4', '#0a0a0a'],
  },
  neumorphic: {
    icon: '💿',
    label: 'Neumorphic',
    colors: ['#0ea5e9', '#e0e5ec', '#a3b1c6'],
  },
  futuristic: {
    icon: '⚡',
    label: 'Futuristic',
    colors: ['#3b82f6', '#ffffff', '#0f172a'],
  },
};

export default function SettingsPage() {
  const { theme, setTheme, availableThemes } = useTheme();

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <h1 className="text-4xl font-display font-bold text-gradient flex items-center gap-3">
          <Settings className="w-10 h-10" />
          Settings
        </h1>
        <p className="text-foreground-muted text-lg">
          Configure your dashboard preferences
        </p>
      </motion.div>

      {/* Theme Selection */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass rounded-2xl p-6"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-xl bg-primary-500/10">
            <Palette className="w-5 h-5 text-primary-500" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">Theme</h2>
            <p className="text-sm text-foreground-muted">
              Choose your preferred visual style
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {availableThemes.map((themeName) => {
            const config = themeConfig[themeName];
            const isActive = theme === themeName;

            return (
              <motion.button
                key={themeName}
                onClick={() => setTheme(themeName)}
                className={cn(
                  'p-4 rounded-xl text-left transition-all',
                  'border-2',
                  isActive
                    ? 'border-primary-500 bg-primary-500/5 shadow-glow-sm'
                    : 'border-border hover:border-primary-500/50 hover:bg-background-elevated'
                )}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{config.icon}</span>
                    <span className="font-semibold">{config.label}</span>
                  </div>
                  {isActive && (
                    <div className="w-6 h-6 rounded-full bg-primary-500 flex items-center justify-center">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                  )}
                </div>

                {/* Color preview */}
                <div className="flex gap-2">
                  {config.colors.map((color, i) => (
                    <div
                      key={i}
                      className="w-8 h-8 rounded-lg border border-white/20"
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </motion.button>
            );
          })}
        </div>
      </motion.div>

      {/* Other Settings Sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Notifications */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass rounded-2xl p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-xl bg-warning/10">
              <Bell className="w-5 h-5 text-warning" />
            </div>
            <h2 className="text-lg font-semibold">Notifications</h2>
          </div>
          <div className="space-y-3">
            <label className="flex items-center justify-between">
              <span className="text-sm">Agent status changes</span>
              <input type="checkbox" defaultChecked className="toggle" />
            </label>
            <label className="flex items-center justify-between">
              <span className="text-sm">Task completions</span>
              <input type="checkbox" defaultChecked className="toggle" />
            </label>
            <label className="flex items-center justify-between">
              <span className="text-sm">Error alerts</span>
              <input type="checkbox" defaultChecked className="toggle" />
            </label>
          </div>
        </motion.div>

        {/* Governance */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass rounded-2xl p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-xl bg-success/10">
              <Shield className="w-5 h-5 text-success" />
            </div>
            <h2 className="text-lg font-semibold">Governance</h2>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-foreground-muted">Kill Switch</span>
              <span className="text-success font-medium">NORMAL</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-foreground-muted">QA Team Autonomy</span>
              <span className="font-medium">L2</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-foreground-muted">Dev Team Autonomy</span>
              <span className="font-medium">L1</span>
            </div>
          </div>
        </motion.div>

        {/* API Configuration */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass rounded-2xl p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-xl bg-info/10">
              <Database className="w-5 h-5 text-info" />
            </div>
            <h2 className="text-lg font-semibold">API Configuration</h2>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-foreground-muted">Backend URL</span>
              <span className="font-mono text-xs bg-background-elevated px-2 py-1 rounded">
                localhost:8000
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-foreground-muted">Connection</span>
              <span className="text-success font-medium">Connected</span>
            </div>
          </div>
        </motion.div>

        {/* Performance */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass rounded-2xl p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-xl bg-primary-500/10">
              <Zap className="w-5 h-5 text-primary-500" />
            </div>
            <h2 className="text-lg font-semibold">Performance</h2>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-foreground-muted">KO Cache</span>
              <span className="text-success font-medium">457x speedup</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-foreground-muted">Autonomy Rate</span>
              <span className="font-medium">91%</span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
