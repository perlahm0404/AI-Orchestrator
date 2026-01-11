#!/usr/bin/env python3
"""
Documentation Structure Validator

Validates documentation organization according to ADR-010:
- File locations (work/, archive/, docs/, tasks/)
- Naming conventions ({scope}-{type}-{identifier})
- SOC2/ISO frontmatter presence and completeness
- Classification correctness (HIPAA requires 'confidential')

Usage:
    python documentation_validator.py --check              # Validate all
    python documentation_validator.py --check work/        # Validate work/ only
    python documentation_validator.py --fix                # Auto-fix issues
    python documentation_validator.py --report             # Generate compliance report
"""

import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    ERROR = "ERROR"    # Blocks commit/deployment
    WARNING = "WARNING"  # Should fix, but not blocking
    INFO = "INFO"      # Informational only


@dataclass
class Violation:
    severity: Severity
    rule: str
    file: str
    message: str
    fix_available: bool = False

    def __str__(self):
        icon = "🚫" if self.severity == Severity.ERROR else "⚠️" if self.severity == Severity.WARNING else "ℹ️"
        fix_hint = " [auto-fix available]" if self.fix_available else ""
        return f"{icon} {self.severity.value}: {self.rule}\n   File: {self.file}\n   {self.message}{fix_hint}"


