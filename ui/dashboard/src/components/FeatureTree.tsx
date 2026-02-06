/**
 * FeatureTree: Hierarchical view of work queue (Epic → Feature → Task)
 *
 * Displays collapsible tree with progress bars and status color coding.
 * Reference: KO-aio-003, KO-aio-004
 */

import { useState } from 'react'

interface Task {
  id: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'blocked'
  retry_budget: number
  retries_used: number
}

interface Feature {
  id: string
  name: string
  priority: number
  status: 'pending' | 'in_progress' | 'completed' | 'blocked'
  tasks: Task[]
}

interface Epic {
  id: string
  name: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed' | 'blocked'
  features: Feature[]
}

interface FeatureTreeProps {
  data: { epics: Epic[] }
  onTaskClick?: (task: Task) => void
}

export function FeatureTree({ data, onTaskClick }: FeatureTreeProps) {
  const [expandedEpics, setExpandedEpics] = useState<Set<string>>(
    new Set(data.epics.map(e => e.id)) // Expand all by default
  )
  const [expandedFeatures, setExpandedFeatures] = useState<Set<string>>(
    new Set(data.epics.flatMap(e => e.features.map(f => f.id))) // Expand all by default
  )

  const toggleEpic = (epicId: string) => {
    setExpandedEpics(prev => {
      const next = new Set(prev)
      if (next.has(epicId)) {
        next.delete(epicId)
      } else {
        next.add(epicId)
      }
      return next
    })
  }

  const toggleFeature = (featureId: string) => {
    setExpandedFeatures(prev => {
      const next = new Set(prev)
      if (next.has(featureId)) {
        next.delete(featureId)
      } else {
        next.add(featureId)
      }
      return next
    })
  }

  const calculateProgress = (items: { status: string }[]) => {
    if (items.length === 0) return 0
    const completed = items.filter(i => i.status === 'completed').length
    return Math.round((completed / items.length) * 100)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'text-gray-400'
      case 'in_progress':
        return 'text-blue-400'
      case 'completed':
        return 'text-green-400'
      case 'blocked':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-500/20'
      case 'in_progress':
        return 'bg-blue-500/20'
      case 'completed':
        return 'bg-green-500/20'
      case 'blocked':
        return 'bg-red-500/20'
      default:
        return 'bg-gray-500/20'
    }
  }

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 0:
        return 'bg-red-500 text-white'
      case 1:
        return 'bg-orange-500 text-white'
      default:
        return 'bg-gray-500 text-white'
    }
  }

  if (!data.epics || data.epics.length === 0) {
    return (
      <div className="text-center text-gray-400 py-8">
        No work queue data available
      </div>
    )
  }

  return (
    <div role="tree" className="space-y-4">
      {data.epics.map(epic => {
        const isExpanded = expandedEpics.has(epic.id)
        const allTasks = epic.features.flatMap(f => f.tasks)
        const epicProgress = calculateProgress(allTasks)

        return (
          <div key={epic.id} className="border border-gray-700 rounded-lg p-4">
            {/* Epic Header */}
            <div
              className="flex items-center justify-between cursor-pointer hover:bg-gray-800/50 -m-4 p-4 rounded-lg"
              onClick={() => toggleEpic(epic.id)}
              onKeyDown={(e) => e.key === 'Enter' && toggleEpic(epic.id)}
              tabIndex={0}
            >
              <div className="flex items-center gap-3 flex-1">
                <span className="text-gray-400">
                  {isExpanded ? '▼' : '▶'}
                </span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold ${getStatusColor(epic.status)}`}>
                      📦 {epic.name}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded ${getStatusBg(epic.status)}`}>
                      {epic.status}
                    </span>
                  </div>
                  {epic.description && (
                    <div className="text-sm text-gray-500 mt-1">{epic.description}</div>
                  )}
                </div>
              </div>

              {/* Epic Progress */}
              <div className="flex items-center gap-2 min-w-[200px]">
                <div className="flex-1">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Epic Progress</span>
                    <span>{epicProgress}%</span>
                  </div>
                  <div
                    role="progressbar"
                    aria-label="epic progress"
                    className="h-2 bg-gray-700 rounded-full overflow-hidden"
                  >
                    <div
                      className="h-full bg-green-500 transition-all duration-300"
                      style={{ width: `${epicProgress}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Features */}
            {isExpanded && (
              <div className="mt-4 ml-8 space-y-3">
                {epic.features.length === 0 ? (
                  <div className="text-gray-500 text-sm">No features in this epic</div>
                ) : (
                  epic.features.map(feature => {
                    const featureExpanded = expandedFeatures.has(feature.id)
                    const featureProgress = calculateProgress(feature.tasks)

                    return (
                      <div key={feature.id} className="border-l-2 border-gray-700 pl-4">
                        {/* Feature Header */}
                        <div
                          className="flex items-center justify-between cursor-pointer hover:bg-gray-800/30 -ml-4 pl-4 py-2 rounded"
                          onClick={() => toggleFeature(feature.id)}
                          onKeyDown={(e) => e.key === 'Enter' && toggleFeature(feature.id)}
                          tabIndex={0}
                        >
                          <div className="flex items-center gap-2 flex-1">
                            <span className="text-gray-400 text-sm">
                              {featureExpanded ? '▼' : '▶'}
                            </span>
                            <span className={`text-sm ${getStatusColor(feature.status)}`}>
                              📂 {feature.name}
                            </span>
                            <span className={`text-xs px-1.5 py-0.5 rounded ${getPriorityColor(feature.priority)}`}>
                              P{feature.priority}
                            </span>
                            <span className={`text-xs px-2 py-0.5 rounded ${getStatusBg(feature.status)}`}>
                              {feature.status}
                            </span>
                          </div>

                          {/* Feature Progress */}
                          <div className="flex items-center gap-2 min-w-[180px]">
                            <div className="flex-1">
                              <div className="flex justify-between text-xs text-gray-400 mb-1">
                                <span>Feature Progress</span>
                                <span>{featureProgress}%</span>
                              </div>
                              <div
                                role="progressbar"
                                aria-label="feature progress"
                                className="h-1.5 bg-gray-700 rounded-full overflow-hidden"
                              >
                                <div
                                  className="h-full bg-blue-500 transition-all duration-300"
                                  style={{ width: `${featureProgress}%` }}
                                />
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Tasks */}
                        {featureExpanded && (
                          <div className="mt-2 ml-6 space-y-1">
                            {feature.tasks.map(task => (
                              <div
                                key={task.id}
                                className="flex items-center gap-2 text-sm hover:bg-gray-800/20 p-2 rounded cursor-pointer"
                                onClick={() => onTaskClick?.(task)}
                              >
                                <span className={getStatusColor(task.status)}>
                                  {task.status === 'completed' ? '✓' : '○'}
                                </span>
                                <span className={`flex-1 ${getStatusColor(task.status)}`}>
                                  {task.description}
                                </span>
                                <span className="text-xs text-gray-500">
                                  {task.retries_used}/{task.retry_budget} retries
                                </span>
                                <span className={`text-xs px-2 py-0.5 rounded ${getStatusBg(task.status)}`}>
                                  {task.status}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
