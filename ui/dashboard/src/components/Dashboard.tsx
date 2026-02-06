/**
 * Dashboard Component
 *
 * Main monitoring dashboard for AI Orchestrator autonomous loop.
 * Displays real-time task execution, Ralph verdicts, and event log.
 */

import { useQuery } from '@tanstack/react-query'
import { useWebSocket } from '../hooks/useWebSocket'

export function Dashboard() {
  const { isConnected, events, reconnectAttempts } = useWebSocket()

  // Get current task from cache (updated by useWebSocket)
  const { data: currentTask } = useQuery({
    queryKey: ['currentTask'],
    enabled: false, // Only updated via WebSocket
  })

  // Get verdicts from cache
  const { data: verdicts = [] } = useQuery<Array<{
    task_id: string
    verdict: string
    iterations: number
    summary?: string
  }>>({
    queryKey: ['verdicts'],
    enabled: false,
  })

  // Get loop status from cache
  const { data: loopStatus } = useQuery<{
    status: 'running' | 'completed'
    project?: string
    max_iterations?: number
  }>({
    queryKey: ['loopStatus'],
    enabled: false,
  })

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-4">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-blue-400">
              AI Orchestrator Monitoring
            </h1>
            <p className="text-gray-400 mt-2">
              Real-time autonomous loop monitoring dashboard
            </p>
          </div>

          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              } ${isConnected ? 'animate-pulse' : ''}`}
            ></div>
            <span className={isConnected ? 'text-green-400' : 'text-red-400'}>
              {isConnected ? 'Connected' : reconnectAttempts > 0 ? `Reconnecting... (${reconnectAttempts})` : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Loop Status */}
        {loopStatus && (
          <div className="mt-4 bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-gray-400">Loop Status:</span>
                <span className={`ml-2 font-semibold ${
                  loopStatus.status === 'running' ? 'text-blue-400' : 'text-green-400'
                }`}>
                  {loopStatus.status === 'running' ? '🔄 Running' : '✅ Completed'}
                </span>
              </div>
              {loopStatus.project && (
                <div className="text-sm text-gray-400">
                  Project: <span className="text-gray-200">{loopStatus.project}</span>
                  {loopStatus.max_iterations && (
                    <span className="ml-4">
                      Max Iterations: <span className="text-gray-200">{loopStatus.max_iterations}</span>
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Task */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4 text-blue-300">Current Task</h2>
          {currentTask ? (
            <div className="space-y-2">
              <div>
                <span className="text-gray-400">Task ID:</span>
                <span className="ml-2 font-mono text-yellow-400">{currentTask.task_id}</span>
              </div>
              <div>
                <span className="text-gray-400">Description:</span>
                <p className="mt-1 text-gray-200">{currentTask.description}</p>
              </div>
              <div>
                <span className="text-gray-400">File:</span>
                <span className="ml-2 font-mono text-sm text-gray-300">{currentTask.file}</span>
              </div>
              <div>
                <span className="text-gray-400">Attempts:</span>
                <span className="ml-2 text-orange-400">{currentTask.attempts}</span>
              </div>
              {currentTask.agent_type && (
                <div>
                  <span className="text-gray-400">Agent:</span>
                  <span className="ml-2 text-purple-400">{currentTask.agent_type}</span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500 italic">No task currently running</p>
          )}
        </div>

        {/* Recent Verdicts */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4 text-blue-300">Recent Verdicts</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {verdicts.length > 0 ? (
              verdicts.slice().reverse().map((v, i) => (
                <div
                  key={i}
                  className={`p-3 rounded border ${
                    v.verdict === 'PASS'
                      ? 'bg-green-900/20 border-green-700'
                      : v.verdict === 'FAIL'
                      ? 'bg-yellow-900/20 border-yellow-700'
                      : 'bg-red-900/20 border-red-700'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <span className="font-mono text-sm text-gray-300">{v.task_id}</span>
                    <span
                      className={`font-bold text-sm ${
                        v.verdict === 'PASS'
                          ? 'text-green-400'
                          : v.verdict === 'FAIL'
                          ? 'text-yellow-400'
                          : 'text-red-400'
                      }`}
                    >
                      {v.verdict === 'PASS' && '✅'}
                      {v.verdict === 'FAIL' && '⚠️'}
                      {v.verdict === 'BLOCKED' && '🚫'}
                      {' '}{v.verdict}
                    </span>
                  </div>
                  {v.summary && (
                    <p className="text-xs text-gray-400 mt-1">{v.summary}</p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    Iterations: {v.iterations}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-gray-500 italic">No verdicts yet</p>
            )}
          </div>
        </div>

        {/* Event Log (Full Width) */}
        <div className="lg:col-span-2 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4 text-blue-300">Event Log</h2>
          <div className="bg-gray-950 text-green-400 p-4 rounded font-mono text-xs h-96 overflow-y-auto">
            {events.length > 0 ? (
              events.map((event, i) => (
                <div key={i} className="mb-1">
                  <span className="text-gray-500">[{new Date(event.timestamp).toLocaleTimeString()}]</span>
                  {' '}
                  <span
                    className={
                      event.severity === 'error'
                        ? 'text-red-400'
                        : event.severity === 'warning'
                        ? 'text-yellow-400'
                        : 'text-green-400'
                    }
                  >
                    {event.type}
                  </span>
                  {': '}
                  <span className="text-gray-400">{JSON.stringify(event.data)}</span>
                </div>
              ))
            ) : (
              <p className="text-gray-600 italic">
                Waiting for events... Start autonomous loop with --enable-monitoring to see live updates.
              </p>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-8 text-center text-gray-500 text-sm">
        <p>
          WebSocket: <code className="text-gray-400">ws://localhost:8080/ws</code>
        </p>
        <p className="mt-2">
          Events tracked: {events.length}
        </p>
      </footer>
    </div>
  )
}
