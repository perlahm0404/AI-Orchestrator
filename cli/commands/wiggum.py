from typing import Any, Optional

"""
CLI command for starting Wiggum iteration loops.

Usage:
    aibrain wiggum "Fix bug #123" --agent bugfix --project karematch --max-iterations 10 --promise "DONE"

This command starts an agent in Wiggum iteration mode where it can:
- Execute multiple times to self-correct failures
- Stop when completion promise is detected
- Ask human approval when budget exhausted or guardrails blocked
- Use Ralph for verification after each iteration

Wiggum = Iteration control system (uses Ralph for verification)
Ralph = Code quality verification system (PASS/FAIL/BLOCKED)
"""

import argparse
from pathlib import Path
from datetime import datetime
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestration.state_file import write_state_file, LoopState, cleanup_state_file
from orchestration.iteration_loop import IterationLoop
from adapters import get_adapter
from agents.base import AgentConfig
from agents.bugfix import BugFixAgent
from agents.codequality import CodeQualityAgent


def load_agent(agent_name: str, project: str, expected_completion_signal: Optional[str] = None, max_iterations: Optional[int] = None) -> Any:
    """
    Load and configure an agent for Wiggum loop.

    Args:
        agent_name: Agent to use (bugfix, codequality)
        project: Project name (karematch, credentialmate)
        expected_completion_signal: Completion promise text
        max_iterations: Max iterations override

    Returns:
        Configured agent instance
    """
    # Load adapter
    adapter = get_adapter(project)
    app_context = adapter.get_context()

    # Create config
    config = AgentConfig(
        project_name=app_context.project_name,
        agent_name=agent_name,
        expected_completion_signal=expected_completion_signal,
        max_iterations=max_iterations or 10
    )

    # Load agent
    if agent_name == "bugfix":
        return BugFixAgent(adapter, config)
    elif agent_name == "codequality":
        return CodeQualityAgent(adapter, config)
    else:
        raise ValueError(f"Unknown agent: {agent_name}")


def wiggum_command(args: Any) -> int:
    """Start a Wiggum iteration loop."""

    print(f"\n{'='*60}")
    print(f"🔄 Starting Wiggum Loop")
    print(f"{'='*60}")
    print(f"Agent: {args.agent}")
    print(f"Project: {args.project}")
    print(f"Max iterations: {args.max_iterations}")
    if args.promise:
        print(f"Completion promise: <promise>{args.promise}</promise>")
    print(f"Task: {args.task}")
    print(f"{'='*60}\n")

    # Create session ID
    session_id = f"wiggum-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Write state file for persistence
    state = LoopState(
        iteration=0,
        max_iterations=args.max_iterations,
        completion_promise=args.promise,
        task_description=args.task,
        agent_name=args.agent,
        session_id=session_id,
        started_at=datetime.now().isoformat(),
        project_name=args.project,
        task_id=session_id
    )

    state_dir = Path.cwd() / ".aibrain"
    state_file = write_state_file(state, state_dir)
    print(f"📄 State file: {state_file}\n")

    # Load agent
    try:
        agent = load_agent(
            args.agent,
            args.project,
            expected_completion_signal=args.promise,
            max_iterations=args.max_iterations
        )
    except Exception as e:
        print(f"❌ Failed to load agent: {e}")
        cleanup_state_file(state_dir)
        return 1

    # Get app context
    adapter = get_adapter(args.project)
    app_context = adapter.get_context()

    # Run iteration loop
    try:
        loop = IterationLoop(agent, app_context, state_dir=state_dir)
        result = loop.run(
            task_id=session_id,
            task_description=args.task,
            max_iterations=args.max_iterations
        )
    except KeyboardInterrupt:
        print("\n⚠️  Loop interrupted by user")
        cleanup_state_file(state_dir)
        return 1
    except Exception as e:
        print(f"\n❌ Loop failed: {e}")
        cleanup_state_file(state_dir)
        return 1

    # Print summary
    print(f"\n{'='*60}")
    print(f"Wiggum Loop Complete: {result.status.upper()}")
    print(f"{'='*60}")
    print(f"Iterations: {result.iterations}/{args.max_iterations}")

    if result.iteration_summary:
        summary = result.iteration_summary
        print(f"Pass: {summary.get('pass_count', 0)}")
        print(f"Fail: {summary.get('fail_count', 0)}")
        print(f"Blocked: {summary.get('blocked_count', 0)}")

    if result.reason:
        print(f"Reason: {result.reason}")

    if result.verdict:
        print(f"\nFinal verdict: {result.verdict.type.value}")
        print(result.verdict.summary())

    print(f"{'='*60}\n")

    # Cleanup state file
    cleanup_state_file(state_dir)

    # Return exit code
    return 0 if result.status == "completed" else 1


def setup_parser(subparsers: Any) -> int:
    """Setup argparse for wiggum command."""
    parser = subparsers.add_parser(
        "wiggum",
        help="Start Wiggum iteration loop",
        description="""
Run an agent in Wiggum iteration mode with stop hook governance.

The agent will execute multiple times, self-correcting failures until:
- It outputs the completion promise (e.g., <promise>DONE</promise>)
- Ralph verification passes
- Iteration budget exhausted (requires human approval)
- Guardrails blocked (requires human decision)

Wiggum manages iterations, Ralph verifies quality.

Example:
    aibrain wiggum "Fix authentication bug in login.ts" \\
        --agent bugfix --project karematch --max-iterations 15 --promise "DONE"
        """
    )
    parser.add_argument("task", help="Task description")
    parser.add_argument("--agent", required=True, choices=["bugfix", "codequality"],
                       help="Agent to use")
    parser.add_argument("--project", required=True, choices=["karematch", "credentialmate"],
                       help="Project name")
    parser.add_argument("--max-iterations", type=int, default=10,
                       help="Max iterations (default: 10)")
    parser.add_argument("--promise", help="Completion promise text (e.g., 'DONE', 'COMPLETE')")
    parser.set_defaults(func=wiggum_command)
