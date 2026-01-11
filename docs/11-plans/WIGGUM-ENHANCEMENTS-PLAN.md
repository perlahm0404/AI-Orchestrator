# Wiggum System Enhancements Plan

**Date**: 2026-01-06
**Status**: PLANNED
**Priority**: Optional (Post-Production Improvements)

## Overview

Four enhancements to improve the Wiggum system's usability, visibility, and capabilities. None of these are blockers for production use - they are quality-of-life improvements.

---

## Enhancement 1: Knowledge Object CLI Commands

**Priority**: P1 (High Value, Low Effort)
**Effort**: 2-3 hours
**Complexity**: Low

### What It Does

Adds CLI commands for managing Knowledge Objects:
- `aibrain ko approve KO-ID` - Approve a draft KO
- `aibrain ko reject KO-ID "reason"` - Reject a draft KO
- `aibrain ko show KO-ID` - Display full KO details
- `aibrain ko search --tags "ts,orm"` - Search by tags
- `aibrain ko list` - List all approved KOs
- `aibrain ko pending` - List all draft KOs

### Current State

- ✅ Backend fully implemented (`knowledge/service.py`)
- ✅ Data structures defined (`KnowledgeObject` dataclass)
- ❌ CLI commands missing

### Implementation

**File**: `cli/commands/ko.py` (NEW)

