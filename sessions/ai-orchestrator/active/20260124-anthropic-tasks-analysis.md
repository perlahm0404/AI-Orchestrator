# Anthropic Tasks & Agent SDK Analysis

**Date**: 2026-01-24
**Topic**: Should AI Orchestrator adopt Anthropic's Tasks/Agent SDK?
**Status**: Analysis Complete

---

## Executive Summary

**Verdict**: Partial adoption recommended. The Claude Agent SDK provides token-optimized primitives that could replace low-level components, but AI Orchestrator's governance, multi-repo orchestration, and domain-specific features are more sophisticated and should be preserved.

| Anthropic Offering | Overlap with AI Orchestrator | Recommendation |
|-------------------|------------------------------|----------------|
| Claude Tasks Mode | Low (UI-only, web/desktop) | **Skip** - Not relevant for CLI/headless |
| Claude Cowork | Low (file automation) | **Skip** - Different use case |
| Claude Agent SDK | High (core loop + tools) | **Adopt primitives** - Replace `autonomous_loop.py` internals |

---

## What Anthropic Released (2025-2026)

### 1. Claude Tasks Mode (UI Feature)

A dual-panel agentic interface in Claude web/desktop:
- **Left panel**: Conversation + task execution
- **Right panel**: Context files + artifacts
- **Planning**: Claude creates action plans before execution
- **Progress tracking**: Step-by-step visibility
- **MCP integration**: Connects to databases, files, APIs

**Token Impact**: Unknown (UI abstraction)

