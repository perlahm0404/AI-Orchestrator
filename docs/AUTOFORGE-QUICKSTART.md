# AutoForge Quick Start Guide

**Last Updated**: 2026-02-05
**Status**: Production Ready ✅

---

## What is AutoForge?

AutoForge is the AI Orchestrator's autonomous loop system with real-time monitoring. It processes work queues automatically with live visibility into task execution, Ralph verdicts, and agent activity.

**Key Features**:
- 🤖 Autonomous task processing
- 📊 Real-time UI dashboard
- ✅ Ralph verification at every step
- 🔔 Webhook notifications (Slack/Discord)
- 📈 SQLite work queue with epic→feature→task hierarchy

---

## Quick Start (2 Steps)

### Step 1: Start the Dashboard (Terminal 1)

```bash
cd ui/dashboard
npm install              # First time only
npm run dev
```

Dashboard opens at **http://localhost:3000**

### Step 2: Start Autonomous Loop (Terminal 2)

```bash
# Basic (JSON work queue)
python autonomous_loop.py --project karematch --enable-monitoring

# Advanced (SQLite work queue + webhooks)
python autonomous_loop.py \
  --project karematch \
  --use-sqlite \
  --enable-monitoring \
  --webhook-url https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**That's it!** Open your browser to http://localhost:3000 and watch the magic happen. 🎉

---

## What You'll See

### Dashboard Sections

| Section | What It Shows |
|---------|---------------|
| **Connection Status** | 🟢 Connected / 🔴 Disconnected |
| **Loop Status** | Project name, iterations, running/completed |
| **Current Task** | Active task ID, description, file, attempts |
| **Recent Verdicts** | Last 50 Ralph results (🟢 PASS / 🟡 FAIL / 🔴 BLOCKED) |
| **Event Log** | Live stream of all events (last 100) |

### Event Types You'll See

- **loop_start** - 🚀 Autonomous loop begins
- **task_start** - 📝 Task execution starts
- **task_complete** - ✅ Task finishes (PASS/FAIL/BLOCKED)
- **ralph_verdict** - 🔍 Ralph verification result
- **loop_complete** - 🏁 All tasks processed

---

## Common Commands

### JSON Work Queue Mode (Default)

```bash
# Start loop with monitoring
python autonomous_loop.py --project karematch --enable-monitoring

# Limit iterations
python autonomous_loop.py --project karematch --enable-monitoring --max-iterations 50

# Add Slack notifications
python autonomous_loop.py --project karematch --enable-monitoring \
  --webhook-url https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### SQLite Work Queue Mode (Recommended)

```bash
# With epic→feature→task hierarchy
python autonomous_loop.py --project karematch --use-sqlite --enable-monitoring

# Filter by epic
python autonomous_loop.py --project karematch --use-sqlite --enable-monitoring \
  --epic EPIC-001

# With all features
python autonomous_loop.py \
  --project karematch \
  --use-sqlite \
  --enable-monitoring \
  --webhook-url https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  --max-iterations 100
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Orchestrator                            │
│                                                                 │
│  ┌──────────────────┐           ┌──────────────────┐          │
│  │  Autonomous Loop │◄─────────►│  WebSocket Server│          │
│  │  (Task Engine)   │  Events   │  (Port 8080)     │          │
│  └────────┬─────────┘           └────────┬─────────┘          │
│           │                              │                      │
│           ▼                              ▼                      │
│    ┌─────────────┐               ┌─────────────┐              │
│    │ Work Queue  │               │  React UI   │              │
│    │ SQLite/JSON │               │ Dashboard   │              │
│    └─────────────┘               └─────────────┘              │
│                                   http://localhost:3000        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Work Queue Options

### Option 1: JSON Work Queue (Simple)

**File**: `tasks/work_queue_{project}.json`

**Structure**:
```json
{
  "tasks": [
    {
      "id": "BUG-001",
      "description": "Fix TypeScript errors",
      "status": "pending"
    }
  ]
}
```

**Pros**: Simple, human-readable, easy to edit
**Cons**: No hierarchy, manual task management

### Option 2: SQLite Work Queue (Advanced)

**File**: `.aibrain/work_queue.db`

**Structure**: Epic → Feature → Task hierarchy
```
EPIC-001: Code Quality Sprint
  ├── FEAT-001: Fix TypeScript Errors
  │   ├── TASK-001: Fix login.ts errors
  │   └── TASK-002: Fix dashboard.ts errors
  └── FEAT-002: Add Tests
      └── TASK-003: Add unit tests
```

**Pros**: Hierarchy, progress tracking, database queries
**Cons**: Requires SQLite, less visible to humans

**Create SQLite queue**:
```bash
python -c "from orchestration.queue_manager import WorkQueueManager; \
           WorkQueueManager('.aibrain/work_queue.db')._initialize_schema()"