```python
"""
CLI commands for Knowledge Object management.

Usage:
    aibrain ko list
    aibrain ko show KO-km-001
    aibrain ko search --tags "typescript,drizzle-orm" --project karematch
    aibrain ko pending
    aibrain ko approve KO-km-001
    aibrain ko reject KO-km-001 "Duplicate of existing KO"
"""

import argparse
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledge import service


def ko_list_command(args):
    """List all approved Knowledge Objects."""
    kos = service.list_approved(project=args.project)

    if not kos:
        print("No approved Knowledge Objects found.")
        return 0

    print(f"\n{'='*80}")
    print(f"Approved Knowledge Objects ({len(kos)})")
    print(f"{'='*80}\n")

    for ko in kos:
        print(f"📚 {ko.id}: {ko.title}")
        print(f"   Project: {ko.project}")
        print(f"   Tags: {', '.join(ko.tags)}")
        print(f"   Created: {ko.created_at}")
        print()

    return 0


def ko_show_command(args):
    """Show full details of a Knowledge Object."""
    ko_id = args.ko_id

    # Try to load from approved
    ko_file = service.KO_APPROVED_DIR / f"{ko_id}.md"
    if not ko_file.exists():
        # Try drafts
        ko_file = service.KO_DRAFTS_DIR / f"{ko_id}.md"

    if not ko_file.exists():
        print(f"❌ Knowledge Object not found: {ko_id}")
        return 1

    # Read and display file
    content = ko_file.read_text()
    print(content)

    return 0


def ko_search_command(args):
    """Search Knowledge Objects by tags."""
    tags = args.tags.split(',') if args.tags else None
    file_patterns = args.file_patterns.split(',') if args.file_patterns else None

    kos = service.find_relevant(
        project=args.project,
        tags=tags,
        file_patterns=file_patterns
    )

    if not kos:
        print("No matching Knowledge Objects found.")
        return 0

    print(f"\n{'='*80}")
    print(f"Matching Knowledge Objects ({len(kos)})")
    print(f"{'='*80}\n")

    for ko in kos:
        print(f"📚 {ko.id}: {ko.title}")
        print(f"   Project: {ko.project}")
        print(f"   Tags: {', '.join(ko.tags)}")
        print(f"   What Was Learned: {ko.what_was_learned[:100]}...")
        print()

    return 0


def ko_pending_command(args):
    """List all pending draft Knowledge Objects."""
    drafts = service.list_drafts()

    if not drafts:
        print("No pending drafts found.")
        return 0

    print(f"\n{'='*80}")
    print(f"Pending Draft Knowledge Objects ({len(drafts)})")
    print(f"{'='*80}\n")

    for ko in drafts:
        print(f"📝 {ko.id}: {ko.title}")
        print(f"   Project: {ko.project}")
        print(f"   Tags: {', '.join(ko.tags)}")
        print(f"   Created: {ko.created_at}")
        print()

    return 0


def ko_approve_command(args):
    """Approve a draft Knowledge Object."""
    ko_id = args.ko_id

    print(f"Approving {ko_id}...")
    ko = service.approve(ko_id)

    if ko is None:
        print(f"❌ Draft not found: {ko_id}")
        return 1

    print(f"✅ Approved: {ko.title}")
    print(f"   Moved to: knowledge/approved/{ko_id}.md")

    return 0


def ko_reject_command(args):
    """Reject a draft Knowledge Object."""
    ko_id = args.ko_id
    reason = args.reason

    draft_file = service.KO_DRAFTS_DIR / f"{ko_id}.md"

    if not draft_file.exists():
        print(f"❌ Draft not found: {ko_id}")
        return 1

    # Move to rejected directory (create if doesn't exist)
    rejected_dir = service.KO_DRAFTS_DIR.parent / "rejected"
    rejected_dir.mkdir(exist_ok=True)

    rejected_file = rejected_dir / f"{ko_id}.md"
    draft_file.rename(rejected_file)

    # Append rejection reason
    with open(rejected_file, "a") as f:
        f.write(f"\n\n---\n\n**REJECTED**: {reason}\n")

    print(f"✅ Rejected: {ko_id}")
    print(f"   Reason: {reason}")
    print(f"   Moved to: knowledge/rejected/{ko_id}.md")

    return 0


def setup_parser(subparsers):
    """Setup argparse for ko command."""
    parser = subparsers.add_parser(
        "ko",
        help="Manage Knowledge Objects",
        description="Create, search, approve, and manage Knowledge Objects"
    )

    ko_subparsers = parser.add_subparsers(dest='ko_command', help='KO command to run')

    # List command
    list_parser = ko_subparsers.add_parser('list', help='List all approved KOs')
    list_parser.add_argument('--project', help='Filter by project')
    list_parser.set_defaults(func=ko_list_command)

    # Show command
    show_parser = ko_subparsers.add_parser('show', help='Show full KO details')
    show_parser.add_argument('ko_id', help='Knowledge Object ID (e.g., KO-km-001)')
    show_parser.set_defaults(func=ko_show_command)

    # Search command
    search_parser = ko_subparsers.add_parser('search', help='Search KOs by tags')
    search_parser.add_argument('--tags', required=True, help='Comma-separated tags')
    search_parser.add_argument('--project', required=True, help='Project name')
    search_parser.add_argument('--file-patterns', help='Comma-separated file patterns')
    search_parser.set_defaults(func=ko_search_command)

    # Pending command
    pending_parser = ko_subparsers.add_parser('pending', help='List pending drafts')
    pending_parser.set_defaults(func=ko_pending_command)

    # Approve command
    approve_parser = ko_subparsers.add_parser('approve', help='Approve a draft KO')
    approve_parser.add_argument('ko_id', help='Knowledge Object ID (e.g., KO-km-001)')
    approve_parser.set_defaults(func=ko_approve_command)

    # Reject command
    reject_parser = ko_subparsers.add_parser('reject', help='Reject a draft KO')
    reject_parser.add_argument('ko_id', help='Knowledge Object ID (e.g., KO-km-001)')
    reject_parser.add_argument('reason', help='Rejection reason')
    reject_parser.set_defaults(func=ko_reject_command)
```

**File**: `cli/__main__.py` (UPDATE)

```python
# Add import
from cli.commands import wiggum, ko, discover  # Add ko

# Register command
ko.setup_parser(subparsers)
```

### Testing

```bash
# Test list
aibrain ko list

# Test show
aibrain ko show KO-km-001

# Test search
aibrain ko search --tags "typescript,drizzle-orm" --project karematch

# Test pending
aibrain ko pending

# Test approve (if drafts exist)
aibrain ko approve KO-km-002

# Test reject
aibrain ko reject KO-km-003 "Duplicate of KO-km-001"
```

