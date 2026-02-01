'use client';

import { motion } from 'framer-motion';
import { useTheme } from '@ai-orchestrator/design-system';
import {
  Bot,
  ListTodo,
  Brain,
  Activity,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { MetricCard } from '@/components/ui/MetricCard';
import { AgentStatusGrid } from '@/components/agents/AgentStatusGrid';
import { RecentActivity } from '@/components/ui/RecentActivity';

export default function DashboardHome() {
  const { theme } = useTheme();

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <h1 className="text-4xl font-display font-bold text-gradient">
          Mission Control
        </h1>
        <p className="text-foreground-muted text-lg">
          Monitor and orchestrate your AI agent fleet
        </p>
      </motion.div>

      {/* Metrics Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        <MetricCard
          title="Active Agents"
          value={6}
          icon={Bot}
          trend={{ value: 2, isPositive: true }}
          variant="primary"
        />
        <MetricCard
          title="Tasks Completed"
          value={147}
          icon={CheckCircle2}
          trend={{ value: 23, isPositive: true }}
          subtitle="Today"
          variant="success"
        />
        <MetricCard
          title="Pending Tasks"
          value={12}
          icon={ListTodo}
          trend={{ value: 5, isPositive: false }}
          variant="warning"
        />
        <MetricCard
          title="Knowledge Objects"
          value={89}
          icon={Brain}
          trend={{ value: 7, isPositive: true }}
          subtitle="Approved"
          variant="info"
        />
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Status - Takes 2 columns */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2"
        >
          <div className="glass rounded-2xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary-500" />
                Agent Fleet Status
              </h2>
              <span className="text-sm text-foreground-muted">
                Last updated: just now
              </span>
            </div>
            <AgentStatusGrid />
          </div>
        </motion.div>

        {/* Recent Activity - Takes 1 column */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="glass rounded-2xl p-6 h-full">
            <h2 className="text-xl font-semibold flex items-center gap-2 mb-6">
              <Clock className="w-5 h-5 text-primary-500" />
              Recent Activity
            </h2>
            <RecentActivity />
          </div>
        </motion.div>
      </div>

      {/* System Health Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass rounded-2xl p-6"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-3 h-3 rounded-full bg-success animate-pulse" />
            <div>
              <h3 className="font-semibold">System Health: Optimal</h3>
              <p className="text-sm text-foreground-muted">
                All agents operating within normal parameters
              </p>
            </div>
          </div>
          <div className="flex items-center gap-6 text-sm">
            <div className="text-center">
              <div className="text-2xl font-bold text-gradient">91%</div>
              <div className="text-foreground-muted">Autonomy</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">42</div>
              <div className="text-foreground-muted">Tasks/Session</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-success">457x</div>
              <div className="text-foreground-muted">Cache Speed</div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
