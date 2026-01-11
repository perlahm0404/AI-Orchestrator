#!/usr/bin/env python3
"""
Parallel Agent Orchestration using Claude Code Task tool.

This launches multiple agents in parallel within the same Claude Code session,
leveraging the user's claude.ai access and bypass permissions.

Usage:
    python -m orchestration.parallel_agents --config config.yaml
"""

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.contract import load as load_contract
from governance.kill_switch import mode
from adapters import get_adapter


@dataclass
class AgentTask:
    """Configuration for a single agent task."""
    agent_type: str  # bugfix, codequality, qa-team, dev-team
    project: str
    task_description: str
    branch: str
    priority: int = 1


class ParallelAgentOrchestrator:
    """
    Orchestrates multiple agents running in parallel via Claude Code Task tool.

    This doesn't spawn subprocess - it creates task definitions that Claude Code
    will execute in parallel using the current session's permissions.
    """

    def __init__(self, tasks: List[AgentTask]):
        self.tasks = tasks
        self.orchestrator_path = Path(__file__).parent.parent

    def _check_kill_switch(self) -> bool:
        """Check if kill switch allows operation."""
        try:
            mode.require_normal()
            return True
        except Exception as e:
            print(f"❌ Kill switch blocked: {e}")
            return False

    def _validate_task(self, task: AgentTask) -> tuple[bool, str]:
        """Validate a task against its contract."""
        try:
            contract = load_contract(task.agent_type)
            adapter = get_adapter(task.project)

            # Check branch restrictions
            if contract.branch_restrictions:
                allowed_patterns = contract.branch_restrictions.get("allowed_patterns", [])
                if allowed_patterns and not any(
                    task.branch.startswith(p.replace("*", ""))
                    for p in allowed_patterns
                ):
                    return False, f"Branch '{task.branch}' not allowed for {task.agent_type}"

            return True, "OK"

        except Exception as e:
            return False, str(e)

    def generate_task_prompts(self) -> List[Dict[str, str]]:
        """
        Generate task prompts for Claude Code to execute in parallel.

        Returns a list of task configurations that can be passed to Claude Code's
        Task tool for parallel execution.
        """
        if not self._check_kill_switch():
            return []

        task_prompts = []

        for task in self.tasks:
            # Validate
            valid, msg = self._validate_task(task)
            if not valid:
                print(f"⚠️  Skipping {task.agent_type} on {task.project}: {msg}")
                continue

            # Load contract
            contract = load_contract(task.agent_type)
            adapter = get_adapter(task.project)
            context = adapter.get_context()

            # Build governed prompt
            prompt = self._build_governed_prompt(task, contract, context)

            task_prompts.append({
                "agent_type": task.agent_type,
                "project": task.project,
                "branch": task.branch,
                "priority": task.priority,
                "prompt": prompt,
                "description": f"{task.agent_type} on {task.project}: {task.task_description[:50]}"
            })

        return task_prompts

    def _build_governed_prompt(self, task: AgentTask, contract, context) -> str:
        """Build a governed prompt for the agent."""

        # Extract key contract rules
        allowed_ops = ", ".join(contract.allowed_actions or [])
        forbidden_ops = ", ".join(contract.forbidden_actions or [])

        prompt = f"""You are a {task.agent_type} agent working on {task.project}.

**PROJECT CONTEXT**:
- Project path: {context.project_path}
- Branch: {task.branch}
- Language: {context.language}

**YOUR CONTRACT** ({task.agent_type}):
- Allowed: {allowed_ops}
- Forbidden: {forbidden_ops}
- Max files: {contract.limits.get('max_files_changed', 'unlimited')}
- Max lines: {contract.limits.get('max_lines_added', 'unlimited')}

**GOVERNANCE RULES**:
1. Work ONLY in branch: {task.branch}
2. DO NOT modify: migrations, .github, auth, secrets, package-lock.json
3. After changes, verify with Ralph:
   cd {self.orchestrator_path} && .venv/bin/python -m ralph.cli verify --project {task.project} --branch {task.branch}
4. If Ralph returns BLOCKED, revert immediately with:
   cd {context.project_path} && git checkout HEAD -- .
5. Stay within your contract limits

**YOUR TASK**:
{task.task_description}

**WORKFLOW**:
1. Switch to branch: {task.branch}
2. Make changes (respect contract limits)
3. Run Ralph verification
4. If PASS: create commit with evidence
5. If FAIL: fix issues and re-verify
6. If BLOCKED: revert and report why

Begin work autonomously. No human confirmation needed.
Report when complete with Ralph verdict and files changed.
"""
        return prompt

    def save_task_file(self, output_path: Path):
        """Save task configuration to file for execution."""
        task_prompts = self.generate_task_prompts()

        config = {
            "orchestrator_version": "v5.0",
            "generated_at": datetime.now().isoformat(),
            "total_tasks": len(task_prompts),
            "tasks": task_prompts
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ Generated {len(task_prompts)} task configurations")
        print(f"📄 Saved to: {output_path}")
        return task_prompts


def main():
    parser = argparse.ArgumentParser(description="Orchestrate parallel agents")
    parser.add_argument("--config", help="YAML config file with tasks")
    parser.add_argument("--output", default="tasks_to_run.json", help="Output file")

    args = parser.parse_args()

    # Example tasks (would normally load from config)
    tasks = [
        AgentTask(
            agent_type="qa-team",
            project="karematch",
            task_description="Fix failing tests in the test suite",
            branch="fix/test-failures",
            priority=1
        ),
        AgentTask(
            agent_type="bugfix",
            project="karematch",
            task_description="Process bugs from docs/VERIFIED-BUGS.md",
            branch="fix/verified-bugs",
            priority=2
        ),
        AgentTask(
            agent_type="dev-team",
            project="karematch",
            task_description="Implement matching algorithm for therapist-patient pairing",
            branch="feature/matching-algorithm",
            priority=3
        ),
    ]

    orchestrator = ParallelAgentOrchestrator(tasks)
    task_prompts = orchestrator.save_task_file(Path(args.output))

    # Print instructions
    print("\n" + "="*80)
    print("NEXT STEP: Run these tasks in parallel")
    print("="*80)
    print("\nIn Claude Code, ask me to:")
    print('"Launch all tasks from tasks_to_run.json in parallel using the Task tool"')
    print("\nOr manually execute each task prompt as a separate Task agent.")
    print("="*80)


if __name__ == "__main__":
    main()
