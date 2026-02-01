'use client';

import { motion } from 'framer-motion';
import { useTheme, cn } from '@ai-orchestrator/design-system';
import {
  ListTodo,
  Plus,
  Filter,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2
} from 'lucide-react';

interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  priority: 'P0' | 'P1' | 'P2';
  assignee?: string;
  createdAt: string;
}

const mockTasks: Task[] = [
  {
    id: 'task-001',
    title: 'Fix authentication token refresh',
    description: 'Token expires too quickly causing logout issues',
    status: 'in_progress',
    priority: 'P0',
    assignee: 'BugFix-Alpha',
    createdAt: '2 hours ago',
  },
  {
    id: 'task-002',
    title: 'Review component accessibility',
    description: 'Ensure all components meet WCAG 2.1 AA',
    status: 'in_progress',
    priority: 'P1',
    assignee: 'CodeQuality-Prime',
    createdAt: '3 hours ago',
  },
  {
    id: 'task-003',
    title: 'Add user dashboard feature',
    description: 'Create new dashboard with analytics widgets',
    status: 'in_progress',
    priority: 'P1',
    assignee: 'FeatureBuilder-X',
    createdAt: '1 day ago',
  },
  {
    id: 'task-004',
    title: 'Fix flaky integration tests',
    description: 'Tests failing intermittently on CI',
    status: 'pending',
    priority: 'P1',
    createdAt: '1 day ago',
  },
  {
    id: 'task-005',
    title: 'Update API documentation',
    description: 'Document new endpoints and parameters',
    status: 'pending',
    priority: 'P2',
    createdAt: '2 days ago',
  },
  {
    id: 'task-006',
    title: 'Optimize database queries',
    description: 'Improve query performance for user listing',
    status: 'blocked',
    priority: 'P1',
    createdAt: '3 days ago',
  },
];

const statusStyles = {
  pending: { bg: 'bg-foreground-subtle/10', text: 'text-foreground-muted', icon: Clock },
  in_progress: { bg: 'bg-primary-500/10', text: 'text-primary-500', icon: Loader2 },
  completed: { bg: 'bg-success/10', text: 'text-success', icon: CheckCircle2 },
  blocked: { bg: 'bg-error/10', text: 'text-error', icon: AlertCircle },
};

const priorityStyles = {
  P0: 'bg-error text-white',
  P1: 'bg-warning text-black',
  P2: 'bg-info text-white',
};

export default function TasksPage() {
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
            <ListTodo className="w-10 h-10" />
            Task Queue
          </h1>
          <p className="text-foreground-muted text-lg">
            View and manage pending work items
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
            'bg-primary-500 hover:bg-primary-600 text-white',
            'shadow-glow transition-all'
          )}>
            <Plus className="w-4 h-4" />
            Add Task
          </button>
        </motion.div>
      </div>

      {/* Task List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass rounded-2xl overflow-hidden"
      >
        <div className="divide-y divide-border">
          {mockTasks.map((task, index) => {
            const StatusIcon = statusStyles[task.status].icon;

            return (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className={cn(
                  'p-4 hover:bg-background-elevated/50 transition-all cursor-pointer',
                  'flex items-center gap-4'
                )}
              >
                {/* Status Icon */}
                <div className={cn(
                  'p-2 rounded-lg',
                  statusStyles[task.status].bg
                )}>
                  <StatusIcon className={cn(
                    'w-5 h-5',
                    statusStyles[task.status].text,
                    task.status === 'in_progress' && 'animate-spin'
                  )} />
                </div>

                {/* Task Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium truncate">{task.title}</span>
                    <span className={cn(
                      'px-2 py-0.5 rounded text-xs font-medium',
                      priorityStyles[task.priority]
                    )}>
                      {task.priority}
                    </span>
                  </div>
                  <p className="text-sm text-foreground-muted truncate">
                    {task.description}
                  </p>
                </div>

                {/* Assignee */}
                <div className="text-right hidden md:block">
                  {task.assignee ? (
                    <div>
                      <div className="text-sm font-medium">{task.assignee}</div>
                      <div className="text-xs text-foreground-muted">Assigned</div>
                    </div>
                  ) : (
                    <div className="text-sm text-foreground-muted">Unassigned</div>
                  )}
                </div>

                {/* Created Time */}
                <div className="text-sm text-foreground-muted whitespace-nowrap">
                  {task.createdAt}
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}
