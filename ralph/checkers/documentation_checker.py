"""
Ralph Documentation Checker

Integrates documentation validation into Ralph's PASS/FAIL/BLOCKED system.
Checks documentation completeness for code changes.

Rules:
1. New ADRs must have frontmatter
2. Modified files in work/ must have complete metadata
3. CredentialMate files must use 'confidential' classification
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Tuple


class DocumentationChecker:
    """Ralph checker for documentation compliance"""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)

    def check(self, changed_files: List[str]) -> Tuple[str, str, List[str]]:
        """
        Check documentation compliance for changed files

        Args:
            changed_files: List of file paths changed in this commit

        Returns:
            Tuple of (verdict, message, violations)
            verdict: "PASS" | "FAIL" | "BLOCKED"
        """
        violations = []
        blocked = []

        for file_path in changed_files:
            # Only check markdown files in work/
            if not file_path.startswith("work/") or not file_path.endswith(".md"):
                continue

            full_path = self.repo_root / file_path

            # Check frontmatter exists
            if not self._has_frontmatter(full_path):
                blocked.append(f"Missing frontmatter: {file_path}")
                continue

            # Check frontmatter is valid
            metadata = self._parse_frontmatter(full_path)
            if not metadata:
                blocked.append(f"Invalid frontmatter: {file_path}")
                continue

            # Check required fields
            missing_fields = self._check_required_fields(metadata)
            if missing_fields:
                violations.append(f"{file_path}: Missing fields: {', '.join(missing_fields)}")

            # Check HIPAA classification
            if file_path.startswith("work/") and "/cm-" in file_path:
                classification = metadata.get("compliance", {}).get("iso27001", {}).get("classification")
                if classification != "confidential":
                    violations.append(f"{file_path}: CredentialMate docs must use 'confidential' classification")

        # Determine verdict
        if blocked:
            return "BLOCKED", "Documentation compliance violations (CRITICAL)", blocked

        if violations:
            return "FAIL", "Documentation metadata incomplete", violations

        return "PASS", "Documentation compliance checks passed", []

    def _has_frontmatter(self, file_path: Path) -> bool:
        """Check if file has YAML frontmatter"""
        if not file_path.exists():
            return False

        with open(file_path, 'r') as f:
            content = f.read()

        return content.startswith("---\n") and "\n---\n" in content[4:]

    def _parse_frontmatter(self, file_path: Path) -> Dict:
        """Parse YAML frontmatter from file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            if not content.startswith("---\n"):
                return {}

            frontmatter_end = content.find("\n---\n", 4)
            if frontmatter_end == -1:
                return {}

            frontmatter_yaml = content[4:frontmatter_end]
            return yaml.safe_load(frontmatter_yaml) or {}

        except Exception:
            return {}

    def _check_required_fields(self, metadata: Dict) -> List[str]:
        """Check for required frontmatter fields"""
        required = [
            "doc-id",
            "title",
            "status",
            "compliance.soc2.controls",
            "compliance.soc2.evidence-type",
            "compliance.iso27001.controls",
            "compliance.iso27001.classification",
            "project",
            "domain"
        ]

        missing = []
        for field in required:
            if "." in field:
                # Nested field
                keys = field.split(".")
                value = metadata
                for key in keys:
                    if not isinstance(value, dict) or key not in value:
                        missing.append(field)
                        break
                    value = value[key]
            else:
                if field not in metadata:
                    missing.append(field)

        return missing
