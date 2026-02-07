#!/usr/bin/env python3
"""
Validation Runner Script

Runs the ValidationRunner against synthetic or real tasks to
collect metrics and generate reports.

Usage:
    python scripts/run_validation.py --synthetic 20
    python scripts/run_validation.py --queue tasks/work_queue_credentialmate.json
"""

import argparse
import asyncio
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.validation_runner import ValidationRunner


def generate_synthetic_tasks(count: int, project: str = "test") -> List[Dict[str, Any]]:
    """Generate synthetic tasks for validation testing."""
    task_types = ["bug", "feature", "refactor", "test", "docs"]
    priorities = ["P0", "P1", "P2", "P3"]

    titles = [
        "Fix null pointer exception in user service",
        "Add pagination to search results",
        "Refactor authentication module",
        "Update API documentation",
        "Add unit tests for payment flow",
        "Fix race condition in cache layer",
        "Implement retry logic for API calls",
        "Add input validation for forms",
        "Fix memory leak in websocket handler",
        "Update error messages for clarity",
        "Add logging to critical paths",
        "Fix timezone handling in scheduler",
        "Implement rate limiting",
        "Add health check endpoint",
        "Fix SQL injection vulnerability",
        "Update dependencies to latest",
        "Add integration tests for auth",
        "Fix broken image upload",
        "Implement soft delete for records",
        "Add caching for frequent queries",
    ]

    tasks = []
    for i in range(count):
        task = {
            "task_id": f"TASK-{i+1:03d}",
            "project": project,
            "title": titles[i % len(titles)],
            "type": random.choice(task_types),
            "priority": random.choice(priorities),
            "status": "pending",
        }
        tasks.append(task)

    return tasks


async def run_validation(
    tasks: List[Dict[str, Any]],
    output_dir: Path,
    max_parallel: int = 3,
    simulate_execution: bool = True
) -> Dict[str, Any]:
    """
    Run validation on tasks.

    Args:
        tasks: List of task definitions
        output_dir: Directory for output files
        max_parallel: Max parallel task execution
        simulate_execution: If True, simulate rather than execute real agents

    Returns:
        Validation results
    """
    print(f"\n{'='*60}")
    print(f"  Multi-Agent Validation Run")
    print(f"{'='*60}")
    print(f"  Tasks: {len(tasks)}")
    print(f"  Max Parallel: {max_parallel}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}\n")

    # Create runner
    run_id = f"VAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    runner = ValidationRunner(
        output_dir=output_dir,
        max_parallel=max_parallel,
        run_id=run_id
    )

    # Track progress
    def on_progress(completed: int, total: int, task_id: str) -> None:
        pct = (completed / total) * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"\r  [{bar}] {completed}/{total} ({pct:.0f}%) - {task_id}", end="", flush=True)

    print("Running validation...\n")

    # Execute batch
    if simulate_execution:
        # Override internal execution with simulation
        async def simulate_task(task: Dict[str, Any]) -> Dict[str, Any]:
            _ = task  # Unused in simulation
            # Simulate variable execution time
            await asyncio.sleep(random.uniform(0.1, 0.5))

            # Simulate outcomes (80% success rate)
            success = random.random() < 0.8
            iterations = random.randint(3, 15)
            cost = random.uniform(0.01, 0.05)

            if success:
                return {
                    "status": "completed",
                    "verdict": "PASS",
                    "iterations": iterations,
                    "cost": cost,
                    "specialists": {
                        "bugfix": {"iterations": iterations // 2, "cost": cost * 0.6, "verdict": "PASS"},
                        "testwriter": {"iterations": iterations // 2, "cost": cost * 0.4, "verdict": "PASS"},
                    }
                }
            else:
                return {
                    "status": "failed",
                    "verdict": "FAIL",
                    "iterations": iterations,
                    "cost": cost * 0.5,
                    "error_message": "Simulated failure for testing"
                }

        runner._execute_task_internal = simulate_task  # type: ignore[method-assign]

    results = await runner.execute_batch(
        tasks,
        generate_report=True,
        on_progress=on_progress
    )

    print("\n")  # New line after progress bar

    # Generate ROI report
    roi_report = runner.get_roi_report()

    # Save reports
    report_paths = runner.save_reports()

    # Print summary
    summary = runner.generate_summary()

    print(f"\n{'='*60}")
    print(f"  Validation Complete")
    print(f"{'='*60}")
    print(f"  Run ID: {run_id}")
    print(f"  Tasks Total: {summary['tasks_total']}")
    print(f"  Tasks Completed: {summary['tasks_completed']}")
    print(f"  Tasks Failed: {summary['tasks_failed']}")
    print(f"  Success Rate: {summary['success_rate']:.1%}")
    print(f"  Total Cost: ${summary['total_cost']:.4f}")
    print(f"  Avg Cost/Task: ${summary['avg_cost_per_task']:.4f}")
    print(f"{'='*60}")
    print(f"\n  ROI Analysis:")
    print(f"    Total Value: ${roi_report['total_value']:.2f}")
    print(f"    Total Cost: ${roi_report['total_cost']:.4f}")
    print(f"    Net Benefit: ${roi_report['net_benefit']:.2f}")
    print(f"    ROI: {roi_report['run_roi']:.0f}x")
    print(f"{'='*60}")
    print(f"\n  Reports saved to:")
    print(f"    Markdown: {report_paths['markdown']}")
    print(f"    JSON: {report_paths['json']}")
    print(f"{'='*60}\n")

    return {
        "run_id": run_id,
        "summary": summary,
        "roi": roi_report,
        "report_paths": report_paths,
        "results": results
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-agent validation")
    parser.add_argument(
        "--synthetic",
        type=int,
        default=0,
        help="Number of synthetic tasks to generate"
    )
    parser.add_argument(
        "--queue",
        type=str,
        help="Path to work queue JSON file"
    )
    parser.add_argument(
        "--project",
        type=str,
        default="test",
        help="Project name for synthetic tasks"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=3,
        help="Max parallel task execution"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".validation",
        help="Output directory for reports"
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Execute real agents (default: simulate)"
    )

    args = parser.parse_args()

    # Determine tasks
    if args.synthetic > 0:
        tasks = generate_synthetic_tasks(args.synthetic, args.project)
    elif args.queue:
        runner = ValidationRunner(output_dir=Path(args.output))
        tasks = runner.load_from_work_queue(
            Path(args.queue),
            status_filter=["pending"]
        )
    else:
        print("Error: Specify --synthetic N or --queue path")
        sys.exit(1)

    if not tasks:
        print("No tasks to validate")
        sys.exit(0)

    # Run validation
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = asyncio.run(run_validation(
        tasks=tasks,
        output_dir=output_dir,
        max_parallel=args.parallel,
        simulate_execution=not args.real
    ))

    # Exit with appropriate code
    if result["summary"]["success_rate"] >= 0.8:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
