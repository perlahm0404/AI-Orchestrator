"""
Report Formatter - Format reports in markdown, grid, and JSON formats.

Supports three output formats:
- Markdown: Human-readable with tables and emojis
- Grid: Plain ASCII tables (parseable, no emojis)
- JSON: Machine-readable for programmatic access
"""

import json
from typing import Dict, Any
from datetime import datetime


class ReportFormatter:
    """Format reports in multiple formats"""

    @staticmethod
    def format_markdown(data: Dict[str, Any]) -> str:
        """Format as markdown with tables and emojis"""
        lines = []

        # Header
        lines.append(f"# 📊 {data['project'].upper()} - STATUS REPORT")
        lines.append(f"Generated: {data['generated_at']}")
        lines.append("PM Reporting System v6.1")
        lines.append("")
        lines.append("━" * 60)
        lines.append("")

        # Task Summary
        lines.append("## 📈 TASK SUMMARY")
        lines.append("")
        lines.append("| Status | Count | % |")
        lines.append("|--------|-------|---|")
        lines.append(f"| ✅ Completed | {data['tasks_completed']} | {int(data['tasks_completed']/max(data['total_tasks'],1)*100)}% |")
        lines.append(f"| 🚧 In Progress | {data['tasks_in_progress']} | {int(data['tasks_in_progress']/max(data['total_tasks'],1)*100)}% |")
        lines.append(f"| ⏸️  Pending | {data['tasks_pending']} | {int(data['tasks_pending']/max(data['total_tasks'],1)*100)}% |")
        lines.append(f"| 🚫 Blocked | {data['tasks_blocked']} | {int(data['tasks_blocked']/max(data['total_tasks'],1)*100)}% |")
        lines.append(f"| **Total** | **{data['total_tasks']}** | **100%** |")
        lines.append("")

        # ADR Rollup
        lines.append("## 🎯 ADR ROLLUP")
        lines.append("")
        if data.get('adrs'):
            lines.append("| ADR | Title | Tasks | Open | Complete | Evidence |")
            lines.append("|-----|-------|-------|------|----------|----------|")
            for adr in data['adrs']:
                evidence_badge = "✅" if adr['evidence_refs'] else "❌ None"
                evidence_str = f"{evidence_badge} {', '.join(adr['evidence_refs'][:2])}" if adr['evidence_refs'] else evidence_badge
                lines.append(
                    f"| {adr['adr_id']} | {adr['title'][:30]} | {adr['total_tasks']} | "
                    f"{adr['tasks_pending'] + adr['tasks_in_progress']} | {adr['tasks_completed']} | {evidence_str} |"
                )
        else:
            lines.append("*No ADRs found with tasks*")
        lines.append("")

        # Evidence Coverage
        lines.append("## 📋 EVIDENCE COVERAGE")
        lines.append("")
        total_adrs = len(data.get('adrs', []))
        adrs_with_evidence = sum(1 for adr in data.get('adrs', []) if adr['evidence_refs'])
        coverage_pct = data.get('evidence_coverage_pct', 0)
        lines.append(f"- **Total ADRs**: {total_adrs}")
        lines.append(f"- **With Evidence**: {adrs_with_evidence} ({coverage_pct}%)")
        lines.append(f"- **Target**: 80%")
        gap = 80 - coverage_pct
        if gap > 0:
            lines.append(f"- **Gap**: -{gap}%")
        lines.append("")

        # Meta-Agent Verdicts (placeholder)
        lines.append("## ⚠️  META-AGENT VERDICTS")
        lines.append("")
        lines.append("**CMO** (GTM Tasks):")
        lines.append("- Status: ✅ Available")
        lines.append("")
        lines.append("**Governance** (Risk Assessment):")
        lines.append("- Status: 🚧 In Progress")
        lines.append("")
        lines.append("**COO** (Resource Management):")
        lines.append("- Status: 🚧 In Progress")
        lines.append("")

        # Blockers
        if data.get('blockers'):
            lines.append("## 🚨 BLOCKERS")
            lines.append("")
            lines.append("| Task ID | ADR | Blocker |")
            lines.append("|---------|-----|---------|")
            for blocker in data['blockers'][:5]:  # Top 5
                lines.append(f"| {blocker['task_id']} | {blocker['adr']} | {blocker['reason'][:50]} |")
            lines.append("")

        # Footer
        lines.append("━" * 60)
        lines.append("")
        lines.append(f"**Report saved**: work/reports/{data['project']}-{data['date']}.md")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def format_grid(data: Dict[str, Any]) -> str:
        """Format as plain tables (no emojis) - PARSEABLE"""
        lines = []

        # Header
        lines.append(f"{data['project'].upper()} - STATUS REPORT")
        lines.append(f"Generated: {data['generated_at']}")
        lines.append("")

        # Task Summary
        lines.append("TASK SUMMARY")
        lines.append("+------------+-------+-----+")
        lines.append("| Status     | Count | %   |")
        lines.append("+------------+-------+-----+")
        lines.append(f"| Completed  | {data['tasks_completed']:<5} | {int(data['tasks_completed']/max(data['total_tasks'],1)*100):>3}% |")
        lines.append(f"| In Progress| {data['tasks_in_progress']:<5} | {int(data['tasks_in_progress']/max(data['total_tasks'],1)*100):>3}% |")
        lines.append(f"| Pending    | {data['tasks_pending']:<5} | {int(data['tasks_pending']/max(data['total_tasks'],1)*100):>3}% |")
        lines.append(f"| Blocked    | {data['tasks_blocked']:<5} | {int(data['tasks_blocked']/max(data['total_tasks'],1)*100):>3}% |")
        lines.append(f"| Total      | {data['total_tasks']:<5} | 100% |")
        lines.append("+------------+-------+-----+")
        lines.append("")

        # ADR Rollup
        lines.append("ADR ROLLUP")
        if data.get('adrs'):
            lines.append("+---------+---------------------------+-------+------+----------+----------+")
            lines.append("| ADR     | Title                     | Tasks | Open | Complete | Evidence |")
            lines.append("+---------+---------------------------+-------+------+----------+----------+")
            for adr in data['adrs']:
                evidence_str = "Yes" if adr['evidence_refs'] else "No"
                title = adr['title'][:25].ljust(25)
                lines.append(
                    f"| {adr['adr_id']:<7} | {title} | {adr['total_tasks']:<5} | "
                    f"{adr['tasks_pending'] + adr['tasks_in_progress']:<4} | {adr['tasks_completed']:<8} | {evidence_str:<8} |"
                )
            lines.append("+---------+---------------------------+-------+------+----------+----------+")
        else:
            lines.append("No ADRs found with tasks")
        lines.append("")

        # Footer
        lines.append(f"Report saved: work/reports/{data['project']}-{data['date']}-grid.txt")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def format_json(data: Dict[str, Any]) -> str:
        """Format as JSON for programmatic access"""
        return json.dumps(data, indent=2)

    @staticmethod
    def save_report(content: str, filepath: str) -> None:
        """Save report to file"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w') as f:
            f.write(content)
