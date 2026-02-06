import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-900 text-gray-100 p-4">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-blue-400">
            AI Orchestrator Monitoring
          </h1>
          <p className="text-gray-400 mt-2">
            Real-time autonomous loop monitoring dashboard
          </p>
        </header>

        <main>
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">Dashboard Status</h2>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-gray-500"></div>
              <span className="text-gray-400">Disconnected</span>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              WebSocket connection will be established when autonomous loop is running with --enable-monitoring flag
            </p>
          </div>
        </main>
      </div>
    </QueryClientProvider>
  )
}

export default App
