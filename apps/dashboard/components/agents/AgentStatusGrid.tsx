'use client';

import { motion } from 'framer-motion';
import { useTheme, cn } from '@ai-orchestrator/design-system';
import {
  Bot,
  Wrench,
  Code,
  TestTube,
  Rocket,
  Shield,
  Activity,
  Pause,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  type: 'BugFix' | 'CodeQuality' | 'TestFixer' | 'FeatureBuilder' | 'TestWriter' | 'Operator';
  status: 'active' | 'idle' | 'paused' | 'error';
  currentTask?: string;
  progress?: number;
  retries?: { used: number; max: number };
}

const mockAgents: Agent[] = [
  {
    id: 'bf-001',
    name: 'BugFix-Alpha',
    type: 'BugFix',
    status: 'active',
    currentTask: 'Fixing auth token refresh',
    progress: 67,
    retries: { used: 3, max: 15 },
  },
  {
    id: 'cq-001',
    name: 'CodeQuality-Prime',
    type: 'CodeQuality',
    status: 'active',
    currentTask: 'Reviewing src/components',
    progress: 45,
    retries: { used: 8, max: 20 },
  },
  {
    id: 'tf-001',
    name: 'TestFixer-Beta',
    type: 'TestFixer',
    status: 'idle',
    retries: { used: 0, max: 15 },
  },
  {
    id: 'fb-001',
    name: 'FeatureBuilder-X',
    type: 'FeatureBuilder',
    status: 'active',
    currentTask: 'Building user dashboard',
    progress: 23,
    retries: { used: 40, max: 50 },
  },
  {
    id: 'tw-001',
    name: 'TestWriter-Omega',
    type: 'TestWriter',
    status: 'paused',
    retries: { used: 5, max: 15 },
  },
  {
    id: 'op-001',
    name: 'Operator-Delta',
    type: 'Operator',
    status: 'idle',
    retries: { used: 0, max: 10 },
  },
];

const typeIcons = {
  BugFix: Wrench,
  CodeQuality: Code,
  TestFixer: TestTube,
  FeatureBuilder: Rocket,
  TestWriter: Shield,
  Operator: Bot,
};

const statusStyles = {
  active: {
    bg: 'bg-success/10',
    text: 'text-success',
    border: 'border-success/30',
    dot: 'bg-success',
  },
  idle: {
    bg: 'bg-foreground-subtle/10',
    text: 'text-foreground-muted',
    border: 'border-foreground-subtle/20',
    dot: 'bg-foreground-subtle',
  },
  paused: {
    bg: 'bg-warning/10',
    text: 'text-warning',
    border: 'border-warning/30',
    dot: 'bg-warning',
  },
  error: {
    bg: 'bg-error/10',
    text: 'text-error',
    border: 'border-error/30',
    dot: 'bg-error',
  },
};

export function AgentStatusGrid() {
  const { theme } = useTheme();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {mockAgents.map((agent, index) => {
        const Icon = typeIcons[agent.type];
        const styles = statusStyles[agent.status];
        const retryPercentage = agent.retries
          ? (agent.retries.used / agent.retries.max) * 100
          : 0;

        return (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            className={cn(
              'p-4 rounded-xl border transition-all cursor-pointer',
              'hover:border-primary-500/30 hover:shadow-glow-sm',
              styles.border,
              styles.bg
            )}
            whileHover={{ y: -2 }}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className={cn(
                  'p-2 rounded-lg',
                  styles.bg,
                  styles.text
                )}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-medium text-sm">{agent.name}</div>
                  <div className="text-xs text-foreground-muted">{agent.type}</div>
                </div>
              </div>

              {/* Status indicator */}
              <div className="flex items-center gap-2">
                <div className={cn(
                  'w-2 h-2 rounded-full',
                  styles.dot,
                  agent.status === 'active' && 'animate-pulse'
                )} />
                <span className={cn('text-xs capitalize', styles.text)}>
                  {agent.status}
                </span>
              </div>
            </div>

            {/* Current Task */}
            {agent.currentTask && (
              <div className="mb-3">
                <div className="text-xs text-foreground-muted mb-1">Current Task</div>
                <div className="text-sm truncate">{agent.currentTask}</div>

                {/* Progress bar */}
                {agent.progress !== undefined && (
                  <div className="mt-2 h-1.5 bg-background-muted rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-primary-500 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${agent.progress}%` }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                    />
                  </div>
                )}
              </div>
            )}

            {/* Retry Budget */}
            {agent.retries && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-foreground-muted">Retry Budget</span>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1 bg-background-muted rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full transition-all',
                        retryPercentage > 80 ? 'bg-error' :
                        retryPercentage > 50 ? 'bg-warning' : 'bg-success'
                      )}
                      style={{ width: `${retryPercentage}%` }}
                    />
                  </div>
                  <span className={cn(
                    retryPercentage > 80 ? 'text-error' :
                    retryPercentage > 50 ? 'text-warning' : 'text-foreground-muted'
                  )}>
                    {agent.retries.used}/{agent.retries.max}
                  </span>
                </div>
              </div>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
