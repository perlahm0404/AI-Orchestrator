# AI Orchestrator Monitoring Dashboard

Real-time monitoring UI for the AI Orchestrator autonomous loop. Provides live visibility into task execution, Ralph verdicts, and agent activity via WebSocket streaming.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- 🔄 **Real-time Updates** - WebSocket connection to autonomous loop
- 📊 **Task Monitoring** - See currently executing tasks with details
- ✅ **Verdict Tracking** - Color-coded Ralph verification results
- 📝 **Event Log** - Terminal-style event stream (last 100 events)
- 🔌 **Auto-Reconnect** - Handles connection failures gracefully
- 🎨 **Dark Theme** - Easy-on-the-eyes UI for long monitoring sessions

## Quick Start

### Prerequisites

- Node.js 18+ (for Vite)
- Autonomous loop running with `--enable-monitoring` flag

### Installation

```bash
cd ui/dashboard
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

Dashboard will be available at **http://localhost:3000**

### Production Build

```bash
npm run build
npm run preview
```

## Usage

### 1. Start Autonomous Loop with Monitoring

```bash
# From project root
python autonomous_loop.py --project karematch --enable-monitoring
```

This starts:
- Autonomous loop (processes tasks)
- WebSocket server at `ws://localhost:8080/ws`

### 2. Open Dashboard

Navigate to **http://localhost:3000** in your browser.

### 3. Monitor Real-time Activity

The dashboard will automatically connect and display:

| Section | Description |
|---------|-------------|
| **Connection Status** | Green = connected, Red = disconnected |
| **Loop Status** | Shows project name, max iterations, running/completed |
| **Current Task** | Active task details (ID, description, file, attempts) |
| **Recent Verdicts** | Last 50 Ralph verdicts with color coding |
| **Event Log** | Live stream of all events (100 event buffer) |

## Architecture

```
┌─────────────────────┐         WebSocket          ┌─────────────────────┐
│  Autonomous Loop    │ ◄──────────────────────────►│  React Dashboard    │
│  (Python)           │  JSON event stream          │  (TypeScript)       │
└──────────┬──────────┘                             └──────────┬──────────┘
           │                                                   │
           │ Events:                                           │
           │ - loop_start                                      │
           │ - task_start                                      │
           │ - task_complete                                   │
           │ - ralph_verdict                                   │
           │ - loop_complete                                   │
           ▼                                                   ▼
    ┌─────────────┐                                    ┌─────────────┐
    │ FastAPI     │                                    │ TanStack    │
    │ WS Server   │                                    │ Query Cache │
    └─────────────┘                                    └─────────────┘
```

### Components

| Component | File | Purpose |
|-----------|------|---------|
| **Dashboard** | `src/components/Dashboard.tsx` | Main UI layout and data display |
| **useWebSocket** | `src/hooks/useWebSocket.ts` | WebSocket connection management |
| **App** | `src/App.tsx` | Root component with QueryClient |

### Event Types

Events streamed from autonomous loop:

```typescript
{
  type: "task_start",
  severity: "info" | "warning" | "error",
  timestamp: "2026-02-05T18:00:00.000Z",
  data: {
    task_id: "BUG-001",
    description: "Fix TypeScript errors",
    file: "src/app.ts",
    attempts: 0
  }
}
```

**Event Types:**
- `connection_established` - Initial connection confirmed
- `loop_start` - Autonomous loop begins
- `task_start` - Task execution starts
- `task_complete` - Task finishes (verdict: PASS/FAIL/BLOCKED)
- `ralph_verdict` - Ralph verification result
- `loop_complete` - All tasks processed

## Configuration

### WebSocket URL

Default: `ws://localhost:8080/ws`

To change:

```typescript
// src/hooks/useWebSocket.ts
const { isConnected, events } = useWebSocket({
  url: 'ws://your-server:port/ws'
})
```

### Event History Limit

Default: 100 events

```typescript
useWebSocket({
  eventHistoryLimit: 200 // Keep last 200 events
})
```

### Reconnection Settings