```

---

## Webhook Notifications

Send real-time notifications to Slack, Discord, or N8N when tasks complete.

### Setup Slack

1. **Create webhook**: https://api.slack.com/messaging/webhooks
2. **Copy webhook URL**: `https://hooks.slack.com/services/XXX/YYY/ZZZ`
3. **Add to command**:
   ```bash
   python autonomous_loop.py --project karematch --enable-monitoring \
     --webhook-url https://hooks.slack.com/services/XXX/YYY/ZZZ
   ```

**Slack Message Example**:
```
✅ Task Complete

Task ID: TASK-ABC123
Verdict: ✅ PASS
Iterations: 5
Files Changed: 2

Changed Files:
• src/auth/login.ts
• tests/auth/test_login.py
```

### Setup Discord

1. **Create webhook**: Channel Settings → Integrations → Webhooks
2. **Copy webhook URL**: `https://discord.com/api/webhooks/XXX/YYY`
3. **Add to command** (same as Slack)

### Setup N8N

See `examples/n8n_workflow.json` for complete workflow with:
- Error filtering (only alerts on BLOCKED tasks)
- Slack notifications
- Jira ticket creation
- Database logging

---

## Troubleshooting

### Dashboard shows "Disconnected"

**Cause**: WebSocket server not running

**Fix**:
1. Make sure autonomous loop is running with `--enable-monitoring`
2. Check server health:
   ```bash
   curl http://localhost:8080/health
   # Should return: {"status":"healthy","active_connections":0}
   ```
3. Restart autonomous loop with monitoring enabled

### Events not appearing

**Cause**: No tasks in queue or queue not loading

**Fix**:
1. Check work queue has tasks:
   ```bash
   # JSON mode
   cat tasks/work_queue_karematch.json

   # SQLite mode
   sqlite3 .aibrain/work_queue.db "SELECT * FROM tasks WHERE status='pending';"
   ```
2. Add test task to queue
3. Restart autonomous loop

### Port 3000 already in use

**Cause**: Another app using port 3000

**Fix**:
```bash
# Use different port
npm run dev -- --port 3001
```

Then open http://localhost:3001

### "Max reconnection attempts reached"

**Cause**: WebSocket server crashed or restarted

**Fix**:
1. Refresh dashboard (Ctrl+R / Cmd+R)
2. Restart autonomous loop with monitoring
3. Check server logs for errors

---

## CLI Flags Reference

### Required

| Flag | Description |
|------|-------------|
| `--project <name>` | Project to process (karematch, credentialmate, ai-orchestrator) |

### Optional

| Flag | Description | Default |
|------|-------------|---------|
| `--enable-monitoring` | Start WebSocket server for UI dashboard | Disabled |
| `--use-sqlite` | Use SQLite work queue (epic→feature→task) | JSON mode |
| `--webhook-url <url>` | Send notifications to webhook endpoint | None |
| `--max-iterations <n>` | Maximum tasks to process | 100 |
| `--epic <id>` | Filter to specific epic (SQLite only) | All epics |
| `--non-interactive` | Auto-revert guardrail violations | Interactive |
| `--bypass-mode <mode>` | SAFE/FAST/DANGEROUS/YOLO (governance bypass) | SAFE |

---

## Examples

### Example 1: Simple Monitoring

```bash
# Terminal 1: Start dashboard
cd ui/dashboard && npm run dev

# Terminal 2: Start loop
python autonomous_loop.py --project karematch --enable-monitoring
```

**Use Case**: Quick testing, watching task execution

---

### Example 2: Production Setup

```bash
# Terminal 1: Dashboard
cd ui/dashboard && npm run dev

# Terminal 2: Loop with SQLite + Slack
python autonomous_loop.py \
  --project karematch \
  --use-sqlite \
  --enable-monitoring \
  --webhook-url https://hooks.slack.com/services/XXX/YYY/ZZZ \
  --max-iterations 200
```

**Use Case**: Full-featured production run with notifications

---

### Example 3: Epic-Specific Work

```bash
# Terminal 1: Dashboard
cd ui/dashboard && npm run dev

# Terminal 2: Process specific epic only
python autonomous_loop.py \
  --project karematch \
  --use-sqlite \
  --enable-monitoring \
  --epic EPIC-QUALITY-001
```

**Use Case**: Focused work on single epic (e.g., "Code Quality Sprint")

---

### Example 4: Fast Mode (Dangerous Bypass)

```bash
# Terminal 1: Dashboard
cd ui/dashboard && npm run dev

# Terminal 2: Fast mode (bypasses most Ralph checks)
python autonomous_loop.py \
  --project karematch \
  --use-sqlite \
  --enable-monitoring \
  --bypass-mode fast \
  --max-iterations 50
```

**Use Case**: Rapid iteration on stable code (⚠️ use with caution)

---

## Related Documentation

### Core Documentation

