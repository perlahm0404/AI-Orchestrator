"""
IceboxIdea - Dataclass for raw idea capture

Ideas are stored as markdown files with YAML frontmatter in .aibrain/icebox/
"""

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Literal


IdeaCategory = Literal["feature", "improvement", "research", "tech-debt", "bug"]
IdeaStatus = Literal["raw", "reviewed", "promoted", "archived"]
EffortEstimate = Literal["XS", "S", "M", "L", "XL"]


@dataclass
class IceboxIdea:
    """
    Raw idea captured for future consideration.

    Stored as markdown with YAML frontmatter in .aibrain/icebox/
    """
    id: str                                    # IDEA-20260207-1430-001
    title: str                                 # Short, memorable title
    description: str                           # Full details
    project: str                               # credentialmate | karematch | ai-orchestrator

    # Classification
    category: IdeaCategory = "improvement"     # feature | improvement | research | tech-debt | bug
    priority: int = 2                          # 0=urgent, 1=high, 2=medium, 3=someday
    effort_estimate: EffortEstimate = "M"      # XS | S | M | L | XL

    # Discovery context
    tags: List[str] = field(default_factory=list)           # For discovery
    dependencies: List[str] = field(default_factory=list)   # Task IDs or IDEA IDs this depends on
    source: str = "human"                      # human | agent | advisor | council
    discovered_by: str = "cli"                 # Who captured it

    # Lifecycle tracking
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_reviewed: Optional[str] = None        # For age tracking
    status: IdeaStatus = "raw"                 # raw | reviewed | promoted | archived

    # Promotion tracking
    promoted_to: Optional[str] = None          # Task ID if promoted
    archived_reason: Optional[str] = None      # Why archived (if applicable)

    # Deduplication
    fingerprint: str = ""                      # SHA256 for deduplication (auto-generated)

    # Extensible metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Generate fingerprint if not provided."""
        if not self.fingerprint:
            self.fingerprint = self._generate_fingerprint()

    def _generate_fingerprint(self) -> str:
        """Generate SHA256 fingerprint for deduplication."""
        normalized = f"{self.project}:{self.title.lower().strip()}:{self.description[:100].lower().strip()}"
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for YAML serialization)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IceboxIdea":
        """Create from dictionary (from YAML)."""
        # Handle unknown fields gracefully
        known_fields = set(cls.__dataclass_fields__.keys())
        known = {k: v for k, v in data.items() if k in known_fields}
        extra = {k: v for k, v in data.items() if k not in known_fields}
        if extra:
            known.setdefault("metadata", {}).update(extra)
        return cls(**known)

    def to_markdown(self) -> str:
        """
        Convert to markdown with YAML frontmatter.

        Returns:
            Markdown string ready to write to file
        """
        import yaml

        # Build frontmatter data (exclude description and metadata)
        frontmatter = {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "priority": self.priority,
            "effort_estimate": self.effort_estimate,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "project": self.project,
            "source": self.source,
            "discovered_by": self.discovered_by,
            "created_at": self.created_at,
            "last_reviewed": self.last_reviewed,
            "status": self.status,
            "promoted_to": self.promoted_to,
            "archived_reason": self.archived_reason,
            "fingerprint": self.fingerprint,
        }

        # Add metadata fields to frontmatter
        if self.metadata:
            frontmatter.update(self.metadata)

        yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True)

        return f"""---
{yaml_str.strip()}
---

# {self.title}

## Description

{self.description}
"""

    @classmethod
    def from_markdown(cls, content: str) -> "IceboxIdea":
        """
        Parse markdown with YAML frontmatter.

        Args:
            content: Markdown file content

        Returns:
            IceboxIdea instance
        """
        import yaml

        # Parse frontmatter
        if not content.startswith("---"):
            raise ValueError("Missing YAML frontmatter")

        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Invalid frontmatter format")

        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()

        # Extract description from body
        description = ""
        if "## Description" in body:
            desc_start = body.find("## Description") + len("## Description")
            description = body[desc_start:].strip()
        else:
            # Fallback: use all body content after title
            lines = body.split("\n")
            if lines and lines[0].startswith("# "):
                description = "\n".join(lines[1:]).strip()
            else:
                description = body

        frontmatter["description"] = description

        return cls.from_dict(frontmatter)


def generate_idea_id(project: str, sequence: int = 0) -> str:
    """
    Generate a unique idea ID.

    Format: IDEA-{YYYYMMDD}-{HHMM}-{SEQ}

    Args:
        project: Project name (not used in ID, but passed for context)
        sequence: Sequence number for this timestamp

    Returns:
        Unique idea ID
    """
    now = datetime.now()
    return f"IDEA-{now.strftime('%Y%m%d')}-{now.strftime('%H%M')}-{sequence:03d}"
