"""Baseline tracking for distinguishing known bugs from new regressions.

Uses fingerprinting (sha256 hashes) to detect when bugs are introduced.
"""

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from .scanner import ScanResult


class BaselineManager:
    """Manages baseline snapshots and comparison with current scan results."""

    def __init__(self, project_name: str):
        """
        Initialize baseline manager.

        Args:
            project_name: Project name (e.g., 'karematch')
        """
        self.project_name = project_name
        self.baseline_dir = Path('discovery/baselines')
        self.baseline_file = self.baseline_dir / f'{project_name}-baseline.json'

    def create_baseline(self, scan_result: ScanResult) -> None:
        """
        Create initial baseline snapshot.

        Args:
            scan_result: Current scan result to use as baseline
        """
        bugs = self._compute_fingerprints(scan_result)

        # Create serializable version of bugs (without original_error objects)
        serializable_bugs = [
            {k: v for k, v in bug.items() if k != 'original_error'}
            for bug in bugs
        ]

        baseline = {
            'timestamp': datetime.now().isoformat(),
            'project': scan_result.project,
            'commit_sha': self._get_git_sha(),
            'total_bugs': len(bugs),
            'bugs': serializable_bugs
        }

        # Ensure baseline directory exists
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

        # Write baseline file
        with open(self.baseline_file, 'w') as f:
            json.dump(baseline, f, indent=2)

        print(f"✅ Baseline created: {len(bugs)} bugs tracked")

    def compare_with_baseline(self, scan_result: ScanResult) -> tuple[list[dict], list[dict]]:
        """
        Compare current scan with baseline.

        Args:
            scan_result: Current scan result

        Returns:
            Tuple of (new_bugs, baseline_bugs)
            - new_bugs: Bugs not in baseline (regressions)
            - baseline_bugs: Bugs that were in baseline (known issues)
        """
        # If no baseline exists, create one and return all bugs as baseline
        if not self.baseline_file.exists():
            print("⚠️  No baseline found - creating one now")
            self.create_baseline(scan_result)
            return ([], self._compute_fingerprints(scan_result))

        # Load baseline
        with open(self.baseline_file) as f:
            baseline = json.load(f)

        # Extract fingerprints
        baseline_fingerprints = {bug['fingerprint'] for bug in baseline['bugs']}
        current_bugs = self._compute_fingerprints(scan_result)

        # Separate new vs baseline bugs
        new_bugs = [
            bug for bug in current_bugs
            if bug['fingerprint'] not in baseline_fingerprints
        ]
        baseline_bugs = [
            bug for bug in current_bugs
            if bug['fingerprint'] in baseline_fingerprints
        ]

        print(f"📊 Baseline comparison:")
        print(f"   New bugs: {len(new_bugs)} (high priority)")
        print(f"   Baseline bugs: {len(baseline_bugs)} (lower priority)")

        return (new_bugs, baseline_bugs)

    def _compute_fingerprints(self, scan_result: ScanResult) -> list[dict]:
        """
        Compute fingerprints for all bugs in scan result.

        Fingerprint format: sha256(file:line:rule)

        Args:
            scan_result: Scan result to fingerprint

        Returns:
            List of bug dicts with fingerprints and original error objects
        """
        bugs = []

        # Lint errors
        for err in scan_result.lint_errors:
            fingerprint = self._compute_fingerprint(
                err.file, err.line, err.rule_id
            )
            bugs.append({
                'file': err.file,
                'line': err.line,
                'type': 'lint',
                'rule': err.rule_id,
                'fingerprint': fingerprint,
                'original_error': err
            })

        # Type errors
        for err in scan_result.type_errors:
            fingerprint = self._compute_fingerprint(
                err.file, err.line, err.error_code
            )
            bugs.append({
                'file': err.file,
                'line': err.line,
                'type': 'typecheck',
                'rule': err.error_code,
                'fingerprint': fingerprint,
                'original_error': err
            })

        # Test failures
        for failure in scan_result.test_failures:
            # For tests, use test file + test name as fingerprint
            fingerprint = self._compute_fingerprint(
                failure.test_file, 0, failure.test_name
            )
            bugs.append({
                'file': failure.source_file,  # Use source file for grouping
                'line': 0,
                'type': 'test',
                'rule': failure.test_name,
                'fingerprint': fingerprint,
                'original_error': failure
            })

        # Guardrail violations
        for violation in scan_result.guardrail_violations:
            fingerprint = self._compute_fingerprint(
                violation.file, violation.line, violation.pattern
            )
            bugs.append({
                'file': violation.file,
                'line': violation.line,
                'type': 'guardrail',
                'rule': violation.pattern,
                'fingerprint': fingerprint,
                'original_error': violation
            })

        return bugs

    def _compute_fingerprint(self, file: str, line: int, rule: str) -> str:
        """
        Compute SHA256 fingerprint for a bug.

        Args:
            file: File path
            line: Line number
            rule: Rule ID or error code

        Returns:
            SHA256 hash hex string
        """
        key = f"{file}:{line}:{rule}"
        return hashlib.sha256(key.encode()).hexdigest()

    def _get_git_sha(self) -> str:
        """
        Get current git commit SHA.

        Returns:
            Git commit SHA, or 'unknown' if not a git repo
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return 'unknown'
