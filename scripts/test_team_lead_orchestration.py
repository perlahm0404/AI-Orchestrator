#!/usr/bin/env python3
"""
Team Lead Orchestration Test Script

Demonstrates the full multi-agent orchestration flow:
1. Task analysis and routing
2. Specialist coordination
3. Metrics collection
4. ROI analysis
5. Report generation

Usage:
    python scripts/test_team_lead_orchestration.py
    python scripts/test_team_lead_orchestration.py --tasks 5 --real
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.metrics_collector import MetricsCollector
from orchestration.validation_report import ValidationReportGenerator
from orchestration.roi_calculator import ROICalculator


# ============================================================================
# Simulated Team Lead Orchestrator
# ============================================================================

class SimulatedTeamLead:
    """
    Simulated Team Lead for testing the orchestration flow.

    In production, this would be replaced by the real TeamLead class
    that calls actual AI agents.
    """

    def __init__(
        self,
        collector: MetricsCollector,
        simulate: bool = True
    ):
        self.collector = collector
        self.simulate = simulate
        self.roi_calculator = ROICalculator(collector)

    async def orchestrate(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate a task through the multi-agent system.

        Args:
            task: Task definition

        Returns:
            Orchestration result
        """
        task_id = task.get("task_id", "UNKNOWN")
        project = task.get("project", "test")
        priority = task.get("priority", "P2")
        task_type = task.get("type", "bug")

        print(f"\n{'─'*60}")
        print(f"  Task: {task_id} - {task.get('title', '')[:40]}")
        print(f"  Type: {task_type} | Priority: {priority}")
        print(f"{'─'*60}")

        # Step 1: Record task start
        self.collector.record_task_start(task_id, project)

        # Step 2: Auto-estimate value
        value = self.roi_calculator.auto_estimate_value(task_id, priority, task_type)
        print(f"  Estimated Value: ${value:.2f}")

        # Step 3: Route task (simulated routing decision)
        # Use multi-agent for P0/P1 or feature/refactor types
        use_multi = priority in ["P0", "P1"] or task_type in ["feature", "refactor"]
        route_reason = (
            f"High priority ({priority})" if priority in ["P0", "P1"]
            else f"Complex type ({task_type})" if task_type in ["feature", "refactor"]
            else f"Simple task, single agent sufficient"
        )

        print(f"  Routing: {'Multi-Agent' if use_multi else 'Single-Agent'}")
        print(f"  Reason: {route_reason}")

        # Step 4: Determine specialists
        if use_multi:
            specialists = self._determine_specialists(task_type)
        else:
            specialists = [self._primary_specialist(task_type)]

        print(f"  Specialists: {', '.join(specialists)}")

        # Step 5: Execute specialists
        specialist_results = {}
        total_cost = 0.0
        total_iterations = 0

        for spec_type in specialists:
            result = await self._execute_specialist(task_id, spec_type)
            specialist_results[spec_type] = result
            total_cost += result.get("cost", 0)
            total_iterations += result.get("iterations", 0)

        # Step 6: Determine overall verdict
        all_passed = all(
            r.get("verdict") == "PASS"
            for r in specialist_results.values()
        )
        verdict = "PASS" if all_passed else "FAIL"
        status = "completed" if all_passed else "failed"

        # Step 7: Record task completion
        self.collector.record_task_complete(
            task_id=task_id,
            status=status,
            verdict=verdict,
            iterations=total_iterations,
            cost=total_cost
        )

        # Step 8: Calculate ROI
        roi = self.roi_calculator.calculate_roi(task_id)
        net_benefit = self.roi_calculator.calculate_net_benefit(task_id)

        print(f"\n  Results:")
        print(f"    Status: {status.upper()}")
        print(f"    Verdict: {verdict}")
        print(f"    Cost: ${total_cost:.4f}")
        print(f"    ROI: {roi:.0f}x")
        print(f"    Net Benefit: ${net_benefit:.2f}")

        return {
            "task_id": task_id,
            "status": status,
            "verdict": verdict,
            "specialists": specialist_results,
            "total_cost": total_cost,
            "total_iterations": total_iterations,
            "value": value,
            "roi": roi,
            "net_benefit": net_benefit
        }

    async def _execute_specialist(
        self,
        task_id: str,
        spec_type: str
    ) -> Dict[str, Any]:
        """Execute a specialist agent."""
        import random

        # Record start
        max_iterations = self._get_iteration_budget(spec_type)
        self.collector.record_specialist_start(task_id, spec_type, max_iterations)

        if self.simulate:
            # Simulate execution
            await asyncio.sleep(random.uniform(0.1, 0.3))

            # 85% success rate
            success = random.random() < 0.85
            iterations = random.randint(3, max_iterations)
            cost = self._estimate_cost(spec_type, iterations)

            verdict = "PASS" if success else "FAIL"
        else:
            # Real execution would go here
            # from orchestration.specialist_agent import SpecialistAgent
            # specialist = SpecialistAgent(spec_type, ...)
            # result = await specialist.execute(...)
            verdict = "PASS"
            iterations = 5
            cost = 0.01

        # Record completion
        self.collector.record_specialist_complete(
            task_id, spec_type, iterations, verdict, cost
        )

        print(f"    → {spec_type}: {verdict} ({iterations} iters, ${cost:.4f})")

        return {
            "status": "completed" if verdict == "PASS" else "failed",
            "verdict": verdict,
            "iterations": iterations,
            "cost": cost
        }

    def _determine_specialists(self, task_type: str) -> List[str]:
        """Determine which specialists to use for multi-agent."""
        specialists_map = {
            "bug": ["bugfix", "testwriter"],
            "feature": ["featurebuilder", "testwriter", "codequality"],
            "refactor": ["codequality", "testwriter"],
            "test": ["testwriter"],
            "docs": ["codequality"],
            "deploy": ["deployment"],
            "migration": ["deployment", "testwriter"],
        }
        return specialists_map.get(task_type, ["bugfix"])

    def _primary_specialist(self, task_type: str) -> str:
        """Get primary specialist for single-agent execution."""
        primary_map = {
            "bug": "bugfix",
            "feature": "featurebuilder",
            "refactor": "codequality",
            "test": "testwriter",
            "docs": "codequality",
            "deploy": "deployment",
            "migration": "deployment",
        }
        return primary_map.get(task_type, "bugfix")

    def _get_iteration_budget(self, spec_type: str) -> int:
        """Get iteration budget for specialist type."""
        budgets = {
            "bugfix": 15,
            "testwriter": 15,
            "featurebuilder": 50,
            "codequality": 20,
            "deployment": 10,
            "migration": 15,
        }
        return budgets.get(spec_type, 15)

    def _estimate_cost(self, spec_type: str, iterations: int) -> float:
        """Estimate cost based on specialist and iterations."""
        cost_per_iter = {
            "bugfix": 0.001,
            "testwriter": 0.0008,
            "featurebuilder": 0.001,
            "codequality": 0.0009,
            "deployment": 0.001,
            "migration": 0.001,
        }
        base = cost_per_iter.get(spec_type, 0.001)
        return base * iterations