class DocumentationValidator:
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.violations: List[Violation] = []

    def validate_all(self) -> List[Violation]:
        """Run all validation rules"""
        self.violations = []

        # Rule 1: Root directory file count
        self.check_root_file_limit()

        # Rule 2: work/ directory frontmatter
        self.check_work_frontmatter()

        # Rule 3: archive/ directory archival metadata
        self.check_archive_metadata()

        # Rule 4: Naming conventions
        self.check_naming_conventions()

        # Rule 5: Classification correctness
        self.check_classification()

        # Rule 6: File location correctness
        self.check_file_locations()

        return self.violations

    def check_root_file_limit(self):
        """Root directory should have max 15 markdown files"""
        root_md_files = list(self.repo_root.glob("*.md"))
        if len(root_md_files) > 15:
            self.violations.append(Violation(
                severity=Severity.WARNING,
                rule="root-file-limit",
                file="<root>",
                message=f"Root has {len(root_md_files)} markdown files (target: ≤15). Consider moving to docs/ or archive/",
                fix_available=False
            ))

    def check_work_frontmatter(self):
        """All files in work/ must have SOC2/ISO frontmatter"""
        work_files = list(self.repo_root.glob("work/**/*.md"))

        for file_path in work_files:
            # Check frontmatter exists
            with open(file_path, 'r') as f:
                content = f.read()

            if not content.startswith("---\n"):
                self.violations.append(Violation(
                    severity=Severity.ERROR,
                    rule="work-frontmatter-required",
                    file=str(file_path.relative_to(self.repo_root)),
                    message="Missing YAML frontmatter. All work/ documents require SOC2/ISO compliance metadata",
                    fix_available=True
                ))
                continue

            # Parse frontmatter
            try:
                frontmatter_end = content.find("\n---\n", 4)
                if frontmatter_end == -1:
                    raise ValueError("No closing ---")

                frontmatter_yaml = content[4:frontmatter_end]
                metadata = yaml.safe_load(frontmatter_yaml)

                # Check required fields
                required_fields = [
                    "doc-id",
                    "title",
                    "created",
                    "updated",
                    "author",
                    "status",
                    "compliance.soc2.controls",
                    "compliance.soc2.evidence-type",
                    "compliance.soc2.retention-period",
                    "compliance.iso27001.controls",
                    "compliance.iso27001.classification",
                    "project",
                    "domain"
                ]

                for field in required_fields:
                    if "." in field:
                        # Nested field
                        keys = field.split(".")
                        value = metadata
                        for key in keys:
                            if not isinstance(value, dict) or key not in value:
                                self.violations.append(Violation(
                                    severity=Severity.ERROR,
                                    rule="work-frontmatter-incomplete",
                                    file=str(file_path.relative_to(self.repo_root)),
                                    message=f"Missing required field: {field}",
                                    fix_available=False
                                ))
                                break
                            value = value[key]
                    else:
                        if field not in metadata:
                            self.violations.append(Violation(
                                severity=Severity.ERROR,
                                rule="work-frontmatter-incomplete",
                                file=str(file_path.relative_to(self.repo_root)),
                                message=f"Missing required field: {field}",
                                fix_available=False
                            ))

            except Exception as e:
                self.violations.append(Violation(
                    severity=Severity.ERROR,
                    rule="work-frontmatter-invalid",
                    file=str(file_path.relative_to(self.repo_root)),
                    message=f"Invalid YAML frontmatter: {str(e)}",
                    fix_available=False
                ))

    def check_archive_metadata(self):
        """Archive files should have archival metadata"""
        archive_files = list(self.repo_root.glob("archive/**/*.md"))

        for file_path in archive_files:
            # Skip README files
            if file_path.name == "README.md":
                continue

            with open(file_path, 'r') as f:
                content = f.read()

            if not content.startswith("---\n"):
                self.violations.append(Violation(
                    severity=Severity.WARNING,
                    rule="archive-metadata-missing",
                    file=str(file_path.relative_to(self.repo_root)),
                    message="Archived files should have frontmatter with archived-date and archived-reason",
                    fix_available=True
                ))

    def check_naming_conventions(self):
        """Validate naming conventions for work/, tasks/"""

        # ADR naming: {scope}-ADR-XXX-description.md
        adr_pattern = re.compile(r"^(cm|km|g)-ADR-\d{3}-.+\.md$")
        for file_path in self.repo_root.glob("work/adrs-active/*.md"):
            if not adr_pattern.match(file_path.name):
                self.violations.append(Violation(
                    severity=Severity.ERROR,
                    rule="adr-naming-convention",
                    file=str(file_path.relative_to(self.repo_root)),
                    message=f"Invalid ADR name. Expected: {{cm|km|g}}-ADR-XXX-description.md",
                    fix_available=False
                ))

        # Plan naming: {scope}-plan-description.md
        plan_pattern = re.compile(r"^(cm|km|g)-plan-.+\.md$")
        for file_path in self.repo_root.glob("work/plans-active/*.md"):
            if not plan_pattern.match(file_path.name):
                self.violations.append(Violation(
                    severity=Severity.ERROR,
                    rule="plan-naming-convention",
                    file=str(file_path.relative_to(self.repo_root)),
                    message=f"Invalid plan name. Expected: {{cm|km|g}}-plan-description.md",
                    fix_available=False
                ))

        # Queue naming: {scope}-queue-active.json
        queue_pattern = re.compile(r"^(cm|km|g)-queue-active\.json$")
        for file_path in self.repo_root.glob("tasks/queues-active/*.json"):
            if not queue_pattern.match(file_path.name):
                self.violations.append(Violation(
                    severity=Severity.ERROR,
                    rule="queue-naming-convention",
                    file=str(file_path.relative_to(self.repo_root)),
                    message=f"Invalid queue name. Expected: {{cm|km|g}}-queue-active.json",
                    fix_available=False
                ))

    def check_classification(self):
        """CredentialMate (HIPAA) documents should be classified as 'confidential'"""
        cm_files = list(self.repo_root.glob("work/**/cm-*.md"))

        for file_path in cm_files:
            with open(file_path, 'r') as f:
                content = f.read()

            if not content.startswith("---\n"):
                continue  # Already caught by frontmatter check

            try:
                frontmatter_end = content.find("\n---\n", 4)
                if frontmatter_end == -1:
                    continue

                frontmatter_yaml = content[4:frontmatter_end]
                metadata = yaml.safe_load(frontmatter_yaml)

                classification = metadata.get("compliance", {}).get("iso27001", {}).get("classification")
                if classification != "confidential":
                    self.violations.append(Violation(
                        severity=Severity.WARNING,
                        rule="hipaa-classification",
                        file=str(file_path.relative_to(self.repo_root)),
                        message=f"CredentialMate documents should use 'confidential' classification (found: {classification or 'none'})",
                        fix_available=True
                    ))
            except:
                pass  # Invalid frontmatter already caught

    def check_file_locations(self):
        """Check for files in wrong locations"""

        # No markdown files should be added to root (except core docs)
        root_md_files = list(self.repo_root.glob("*.md"))
        allowed_root_files = {
            "CATALOG.md", "CLAUDE.md", "STATE.md", "DECISIONS.md",
            "USER-PREFERENCES.md", "ROADMAP.md", "QUICKSTART.md",
            "SYSTEM-CONFIGURATION.md", "AI-RUN-COMPANY.md", "claude.md",
            "gemini.md", "README.md"
        }

        for file_path in root_md_files:
            if file_path.name not in allowed_root_files:
                suggested_location = self._suggest_location(file_path.name)
                self.violations.append(Violation(
                    severity=Severity.WARNING,
                    rule="file-location",
                    file=str(file_path.relative_to(self.repo_root)),
                    message=f"File should not be at root. Suggested location: {suggested_location}",
                    fix_available=True
                ))

    def _suggest_location(self, filename: str) -> str:
        """Suggest correct location for misplaced file"""
        if "plan" in filename.lower():
            return "work/plans-active/"
        elif "adr" in filename.lower():
            return "work/adrs-active/"
        elif "session" in filename.lower():
            return "sessions/"
        elif "guide" in filename.lower() or "how-to" in filename.lower():
            return "docs/guides/"
        elif "architecture" in filename.lower():
            return "docs/architecture/"
        else:
            return "docs/"

    def generate_report(self) -> str:
        """Generate compliance report"""
        report = []
        report.append("=" * 60)
        report.append("DOCUMENTATION STRUCTURE COMPLIANCE REPORT")
        report.append("=" * 60)
        report.append(f"\nRepository: {self.repo_root.absolute()}")
        report.append(f"Total violations: {len(self.violations)}\n")

        errors = [v for v in self.violations if v.severity == Severity.ERROR]
        warnings = [v for v in self.violations if v.severity == Severity.WARNING]
        infos = [v for v in self.violations if v.severity == Severity.INFO]

        report.append(f"  Errors:   {len(errors)} 🚫")
        report.append(f"  Warnings: {len(warnings)} ⚠️")
        report.append(f"  Info:     {len(infos)} ℹ️\n")

        if errors:
            report.append("\n" + "=" * 60)
            report.append("ERRORS (Must Fix)")
            report.append("=" * 60)
            for v in errors:
                report.append(f"\n{v}\n")

        if warnings:
            report.append("\n" + "=" * 60)
            report.append("WARNINGS (Should Fix)")
            report.append("=" * 60)
            for v in warnings:
                report.append(f"\n{v}\n")

        if not self.violations:
            report.append("\n✅ All documentation structure checks passed!")

        return "\n".join(report)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate documentation structure (ADR-010)")
    parser.add_argument("--check", nargs="?", const=".", help="Validate directory (default: entire repo)")
    parser.add_argument("--report", action="store_true", help="Generate compliance report")
    parser.add_argument("--fix", action="store_true", help="Auto-fix violations where possible")

    args = parser.parse_args()

    validator = DocumentationValidator()
    violations = validator.validate_all()

    if args.report or args.check:
        print(validator.generate_report())

        # Exit with error code if violations exist
        errors = [v for v in violations if v.severity == Severity.ERROR]
        if errors:
            exit(1)

    if args.fix:
        print("🔧 Auto-fix not yet implemented. Coming soon!")
        exit(1)


if __name__ == "__main__":
    main()
