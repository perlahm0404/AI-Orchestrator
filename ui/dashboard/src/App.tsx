/**
 * AI Orchestrator Dashboard
 *
 * Main application with Kanban board for tracking multi-agent tasks.
 * Supports multiple projects with real-time WebSocket updates.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useWebSocket } from './hooks/useWebSocket'
import { useTaskStore } from './stores/taskStore'
import { KanbanBoard } from './components/kanban/KanbanBoard'
import { ProjectSwitcher } from './components/projects/ProjectSwitcher'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

/**
 * Main Dashboard Layout
 *
 * Includes header with project switcher, connection status,
 * and main content area with Kanban board.
 */
function DashboardLayout() {
  const { isConnected, events, reconnectAttempts } = useWebSocket()
  const selectedProject = useTaskStore((state) => state.selectedProject)

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div>
              <h1 className="text-xl font-bold text-blue-400">
                AI Orchestrator
              </h1>
              <p className="text-xs text-gray-500">
                Multi-Agent Task Dashboard
              </p>
            </div>

            {/* Project Switcher */}
            <ProjectSwitcher />
          </div>

          {/* Connection Status */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div
                className={`w-2.5 h-2.5 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                } ${isConnected ? 'animate-pulse' : ''}`}
              ></div>
              <span className={`text-sm ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
                {isConnected
                  ? 'Connected'
                  : reconnectAttempts > 0
                  ? `Reconnecting (${reconnectAttempts})`
                  : 'Disconnected'}
              </span>
            </div>

            {/* Event counter */}
            <span className="text-xs text-gray-500">
              {events.length} events
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-4 overflow-hidden">
        {selectedProject ? (
          <KanbanBoard project={selectedProject} />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <h2 className="text-2xl font-semibold text-gray-400 mb-2">
                Select a Project
              </h2>
              <p className="text-gray-500">
                Choose a project from the dropdown above to view its Kanban board.
              </p>
              <p className="text-gray-600 text-sm mt-4">
                Make sure the WebSocket server is running:
              </p>
              <code className="text-gray-400 text-sm bg-gray-800 px-3 py-1 rounded mt-2 inline-block">
                python -m orchestration.websocket_server
              </code>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 px-4 py-2 text-center text-xs text-gray-500">
        <span>WebSocket: </span>
        <code className="text-gray-400">ws://localhost:8080/ws</code>
        <span className="mx-2">|</span>
        <span>API: </span>
        <code className="text-gray-400">http://localhost:8080/api</code>
      </footer>
    </div>
  )
}

/**
 * Project-specific Kanban page
 */
function ProjectKanban() {
  const selectedProject = useTaskStore((state) => state.selectedProject)

  if (!selectedProject) {
    return <Navigate to="/" replace />
  }

  return <KanbanBoard project={selectedProject} />
}

/**
 * Root App Component
 */
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<DashboardLayout />} />
          <Route path="/project/:projectName" element={<ProjectKanban />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
