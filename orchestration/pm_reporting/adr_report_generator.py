"""
ADR Status Report Generator - Shows status of all Architecture Decision Records.

Generates a focused report showing:
- All ADRs across all projects
- Current status (draft, approved, in-progress, complete)
- Completion dates
- What was delivered/implemented
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import os
import re
from datetime import datetime


@dataclass
class ADRRecord:
    """Single ADR record with status and completion info"""
    adr_id: str
    title: str
    project: str
    status: str  # draft, approved, in-progress, complete
    date_created: str
    date_completed: Optional[str]
    advisor: str
    description: str
    outcome: Optional[str]
    file_path: str


class ADRReportGenerator:
    """Generate ADR status reports"""

    def __init__(self) -> None:
        self.adr_index_path = "AI-Team-Plans/ADR-INDEX.md"
        self.orchestrator_adr_dir = "AI-Team-Plans/decisions"
        self.credentialmate_adr_dir = "adapters/credentialmate/plans/decisions"

    def parse_adr_index(self) -> List[ADRRecord]:
        """Parse ADR-INDEX.md to get basic metadata"""
        records: List[ADRRecord] = []

        if not os.path.exists(self.adr_index_path):
            return records

        try:
            with open(self.adr_index_path, 'r') as f:
                content = f.read()

            # Parse main ADR Registry table
            in_main_table = False
            for line in content.split('\n'):
                if '## ADR Registry' in line:
                    in_main_table = True
                    continue
                if in_main_table and line.startswith('##'):
                    in_main_table = False
                    continue

                if in_main_table and '| ADR-' in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 6:
                        adr_id = parts[0]
                        title_raw = parts[1]
                        project = parts[2]
                        status = parts[3].replace('✅', '').replace('🚧', '').replace('📝', '').strip()
                        date_created = parts[4]
                        advisor = parts[5]

                        # Extract clean title (remove markdown links)
                        title = title_raw.split('](')[0].strip('[').strip()

                        # Determine file path
                        file_path = self._get_adr_file_path(adr_id, project)

                        records.append(ADRRecord(
                            adr_id=adr_id,
                            title=title,
                            project=project,
                            status=status,
                            date_created=date_created,
                            date_completed=None,  # Will enrich from file
                            advisor=advisor,
                            description="",  # Will enrich from file
                            outcome=None,  # Will enrich from file
                            file_path=file_path
                        ))

        except Exception as e:
            print(f"Warning: Could not parse ADR-INDEX.md: {e}")

        return records

    def _get_adr_file_path(self, adr_id: str, project: str) -> str:
        """Determine file path for an ADR"""
        # Try to find the actual file
        if 'orchestrator' in project.lower() or 'ai_orchestrator' in project.lower():
            base_dir = self.orchestrator_adr_dir
        else:
            base_dir = self.credentialmate_adr_dir

        # Find matching file
        if os.path.exists(base_dir):
            for filename in os.listdir(base_dir):
                if filename.startswith(adr_id) and filename.endswith('.md'):
                    return os.path.join(base_dir, filename)

        return ""

    def enrich_from_adr_files(self, records: List[ADRRecord]) -> List[ADRRecord]:
        """Read ADR files to get description, outcome, completion date"""
        enriched = []

        for record in records:
            if not record.file_path or not os.path.exists(record.file_path):
                enriched.append(record)
                continue

            try:
                with open(record.file_path, 'r') as f:
                    content = f.read()

                # Extract completion date (look for various patterns)
                date_completed = self._extract_completion_date(content, record.status)

                # Extract description (first paragraph after context/summary)
                description = self._extract_description(content)

                # Extract outcome (from outcome/result section)
                outcome = self._extract_outcome(content, record.status)

                enriched.append(ADRRecord(
                    adr_id=record.adr_id,
                    title=record.title,
                    project=record.project,
                    status=record.status,
                    date_created=record.date_created,
                    date_completed=date_completed,
                    advisor=record.advisor,
                    description=description,
                    outcome=outcome,
                    file_path=record.file_path
                ))

            except Exception as e:
                print(f"Warning: Could not read {record.file_path}: {e}")
                enriched.append(record)

        return enriched

    def _extract_completion_date(self, content: str, status: str) -> Optional[str]:
        """Extract completion date from ADR content"""
        # Only look for completion date if status is 'complete' or 'approved'
        if status not in ['complete', 'approved']:
            return None

        # Look for patterns like "Completed: YYYY-MM-DD" or "Implemented: YYYY-MM-DD"
        patterns = [
            r'(?:Completed|Implemented|Finished):\s*(\d{4}-\d{2}-\d{2})',
            r'\*\*Completed\*\*:\s*(\d{4}-\d{2}-\d{2})',
            r'\*\*Implemented\*\*:\s*(\d{4}-\d{2}-\d{2})'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return None

    def _extract_description(self, content: str) -> str:
        """Extract brief description from ADR content"""
        # Look for Context or Summary section
        sections = ['## Context', '## Summary', '## Problem']

        for section in sections:
            if section in content:
                # Get text after section header
                parts = content.split(section, 1)
                if len(parts) > 1:
                    # Get first paragraph (up to next ## or 200 chars)
                    text = parts[1].split('##')[0].strip()
                    # Take first 200 chars
                    desc = text[:200].replace('\n', ' ').strip()
                    if desc:
                        return desc + ('...' if len(text) > 200 else '')

        return ""

    def _extract_outcome(self, content: str, status: str) -> Optional[str]:
        """Extract outcome/result from ADR content"""
        # Only extract outcome if complete or approved
        if status not in ['complete', 'approved']:
            return None

        # Look for Decision or Outcome sections
        sections = ['## Decision', '## Outcome', '## Result', '## Solution']

        for section in sections:
            if section in content:
                parts = content.split(section, 1)
                if len(parts) > 1:
                    # Get first paragraph
                    text = parts[1].split('##')[0].strip()
                    outcome = text[:300].replace('\n', ' ').strip()
                    if outcome:
                        return outcome + ('...' if len(text) > 300 else '')

        return None

    def generate_report(self, project: Optional[str] = None) -> List[ADRRecord]:
        """Generate complete ADR status report"""
        # Parse index
        records = self.parse_adr_index()

        # Filter by project if specified
        if project:
            records = [r for r in records if r.project.lower() == project.lower()]

        # Enrich from files
        records = self.enrich_from_adr_files(records)

        # Sort by ADR ID
        records.sort(key=lambda r: (
            int(r.adr_id.replace('ADR-', '').split('-')[0]),
            r.adr_id
        ))

        return records

    def format_grid(self, records: List[ADRRecord]) -> str:
        """Format as ASCII grid table"""
        if not records:
            return "No ADRs found."

        # Calculate column widths
        col_widths = {
            'adr_id': max(len('ADR'), max(len(r.adr_id) for r in records)),
            'title': max(len('Title'), max(len(r.title[:40]) for r in records)),
            'project': max(len('Project'), max(len(r.project[:15]) for r in records)),
            'status': max(len('Status'), max(len(r.status) for r in records)),
            'created': len('Created'),
            'completed': len('Completed'),
        }

        # Build table
        lines = []

        # Header
        header = (
            f"{'ADR':<{col_widths['adr_id']}} | "
            f"{'Title':<{col_widths['title']}} | "
            f"{'Project':<{col_widths['project']}} | "
            f"{'Status':<{col_widths['status']}} | "
            f"{'Created':<{col_widths['created']}} | "
            f"{'Completed':<{col_widths['completed']}}"
        )
        lines.append(header)

        # Separator
        sep = (
            f"{'-' * col_widths['adr_id']}-+-"
            f"{'-' * col_widths['title']}-+-"
            f"{'-' * col_widths['project']}-+-"
            f"{'-' * col_widths['status']}-+-"
            f"{'-' * col_widths['created']}-+-"
            f"{'-' * col_widths['completed']}"
        )
        lines.append(sep)

        # Data rows
        for record in records:
            title_display = record.title[:40] + ('...' if len(record.title) > 40 else '')
            project_display = record.project[:15]
            completed_display = record.date_completed or '-'

            row = (
                f"{record.adr_id:<{col_widths['adr_id']}} | "
                f"{title_display:<{col_widths['title']}} | "
                f"{project_display:<{col_widths['project']}} | "
                f"{record.status:<{col_widths['status']}} | "
                f"{record.date_created:<{col_widths['created']}} | "
                f"{completed_display:<{col_widths['completed']}}"
            )
            lines.append(row)

        # Add summary
        lines.append("")
        lines.append(f"Total ADRs: {len(records)}")

        # Status breakdown
        status_counts: Dict[str, int] = {}
        for record in records:
            status_counts[record.status] = status_counts.get(record.status, 0) + 1

        lines.append("")
        lines.append("Status Breakdown:")
        for status, count in sorted(status_counts.items()):
            lines.append(f"  {status}: {count}")

        return '\n'.join(lines)

    def format_markdown(self, records: List[ADRRecord], detailed: bool = False) -> str:
        """Format as Markdown"""
        if not records:
            return "# ADR Status Report\n\nNo ADRs found."

        lines = []

        # Title
        lines.append("# ADR Status Report")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Summary stats
        status_counts: Dict[str, int] = {}
        for record in records:
            status_counts[record.status] = status_counts.get(record.status, 0) + 1

        lines.append("## Summary")
        lines.append("")
        lines.append(f"**Total ADRs**: {len(records)}")
        lines.append("")
        lines.append("**Status Breakdown**:")
        lines.append("")
        for status, count in sorted(status_counts.items()):
            # Add emoji based on status
            emoji = {
                'complete': '✅',
                'approved': '✅',
                'in-progress': '🚧',
                'draft': '📝'
            }.get(status, '•')
            lines.append(f"- {emoji} **{status}**: {count}")
        lines.append("")

        # Main table
        lines.append("## ADR Status Table")
        lines.append("")
        lines.append("| ADR | Title | Project | Status | Created | Completed |")
        lines.append("|-----|-------|---------|--------|---------|-----------|")

        for record in records:
            # Add status emoji
            status_emoji = {
                'complete': '✅',
                'approved': '✅',
                'in-progress': '🚧',
                'draft': '📝'
            }.get(record.status, '')

            completed = record.date_completed or '-'

            lines.append(
                f"| {record.adr_id} | {record.title} | {record.project} | "
                f"{status_emoji} {record.status} | {record.date_created} | {completed} |"
            )

        lines.append("")

        # Detailed sections if requested
        if detailed:
            lines.append("---")
            lines.append("")
            lines.append("## Detailed Status")
            lines.append("")

            for record in records:
                lines.append(f"### {record.adr_id}: {record.title}")
                lines.append("")
                lines.append(f"- **Project**: {record.project}")
                lines.append(f"- **Status**: {record.status}")
                lines.append(f"- **Created**: {record.date_created}")
                lines.append(f"- **Completed**: {record.date_completed or 'Not completed'}")
                lines.append(f"- **Advisor**: {record.advisor}")

                if record.description:
                    lines.append("")
                    lines.append(f"**Description**: {record.description}")

                if record.outcome:
                    lines.append("")
                    lines.append(f"**Outcome**: {record.outcome}")

                if record.file_path:
                    lines.append("")
                    lines.append(f"**File**: `{record.file_path}`")

                lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Generated by AI Orchestrator PM Reporting System*")

        return '\n'.join(lines)

    def format_detailed_grid(self, records: List[ADRRecord]) -> str:
        """Format as detailed grid with outcomes"""
        if not records:
            return "No ADRs found."

        lines = []
        lines.append("=" * 100)
        lines.append("ADR STATUS REPORT - DETAILED")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 100)
        lines.append("")

        for record in records:
            lines.append(f"ADR ID:      {record.adr_id}")
            lines.append(f"Title:       {record.title}")
            lines.append(f"Project:     {record.project}")
            lines.append(f"Status:      {record.status}")
            lines.append(f"Created:     {record.date_created}")
            lines.append(f"Completed:   {record.date_completed or 'Not completed'}")
            lines.append(f"Advisor:     {record.advisor}")

            if record.description:
                lines.append(f"Description: {record.description}")

            if record.outcome:
                lines.append(f"Outcome:     {record.outcome}")

            lines.append("-" * 100)
            lines.append("")

        # Summary
        lines.append("=" * 100)
        lines.append(f"SUMMARY: {len(records)} ADRs")

        status_counts: Dict[str, int] = {}
        for record in records:
            status_counts[record.status] = status_counts.get(record.status, 0) + 1

        for status, count in sorted(status_counts.items()):
            lines.append(f"  {status}: {count}")

        lines.append("=" * 100)

        return '\n'.join(lines)
