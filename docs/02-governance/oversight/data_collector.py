"""
Data Collector - Aggregate metrics from sessions, work queues, KO system

Reads data from:
- sessions/*.md (session handoffs)
- tasks/work_queue*.json (task completion data)
- knowledge/metrics.json (KO consultation rates)
- governance/resource_tracker_state.json (cost data)

Usage:
    from governance.oversight.data_collector import DataCollector
    collector = DataCollector()
    data = collector.collect_all()
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class DataCollector:
    """Collect metrics data from various sources."""
    
    def __init__(self, orchestrator_root: Optional[Path] = None):
        """
        Initialize data collector.
        
        Args:
            orchestrator_root: AI_Orchestrator root directory (auto-detects if None)
        """
        if orchestrator_root is None:
            # Auto-detect: assumes we're in governance/oversight/
            self.root = Path(__file__).parent.parent.parent
        else:
            self.root = Path(orchestrator_root)
        
        self.sessions_dir = self.root / "sessions"
        self.tasks_dir = self.root / "tasks"
        self.knowledge_dir = self.root / "knowledge"
        self.governance_dir = self.root / "governance"
    
    def collect_all(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Collect all metrics data.
        
        Args:
            days_back: How many days of history to collect
            
        Returns:
            Dict with all collected data
        """
        return {
            "sessions": self.collect_sessions(days_back),
            "work_queues": self.collect_work_queues(),
            "ko_metrics": self.collect_ko_metrics(),
            "resource_tracker": self.collect_resource_tracker(),
            "collection_timestamp": datetime.now().isoformat()
        }
    
    def collect_sessions(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Parse session handoff files for metrics.
        
        Args:
            days_back: How many days of session history to read
            
        Returns:
            List of session data dicts
        """
        sessions = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        if not self.sessions_dir.exists():
            return sessions
        
        # Read all session markdown files
        for session_file in sorted(self.sessions_dir.glob("*.md")):
            # Extract date from filename (format: YYYY-MM-DD-*.md)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', session_file.name)
            if not date_match:
                continue
            
            try:
                file_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                if file_date < cutoff_date:
                    continue
            except ValueError:
                continue
            
            # Parse session file
            session_data = self._parse_session_file(session_file)
            if session_data:
                sessions.append(session_data)
        
        return sessions
    
    def _parse_session_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a session handoff markdown file."""
        try:
            content = file_path.read_text()
            
            # Extract key metrics from markdown
            session = {
                "filename": file_path.name,
                "date": self._extract_date(file_path.name),
                "tasks_completed": self._count_completed_tasks(content),
                "ralph_verdict": self._extract_ralph_verdict(content),
                "iterations": self._extract_iterations(content),
                "human_intervention_required": "BLOCKED" in content or "approval" in content.lower(),
                "completed": "COMPLETE" in content,
                "files_modified": self._extract_file_count(content),
            }
            
            return session
            
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return None
    
    def _extract_date(self, filename: str) -> str:
        """Extract date from filename."""
        match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        return match.group(1) if match else "unknown"
    
    def _count_completed_tasks(self, content: str) -> int:
        """Count completed tasks in session content."""
        # Look for checkmarks or "completed" mentions
        checkmarks = content.count("✅")
        completed_mentions = len(re.findall(r'completed\s+\d+\s+task', content, re.IGNORECASE))
        return max(checkmarks, completed_mentions, 1)  # At least 1 if session exists
    
    def _extract_ralph_verdict(self, content: str) -> str:
        """Extract Ralph verdict from content."""
        if "Verdict: PASS" in content:
            return "PASS"
        elif "Verdict: FAIL" in content:
            return "FAIL"
        elif "Verdict: BLOCKED" in content or "BLOCKED" in content:
            return "BLOCKED"
        return "UNKNOWN"
    
    def _extract_iterations(self, content: str) -> int:
        """Extract iteration count from content."""
        # Look for "iteration X" or "X iterations"
        match = re.search(r'(\d+)\s+iteration', content, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 1  # Default assumption
    
    def _extract_file_count(self, content: str) -> int:
        """Extract number of files modified."""
        # Look for file paths or "X files"
        file_mentions = len(re.findall(r'\.(py|ts|tsx|js|yaml|md):', content))
        count_match = re.search(r'(\d+)\s+files?\s+(changed|modified)', content, re.IGNORECASE)
        if count_match:
            return int(count_match.group(1))
        return max(file_mentions, 1)
    
    def collect_work_queues(self) -> List[Dict[str, Any]]:
        """Collect work queue data."""
        work_queues = []
        
        if not self.tasks_dir.exists():
            return work_queues
        
        # Read all work queue JSON files
        for queue_file in self.tasks_dir.glob("work_queue*.json"):
            try:
                with open(queue_file) as f:
                    data = json.load(f)
                    work_queues.append({
                        "filename": queue_file.name,
                        "project": data.get("project", "unknown"),
                        "task_count": len(data.get("features", [])),
                        "data": data
                    })
            except Exception as e:
                print(f"Warning: Failed to read {queue_file}: {e}")
        
        return work_queues
    
    def collect_ko_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect Knowledge Object metrics."""
        metrics_file = self.knowledge_dir / "metrics.json"
        
        if not metrics_file.exists():
            return None
        
        try:
            with open(metrics_file) as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to read KO metrics: {e}")
            return None
    
    def collect_resource_tracker(self) -> Optional[Dict[str, Any]]:
        """Collect resource tracker state (cost data)."""
        tracker_file = self.governance_dir / "resource_tracker_state.json"
        
        if not tracker_file.exists():
            return None
        
        try:
            with open(tracker_file) as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to read resource tracker: {e}")
            return None