### Success Criteria

- ✅ All 6 commands working
- ✅ Help text clear and accurate
- ✅ Error handling for missing KOs
- ✅ Integration with existing `knowledge/service.py`

---

## Enhancement 2: Metrics Dashboard

**Priority**: P2 (Medium Value, Medium Effort)
**Effort**: 4-6 hours
**Complexity**: Medium

### What It Does

Visual display of iteration statistics across all Wiggum sessions:
- Total iterations executed
- Average iterations per task
- Success rate (PASS verdicts)
- Failure rate (FAIL verdicts)
- Block rate (BLOCKED verdicts)
- Top Knowledge Objects consulted
- Agent performance breakdown

### Current State

- ✅ Iteration history tracked in state files (`.aibrain/agent-loop.local.md`)
- ✅ Knowledge Object consultation metrics tracked
- ❌ No aggregation or visualization

### Implementation

**Phase 1: Metrics Collection** (2 hours)

**File**: `orchestration/metrics.py` (NEW)

```python
"""
Wiggum Iteration Metrics Collection and Analysis.

Aggregates metrics from state files and KO consultation logs.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional
import json
import yaml
from datetime import datetime


@dataclass
class SessionMetrics:
    """Metrics for a single Wiggum session."""
    session_id: str
    agent_name: str
    task_id: str
    iterations: int
    verdict: str  # "PASS", "FAIL", "BLOCKED", "ABORTED"
    duration_seconds: Optional[float] = None
    kos_consulted: List[str] = None
    files_changed: List[str] = None
    timestamp: Optional[str] = None


@dataclass
class AggregateMetrics:
    """Aggregate metrics across all sessions."""
    total_sessions: int
    total_iterations: int
    avg_iterations_per_session: float
    success_rate: float  # % PASS
    fail_rate: float     # % FAIL
    block_rate: float    # % BLOCKED
    abort_rate: float    # % ABORTED
    agent_breakdown: Dict[str, int]  # agent_name -> session_count
    top_kos: List[tuple]  # [(ko_id, consult_count), ...]


def collect_session_metrics(state_dir: Path) -> List[SessionMetrics]:
    """
    Collect metrics from all Wiggum state files.

    Args:
        state_dir: Path to .aibrain directory

    Returns:
        List of SessionMetrics
    """
    metrics = []

    # Find all state files (pattern: agent-loop-*.md)
    for state_file in state_dir.glob("agent-loop-*.md"):
        try:
            content = state_file.read_text()

            # Extract YAML frontmatter
            if not content.startswith("---"):
                continue

            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            frontmatter = yaml.safe_load(parts[1])

            # Extract metrics
            session_id = frontmatter.get("session_id", "")
            agent_name = frontmatter.get("agent_name", "")
            task_id = frontmatter.get("task_id", "")
            iterations = frontmatter.get("iteration", 0)
            verdict = frontmatter.get("last_verdict", {}).get("type", "UNKNOWN")
            kos_consulted = frontmatter.get("kos_consulted", [])

            metrics.append(SessionMetrics(
                session_id=session_id,
                agent_name=agent_name,
                task_id=task_id,
                iterations=iterations,
                verdict=verdict,
                kos_consulted=kos_consulted
            ))

        except Exception as e:
            print(f"Warning: Failed to parse {state_file.name}: {e}")
            continue

    return metrics


def aggregate_metrics(sessions: List[SessionMetrics]) -> AggregateMetrics:
    """
    Aggregate metrics across all sessions.

    Args:
        sessions: List of SessionMetrics

    Returns:
        AggregateMetrics
    """
    if not sessions:
        return AggregateMetrics(
            total_sessions=0,
            total_iterations=0,
            avg_iterations_per_session=0.0,
            success_rate=0.0,
            fail_rate=0.0,
            block_rate=0.0,
            abort_rate=0.0,
            agent_breakdown={},
            top_kos=[]
        )

    total_sessions = len(sessions)
    total_iterations = sum(s.iterations for s in sessions)
    avg_iterations = total_iterations / total_sessions

    # Verdict breakdown
    pass_count = sum(1 for s in sessions if s.verdict == "PASS")
    fail_count = sum(1 for s in sessions if s.verdict == "FAIL")
    blocked_count = sum(1 for s in sessions if s.verdict == "BLOCKED")
    aborted_count = sum(1 for s in sessions if s.verdict == "ABORTED")

    success_rate = (pass_count / total_sessions) * 100
    fail_rate = (fail_count / total_sessions) * 100
    block_rate = (blocked_count / total_sessions) * 100
    abort_rate = (aborted_count / total_sessions) * 100

    # Agent breakdown
    agent_breakdown = {}
    for session in sessions:
        agent_name = session.agent_name
        agent_breakdown[agent_name] = agent_breakdown.get(agent_name, 0) + 1

    # Top KOs
    ko_counts = {}
    for session in sessions:
        if session.kos_consulted:
            for ko_id in session.kos_consulted:
                ko_counts[ko_id] = ko_counts.get(ko_id, 0) + 1

    top_kos = sorted(ko_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return AggregateMetrics(
        total_sessions=total_sessions,
        total_iterations=total_iterations,
        avg_iterations_per_session=avg_iterations,
        success_rate=success_rate,
        fail_rate=fail_rate,
        block_rate=block_rate,
        abort_rate=abort_rate,
        agent_breakdown=agent_breakdown,
        top_kos=top_kos
    )
```

