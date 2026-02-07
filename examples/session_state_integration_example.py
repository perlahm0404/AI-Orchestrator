"""
Example: Using SessionState with IterationLoop

This example demonstrates how to integrate SessionState with the IterationLoop
to enable session persistence and resumption across context resets.

Usage:
    # First run (creates and saves session)
    python examples/session_state_integration_example.py --task-id TASK-123

    # Resume after context reset
    python examples/session_state_integration_example.py --task-id TASK-123 --resume
"""

import argparse
from pathlib import Path
from orchestration.session_state import SessionState, format_session_markdown


class IterationLoopWithSessions:
    """
    Example showing how IterationLoop would use SessionState.
    (Simplified for demonstration purposes)
    """

    def __init__(self, task_id: str, project: str, max_iterations: int = 50):
        self.task_id = task_id
        self.project = project
        self.max_iterations = max_iterations
        self.session = SessionState(task_id, project)
        self.current_iteration = 0

    def load_existing_session(self) -> bool:
        """
        Load existing session if available.
        Returns True if session loaded, False if new session.
        """
        try:
            session_data = self.session.get_latest()
            self.current_iteration = session_data["iteration_count"]
            print(f"✅ Resumed session at iteration {self.current_iteration}")
            return True
        except FileNotFoundError:
            print("🆕 Starting new session")
            return False

    def run_iterations(self, num_iterations: int = 5) -> None:
        """
        Run specified number of iterations and checkpoint after each.
        """
        for i in range(num_iterations):
            self.current_iteration += 1

            # Simulate agent work
            print(f"\n📝 Iteration {self.current_iteration}: Simulated agent work...")

            # Generate simulated output
            output = f"Completed iteration {self.current_iteration} successfully"
            verdict = "PASS"

            # Determine phase based on iteration count
            if self.current_iteration <= 5:
                phase = "design"
            elif self.current_iteration <= 15:
                phase = "implementation"
            elif self.current_iteration <= 30:
                phase = "testing"
            else:
                phase = "finalization"

            # Create progress markdown
            progress_emoji = "✅" if verdict == "PASS" else "❌"
            markdown_line = f"{progress_emoji} Iteration {self.current_iteration}: {phase.title()}"

            # Checkpoint after iteration
            self._checkpoint(
                iteration=self.current_iteration,
                phase=phase,
                output=output,
                verdict=verdict,
                markdown_line=markdown_line,
            )

    def _checkpoint(
        self,
        iteration: int,
        phase: str,
        output: str,
        verdict: str,
        markdown_line: str,
    ) -> None:
        """
        Checkpoint session state after iteration.
        This is called after each iteration to persist progress.
        """
        status = "in_progress" if verdict == "PASS" else "blocked"

        # Determine next steps based on verdict
        if verdict == "PASS":
            next_steps = [f"Continue to iteration {iteration + 1}"]
        else:
            next_steps = ["Fix blocker", f"Retry iteration {iteration}"]

        # Get current session data if exists
        try:
            session_data = self.session.get_latest()
            current_markdown = session_data.get("markdown_content", "")
        except FileNotFoundError:
            current_markdown = "## Progress\n"

        # Append new line
        if not current_markdown.startswith("## Progress"):
            current_markdown = "## Progress\n" + current_markdown
        new_markdown = current_markdown + f"{markdown_line}\n"

        # Save checkpoint
        self.session.save({
            "iteration_count": iteration,
            "phase": phase,
            "status": status,
            "last_output": output,
            "next_steps": next_steps,
            "context_window": 1,  # Would be set by autonomous loop
            "tokens_used": 3847,  # Would be set by actual loop
            "max_iterations": self.max_iterations,
            "agent_type": "feature-builder",
            "markdown_content": new_markdown,
        })

        print(f"   💾 Checkpoint saved (iteration {iteration})")

    def print_session_summary(self) -> None:
        """Print current session summary."""
        try:
            session_data = self.session.get_latest()

            print("\n" + "=" * 70)
            print("SESSION SUMMARY")
            print("=" * 70)
            print(f"Task ID:           {session_data['task_id']}")
            print(f"Project:           {session_data['project']}")
            print(f"Iteration:         {session_data['iteration_count']}/{session_data.get('max_iterations', 50)}")
            print(f"Phase:             {session_data['phase']}")
            print(f"Status:            {session_data['status']}")
            print(f"Last Output:       {session_data.get('last_output', 'N/A')}")
            print(f"Next Steps:        {', '.join(session_data.get('next_steps', []))}")
            print("=" * 70)

            # Also show the markdown content
            if session_data.get("markdown_content"):
                print("\nMARKDOWN CONTENT:")
                print("-" * 70)
                print(session_data["markdown_content"])
                print("-" * 70)

        except FileNotFoundError:
            print("No session found")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Example: SessionState Integration with IterationLoop"
    )
    parser.add_argument("--task-id", default="EXAMPLE-TASK-001", help="Task ID")
    parser.add_argument("--project", default="credentialmate", help="Project name")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume existing session instead of starting new",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of iterations to run",
    )

    args = parser.parse_args()

    print("🚀 SessionState Integration Example")
    print(f"   Task: {args.task_id}")
    print(f"   Project: {args.project}")
    print()

    # Initialize loop
    loop = IterationLoopWithSessions(args.task_id, args.project)

    # Load existing session if requested
    if args.resume:
        session_loaded = loop.load_existing_session()
        if not session_loaded:
            print("⚠️  No existing session found. Starting new.")
    else:
        # Clean up any existing session for fresh start
        try:
            SessionState.delete_session(args.task_id)
            print("🧹 Cleaned up previous session")
        except Exception:
            pass

    # Run iterations
    print(f"\n▶️  Running {args.iterations} iterations...")
    loop.run_iterations(num_iterations=args.iterations)

    # Print summary
    loop.print_session_summary()

    # Show how to load in next context
    print("\n" + "=" * 70)
    print("HOW TO RESUME IN NEXT CONTEXT:")
    print("=" * 70)
    print(f"python examples/session_state_integration_example.py \\")
    print(f"    --task-id {args.task_id} \\")
    print(f"    --project {args.project} \\")
    print(f"    --resume")
    print("=" * 70)


if __name__ == "__main__":
    main()