- **[Dashboard README](../ui/dashboard/README.md)** - Detailed UI documentation (335 lines)
- **[Webhook Guide](./16-testing/webhooks.md)** - Webhook notifications setup (562 lines)
- **[Bypass Mode](./17-governance/bypass-mode.md)** - Fast mode documentation (400+ lines)

### Knowledge Objects

- **[KO-aio-002](../knowledge/approved/KO-aio-002.md)** - SQLite work queue design
- **[KO-aio-003](../knowledge/approved/KO-aio-003.md)** - Real-time monitoring UI
- **[KO-aio-004](../knowledge/approved/KO-aio-004.md)** - Feature hierarchy system
- **[KO-aio-005](../knowledge/approved/KO-aio-005.md)** - Webhook notifications

### Session Reflections

- **[Phase 4 Reflection](../sessions/ai-orchestrator/active/20260205-PHASE4-REFLECTION-webhook-system-learnings.md)** - Complete learnings (832 lines)
- **[Phase 4 Summary](../sessions/ai-orchestrator/active/20260205-PHASE4-COMPLETE-webhook-notifications-tdd.md)** - Implementation details (632 lines)

---

## Advanced Topics

### Custom Event Handlers

Add custom event types in `orchestration/monitoring_integration.py`:

```python
async def send_custom_event(websocket_server, data):
    await websocket_server.broadcast({
        "type": "custom_event",
        "severity": "info",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    })
```

### SQLite Database Queries

Query work queue directly:

```bash
# Show all epics
sqlite3 .aibrain/work_queue.db "SELECT * FROM epics;"

# Show pending tasks
sqlite3 .aibrain/work_queue.db \
  "SELECT t.id, t.description, f.name as feature
   FROM tasks t JOIN features f ON t.feature_id = f.id
   WHERE t.status = 'pending';"

# Show epic progress
sqlite3 .aibrain/work_queue.db \
  "SELECT e.name,
   COUNT(t.id) as total_tasks,
   SUM(CASE WHEN t.status='completed' THEN 1 ELSE 0 END) as completed
   FROM epics e
   JOIN features f ON e.id = f.epic_id
   JOIN tasks t ON f.id = t.feature_id
   GROUP BY e.id;"
```

### Multiple Projects

Run multiple autonomous loops with monitoring:

```bash
# Terminal 1: Dashboard (shared)
cd ui/dashboard && npm run dev

# Terminal 2: KareMatch loop (port 8080)
python autonomous_loop.py --project karematch --enable-monitoring

# Terminal 3: CredentialMate loop (port 8081)
python autonomous_loop.py --project credentialmate --enable-monitoring --port 8081
```

Then update `ui/dashboard/src/hooks/useWebSocket.ts` to switch between servers.

---

## Production Deployment

### Dashboard Production Build

```bash
cd ui/dashboard
npm run build
npm run preview  # Test production build
```

**Deployment options**:
- Serve `dist/` with nginx/Apache
- Deploy to Vercel/Netlify
- Use Docker container

### WebSocket Server in Production

**Options**:
1. **Run as systemd service** (Linux)
2. **Run in tmux/screen** (Unix)
3. **Use process manager** (PM2, supervisord)

**Example systemd service**:
```ini
[Unit]
Description=AI Orchestrator Autonomous Loop
After=network.target

[Service]
Type=simple
User=tmac
WorkingDirectory=/Users/tmac/1_REPOS/AI_Orchestrator
ExecStart=/usr/bin/python3 autonomous_loop.py --project karematch --enable-monitoring --use-sqlite
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## FAQ

**Q: Can I run the loop without the dashboard?**
A: Yes! Just omit `--enable-monitoring` flag. Dashboard is optional.

**Q: Does the dashboard work with JSON and SQLite modes?**
A: Yes! It works with both work queue modes.

**Q: Can I have multiple dashboards open?**
A: Yes! WebSocket server supports multiple concurrent connections.

**Q: Will the loop crash if the dashboard disconnects?**
A: No! The loop continues running. Dashboard can reconnect anytime.

**Q: Can I use webhooks without the dashboard?**
A: Yes! Webhooks and monitoring are independent features.

**Q: How do I stop the loop gracefully?**
A: Press Ctrl+C in the terminal. It will finish the current task and exit.

**Q: Where are the logs?**
A: Check `.aibrain/agent-loop.local.md` for state and terminal output for real-time logs.

---

## Next Steps

1. **Try it out**: Start with Example 1 (Simple Monitoring)
2. **Add Slack**: Follow webhook setup to get notifications
3. **Use SQLite**: Switch to SQLite mode for better organization
4. **Read the docs**: Dive into Dashboard README for advanced features

---

**Version**: 1.0.0
**Status**: Production Ready ✅
**Support**: Check troubleshooting section or create GitHub issue

Happy automating! 🚀