**Phase 2: CLI Display** (2 hours)

**File**: `cli/commands/metrics.py` (NEW)

```python
"""
CLI command for displaying Wiggum metrics dashboard.

Usage:
    aibrain metrics --project karematch
    aibrain metrics --project karematch --agent bugfix
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestration.metrics import collect_session_metrics, aggregate_metrics


def metrics_command(args):
    """Display Wiggum metrics dashboard."""

    # Determine project directory
    project_name = args.project

    if project_name == "karematch":
        from adapters.karematch import KareMatchAdapter
        adapter = KareMatchAdapter()
    elif project_name == "credentialmate":
        from adapters.credentialmate import CredentialMateAdapter
        adapter = CredentialMateAdapter()
    else:
        print(f"❌ Unknown project: {project_name}")
        return 1

    app_context = adapter.get_context()
    state_dir = Path(app_context.project_path) / ".aibrain"

    if not state_dir.exists():
        print(f"No metrics found for {project_name}")
        return 0

    # Collect metrics
    sessions = collect_session_metrics(state_dir)

    # Filter by agent if specified
    if args.agent:
        sessions = [s for s in sessions if s.agent_name == args.agent]

    if not sessions:
        print(f"No sessions found for {project_name}" + (f" (agent: {args.agent})" if args.agent else ""))
        return 0

    # Aggregate
    metrics = aggregate_metrics(sessions)

    # Display dashboard
    print(f"\n{'='*80}")
    print(f"📊 Wiggum Metrics Dashboard - {project_name.upper()}")
    if args.agent:
        print(f"   (Filtered: {args.agent})")
    print(f"{'='*80}\n")

    print(f"📈 Overall Statistics")
    print(f"   Total Sessions: {metrics.total_sessions}")
    print(f"   Total Iterations: {metrics.total_iterations}")
    print(f"   Avg Iterations/Session: {metrics.avg_iterations_per_session:.1f}")
    print()

    print(f"✅ Verdict Breakdown")
    print(f"   Success (PASS): {metrics.success_rate:.1f}%")
    print(f"   Failure (FAIL): {metrics.fail_rate:.1f}%")
    print(f"   Blocked: {metrics.block_rate:.1f}%")
    print(f"   Aborted: {metrics.abort_rate:.1f}%")
    print()

    if not args.agent:
        print(f"🤖 Agent Breakdown")
        for agent_name, count in metrics.agent_breakdown.items():
            print(f"   {agent_name}: {count} sessions")
        print()

    if metrics.top_kos:
        print(f"📚 Top Knowledge Objects Consulted")
        for ko_id, count in metrics.top_kos[:5]:
            print(f"   {ko_id}: {count} times")
        print()

    print(f"{'='*80}\n")

    return 0


def setup_parser(subparsers):
    """Setup argparse for metrics command."""
    parser = subparsers.add_parser(
        "metrics",
        help="Display Wiggum metrics dashboard",
        description="View iteration statistics, success rates, and agent performance"
    )
    parser.add_argument('--project', required=True, choices=['karematch', 'credentialmate'],
                       help='Project name')
    parser.add_argument('--agent', help='Filter by agent (bugfix, codequality)')
    parser.set_defaults(func=metrics_command)
```

