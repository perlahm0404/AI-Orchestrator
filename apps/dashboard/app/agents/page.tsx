'use client';

import { motion } from 'framer-motion';
import { useTheme, cn } from '@ai-orchestrator/design-system';
import { Bot, Plus, Filter, RefreshCw } from 'lucide-react';
import { AgentStatusGrid } from '@/components/agents/AgentStatusGrid';

export default function AgentsPage() {
  const { theme } = useTheme();

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          <h1 className="text-4xl font-display font-bold text-gradient flex items-center gap-3">
            <Bot className="w-10 h-10" />
            Agent Fleet
          </h1>
          <p className="text-foreground-muted text-lg">
            Monitor and manage your AI agents
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-3"
        >
          <button className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-xl',
            'bg-background-elevated hover:bg-background-muted',
            'border border-border transition-all'
          )}>
            <Filter className="w-4 h-4" />
            Filter
          </button>
          <button className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-xl',
            'bg-background-elevated hover:bg-background-muted',
            'border border-border transition-all'
          )}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-xl',
            'bg-primary-500 hover:bg-primary-600 text-white',
            'shadow-glow transition-all'
          )}>
            <Plus className="w-4 h-4" />
            Deploy Agent
          </button>
        </motion.div>
      </div>

      {/* Stats Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass rounded-2xl p-4"
      >
        <div className="flex items-center justify-around">
          <div className="text-center">
            <div className="text-3xl font-bold text-success">3</div>
            <div className="text-sm text-foreground-muted">Active</div>
          </div>
          <div className="w-px h-10 bg-border" />
          <div className="text-center">
            <div className="text-3xl font-bold text-foreground-muted">2</div>
            <div className="text-sm text-foreground-muted">Idle</div>
          </div>
          <div className="w-px h-10 bg-border" />
          <div className="text-center">
            <div className="text-3xl font-bold text-warning">1</div>
            <div className="text-sm text-foreground-muted">Paused</div>
          </div>
          <div className="w-px h-10 bg-border" />
          <div className="text-center">
            <div className="text-3xl font-bold text-error">0</div>
            <div className="text-sm text-foreground-muted">Error</div>
          </div>
        </div>
      </motion.div>

      {/* Agent Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <AgentStatusGrid />
      </motion.div>
    </div>
  );
}
