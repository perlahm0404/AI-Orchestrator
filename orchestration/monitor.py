#!/usr/bin/env python3
"""
Real-time Agent Monitor Dashboard

Watches agent output files and displays live status in a terminal UI.

Usage:
    python -m orchestration.monitor
"""

import time
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def clear_screen():
    """Clear terminal screen."""
    print("\033[2J\033[H", end="")

def format_duration(seconds):
    """Format seconds into human readable duration."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds / 3600)
        mins = int((seconds % 3600) / 60)
        return f"{hours}h {mins}m"

class AgentMonitor:
    """Monitor multiple agents running in parallel."""

    def __init__(self):
        self.orchestrator_path = Path(__file__).parent.parent
        self.audit_path = self.orchestrator_path / "audit" / "sessions"
        self.agent_states = {}
        self.start_time = time.time()

    def get_recent_sessions(self):
        """Get most recent session files for active agents."""
        if not self.audit_path.exists():
            return []

        # Get all session files from last hour
        one_hour_ago = time.time() - 3600
        sessions = []

        for session_file in self.audit_path.glob("session-*.json"):
            if session_file.stat().st_mtime > one_hour_ago:
                try:
                    with open(session_file) as f:
                        data = json.load(f)
                        sessions.append({
                            "file": session_file,
                            "data": data,
                            "mtime": session_file.stat().st_mtime
                        })
                except:
                    pass

        # Sort by modification time (most recent first)
        sessions.sort(key=lambda x: x["mtime"], reverse=True)
        return sessions[:10]  # Show last 10 sessions

    def extract_agent_info(self, session):
        """Extract agent status from session data."""
        data = session["data"]

        # Find key events
        agent_type = "unknown"
        project = "unknown"
        task = ""
        status = "running"
        files_changed = []
        verdict = None
        last_event = None

        for entry in data:
            event = entry.get("event", "")
            details = entry.get("details", {})

            if event == "SESSION_STARTING":
                agent_type = details.get("agent_type", "unknown")
                project = details.get("project", "unknown")
                task = details.get("task", "")[:60]

            elif event == "CHANGES_DETECTED":
                files_changed = details.get("files", [])

            elif event == "FINAL_VERIFICATION_COMPLETE":
                verdict = details.get("verdict", "unknown")

            elif event == "SESSION_SUCCESS":
                status = "success"

            elif event == "VERDICT_BLOCKED_REVERTING":
                status = "blocked"
                verdict = "BLOCKED"

            elif event == "VERDICT_FAILED":
                status = "failed"
                verdict = "FAIL"

            last_event = entry

        return {
            "session_id": data[0].get("session_id", "unknown"),
            "agent_type": agent_type,
            "project": project,
            "task": task,
            "status": status,
            "files_changed": len(files_changed),
            "verdict": verdict,
            "last_event": last_event.get("event", "") if last_event else "",
            "last_time": last_event.get("timestamp", "") if last_event else "",
            "file": session["file"]
        }

    def render_dashboard(self, agents):
        """Render the monitoring dashboard."""
        clear_screen()

        # Header
        runtime = time.time() - self.start_time
        print("="*100)
        print(f"🤖 AI ORCHESTRATOR - PARALLEL AGENT MONITOR")
        print(f"Runtime: {format_duration(runtime)} | Active Agents: {len(agents)} | Last Update: {datetime.now().strftime('%H:%M:%S')}")
        print("="*100)
        print()

        if not agents:
            print("⏳ Waiting for agents to start...")
            print()
            print("No active sessions found in last hour.")
            print(f"Monitoring: {self.audit_path}")
            return

        # Agent status table
        print(f"{'AGENT':<15} {'PROJECT':<12} {'STATUS':<10} {'FILES':<6} {'VERDICT':<8} {'TASK':<50}")
        print("-"*100)

        for agent in agents:
            # Status emoji
            status_emoji = {
                "running": "🏃",
                "success": "✅",
                "blocked": "🚫",
                "failed": "❌"
            }.get(agent["status"], "❓")

            # Color coding (ANSI)
            status_color = {
                "running": "\033[93m",  # Yellow
                "success": "\033[92m",  # Green
                "blocked": "\033[91m",  # Red
                "failed": "\033[91m"    # Red
            }.get(agent["status"], "\033[0m")
            reset = "\033[0m"

            print(
                f"{status_emoji} {agent['agent_type']:<13} "
                f"{agent['project']:<12} "
                f"{status_color}{agent['status']:<10}{reset} "
                f"{agent['files_changed']:<6} "
                f"{agent['verdict'] or '-':<8} "
                f"{agent['task']}"
            )

        print()
        print("-"*100)
        print()

        # Recent events
        print("📋 RECENT EVENTS:")
        print()
        for agent in agents[:3]:  # Show last 3 agents
            print(f"  [{agent['last_time'][-8:]}] {agent['agent_type']}: {agent['last_event']}")

        print()
        print("="*100)
        print("Press Ctrl+C to exit | Refreshing every 3 seconds...")
        print()

    def run(self):
        """Run the monitoring loop."""
        try:
            while True:
                sessions = self.get_recent_sessions()
                agents = [self.extract_agent_info(s) for s in sessions]
                self.render_dashboard(agents)
                time.sleep(3)

        except KeyboardInterrupt:
            print("\n\n👋 Monitor stopped.")
            sys.exit(0)


def main():
    monitor = AgentMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