**Sources**: [SuperGok](https://supergok.com/claude-tasks-mode-agent-workflow/), [TestingCatalog](https://www.testingcatalog.com/exclusive-early-look-at-claude-tasks-mode-agent-from-anthropic/)

### 2. Claude Cowork (Desktop Agent - Jan 2026)

File automation agent for macOS (Claude Max subscribers):
- **Folder-sandboxed**: Read/write only in designated directories
- **Subagent spawning**: Parallel execution for independent subtasks
- **VM isolation**: Runs in Apple Virtualization Framework
- **Skill layers**: Local files + Claude connectors (Notion, Asana) + browser actions

**Token Impact**: High - "50-100 standard messages" per complex session

**Sources**: [InfoQ](https://www.infoq.com/news/2026/01/claude-cowork/), [VentureBeat](https://venturebeat.com/technology/anthropic-launches-cowork-a-claude-desktop-agent-that-works-in-your-files-no)

### 3. Claude Agent SDK (Python/TypeScript - Jan 2026)

Programmable agent framework with built-in tools:

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt="Find and fix the bug in auth.py",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"])
):
    print(message)  # Claude handles the tool loop
```

**Key Features**:
| Feature | Description |
|---------|-------------|
| Built-in tools | Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch |
| Hooks | PreToolUse, PostToolUse, Stop, SessionStart, SessionEnd |
| Subagents | Spawn specialized agents via Task tool |
| Sessions | Context persistence across multiple queries |
| Permissions | allowedTools, permissionMode, blocked patterns |
| MCP | Connect databases, browsers, APIs via Model Context Protocol |
| Compaction | Automatic context summarization when limits approach |

**Token Optimization**:
- Built-in compaction (automatic summarization)
- Progressive skill loading ("loads skill instructions only when relevant")
- Session reuse (avoid re-sending context)

**Sources**: [Anthropic Docs](https://platform.claude.com/docs/en/api/agent-sdk/overview), [GitHub](https://github.com/anthropics/claude-agent-sdk-python)

---

## Comparison: Agent SDK vs AI Orchestrator

### Feature-by-Feature Analysis

| Capability | Agent SDK | AI Orchestrator | Winner |
|------------|-----------|-----------------|--------|
| **Tool execution** | Built-in, zero code | Custom wrappers | Agent SDK (simpler) |
| **Retry control** | None built-in | Wiggum (15-50 iterations) | **AI Orchestrator** |
| **Verification** | Hooks (PostToolUse) | Ralph (PASS/FAIL/BLOCKED) | **AI Orchestrator** |
| **Multi-repo** | Single directory | Cross-repo memory, Mission Control | **AI Orchestrator** |
| **Governance** | Permission modes | YAML contracts, team isolation | **AI Orchestrator** |
| **Task queues** | None | work_queue_*.json, auto-discovery | **AI Orchestrator** |
| **Knowledge persistence** | CLAUDE.md, sessions | Knowledge Objects (457x cache) | **AI Orchestrator** |
| **Content pipelines** | None | 7-stage editorial workflow | **AI Orchestrator** |
| **Subagents** | Task tool | Team architecture (QA/Dev/Operator) | Comparable |
| **Token compaction** | Built-in | None (manual) | Agent SDK |
| **Prompt caching** | Automatic | None | Agent SDK |

### Token Optimization Comparison

**Agent SDK Advantages**:
1. **Automatic compaction**: Summarizes conversation when context limits approach
2. **Prompt caching**: Reuses cached prompts across calls
3. **Progressive loading**: Skills/tools loaded on-demand
4. **Session persistence**: Avoid re-sending system prompts

**AI Orchestrator Current State**:
- No automatic compaction (relies on human session handoffs)
- No prompt caching (each call sends full context)
- Full tool definitions always loaded
- Session state via external files (STATE.md, sessions/*.md)

**Estimated Token Savings**: 20-40% per session if Agent SDK primitives adopted

---

## Recommendation: Hybrid Adoption

### Phase 1: Replace Core Loop (Low Risk)

Replace `autonomous_loop.py` internals with Agent SDK's `query()` function:

```python
# Before (AI Orchestrator)
async def run_task(task):
    agent = create_agent(task)
    for iteration in range(max_iterations):
        result = await agent.execute()
        verdict = ralph.verify(result)
        if verdict == "PASS":
            break
        # Manual retry logic

# After (Hybrid)
from claude_agent_sdk import query, ClaudeAgentOptions

async def run_task(task):
    options = ClaudeAgentOptions(
        allowed_tools=task.tools,
        hooks={
            "PostToolUse": [ralph_verification_hook],
            "Stop": [wiggum_iteration_hook]
        }
    )
    async for message in query(prompt=task.prompt, options=options):
        yield message
```

**Benefits**:
- Free token compaction
- Free prompt caching
- Simpler tool execution
- Maintained compatibility with Ralph/Wiggum via hooks

### Phase 2: Keep Custom Orchestration (Critical)

Do NOT replace these AI Orchestrator systems:

| System | Why Keep |
|--------|----------|
| **Mission Control** | Multi-repo orchestration not in Agent SDK |
| **Ralph** | Domain-specific verification (PASS/FAIL/BLOCKED) |
| **Wiggum** | Iteration budgets (15-50) with completion signals |
| **Governance contracts** | Team isolation (QA/Dev/Operator) not in SDK |
| **Knowledge Objects** | Institutional memory with 457x cached queries |
| **Editorial pipelines** | 7-stage content workflow with approval gates |
| **Task queues** | Auto-discovery, prioritization, bug grouping |

### Phase 3: Adopt Agent SDK Subagents (Medium Term)

Replace custom subagent spawning with SDK's Task tool:

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Glob", "Grep", "Task"],
    agents={
        "qa-bugfix": AgentDefinition(
            description="Bug fix specialist",
            prompt="Fix bugs, run tests, verify with Ralph",
            tools=["Read", "Edit", "Bash", "Grep"]
        ),
        "dev-feature": AgentDefinition(
            description="Feature developer",
            prompt="Build features on feature/* branches",
            tools=["Read", "Write", "Edit", "Bash"]
        )
    }
)
```

**Benefits**:
- Isolated context windows per subagent
- Built-in message passing (parent_tool_use_id)
- Automatic result aggregation

---

## Token Cost Analysis

### Current AI Orchestrator (Estimated)

| Component | Tokens/Task | Notes |
|-----------|-------------|-------|
| System prompt | ~5,000 | Governance + memory + tools |
| Context window | ~50,000 | Files + conversation |
| Tool definitions | ~3,000 | Always loaded |
| **Total (no caching)** | ~58,000 | |

### With Agent SDK Optimization

| Component | Tokens/Task | Savings |
|-----------|-------------|---------|
| System prompt | ~5,000 (cached) | 0 after first call |
| Context window | ~30,000 (compacted) | 40% reduction |
| Tool definitions | ~1,500 (progressive) | 50% reduction |
| **Total** | ~36,500 | **37% savings** |

**Annual Impact** (at 100 tasks/day):
- Current: ~2.1B tokens/year
- With SDK: ~1.3B tokens/year
- **Savings**: ~800M tokens/year (~$2,400/year at $3/1M tokens)

---

## Migration Path

### Week 1: Proof of Concept
1. Install Agent SDK: `pip install claude-agent-sdk`
2. Create wrapper: `agents/core/sdk_adapter.py`
3. Run single task through SDK query loop
4. Compare token usage (before/after)

### Week 2: Hook Integration
1. Port Ralph verification to PostToolUse hook
2. Port Wiggum iteration control to Stop hook
3. Test with 10 tasks from work queue

### Week 3: Production Rollout
1. Replace `autonomous_loop.py` internals
2. Keep Mission Control, governance, pipelines unchanged
3. Monitor token savings via Resource Tracker

### Week 4: Subagent Migration (Optional)
1. Convert QA/Dev teams to SDK AgentDefinitions
2. Test team isolation via SDK permissions
3. Validate governance contracts still enforced

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SDK bugs | Medium | High | Pin version, fallback to current loop |
| Lost governance | Low | Critical | Hooks enforce contracts, not SDK permissions |
| Token regression | Low | Medium | A/B test with Resource Tracker |
| Session state mismatch | Medium | Medium | Continue using external state files |

---

## Conclusion

**Adopt**: Agent SDK core loop (query, hooks, compaction)
**Keep**: AI Orchestrator governance, Ralph, Wiggum, Mission Control, pipelines
**Skip**: Claude Tasks Mode (UI-only), Claude Cowork (different use case)

The Agent SDK provides token-optimized primitives that complement AI Orchestrator's sophisticated orchestration layer. A hybrid approach yields ~37% token savings while preserving the governance, verification, and multi-repo capabilities that make AI Orchestrator unique.

---

## Sources

- [Claude Agent SDK Docs](https://platform.claude.com/docs/en/api/agent-sdk/overview)
- [Claude Agent SDK Python GitHub](https://github.com/anthropics/claude-agent-sdk-python)
- [Claude Cowork Announcement - InfoQ](https://www.infoq.com/news/2026/01/claude-cowork/)
- [Claude Tasks Mode - SuperGok](https://supergok.com/claude-tasks-mode-agent-workflow/)
- [Building Agents with Claude Agent SDK - Anthropic](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Claude Cowork - VentureBeat](https://venturebeat.com/technology/anthropic-launches-cowork-a-claude-desktop-agent-that-works-in-your-files-no)