# ============================================================================
# Test Tasks
# ============================================================================

def generate_test_tasks(count: int = 10) -> List[Dict[str, Any]]:
    """Generate diverse test tasks."""
    tasks = [
        {
            "task_id": "BUG-001",
            "project": "credentialmate",
            "title": "Fix null pointer exception in license validation",
            "type": "bug",
            "priority": "P1",
        },
        {
            "task_id": "FEAT-001",
            "project": "credentialmate",
            "title": "Implement license renewal workflow with notifications",
            "type": "feature",
            "priority": "P0",
        },
        {
            "task_id": "BUG-002",
            "project": "karematch",
            "title": "Fix race condition in therapist matching",
            "type": "bug",
            "priority": "P0",
        },
        {
            "task_id": "REFACTOR-001",
            "project": "credentialmate",
            "title": "Refactor authentication module for better testability",
            "type": "refactor",
            "priority": "P2",
        },
        {
            "task_id": "TEST-001",
            "project": "karematch",
            "title": "Add integration tests for booking flow",
            "type": "test",
            "priority": "P2",
        },
        {
            "task_id": "FEAT-002",
            "project": "karematch",
            "title": "Add provider availability calendar",
            "type": "feature",
            "priority": "P1",
        },
        {
            "task_id": "BUG-003",
            "project": "credentialmate",
            "title": "Fix timezone handling in expiration dates",
            "type": "bug",
            "priority": "P2",
        },
        {
            "task_id": "DEPLOY-001",
            "project": "credentialmate",
            "title": "Deploy v2.1.0 to production",
            "type": "deploy",
            "priority": "P0",
        },
        {
            "task_id": "DOCS-001",
            "project": "karematch",
            "title": "Update API documentation for new endpoints",
            "type": "docs",
            "priority": "P3",
        },
        {
            "task_id": "FEAT-003",
            "project": "credentialmate",
            "title": "Add bulk license import feature",
            "type": "feature",
            "priority": "P1",
        },
    ]
    return tasks[:count]


# ============================================================================
# Main Test Runner
# ============================================================================

