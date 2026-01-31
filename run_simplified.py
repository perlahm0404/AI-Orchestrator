#!/usr/bin/env python3
"""
Simplified Autonomous Loop Runner (v7.3)

Uses the new SimplifiedLoop with FastVerify and SelfCorrector.
Lighter weight than autonomous_loop.py, focuses on core execution.

Usage:
    python run_simplified.py --project karematch
    python run_simplified.py --project credentialmate --max-iterations 100
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from orchestration.simplified_loop import SimplifiedLoop, LoopConfig
from adapters.karematch import KareMatchAdapter
from adapters.credentialmate import CredentialMateAdapter


def main() -> None:
    """CLI entry point for simplified autonomous loop."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Simplified Autonomous Loop (v7.3)",
        epilog="""
Examples:
  python run_simplified.py --project karematch
  python run_simplified.py --project credentialmate --max-iterations 100
  python run_simplified.py --project karematch --no-commit

Features:
  - SimplifiedLoop: <100 lines core logic
  - FastVerify: Tiered verification (INSTANT/QUICK/RELATED/FULL)
  - SelfCorrector: Bounded retries with progressive context
  - Progress persistence: Session resume from claude-progress.txt
  - Simplified governance: Single enforcement point
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--project",
        default="karematch",
        choices=["karematch", "credentialmate"],
        help="Project to work on (default: karematch)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=50,
        help="Maximum iterations (default: 50)"
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Disable auto-commit on success"
    )
    parser.add_argument(
        "--queue",
        default="bugs",
        choices=["bugs", "features"],
        help="Queue type (default: bugs)"
    )

    args = parser.parse_args()

    # Get project directory from adapter
    if args.project == "karematch":
        adapter = KareMatchAdapter()  # type: ignore[no-untyped-call]
        project_dir = Path(adapter.get_context().project_path)
    else:
        cm_adapter = CredentialMateAdapter()  # type: ignore[no-untyped-call]
        project_dir = Path(cm_adapter.get_context().project_path)

    # Determine work queue path
    if args.queue == "features":
        queue_path = Path(__file__).parent / "tasks" / f"work_queue_{args.project}_features.json"
    else:
        queue_path = Path(__file__).parent / "tasks" / f"work_queue_{args.project}.json"

    # Create config
    config = LoopConfig(
        project_dir=project_dir,
        max_iterations=args.max_iterations,
        auto_commit=not args.no_commit,
        work_queue_path=queue_path
    )

    print(f"\n{'='*60}")
    print(f"🚀 Simplified Autonomous Loop (v7.3)")
    print(f"{'='*60}\n")
    print(f"Project: {args.project}")
    print(f"Directory: {project_dir}")
    print(f"Queue: {queue_path}")
    print(f"Max iterations: {args.max_iterations}")
    print(f"Auto-commit: {not args.no_commit}\n")

    # Run loop
    try:
        loop = SimplifiedLoop(config)
        result = asyncio.run(loop.run())

        print(f"\n{'='*60}")
        print(f"📊 Results")
        print(f"{'='*60}\n")
        print(f"Completed: {result.completed}")
        print(f"Failed: {result.failed}")
        print(f"Blocked: {result.blocked}")
        print(f"Iterations: {result.iterations}\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted. Resume by running again.\n")
    except FileNotFoundError as e:
        print(f"\n❌ Work queue not found: {e}\n")
        print(f"Create it at: {queue_path}")


if __name__ == "__main__":
    main()