**Phase 3: Integration** (1 hour)

Update `cli/__main__.py`:
```python
from cli.commands import wiggum, ko, discover, metrics  # Add metrics

metrics.setup_parser(subparsers)
```

### Testing

```bash
# View overall metrics
aibrain metrics --project karematch

# Filter by agent
aibrain metrics --project karematch --agent bugfix

# After running autonomous loop
python autonomous_loop.py --project karematch --max-iterations 10
aibrain metrics --project karematch
```

### Success Criteria

- ✅ Dashboard displays all key metrics
- ✅ Agent filtering works
- ✅ KO consultation tracking works
- ✅ Handles missing/corrupted state files gracefully

---

## Enhancement 3: CodeQualityAgent Claude CLI Integration

**Priority**: P2 (Medium Value, Low Effort)
**Effort**: 1-2 hours
**Complexity**: Low

### What It Does

Extends Claude CLI integration to CodeQualityAgent (currently only BugFixAgent has it).

### Current State

- ✅ BugFixAgent has Claude CLI integration (lines 113-169 in `agents/bugfix.py`)
- ❌ CodeQualityAgent still uses placeholder execute()

### Implementation

**File**: `agents/codequality.py` (UPDATE)

Copy the Claude CLI integration from BugFixAgent.execute() and adapt for code quality improvements:

```python
def execute(self, task_id: str, context: Optional[Dict] = None) -> Dict:
    """
    Execute code quality improvement task using Claude CLI.

    Args:
        task_id: Task identifier
        context: Optional task context with target files

    Returns:
        Execution result dict
    """
    self.current_iteration += 1

    # Get task description (set by IterationLoop.run())
    task_description = getattr(self, 'task_description', task_id)

    # Execute via Claude CLI
    from claude.cli_wrapper import ClaudeCliWrapper
    from pathlib import Path

    project_dir = Path(self.app_context.project_path)
    wrapper = ClaudeCliWrapper(project_dir)

    print(f"🔧 Executing code quality task via Claude CLI...")
    print(f"   Prompt: {task_description}")

    # For code quality, add specific instructions
    quality_prompt = f"""
{task_description}

Focus on code quality improvements:
- Remove unused imports and variables
- Fix linting issues
- Improve type annotations
- Refactor for clarity
- Follow project style guide

Do NOT change functionality or add new features.
Run lint and type checks after changes.
Output <promise>CODEQUALITY_COMPLETE</promise> when done.
"""

    result = wrapper.execute_task(
        prompt=quality_prompt,
        files=context.get('files') if context else None,
        timeout=300  # 5 minutes
    )

    if not result.success:
        return {
            "task_id": task_id,
            "status": "failed",
            "reason": f"Claude CLI execution failed: {result.error}",
            "iterations": self.current_iteration,
            "output": result.error or "Execution failed"
        }

    # Use Claude's output for completion signal checking
    output = result.output

    # Check for completion signal if configured
    if self.config.expected_completion_signal:
        promise = self.check_completion_signal(output)
        if promise == self.config.expected_completion_signal:
            return {
                "task_id": task_id,
                "status": "completed",
                "signal": "promise",
                "promise_text": promise,
                "output": output,
                "iterations": self.current_iteration,
                "files_changed": result.files_changed
            }

    # No completion signal yet, will iterate again
    return {
        "task_id": task_id,
        "status": "in_progress",
        "output": output,
        "iterations": self.current_iteration,
        "files_changed": result.files_changed
    }
```