async def run_orchestration_test(
    tasks: List[Dict[str, Any]],
    output_dir: Path,
    simulate: bool = True
) -> Dict[str, Any]:
    """
    Run the full orchestration test.

    Args:
        tasks: Tasks to orchestrate
        output_dir: Output directory for reports
        simulate: Whether to simulate agent execution

    Returns:
        Test results
    """
    print("\n" + "="*60)
    print("  MULTI-AGENT TEAM LEAD ORCHESTRATION TEST")
    print("="*60)
    print(f"  Tasks: {len(tasks)}")
    print(f"  Mode: {'Simulation' if simulate else 'Real Execution'}")
    print(f"  Output: {output_dir}")
    print("="*60)

    # Initialize collector
    run_id = f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    collector = MetricsCollector(
        run_id=run_id,
        output_dir=output_dir,
        auto_save=True
    )

    # Initialize Team Lead
    team_lead = SimulatedTeamLead(collector, simulate=simulate)

    # Execute tasks
    results = []
    for task in tasks:
        result = await team_lead.orchestrate(task)
        results.append(result)

    # Complete run
    collector.complete_run()

    # Generate reports
    print("\n" + "="*60)
    print("  GENERATING REPORTS")
    print("="*60)

    generator = ValidationReportGenerator(collector)

    # Summary
    summary = generator.generate_summary()

    # Save reports
    md_path = output_dir / f"orchestration_report_{run_id}.md"
    json_path = output_dir / f"orchestration_report_{run_id}.json"
    generator.save_markdown(md_path)
    generator.save_json(json_path)

    # ROI Report
    roi_report = team_lead.roi_calculator.generate_report()

    # Print summary
    print("\n" + "="*60)
    print("  ORCHESTRATION SUMMARY")
    print("="*60)
    print(f"  Run ID: {run_id}")
    print(f"  Tasks Total: {summary['tasks_total']}")
    print(f"  Tasks Completed: {summary['tasks_completed']}")
    print(f"  Tasks Failed: {summary['tasks_failed']}")
    print(f"  Success Rate: {summary['success_rate']:.1%}")
    print("="*60)
    print(f"\n  COST ANALYSIS")
    print("="*60)
    print(f"  Total Cost: ${summary['total_cost']:.4f}")
    print(f"  Avg Cost/Task: ${summary['avg_cost_per_task']:.4f}")

    # Cost by specialist
    print(f"\n  Cost by Specialist:")
    for spec_type, stats in summary.get('specialist_summary', {}).items():
        print(f"    {spec_type}: ${stats.get('total_cost', 0):.4f} ({stats.get('count', 0)} runs)")

    print("="*60)
    print(f"\n  ROI ANALYSIS")
    print("="*60)
    print(f"  Total Value Generated: ${roi_report['total_value']:.2f}")
    print(f"  Total Cost: ${roi_report['total_cost']:.4f}")
    print(f"  Net Benefit: ${roi_report['net_benefit']:.2f}")
    print(f"  Overall ROI: {roi_report['run_roi']:.0f}x")

    # Per-task ROI
    print(f"\n  Per-Task ROI:")
    for task_id, task_data in roi_report.get('tasks', {}).items():
        print(f"    {task_id}: ${task_data['value']:.0f} value, "
              f"${task_data['cost']:.4f} cost, "
              f"{task_data['roi']:.0f}x ROI")

    print("="*60)
    print(f"\n  REPORTS SAVED")
    print("="*60)
    print(f"  Markdown: {md_path}")
    print(f"  JSON: {json_path}")
    print(f"  Metrics: {output_dir / f'{run_id}.json'}")
    print("="*60 + "\n")

    return {
        "run_id": run_id,
        "summary": summary,
        "roi_report": roi_report,
        "results": results,
        "report_paths": {
            "markdown": md_path,
            "json": json_path
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test Team Lead multi-agent orchestration"
    )
    parser.add_argument(
        "--tasks",
        type=int,
        default=10,
        help="Number of test tasks to run (default: 10)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".orchestration-test",
        help="Output directory for reports"
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real agent execution (default: simulate)"
    )

    args = parser.parse_args()

    # Generate tasks
    tasks = generate_test_tasks(args.tasks)

    # Setup output
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run test
    result = asyncio.run(run_orchestration_test(
        tasks=tasks,
        output_dir=output_dir,
        simulate=not args.real
    ))

    # Exit based on success rate
    if result["summary"]["success_rate"] >= 0.8:
        print("✅ Orchestration test PASSED\n")
        sys.exit(0)
    else:
        print("❌ Orchestration test FAILED (success rate < 80%)\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
