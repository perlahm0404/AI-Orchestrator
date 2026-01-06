#!/usr/bin/env python3
"""
Autonomous Agent Loop - Anthropic's Proven Pattern

Replaces manual run_agent.py with autonomous work discovery:
1. Pull next task from work_queue.json
2. Implement feature with Claude Code CLI
3. Fast verify (30 seconds, not 5 minutes)
4. Self-correct on failures
5. Commit on success
6. Update progress file
7. Repeat

Note: Uses Claude Code CLI (authenticated via claude.ai), not Anthropic API.

Based on: https://github.com/anthropics/claude-quickstarts/autonomous-coding
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tasks.work_queue import WorkQueue, Task
from governance.kill_switch import mode
from adapters.karematch import KareMatchAdapter
from adapters.credentialmate import CredentialMateAdapter
from agents.bugfix import BugFixAgent


def read_progress_file(project_dir: Path) -> str:
    """Read claude-progress.txt for session continuity"""
    progress_file = project_dir / "claude-progress.txt"
    if progress_file.exists():
        return progress_file.read_text()
    return ""


def update_progress_file(project_dir: Path, task: Task, status: str, details: str) -> None:
    """Update claude-progress.txt with latest status"""
    progress_file = project_dir / "claude-progress.txt"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n## {timestamp}\n\n"

    if status == "complete":
        entry += f"- [x] {task.id}: {task.description}\n"
        entry += f"  - Files: {task.file}\n"
        entry += f"  - Status: ✅ Complete\n"
        entry += f"  - {details}\n"
    elif status == "in_progress":
        entry += f"- [ ] {task.id}: {task.description}\n"
        entry += f"  - Status: 🔄 In Progress (attempt {task.attempts})\n"
        entry += f"  - {details}\n"
    elif status == "blocked":
        entry += f"- [ ] {task.id}: {task.description}\n"
        entry += f"  - Status: 🛑 Blocked\n"
        entry += f"  - Reason: {details}\n"

    # Append to file
    with progress_file.open("a") as f:
        f.write(entry)


def git_commit(message: str, project_dir: Path) -> bool:
    """Create git commit for completed task"""
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=project_dir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=project_dir,
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git commit failed: {e.stderr.decode()}")
        return False


async def run_autonomous_loop(
    project_dir: Path,
    max_iterations: int = 50,
    project_name: str = "karematch",
    enable_self_correction: bool = True
) -> None:
    """
    Main autonomous loop - runs until all tasks complete or max iterations reached

    Args:
        project_dir: Path to project directory
        max_iterations: Maximum iterations before stopping
        project_name: Project to work on (karematch or credentialmate)
        enable_self_correction: Enable fast verification and self-correction loop
    """
    print(f"\n{'='*80}")
    print(f"🤖 Starting Autonomous Agent Loop")
    print(f"{'='*80}\n")
    print(f"Project: {project_name}")
    print(f"Max iterations: {max_iterations}\n")

    # Load work queue
    queue_path = Path(__file__).parent / "tasks" / "work_queue.json"
    queue = WorkQueue.load(queue_path)

    print(f"📋 Work Queue Stats:")
    stats = queue.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print()

    # Load adapter
    if project_name == "karematch":
        adapter = KareMatchAdapter()
    elif project_name == "credentialmate":
        adapter = CredentialMateAdapter()
    else:
        print(f"❌ Unknown project: {project_name}")
        return

    app_context = adapter.get_context()
    actual_project_dir = Path(app_context.project_path)

    # Main loop
    for iteration in range(max_iterations):
        print(f"\n{'─'*80}")
        print(f"Iteration {iteration + 1}/{max_iterations}")
        print(f"{'─'*80}\n")

        # 1. Check kill-switch
        try:
            mode.require_normal()
        except Exception as e:
            print(f"🛑 Kill-switch activated: {e}")
            break

        # 2. Get next task
        task = queue.get_in_progress() or queue.get_next_pending()
        if not task:
            print("✅ All tasks complete!")
            break

        print(f"📌 Current Task: {task.id}")
        print(f"   Description: {task.description}")
        print(f"   File: {task.file}")
        print(f"   Attempts: {task.attempts}\n")

        # 3. Mark as in progress
        queue.mark_in_progress(task.id)
        queue.save(queue_path)
        update_progress_file(actual_project_dir, task, "in_progress", "Starting work")

        # 4. Run Claude Code CLI
        from claude.cli_wrapper import ClaudeCliWrapper
        from claude.prompts import generate_smart_prompt

        wrapper = ClaudeCliWrapper(actual_project_dir)

        # Generate smart prompt based on task type
        smart_prompt = generate_smart_prompt(
            task_id=task.id,
            description=task.description,
            file_path=task.file,
            test_files=task.tests if hasattr(task, 'tests') and task.tests else None
        )

        try:
            print("🚀 Executing task via Claude CLI...")
            print(f"   Prompt type: {task.id.split('-')[0] if '-' in task.id else 'UNKNOWN'}")
            result = wrapper.execute_task(
                prompt=smart_prompt,
                files=[task.file] if task.file else [],
                timeout=300
            )

            if result.success:
                print(f"✅ Task executed successfully ({result.duration_ms}ms)")
                print(f"   Changed files: {result.files_changed or 'None detected'}\n")
                changed_files = result.files_changed

                # 5. Phase 2: Fast verification with retry
                from ralph.fast_verify import fast_verify

                verification_passed = False
                max_retries = 3

                if changed_files:
                    for retry in range(max_retries):
                        if retry > 0:
                            print(f"\n🔄 Retry {retry}/{max_retries - 1}: Re-running verification...\n")
                        else:
                            print("🔍 Running fast verification...")

                        verify_result = fast_verify(
                            changed_files=changed_files,
                            project_dir=actual_project_dir,
                            app_context=app_context
                        )

                        if verify_result.status == "PASS":
                            print(f"✅ Fast verification PASSED ({verify_result.duration_ms}ms)\n")
                            verification_passed = True
                            break

                        # Verification failed
                        print(f"❌ Verification failed: {verify_result.reason}")
                        print(f"   Duration: {verify_result.duration_ms}ms")

                        # Check if we should retry
                        if retry < max_retries - 1:
                            # Phase 2.5: Basic auto-fix for lint errors
                            if verify_result.has_lint_errors:
                                print("   Attempting auto-fix with linter...")
                                lint_fix = subprocess.run(
                                    ["npm", "run", "lint:fix"],
                                    cwd=actual_project_dir,
                                    capture_output=True,
                                    text=True
                                )
                                if lint_fix.returncode == 0:
                                    print("   ✅ Lint auto-fix completed")
                                    # Update changed files list
                                    git_result = subprocess.run(
                                        ["git", "diff", "--name-only", "HEAD"],
                                        cwd=actual_project_dir,
                                        capture_output=True,
                                        text=True
                                    )
                                    changed_files = [f.strip() for f in git_result.stdout.split('\n') if f.strip()]
                                else:
                                    print(f"   ⚠️  Lint auto-fix failed: {lint_fix.stderr}")
                            else:
                                print(f"   Cannot auto-fix: {verify_result.reason}")
                                break  # Don't waste retries on non-fixable issues
                        else:
                            # Max retries reached
                            print(f"\n⚠️  Max retries ({max_retries}) reached\n")

                    if not verification_passed:
                        queue.mark_blocked(task.id, f"Verification failed after {max_retries} attempts: {verify_result.reason}")
                        queue.save(queue_path)
                        update_progress_file(
                            actual_project_dir,
                            task,
                            "blocked",
                            f"Verification failed after {max_retries} attempts: {verify_result.reason}"
                        )
                        continue
                else:
                    print("⚠️  No changed files detected, skipping verification\n")
                    verification_passed = True

                # 6. Mark as complete
                queue.mark_complete(task.id)
                queue.save(queue_path)

                # 7. Git commit
                commit_msg = f"feat: {task.description}\n\nTask ID: {task.id}\nFiles: {task.file}"
                if git_commit(commit_msg, actual_project_dir):
                    print("✅ Changes committed to git\n")
                    update_progress_file(
                        actual_project_dir,
                        task,
                        "complete",
                        f"Completed in {result.duration_ms}ms"
                    )
                else:
                    print("⚠️  Git commit failed, but task marked complete\n")
                    update_progress_file(
                        actual_project_dir,
                        task,
                        "complete",
                        f"Completed but commit failed ({result.duration_ms}ms)"
                    )

            else:
                print(f"❌ Task failed: {result.error}")
                print(f"   Duration: {result.duration_ms}ms\n")
                queue.mark_blocked(task.id, result.error or "Execution failed")
                queue.save(queue_path)
                update_progress_file(
                    actual_project_dir,
                    task,
                    "blocked",
                    result.error or "Unknown error"
                )
                continue

        except Exception as e:
            print(f"❌ Exception during execution: {e}\n")
            queue.mark_blocked(task.id, str(e))
            queue.save(queue_path)
            update_progress_file(actual_project_dir, task, "blocked", str(e))
            continue

        # Brief pause for rate limiting
        await asyncio.sleep(3)

    # Final stats
    print(f"\n{'='*80}")
    print(f"📊 Final Work Queue Stats")
    print(f"{'='*80}\n")
    stats = queue.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print()


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Run autonomous agent loop")
    parser.add_argument(
        "--project",
        default="karematch",
        choices=["karematch", "credentialmate"],
        help="Project to work on"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=50,
        help="Maximum iterations"
    )

    args = parser.parse_args()

    # Determine project directory
    # For now, using adapter to get path
    if args.project == "karematch":
        adapter = KareMatchAdapter()
    else:
        adapter = CredentialMateAdapter()

    project_dir = Path(adapter.get_context().project_path)

    # Run loop
    try:
        asyncio.run(run_autonomous_loop(
            project_dir=project_dir,
            max_iterations=args.max_iterations,
            project_name=args.project
        ))
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("   To resume, run the same command again")


if __name__ == "__main__":
    main()