### Testing

```bash
# Test CodeQualityAgent with Wiggum
aibrain wiggum "Improve code quality in src/auth.ts" \
  --agent codequality \
  --project karematch \
  --max-iterations 20 \
  --promise "CODEQUALITY_COMPLETE"
```

### Success Criteria

- ✅ CodeQualityAgent calls Claude CLI
- ✅ Completion signal detection works
- ✅ Quality-specific instructions included
- ✅ Tests passing

---

## Enhancement 4: Completion Signal Templates

**Priority**: P3 (Nice-to-Have, Low Effort)
**Effort**: 1-2 hours
**Complexity**: Low

### What It Does

Provides a library of common completion signal templates and prompts for different task types.

### Current State

- ✅ Completion signals working (manual specification)
- ❌ No template library

### Implementation

**File**: `orchestration/signal_templates.py` (NEW)

```python
"""
Completion Signal Templates for Wiggum Agents.

Provides standard promise strings and prompts for different task types.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class SignalTemplate:
    """Template for completion signals."""
    promise: str          # The promise string to match
    prompt_suffix: str    # Instructions to add to prompt
    description: str      # What this signal means


# Standard templates by task type
TEMPLATES = {
    "bugfix": SignalTemplate(
        promise="BUGFIX_COMPLETE",
        prompt_suffix="""
When the bug is fixed and all tests pass, output:
<promise>BUGFIX_COMPLETE</promise>
""",
        description="Bug is fixed, tests passing, no regressions"
    ),

    "codequality": SignalTemplate(
        promise="CODEQUALITY_COMPLETE",
        prompt_suffix="""
When code quality improvements are complete and linting/type checks pass, output:
<promise>CODEQUALITY_COMPLETE</promise>
""",
        description="Code quality improved, lint/type checks passing"
    ),

    "feature": SignalTemplate(
        promise="FEATURE_COMPLETE",
        prompt_suffix="""
When the feature is fully implemented with tests and documentation, output:
<promise>FEATURE_COMPLETE</promise>
""",
        description="Feature implemented, tested, documented"
    ),

    "test": SignalTemplate(
        promise="TESTS_COMPLETE",
        prompt_suffix="""
When all tests are written and passing, output:
<promise>TESTS_COMPLETE</promise>
""",
        description="Tests written and passing"
    ),

    "refactor": SignalTemplate(
        promise="REFACTOR_COMPLETE",
        prompt_suffix="""
When refactoring is complete and all tests still pass, output:
<promise>REFACTOR_COMPLETE</promise>
""",
        description="Refactoring complete, tests still passing"
    ),
}


def get_template(task_type: str) -> Optional[SignalTemplate]:
    """
    Get completion signal template for task type.

    Args:
        task_type: Task type (bugfix, codequality, feature, test, refactor)

    Returns:
        SignalTemplate or None if not found
    """
    return TEMPLATES.get(task_type.lower())


def build_prompt_with_signal(base_prompt: str, task_type: str) -> str:
    """
    Add completion signal instructions to prompt.

    Args:
        base_prompt: Base task prompt
        task_type: Task type for template lookup

    Returns:
        Enhanced prompt with signal instructions
    """
    template = get_template(task_type)
    if template is None:
        return base_prompt

    return f"{base_prompt}\n\n{template.prompt_suffix}"


def infer_task_type(task_description: str) -> str:
    """
    Infer task type from description.

    Args:
        task_description: Task description string

    Returns:
        Inferred task type (defaults to "bugfix")
    """
    desc_lower = task_description.lower()

    if any(word in desc_lower for word in ["bug", "fix", "error", "issue", "failing"]):
        return "bugfix"
    elif any(word in desc_lower for word in ["quality", "lint", "refactor", "clean"]):
        return "codequality"
    elif any(word in desc_lower for word in ["test", "spec", "coverage"]):
        return "test"
    elif any(word in desc_lower for word in ["feature", "add", "implement", "build"]):
        return "feature"
    elif any(word in desc_lower for word in ["refactor", "restructure"]):
        return "refactor"
    else:
        return "bugfix"  # Default
```

