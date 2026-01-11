"""
ADR Registry Management

Handles ADR numbering, registry updates, and fingerprint deduplication.
Uses file locking to prevent numbering collisions.
"""

import fcntl
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ADREntry:
    """Represents an ADR entry in the registry."""
    number: str  # "ADR-006"
    title: str
    project: str
    status: str  # "draft" | "approved" | "complete" | "rejected"
    date: str  # "YYYY-MM-DD"
    advisor: str  # "app-advisor" | "data-advisor" | "uiux-advisor"
    file_path: str  # Relative path from AI_Orchestrator root
    tags: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)


class ADRRegistry:
    """Manages the global ADR registry (ADR-INDEX.md)."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.index_path = self.repo_root / "AI-Team-Plans" / "ADR-INDEX.md"
        self.lock_path = self.repo_root / ".aibrain" / ".adr-registry.lock"
        self.fingerprints_path = self.repo_root / ".aibrain" / "adr-fingerprints.json"

        # Ensure .aibrain directory exists
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

    def reserve_adr_number(self) -> int:
        """
        Reserve next ADR number atomically using file locking.

        Uses fcntl.flock() for thread-safe number reservation.

        Returns:
            Reserved ADR number (e.g., 6 for ADR-006)
        """
        # Create lock file if it doesn't exist
        self.lock_path.touch(exist_ok=True)

        with open(self.lock_path, 'r+') as lock_file:
            # Acquire exclusive lock
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                # Read current number from index
                current_number = self._read_next_number()

                # Write placeholder to index to reserve number
                self._write_placeholder(current_number)

                logger.info(f"Reserved ADR number: {current_number:03d}")
                return current_number
            finally:
                # Release lock
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _read_next_number(self) -> int:
        """Read the next ADR number from index."""
        if not self.index_path.exists():
            logger.warning(f"ADR index not found at {self.index_path}, starting from 1")
            return 1

        content = self.index_path.read_text()

        # Find "## Next ADR Number" section
        # Pattern: **ADR-006** (use this for the next decision)
        match = re.search(r'\*\*ADR-(\d+)\*\*\s*\(use this for the next decision\)', content)
        if match:
            return int(match.group(1))

        # Fallback: Find highest existing ADR number
        adr_numbers = re.findall(r'ADR-(\d+)', content)
        if adr_numbers:
            return max(int(n) for n in adr_numbers) + 1

        return 1

    def _write_placeholder(self, number: int) -> None:
        """Write placeholder entry to reserve number."""
        if not self.index_path.exists():
            logger.error(f"Cannot write placeholder - index file missing: {self.index_path}")
            return

        content = self.index_path.read_text()

        # Update "Next ADR Number" section
        adr_id = f"ADR-{number:03d}"
        next_number = number + 1
        next_adr_id = f"ADR-{next_number:03d}"

        # Replace the next number line
        pattern = r'(\*\*ADR-\d+\*\*\s*\(use this for the next decision\))'
        replacement = f"**{next_adr_id}** (use this for the next decision)"
        content = re.sub(pattern, replacement, content)

        # Add placeholder to registry table
        # Find the ADR Registry section
        registry_match = re.search(r'## ADR Registry\n\n(\|.+\n)+', content)
        if registry_match:
            # Find end of table (empty line)
            table_end = registry_match.end()
            # Insert placeholder row before next section
            placeholder_row = f"| {adr_id} | [RESERVED] | - | draft | {datetime.now().strftime('%Y-%m-%d')} | - |\n"
            content = content[:table_end] + placeholder_row + content[table_end:]

        self.index_path.write_text(content)
        logger.debug(f"Wrote placeholder for {adr_id}")

    def register_adr(self, entry: ADREntry) -> None:
        """
        Update ADR-INDEX.md with new ADR entry.

        Updates:
        1. "ADR Registry" table (main listing)
        2. "By Project" table (project-specific)
        3. "By Tag" table (tag index)
        4. "By Domain" table (domain index)
        5. "Total ADRs" count
        """
        if not self.index_path.exists():
            logger.error(f"Cannot register ADR - index file missing: {self.index_path}")
            return

        content = self.index_path.read_text()

        # 1. Replace placeholder in ADR Registry table
        content = self._update_registry_table(content, entry)

        # 2. Update By Project table
        content = self._update_project_table(content, entry)

        # 3. Update By Tag table
        content = self._update_tag_table(content, entry)

        # 4. Update By Domain table
        content = self._update_domain_table(content, entry)

        # 5. Update total count
        content = self._update_total_count(content)

        # 6. Update last updated timestamp
        content = self._update_timestamp(content)

        self.index_path.write_text(content)
        logger.info(f"Registered {entry.number} in ADR index")

    def _update_registry_table(self, content: str, entry: ADREntry) -> str:
        """Update main ADR Registry table."""
        # Replace placeholder row
        placeholder_pattern = rf'\| {entry.number} \| \[RESERVED\] \| - \| draft \| [^\|]+ \| - \|'
        status_icon = "✅ " if entry.status in ["complete", "approved"] else ""
        new_row = (
            f"| {entry.number} | [{entry.title}]({entry.file_path}) | "
            f"{entry.project} | {status_icon}{entry.status} | {entry.date} | {entry.advisor} |"
        )
        return re.sub(placeholder_pattern, new_row, content)

    def _update_project_table(self, content: str, entry: ADREntry) -> str:
        """Update By Project table."""
        # Find project section
        project_heading = f"### {entry.project}"
        if project_heading not in content:
            # Add new project section
            by_project_match = re.search(r'## By Project\n\n', content)
            if by_project_match:
                new_section = (
                    f"\n### {entry.project}\n"
                    f"| ADR | Title | Status |\n"
                    f"|-----|-------|--------|\n"
                )
                insert_pos = by_project_match.end()
                content = content[:insert_pos] + new_section + content[insert_pos:]

        # Add row to project table
        # Find the table for this project
        project_section_start = content.find(project_heading)
        if project_section_start != -1:
            # Find table end (next heading or section)
            next_section = content.find('\n### ', project_section_start + len(project_heading))
            if next_section == -1:
                next_section = content.find('\n---\n', project_section_start)
            if next_section == -1:
                next_section = content.find('\n## ', project_section_start + len(project_heading))

            # Build new row
            status_icon = "✅ " if entry.status in ["complete", "approved"] else ""
            new_row = f"| {entry.number} | {entry.title} | {status_icon}{entry.status} |\n"

            # Insert row before next section
            if next_section != -1:
                content = content[:next_section] + new_row + content[next_section:]
            else:
                content += new_row

        return content

    def _update_tag_table(self, content: str, entry: ADREntry) -> str:
        """Update By Tag table."""
        return self._update_index_table(content, "## By Tag", entry.tags, entry.number)

    def _update_domain_table(self, content: str, entry: ADREntry) -> str:
        """Update By Domain table."""
        return self._update_index_table(content, "## By Domain", entry.domains, entry.number)

    def _update_index_table(self, content: str, section_heading: str, items: List[str], adr_number: str) -> str:
        """Generic function to update tag or domain index tables."""
        if not items:
            return content

        section_start = content.find(section_heading)
        if section_start == -1:
            return content

        # Find table in section
        table_start = content.find('| ', section_start)
        if table_start == -1:
            return content

        # Find end of section
        next_section = content.find('\n---\n', section_start + len(section_heading))
        if next_section == -1:
            next_section = content.find('\n## ', section_start + len(section_heading))
        if next_section == -1:
            next_section = len(content)

        # Parse existing table
        table_content = content[table_start:next_section]
        lines = table_content.strip().split('\n')

        # Build updated table
        new_lines = [lines[0], lines[1]]  # Headers
        existing_entries = {}

        # Parse existing entries
        for line in lines[2:]:
            if not line.strip() or not line.startswith('|'):
                continue
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 2:
                tag_name = parts[0]
                existing_adrs = parts[1]
                existing_entries[tag_name] = existing_adrs

        # Add new items
        for item in items:
            if item in existing_entries:
                # Append to existing
                if adr_number not in existing_entries[item]:
                    existing_entries[item] += f", {adr_number}"
            else:
                existing_entries[item] = adr_number

        # Sort and rebuild table
        for tag_name in sorted(existing_entries.keys()):
            new_lines.append(f"| {tag_name} | {existing_entries[tag_name]} |")

        # Replace table in content
        new_table = '\n'.join(new_lines) + '\n'
        content = content[:table_start] + new_table + content[next_section:]

        return content

    def _update_total_count(self, content: str) -> str:
        """Update total ADR count in header."""
        # Count non-placeholder entries
        adrs = re.findall(r'\| ADR-\d+ \| (?!\[RESERVED\])', content)
        total = len(adrs)

        # Update count in header
        pattern = r'\*\*Total ADRs\*\*: \d+'
        replacement = f"**Total ADRs**: {total}"
        return re.sub(pattern, replacement, content)

    def _update_timestamp(self, content: str) -> str:
        """Update Last Updated timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        pattern = r'\*\*Last Updated\*\*: [^\n]+'
        replacement = f"**Last Updated**: {timestamp}"
        return re.sub(pattern, replacement, content)

    def check_duplicate_fingerprint(self, fingerprint: str) -> Optional[str]:
        """
        Check if fingerprint already exists.

        Args:
            fingerprint: SHA256 fingerprint (16 chars)

        Returns:
            ADR number (e.g., "ADR-006") if duplicate exists, None otherwise
        """
        if not self.fingerprints_path.exists():
            return None

        try:
            data = json.loads(self.fingerprints_path.read_text())
            fingerprints = data.get("fingerprints", {})
            if fingerprint in fingerprints:
                return fingerprints[fingerprint].get("adr_number")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error reading fingerprints file: {e}")

        return None

    def add_fingerprint(
        self,
        fingerprint: str,
        adr_number: str,
        task_description: str,
        domain_tags: List[str]
    ) -> None:
        """
        Save fingerprint to cache.

        Args:
            fingerprint: SHA256 fingerprint (16 chars)
            adr_number: ADR number (e.g., "ADR-006")
            task_description: Task description
            domain_tags: List of domain tags
        """
        # Load existing fingerprints
        if self.fingerprints_path.exists():
            try:
                data = json.loads(self.fingerprints_path.read_text())
            except json.JSONDecodeError:
                data = {"fingerprints": {}}
        else:
            data = {"fingerprints": {}}

        # Add new fingerprint
        data["fingerprints"][fingerprint] = {
            "adr_number": adr_number,
            "task_description": task_description,
            "domain_tags": domain_tags,
            "created_at": datetime.now().isoformat()
        }

        # Save
        self.fingerprints_path.write_text(json.dumps(data, indent=2))
        logger.debug(f"Added fingerprint {fingerprint} for {adr_number}")

    def get_adr_by_number(self, adr_number: str) -> Optional[ADREntry]:
        """
        Retrieve ADR entry by number from registry.

        Args:
            adr_number: ADR number (e.g., "ADR-006" or "6")

        Returns:
            ADREntry if found, None otherwise
        """
        # Normalize number format
        if not adr_number.startswith("ADR-"):
            adr_number = f"ADR-{int(adr_number):03d}"

        if not self.index_path.exists():
            return None

        content = self.index_path.read_text()

        # Find entry in registry table
        pattern = rf'\| ({adr_number}) \| \[([^\]]+)\]\(([^\)]+)\) \| ([^\|]+) \| ([^\|]+) \| ([^\|]+) \| ([^\|]+) \|'
        match = re.search(pattern, content)
        if match:
            return ADREntry(
                number=match.group(1).strip(),
                title=match.group(2).strip(),
                file_path=match.group(3).strip(),
                project=match.group(4).strip(),
                status=match.group(5).strip().replace("✅ ", ""),
                date=match.group(6).strip(),
                advisor=match.group(7).strip()
            )

        return None

    def list_drafts(self, project: Optional[str] = None) -> List[ADREntry]:
        """
        List all draft ADRs awaiting approval.

        Args:
            project: Optional project filter

        Returns:
            List of draft ADREntry objects
        """
        if not self.index_path.exists():
            return []

        content = self.index_path.read_text()
        drafts = []

        # Find all draft entries
        pattern = r'\| (ADR-\d+) \| \[([^\]]+)\]\(([^\)]+)\) \| ([^\|]+) \| draft \| ([^\|]+) \| ([^\|]+) \|'
        for match in re.finditer(pattern, content):
            entry = ADREntry(
                number=match.group(1).strip(),
                title=match.group(2).strip(),
                file_path=match.group(3).strip(),
                project=match.group(4).strip(),
                status="draft",
                date=match.group(5).strip(),
                advisor=match.group(6).strip()
            )

            # Filter by project if specified
            if project is None or entry.project == project:
                drafts.append(entry)

        return drafts


def get_adr_path(project: str, adr_number: int, title_slug: str, repo_root: Path) -> Path:
    """
    Determine ADR file path based on project.

    Args:
        project: Project name ("AI_Orchestrator", "credentialmate", "karematch")
        adr_number: ADR number (e.g., 6)
        title_slug: Title slug (e.g., "provider-report-generation")
        repo_root: Repository root path

    Returns:
        Full path to ADR file
    """
    repo_root = Path(repo_root)
    adr_filename = f"ADR-{adr_number:03d}-{title_slug}.md"

    if project == "AI_Orchestrator":
        return repo_root / "AI-Team-Plans" / "decisions" / adr_filename
    else:
        return repo_root / "adapters" / project.lower() / "plans" / "decisions" / adr_filename
