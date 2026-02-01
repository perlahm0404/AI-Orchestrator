'use client';

import { motion } from 'framer-motion';
import { cn } from '@ai-orchestrator/design-system';
import {
  CheckCircle2,
  AlertCircle,
  Clock,
  Bot,
  Brain,
  FileText
} from 'lucide-react';

interface ActivityItem {
  id: string;
  type: 'success' | 'warning' | 'info' | 'pending';
  title: string;
  description: string;
  time: string;
  icon: 'agent' | 'task' | 'knowledge';
}

const mockActivities: ActivityItem[] = [
  {
    id: '1',
    type: 'success',
    title: 'BugFix agent completed',
    description: 'Fixed authentication bug in login flow',
    time: '2 min ago',
    icon: 'agent',
  },
  {
    id: '2',
    type: 'info',
    title: 'New Knowledge Object',
    description: 'KO-089: API rate limiting patterns',
    time: '15 min ago',
    icon: 'knowledge',
  },
  {
    id: '3',
    type: 'pending',
    title: 'Task in progress',
    description: 'CodeQuality reviewing src/utils',
    time: '23 min ago',
    icon: 'task',
  },
  {
    id: '4',
    type: 'warning',
    title: 'Retry budget warning',
    description: 'FeatureBuilder at 80% retries',
    time: '1 hour ago',
    icon: 'agent',
  },
  {
    id: '5',
    type: 'success',
    title: 'Ralph verification passed',
    description: '47 tests passed, 0 failures',
    time: '2 hours ago',
    icon: 'task',
  },
];

const typeStyles = {
  success: 'bg-success/10 text-success border-success/20',
  warning: 'bg-warning/10 text-warning border-warning/20',
  info: 'bg-info/10 text-info border-info/20',
  pending: 'bg-foreground-subtle/10 text-foreground-muted border-foreground-subtle/20',
};

const iconComponents = {
  agent: Bot,
  task: FileText,
  knowledge: Brain,
};

export function RecentActivity() {
  return (
    <div className="space-y-3">
      {mockActivities.map((activity, index) => {
        const IconComponent = iconComponents[activity.icon];

        return (
          <motion.div
            key={activity.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className={cn(
              'flex items-start gap-3 p-3 rounded-xl',
              'border transition-all cursor-pointer',
              'hover:bg-background-elevated',
              typeStyles[activity.type]
            )}
          >
            <div className={cn(
              'p-2 rounded-lg',
              typeStyles[activity.type]
            )}>
              <IconComponent className="w-4 h-4" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-sm text-foreground truncate">
                  {activity.title}
                </span>
                <span className="text-xs text-foreground-muted whitespace-nowrap">
                  {activity.time}
                </span>
              </div>
              <p className="text-xs text-foreground-muted truncate mt-0.5">
                {activity.description}
              </p>
            </div>
          </motion.div>
        );
      })}

      <motion.button
        className={cn(
          'w-full py-2 text-sm text-primary-500',
          'hover:text-primary-400 transition-colors'
        )}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        View all activity →
      </motion.button>
    </div>
  );
}
