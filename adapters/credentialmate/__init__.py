"""
CredentialMate Adapter

Connects AI Brain to the CredentialMate repository.

CredentialMate:
- FastAPI backend (Python)
- Next.js frontend (TypeScript)
- PostgreSQL database
- L1 autonomy (stricter, HIPAA compliance)

Location: /Users/tmac/1_REPOS/credentialmate
"""

from pathlib import Path
import yaml

from ..base import BaseAdapter, AppContext


class CredentialMateAdapter(BaseAdapter):
    """Adapter for CredentialMate project."""

    def __init__(self):
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def get_context(self) -> AppContext:
        """Get CredentialMate context for Ralph."""
        return AppContext(
            project_name=self.config["project"]["name"],
            project_path=self.config["project"]["path"],
            language=self.config["project"]["language"],
            lint_command=self.config["commands"]["lint"],
            typecheck_command=self.config["commands"]["typecheck"],
            test_command=self.config["commands"]["test"],
            coverage_command=self.config["commands"]["coverage"],
            source_paths=self.config["paths"]["source"],
            test_paths=self.config["paths"]["tests"],
            coverage_report_path=self.config["paths"]["coverage_report"],
            autonomy_level=self.config["autonomy_level"],
        )

    def get_hipaa_config(self) -> dict:
        """Get HIPAA-specific configuration."""
        return self.config.get("hipaa", {})

    def get_thresholds(self) -> dict:
        """Get L1 autonomy thresholds."""
        return self.config.get("thresholds", {})

    def get_guardrails(self) -> dict:
        """Get CredentialMate-specific guardrails."""
        return self.config.get("guardrails", {})

    def run_ralph(self, changed_files: list[str], session_id: str) -> dict:
        """Run Ralph verification for CredentialMate.

        Includes additional HIPAA checks beyond standard verification.
        """
        from ralph import engine

        context = self.get_context()

        # Run standard Ralph verification
        verdict = engine.verify(
            project=context.project_name,
            changes=changed_files,
            session_id=session_id,
            app_context=context
        )

        # Add HIPAA-specific checks if enabled
        hipaa_config = self.get_hipaa_config()
        hipaa_violations = []

        if hipaa_config.get("enabled", False):
            hipaa_violations = self._check_hipaa_compliance(
                changed_files,
                hipaa_config
            )

            # HIPAA violations escalate to BLOCKED
            if hipaa_violations:
                from ralph.verdict import VerdictType
                verdict.type = VerdictType.BLOCKED
                verdict.reason = f"HIPAA compliance violation: {hipaa_violations[0]}"
                verdict.evidence["hipaa_violations"] = hipaa_violations

        # Convert verdict to dict for JSON serialization
        return {
            "type": verdict.type.value,
            "reason": verdict.reason,
            "steps": [
                {
                    "step": step.step,
                    "passed": step.passed,
                    "duration_ms": step.duration_ms,
                    "output_length": len(step.output)
                }
                for step in verdict.steps
            ],
            "evidence": verdict.evidence,
            "hipaa_violations": hipaa_violations,
            "autonomy_level": "L1"
        }

    def _check_hipaa_compliance(
        self,
        changed_files: list[str],
        hipaa_config: dict
    ) -> list[str]:
        """Check files for HIPAA compliance issues.

        Returns list of violation descriptions.
        """
        import re
        from pathlib import Path as FilePath

        violations = []
        phi_patterns = hipaa_config.get("phi_patterns", [])
        sensitive_paths = hipaa_config.get("sensitive_paths", [])

        project_path = FilePath(self.config["project"]["path"])

        for file_path in changed_files:
            full_path = project_path / file_path

            # Check if file is in sensitive path
            is_sensitive = any(
                file_path.startswith(sp) for sp in sensitive_paths
            )

            if not full_path.exists():
                continue

            try:
                content = full_path.read_text()

                # Check for hardcoded PHI patterns in non-test files
                if "test" not in file_path.lower():
                    for pattern in phi_patterns:
                        # Look for hardcoded values (not variable names)
                        # e.g., "patient_name = 'John Doe'" is bad
                        # but "patient_name = user.name" is fine
                        hardcoded_pattern = rf'{pattern}\s*=\s*["\'][^"\']+["\']'
                        matches = re.findall(hardcoded_pattern, content, re.IGNORECASE)
                        if matches:
                            violations.append(
                                f"Potential hardcoded PHI in {file_path}: {matches[0][:50]}"
                            )

                # Check for logging of sensitive data
                if is_sensitive:
                    log_patterns = [
                        r'print\s*\(',
                        r'logger\.(debug|info|warning|error)\s*\([^)]*\b(patient|ssn|dob)\b',
                    ]
                    for lp in log_patterns:
                        if re.search(lp, content, re.IGNORECASE):
                            violations.append(
                                f"Potential PHI logging in sensitive file: {file_path}"
                            )
                            break

            except Exception:
                # Can't read file, skip HIPAA check
                pass

        return violations
