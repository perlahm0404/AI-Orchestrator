"""
KareMatch Adapter

Connects AI Brain to the KareMatch repository.

KareMatch:
- Node/TS monorepo
- Vitest for testing
- Playwright for E2E
- L2 autonomy (higher trust, not HIPAA)

Location: /Users/tmac/karematch
"""

from pathlib import Path
import yaml

from ..base import BaseAdapter, AppContext


class KareMatchAdapter(BaseAdapter):
    """Adapter for KareMatch project."""

    def __init__(self):
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def get_context(self) -> AppContext:
        """Get KareMatch context for Ralph."""
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

    def run_ralph(self, changed_files: list[str], session_id: str) -> dict:
        """Run Ralph verification for KareMatch."""
        from ralph import engine

        context = self.get_context()

        verdict = engine.verify(
            project=context.project_name,
            changes=changed_files,
            session_id=session_id,
            app_context=context
        )

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
            "evidence": verdict.evidence
        }
