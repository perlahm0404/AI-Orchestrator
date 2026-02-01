'use client';

import { motion } from 'framer-motion';
import { useTheme, cn } from '@ai-orchestrator/design-system';
import {
  Brain,
  Plus,
  Search,
  Tag,
  CheckCircle2,
  Clock,
  TrendingUp
} from 'lucide-react';

interface KnowledgeObject {
  id: string;
  title: string;
  summary: string;
  tags: string[];
  status: 'approved' | 'pending' | 'draft';
  consultations: number;
  successRate: number;
  createdAt: string;
}

const mockKOs: KnowledgeObject[] = [
  {
    id: 'ko-089',
    title: 'API Rate Limiting Patterns',
    summary: 'Best practices for implementing rate limiting in distributed systems',
    tags: ['api', 'security', 'performance'],
    status: 'approved',
    consultations: 47,
    successRate: 94,
    createdAt: '2 days ago',
  },
  {
    id: 'ko-088',
    title: 'React Server Components Guide',
    summary: 'Patterns for effective RSC usage in Next.js App Router',
    tags: ['react', 'nextjs', 'rsc'],
    status: 'approved',
    consultations: 128,
    successRate: 89,
    createdAt: '5 days ago',
  },
  {
    id: 'ko-087',
    title: 'Database Migration Checklist',
    summary: 'Step-by-step guide for safe database schema migrations',
    tags: ['database', 'migrations', 'safety'],
    status: 'approved',
    consultations: 23,
    successRate: 100,
    createdAt: '1 week ago',
  },
  {
    id: 'ko-090',
    title: 'Error Boundary Patterns',
    summary: 'Implementing robust error handling in React applications',
    tags: ['react', 'errors', 'ux'],
    status: 'pending',
    consultations: 0,
    successRate: 0,
    createdAt: '1 hour ago',
  },
  {
    id: 'ko-draft-001',
    title: 'WebSocket Connection Management',
    summary: 'Handling reconnection and state sync in real-time apps',
    tags: ['websocket', 'realtime'],
    status: 'draft',
    consultations: 0,
    successRate: 0,
    createdAt: 'Just now',
  },
];

const statusStyles = {
  approved: { bg: 'bg-success/10', text: 'text-success', label: 'Approved' },
  pending: { bg: 'bg-warning/10', text: 'text-warning', label: 'Pending Review' },
  draft: { bg: 'bg-foreground-subtle/10', text: 'text-foreground-muted', label: 'Draft' },
};

export default function KnowledgePage() {
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
            <Brain className="w-10 h-10" />
            Knowledge Objects
          </h1>
          <p className="text-foreground-muted text-lg">
            Institutional memory that survives sessions
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-3"
        >
          <div className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-xl',
            'bg-background-elevated border border-border',
            'focus-within:border-primary-500/50'
          )}>
            <Search className="w-4 h-4 text-foreground-muted" />
            <input
              type="text"
              placeholder="Search by tag..."
              className="bg-transparent text-sm focus:outline-none w-40"
            />
          </div>
          <button className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-xl',
            'bg-primary-500 hover:bg-primary-600 text-white',
            'shadow-glow transition-all'
          )}>
            <Plus className="w-4 h-4" />
            Create KO
          </button>
        </motion.div>
      </div>

      {/* Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        <div className="glass rounded-xl p-4 flex items-center gap-4">
          <div className="p-3 rounded-xl bg-success/10">
            <CheckCircle2 className="w-6 h-6 text-success" />
          </div>
          <div>
            <div className="text-2xl font-bold">89</div>
            <div className="text-sm text-foreground-muted">Approved KOs</div>
          </div>
        </div>
        <div className="glass rounded-xl p-4 flex items-center gap-4">
          <div className="p-3 rounded-xl bg-warning/10">
            <Clock className="w-6 h-6 text-warning" />
          </div>
          <div>
            <div className="text-2xl font-bold">4</div>
            <div className="text-sm text-foreground-muted">Pending Review</div>
          </div>
        </div>
        <div className="glass rounded-xl p-4 flex items-center gap-4">
          <div className="p-3 rounded-xl bg-primary-500/10">
            <TrendingUp className="w-6 h-6 text-primary-500" />
          </div>
          <div>
            <div className="text-2xl font-bold">457x</div>
            <div className="text-sm text-foreground-muted">Cache Speedup</div>
          </div>
        </div>
      </motion.div>

      {/* KO Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      >
        {mockKOs.map((ko, index) => (
          <motion.div
            key={ko.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            className={cn(
              'glass rounded-2xl p-5 cursor-pointer transition-all',
              'hover:border-primary-500/30 hover:shadow-glow-sm'
            )}
            whileHover={{ y: -2 }}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className={cn(
                'px-2 py-1 rounded-lg text-xs font-medium',
                statusStyles[ko.status].bg,
                statusStyles[ko.status].text
              )}>
                {statusStyles[ko.status].label}
              </div>
              <span className="text-xs text-foreground-muted">{ko.id}</span>
            </div>

            {/* Content */}
            <h3 className="font-semibold mb-2">{ko.title}</h3>
            <p className="text-sm text-foreground-muted mb-4 line-clamp-2">
              {ko.summary}
            </p>

            {/* Tags */}
            <div className="flex flex-wrap gap-2 mb-4">
              {ko.tags.map((tag) => (
                <span
                  key={tag}
                  className={cn(
                    'px-2 py-0.5 rounded-full text-xs',
                    'bg-background-elevated text-foreground-muted'
                  )}
                >
                  #{tag}
                </span>
              ))}
            </div>

            {/* Footer */}
            {ko.status === 'approved' && (
              <div className="flex items-center justify-between text-xs text-foreground-muted pt-3 border-t border-border">
                <span>{ko.consultations} consultations</span>
                <span className={cn(
                  ko.successRate >= 90 ? 'text-success' : 'text-warning'
                )}>
                  {ko.successRate}% success
                </span>
              </div>
            )}
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
