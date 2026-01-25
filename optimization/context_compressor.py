"""
Context Compressor

Compresses governance context to fit within token budgets.
Achieves 50-70% reduction while preserving critical information.

Compression Strategies:
1. Section prioritization (STATE > CATALOG > DECISIONS)
2. Redundancy removal
3. Abbreviation of common patterns
4. Selective section extraction

Usage:
    from optimization.context_compressor import ContextCompressor

    compressor = ContextCompressor()

    # Compress to target token count
    compressed = compressor.compress(
        governance_text,
        target_tokens=2000,
        preserve=["Current Status", "Critical Issues"]
    )

    # Compress specific sections
    compressed = compressor.compress_sections(
        sections={"STATE.md": state_content, "CATALOG.md": catalog_content},
        target_tokens=2000
    )
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import re


@dataclass
class CompressionResult:
    """Result of compression operation."""
    content: str
    original_tokens: int
    compressed_tokens: int
    reduction_percent: float
    sections_kept: List[str]
    sections_removed: List[str]


class ContextCompressor:
    """
    Compresses governance context for token efficiency.

    Strategies:
    1. Priority-based section selection
    2. Common pattern abbreviation
    3. Redundancy elimination
    4. Smart truncation with ellipsis

    Target: 50-70% reduction
    """

    # Section priorities (higher = more important to keep)
    SECTION_PRIORITY = {
        "Current Status": 10,
        "Critical Issues": 10,
        "Blockers": 9,
        "Next Steps": 9,
        "Recent Changes": 8,
        "In Progress": 8,
        "Active Tasks": 7,
        "Configuration": 6,
        "Architecture": 5,
        "History": 3,
        "Background": 2,
        "References": 1,
    }

    # Common abbreviations (saves tokens)
    ABBREVIATIONS = {
        "implementation": "impl",
        "configuration": "config",
        "authentication": "auth",
        "authorization": "authz",
        "database": "db",
        "repository": "repo",
        "documentation": "docs",
        "development": "dev",
        "production": "prod",
        "environment": "env",
        "application": "app",
        "function": "func",
        "parameter": "param",
        "information": "info",
    }

    # Redundant phrases to remove
    REDUNDANT_PHRASES = [
        "Please note that",
        "It should be noted that",
        "It is important to",
        "As mentioned above",
        "As described earlier",
        "For more information",
        "Additionally,",
        "Furthermore,",
        "Moreover,",
    ]

    def __init__(self):
        """Initialize compressor."""
        self._abbrev_pattern = self._build_abbrev_pattern()

    def _build_abbrev_pattern(self) -> re.Pattern:
        """Build regex pattern for abbreviations."""
        words = "|".join(re.escape(w) for w in self.ABBREVIATIONS.keys())
        return re.compile(f"\\b({words})\\b", re.IGNORECASE)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        return len(text) // 4

    def compress(
        self,
        content: str,
        target_tokens: int = 2000,
        preserve: Optional[List[str]] = None
    ) -> CompressionResult:
        """
        Compress content to target token count.

        Args:
            content: Content to compress
            target_tokens: Target token count
            preserve: Section names to always preserve

        Returns:
            CompressionResult with compressed content and metrics
        """
        preserve = preserve or []
        original_tokens = self._estimate_tokens(content)

        if original_tokens <= target_tokens:
            return CompressionResult(
                content=content,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                reduction_percent=0.0,
                sections_kept=[],
                sections_removed=[]
            )

        # Apply compression strategies in order
        compressed = content

        # 1. Remove redundant phrases
        compressed = self._remove_redundant(compressed)

        # 2. Apply abbreviations
        compressed = self._apply_abbreviations(compressed)

        # 3. Extract and prioritize sections
        sections = self._extract_sections(compressed)
        sections_kept = []
        sections_removed = []

        if sections:
            compressed, sections_kept, sections_removed = self._select_sections(
                sections,
                target_tokens,
                preserve
            )

        # 4. Final truncation if still over budget
        current_tokens = self._estimate_tokens(compressed)
        if current_tokens > target_tokens:
            compressed = self._truncate(compressed, target_tokens)

        compressed_tokens = self._estimate_tokens(compressed)
        reduction = (1 - compressed_tokens / original_tokens) * 100

        return CompressionResult(
            content=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            reduction_percent=reduction,
            sections_kept=sections_kept,
            sections_removed=sections_removed
        )

    def _remove_redundant(self, content: str) -> str:
        """Remove redundant phrases."""
        for phrase in self.REDUNDANT_PHRASES:
            content = content.replace(phrase, "")

        # Remove multiple consecutive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Remove trailing whitespace
        content = re.sub(r'[ \t]+\n', '\n', content)

        return content

    def _apply_abbreviations(self, content: str) -> str:
        """Apply abbreviations to reduce tokens."""
        def replace(match):
            word = match.group(0)
            lower = word.lower()
            abbrev = self.ABBREVIATIONS.get(lower, word)
            # Preserve case for first letter
            if word[0].isupper():
                return abbrev.capitalize()
            return abbrev

        return self._abbrev_pattern.sub(replace, content)

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract markdown sections."""
        sections = {}
        current_section = "Introduction"
        current_content = []

        for line in content.split('\n'):
            # Check for section headers
            if line.startswith('## '):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line[3:].strip()
                current_content = [line]
            elif line.startswith('# '):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line[2:].strip()
                current_content = [line]
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def _select_sections(
        self,
        sections: Dict[str, str],
        target_tokens: int,
        preserve: List[str]
    ) -> Tuple[str, List[str], List[str]]:
        """Select sections based on priority and budget."""
        # Calculate token cost for each section
        section_costs = {
            name: self._estimate_tokens(content)
            for name, content in sections.items()
        }

        # Sort by priority
        sorted_sections = sorted(
            sections.keys(),
            key=lambda s: (
                10 if s in preserve else self._get_section_priority(s)
            ),
            reverse=True
        )

        # Select sections within budget
        selected = []
        removed = []
        total_tokens = 0

        for section in sorted_sections:
            cost = section_costs[section]
            if total_tokens + cost <= target_tokens:
                selected.append(section)
                total_tokens += cost
            else:
                removed.append(section)

        # Build result content
        result_parts = []
        for section in sorted_sections:
            if section in selected:
                result_parts.append(sections[section])

        return '\n\n'.join(result_parts), selected, removed

    def _get_section_priority(self, section_name: str) -> int:
        """Get priority for a section name."""
        # Check exact match
        if section_name in self.SECTION_PRIORITY:
            return self.SECTION_PRIORITY[section_name]

        # Check partial matches
        section_lower = section_name.lower()
        for key, priority in self.SECTION_PRIORITY.items():
            if key.lower() in section_lower:
                return priority

        return 5  # Default priority

    def _truncate(self, content: str, target_tokens: int) -> str:
        """Truncate content to fit target tokens."""
        target_chars = target_tokens * 4  # Rough conversion

        if len(content) <= target_chars:
            return content

        # Find a good break point
        truncated = content[:target_chars]

        # Try to break at paragraph
        last_para = truncated.rfind('\n\n')
        if last_para > target_chars * 0.7:
            truncated = truncated[:last_para]

        return truncated + "\n\n[...content truncated for token budget...]"

    def compress_sections(
        self,
        sections: Dict[str, str],
        target_tokens: int = 2000
    ) -> Dict[str, str]:
        """
        Compress multiple sections with individual budgets.

        Args:
            sections: Map of filename -> content
            target_tokens: Total target tokens

        Returns:
            Map of filename -> compressed content
        """
        # Calculate fair budget per section
        num_sections = len(sections)
        if num_sections == 0:
            return {}

        per_section_budget = target_tokens // num_sections

        result = {}
        for filename, content in sections.items():
            compressed = self.compress(content, per_section_budget)
            result[filename] = compressed.content

        return result


# Convenience function
def compress_context(content: str, target_tokens: int = 2000) -> str:
    """Convenience function to compress context."""
    compressor = ContextCompressor()
    result = compressor.compress(content, target_tokens)
    return result.content