**File**: `orchestration/iteration_loop.py` (UPDATE)

```python
from orchestration.signal_templates import build_prompt_with_signal, infer_task_type, get_template

def run(self, task_id: str, task_description: str, max_iterations: Optional[int] = None, resume: bool = False) -> LoopResult:
    """..."""

    # Infer task type and get template
    task_type = infer_task_type(task_description)
    template = get_template(task_type)

    # If agent doesn't have a completion signal configured, use template
    if not self.agent.config.expected_completion_signal and template:
        self.agent.config.expected_completion_signal = template.promise
        print(f"📋 Using standard completion signal: <promise>{template.promise}</promise>")

    # Enhance task description with signal instructions
    if template:
        enhanced_description = build_prompt_with_signal(task_description, task_type)
    else:
        enhanced_description = task_description

    # Store enhanced description in agent
    self.agent.task_description = enhanced_description

    # ... rest of method ...
```

### Testing

```bash
# Without --promise flag, should auto-detect and use template
aibrain wiggum "Fix authentication bug in login.ts" \
  --agent bugfix \
  --project karematch

# Should output: "Using standard completion signal: <promise>BUGFIX_COMPLETE</promise>"
```

### Success Criteria

- ✅ Templates defined for 5 task types
- ✅ Auto-detection of task type working
- ✅ Auto-application of signals working
- ✅ Manual override still possible

---

## Implementation Order (Recommended)

1. **Enhancement 1** (2-3 hours) - KO CLI - High value, low effort
2. **Enhancement 3** (1-2 hours) - CodeQuality integration - Completes agent coverage
3. **Enhancement 4** (1-2 hours) - Signal templates - Improves UX
4. **Enhancement 2** (4-6 hours) - Metrics dashboard - Nice-to-have analytics

**Total Effort**: 8-13 hours (1-2 days)

---

## Decision Points

### When to Implement

- **Immediately**: If KO management is becoming tedious (Enhancement 1)
- **Before scaling**: If planning to run 50+ sessions (Enhancement 2)
- **For parity**: If CodeQualityAgent sees regular use (Enhancement 3)
- **For UX**: If users struggle with completion signals (Enhancement 4)

### What to Skip

- Enhancement 2 (Metrics) if session count < 20
- Enhancement 4 (Templates) if users prefer explicit control

---

## Testing Strategy

For each enhancement:

1. **Unit Tests**: Test individual functions in isolation
2. **Integration Tests**: Test CLI commands end-to-end
3. **Manual Testing**: Run actual Wiggum sessions
4. **Documentation**: Update CLAUDE.md with new features

---

## Success Metrics

| Enhancement | Success Metric |
|-------------|---------------|
| 1. KO CLI | < 5 seconds to approve/reject a KO |
| 2. Metrics | Dashboard displays in < 1 second for 100 sessions |
| 3. CodeQuality | Agent successfully completes quality tasks |
| 4. Templates | 80% of tasks use auto-detected signals |

---

## Documentation Updates Required

After implementation:

- [ ] Update CLAUDE.md with new CLI commands
- [ ] Update STATE.md with enhancement status
- [ ] Add DECISIONS.md entry for enhancement rationale
- [ ] Create session handoff documenting what was added
- [ ] Update README if one exists

---

## Risk Assessment

**Low Risk** - All enhancements are additive:
- No changes to core Wiggum logic
- No breaking changes to existing APIs
- Graceful degradation if features not used
- Can be implemented incrementally

---

## Future Considerations

Beyond these 4 enhancements:

- **Web Dashboard**: Replace CLI metrics with web UI
- **KO Search Engine**: Full-text search, not just tags
- **Agent Plugins**: User-defined custom agents
- **Slack Integration**: Notifications for BLOCKED verdicts
- **GitHub Actions**: CI/CD integration with Wiggum

---

**Status**: Ready for implementation
**Next Step**: Choose enhancement to implement first based on immediate needs