```typescript
useWebSocket({
  reconnectDelay: 3000,        // 3 seconds between attempts
  maxReconnectAttempts: 10     // Max 10 attempts
})
```

## Troubleshooting

### Dashboard shows "Disconnected"

**Problem:** Dashboard can't connect to WebSocket server

**Solutions:**
1. Ensure autonomous loop is running with `--enable-monitoring`:
   ```bash
   python autonomous_loop.py --project karematch --enable-monitoring
   ```

2. Check WebSocket server is running:
   ```bash
   curl http://localhost:8080/health
   # Should return: {"status":"healthy","active_connections":0}
   ```

3. Check browser console for errors (F12 → Console)

### Events not showing

**Problem:** Connected but no events appear

**Solutions:**
1. Verify autonomous loop is processing tasks:
   ```bash
   # Check work queue has pending tasks
   python -m tasks.work_queue list --project karematch
   ```

2. Check autonomous loop terminal for errors

3. Refresh dashboard (Ctrl+R / Cmd+R)

### "Max reconnection attempts reached"

**Problem:** Can't reconnect after 10 attempts

**Solutions:**
1. Restart autonomous loop with monitoring enabled
2. Refresh dashboard browser tab
3. Check server logs for errors

### Port 3000 already in use

**Problem:** `npm run dev` fails with port conflict

**Solution:**
```bash
# Use different port
npm run dev -- --port 3001
```

Or edit `vite.config.ts`:
```typescript
export default defineConfig({
  server: {
    port: 3001
  }
})
```

## Development

### Project Structure

```
ui/dashboard/
├── src/
│   ├── components/
│   │   └── Dashboard.tsx       # Main dashboard component
│   ├── hooks/
│   │   └── useWebSocket.ts     # WebSocket connection hook
│   ├── App.tsx                 # Root component
│   ├── main.tsx                # Entry point
│   └── index.css               # Tailwind styles
├── public/                     # Static assets
├── package.json                # Dependencies
├── vite.config.ts             # Vite configuration
├── tailwind.config.js         # Tailwind configuration
└── tsconfig.json              # TypeScript configuration
```

### Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite 7** - Build tool and dev server
- **TailwindCSS 3** - Styling
- **TanStack Query 5** - State management and caching
- **WebSocket API** - Real-time communication

### Adding New Features

#### Add new event type

1. Update `useWebSocket.ts` event handler:
```typescript
switch (data.type) {
  case 'your_new_event':
    queryClient.setQueryData(['yourData'], data.data)
    break
}
```

2. Display in Dashboard:
```typescript
const { data: yourData } = useQuery({
  queryKey: ['yourData'],
  enabled: false
})
```

#### Add new dashboard section

1. Create component in `src/components/`
2. Import in `Dashboard.tsx`
3. Add to grid layout

## Testing

### Manual Testing

1. Start autonomous loop with monitoring
2. Open dashboard at http://localhost:3000
3. Verify connection status shows "Connected" (green)
4. Check that events appear in Event Log
5. Verify Current Task updates when tasks execute
6. Confirm Recent Verdicts shows PASS/FAIL/BLOCKED results

### WebSocket Testing

Test WebSocket server independently:

```bash
# Install wscat
npm install -g wscat

# Connect to server
wscat -c ws://localhost:8080/ws

# Should receive connection_established event
```

## Related Documentation

- [KO-aio-003](../../knowledge/approved/KO-aio-003.md) - Real-time monitoring UI architecture
- [WebSocket Server](../../orchestration/websocket_server.py) - Backend implementation
- [Monitoring Integration](../../orchestration/monitoring_integration.py) - Autonomous loop integration
- [AutoForge Assessment](../../sessions/ai-orchestrator/active/20260205-autoforge-assessment.md) - Design rationale

## License

MIT

## Support

For issues or questions:
1. Check this README's troubleshooting section
2. Review browser console for errors (F12)
3. Check autonomous loop logs
4. Create issue at GitHub repository

---

**Version**: 1.0.0
**Last Updated**: 2026-02-05
**Status**: Production Ready ✅
