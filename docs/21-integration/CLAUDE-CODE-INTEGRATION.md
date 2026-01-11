# Claude Code Integration Options

This document explains how the AI Orchestrator can integrate with different Claude Code tools.

## Overview

Claude Code offers multiple integration points:
1. **Claude Code CLI** - Command-line tool for automation
2. **Claude Code Extension** - VS Code/IDE integration for human workflows
3. **MCP (Model Context Protocol)** - Structured tool/resource access

---

## Option 1: Claude Code CLI (Current Plan)

**What it is**: Terminal-based tool authenticated via claude.ai

**Pros**:
- ✅ Fully scriptable - can call from Python subprocess
- ✅ Perfect for autonomous loops
- ✅ Works without IDE running
- ✅ Easy to integrate with existing code

**Cons**:
- ⚠️ Requires separate authentication setup
- ⚠️ No visual feedback during execution

**Integration Pattern**:
```python
import subprocess

# Execute task via CLI
result = subprocess.run(
    ["claude", "--prompt", task.description, "--file", task.file],
    capture_output=True,
    text=True,
    timeout=300
)

# Parse output
if result.returncode == 0:
    # Task succeeded
    output = result.stdout
else:
    # Task failed
    error = result.stderr
```

**Usage in autonomous_loop.py**:
```python
# 4. Run Claude Code CLI
result = await run_claude_code_cli(
    prompt=task.description,
    files=[task.file],
    project_dir=project_dir
)
```

---

## Option 2: Claude Code Extension (Alternative)

**What it is**: VS Code extension for interactive Claude sessions

**Pros**:
- ✅ Rich IDE integration
- ✅ Visual feedback and debugging
- ✅ Good for complex, multi-step tasks
- ✅ Access to IDE features (linting, debugging)

**Cons**:
- ❌ Not easily scriptable
- ❌ Requires IDE to be running
- ❌ Less suitable for autonomous loops
- ❌ Harder to integrate with Python code

**Integration Pattern**:
```python
# Option A: Launch VS Code with Claude extension
subprocess.run(["code", "--command", "claude.executeTask", task.file])

# Option B: Use VS Code extension API (complex)
import vscode_cli
vscode_cli.execute_command("claude.chat", {"prompt": task.description})
```

**Best Use Case**:
- Human-in-the-loop workflows
- Complex debugging sessions
- Manual review/approval steps

---

## Option 3: Hybrid Approach (Recommended)

Use **both** tools for different scenarios:

### Autonomous Work (CLI)
```python
# For autonomous bug fixes and quality improvements
if task.type in ["bug_fix", "quality"]:
    result = run_claude_code_cli(task)
```

### Human Review (Extension)
```python
# For complex features requiring human approval
if task.type == "feature" or task.requires_approval:
    # Launch IDE for human review
    open_in_vscode_with_claude(task)
    # Wait for human approval...
```

### Architecture
```
┌─────────────────────────────────────────────────────┐
│              Autonomous Loop                        │
│                                                     │
│  ┌─────────────────┐        ┌──────────────────┐   │
│  │  Simple Tasks   │───────▶│  Claude Code CLI │   │
│  │  (Bugs, QA)     │        │  (Automated)     │   │
│  └─────────────────┘        └──────────────────┘   │
│                                                     │
│  ┌─────────────────┐        ┌──────────────────┐   │
│  │  Complex Tasks  │───────▶│  Claude Code Ext │   │
│  │  (Features)     │        │  (Human Review)  │   │
│  └─────────────────┘        └──────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## Option 4: MCP Integration (Future)

**What it is**: Model Context Protocol for structured agent interactions

**Pros**:
- ✅ Standardized tool/resource access
- ✅ Can integrate with both CLI and Extension
- ✅ Rich context passing
- ✅ Better for complex multi-tool workflows

**Status**: Not yet implemented in autonomous_loop.py

**Future Integration**:
```python
# Use MCP server for structured tasks
from mcp import MCPClient

client = MCPClient()
result = await client.execute_task(
    task_id=task.id,
    context={
        "files": [task.file],
        "tests": task.tests,
        "description": task.description
    }
)
```

---

## Current Implementation Status

### ✅ What's Planned (Phase 1)
- Claude Code CLI integration via subprocess
- Capture stdout/stderr for verification
- Parse output to determine success/failure

### ⏳ What's Not Yet Implemented
- Actual CLI subprocess calls (placeholders exist)
- Output parsing logic
- Error recovery from CLI failures
- Extension integration

### 🔮 Future Considerations
- MCP protocol integration
- Hybrid CLI + Extension workflows
- IDE-aware debugging for complex tasks

---

## Recommended Path Forward

### Phase 1: CLI-Only (Simplest)
1. Implement subprocess calls to `claude` CLI
2. Parse output for success/failure
3. Use for autonomous bug fixes and QA

**Timeline**: 1-2 weeks

### Phase 2: Hybrid (Best of Both)
1. Keep CLI for autonomous work
2. Add Extension integration for complex tasks
3. Human approval prompts open VS Code

**Timeline**: 3-4 weeks

### Phase 3: MCP (Future-Proof)
1. Migrate to MCP protocol
2. Support both CLI and Extension via MCP
3. Enable advanced multi-tool workflows

**Timeline**: TBD (depends on MCP maturity)

---

## Configuration

### ~/.claude_config.yaml (Proposed)
```yaml
# Claude Code integration preferences
integration:
  default: cli  # cli | extension | hybrid

  cli:
    timeout: 300  # 5 minutes
    max_retries: 3

  extension:
    editor: vscode  # vscode | cursor | zed
    auto_open: true

  hybrid:
    autonomous_tasks: [bug_fix, quality]
    manual_tasks: [feature, refactor]
```

---

## Questions to Answer

1. **Do we have Claude Code CLI installed and configured?**
   - Run: `claude --version`
   - If not: Install from https://claude.com/code

2. **Is the CLI authenticated?**
   - Run: `claude auth status`
   - If not: `claude auth login`

3. **Do we want Extension integration too?**
   - Pros: Better UX for complex tasks
   - Cons: More complexity to maintain

4. **Should we use MCP from the start?**
   - Pros: Future-proof, standardized
   - Cons: More setup, less mature

---

## Recommendation

**Start with CLI-only** (Option 1):
- Fastest to implement
- Works for 80% of autonomous use cases
- Can add Extension/MCP later if needed

**Add Extension** (Option 3) if:
- Complex features need human review
- Debugging requires IDE context
- Team prefers visual workflows

**Consider MCP** (Option 4) when:
- Multi-tool orchestration is needed
- Standard protocol support matters
- Long-term maintainability is priority
