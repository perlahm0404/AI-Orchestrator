# Phase 1: Session State Implementation Guide

**Timeline**: Week 1
**Effort**: 40 hours
**Deliverable**: Session save/load/resume capability

---

## Overview

Phase 1 implements the foundational session state system. Once complete, agents will be able to:
1. Save work-in-progress state after each iteration
2. Resume from saved state across context resets
3. Track progress visibly in markdown files

This enables basic stateless operation (context resets won't lose work).

---

## Architecture

```
┌──────────────────────────────┐
│  IterationLoop               │
│  • run_iteration()           │
│  • checkpoint()              │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│  SessionState                │ ← NEW: Phase 1
│  • save()                    │
│  • load()                    │
│  • update()                  │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│  .aibrain/session-{id}.md    │ ← NEW: External store
│  (YAML frontmatter + content)│
└──────────────────────────────┘
```

---

## File Structure

### 1. New File: `orchestration/session_state.py`

**Purpose**: Core session management logic

**Size**: ~300 lines

**Key Classes**:

```python
class SessionState:
    """Manages session save/load/update"""

    def __init__(self, task_id: str, project: str):
        # Initialize session manager

    def save(self, data: dict) -> None:
        """Save session to disk"""

    @classmethod
    def load(cls, task_id: str) -> dict:
        """Load session from disk"""

    def update(self, **kwargs) -> None:
        """Update existing session"""

    def archive(self) -> None:
        """Archive completed session"""
```

**Core Methods**:

```python
def save(self, data: dict) -> None:
    """
    Save session to markdown file with YAML frontmatter

    Args:
        data: Dict with keys:
            - iteration_count: int
            - phase: str
            - status: str ("in_progress", "blocked", "completed")
            - last_output: str
            - next_steps: List[str]
            - error: str (optional)
            - markdown_content: str (human-readable progress)

    Example:
        session.save({
            'iteration_count': 5,
            'phase': 'feature_build',
            'status': 'in_progress',
            'last_output': 'Implemented user auth module',
            'next_steps': ['Add tests', 'Update docs'],
            'markdown_content': '## Progress\n✅ Done'
        })
    """
    # Validate data
    required = ['iteration_count', 'phase', 'status']
    assert all(k in data for k in required)

    # Create frontmatter (JSON in YAML block)
    frontmatter = {
        'id': self._generate_session_id(),
        'task_id': self.task_id,
        'project': self.project,
        'created_at': self._get_created_at(),
        'updated_at': datetime.now().isoformat(),
        'checkpoint_number': data.get('checkpoint_number', 0),
        **{k: v for k, v in data.items() if k != 'markdown_content'}
    }

    # Format: YAML frontmatter + markdown content
    yaml_block = json.dumps(frontmatter, indent=2)
    markdown = data.get('markdown_content', '')

    content = f"""---
{yaml_block}
---

{markdown}
"""

    # Write to disk
    self.file_path.write_text(content)

@classmethod
def load(cls, task_id: str) -> dict:
    """
    Load session from disk

    Args:
        task_id: Task identifier

    Returns:
        Dict with all session data + markdown_content

    Raises:
        FileNotFoundError: If session file doesn't exist
        yaml.YAMLError: If frontmatter is malformed
    """
    file_path = Path('.aibrain') / f'session-{task_id}.md'

    if not file_path.exists():
        raise FileNotFoundError(f"Session file not found: {file_path}")

    content = file_path.read_text()

    # Parse: --- frontmatter --- markdown
    parts = content.split('---', 2)
    if len(parts) < 2:
        raise ValueError("Invalid session file format (missing frontmatter)")

    frontmatter = json.loads(parts[1].strip())
    markdown = parts[2].strip() if len(parts) > 2 else ""

    return {
        **frontmatter,
        'markdown_content': markdown
    }

def update(self, **kwargs) -> None:
    """Update existing session with new data"""
    session = self.load(self.task_id)
    session.update(kwargs)
    self.save(session)

def archive(self) -> None:
    """Move completed session to archive"""
    if self.file_path.exists():
        archive_dir = Path('.aibrain/sessions/archive')
        archive_dir.mkdir(parents=True, exist_ok=True)
        self.file_path.rename(archive_dir / self.file_path.name)
```

---

### 2. Markdown Session File Format

**Location**: `.aibrain/session-{task_id}-{checkpoint_num}.md`

**Example**:
```markdown
---
{
  "id": "SESSION-2026-02-07-001",
  "task_id": "TASK-123",
  "project": "credentialmate",
  "created_at": "2026-02-07T10:00:00Z",
  "updated_at": "2026-02-07T10:35:42Z",
  "iteration_count": 5,
  "checkpoint_number": 2,
  "phase": "feature_build",
  "status": "in_progress",
  "agent_type": "feature-builder",
  "max_iterations": 50,
  "last_output": "Implemented user authentication module with JWT tokens",
  "next_steps": [
    "Add unit tests for auth module",
    "Implement session refresh logic",
    "Update API documentation"
  ],
  "context_window": 2,
  "tokens_used": 3847
}
---

## Task Summary

**ID**: TASK-123
**Project**: credentialmate
**Type**: Feature
**Status**: 🔄 In Progress

### Objective
Implement JWT-based user authentication for web portal

### Constraints
- Must support OAuth2 login
- Session timeout: 24 hours
- HIPAA compliance required
- No external auth services (except OAuth provider)

---

## Progress

### Completed ✅
1. **Phase 1 - Design** (iterations 1-2)
   - Designed JWT token structure
   - Planned OAuth2 integration
   - Reviewed security requirements

2. **Phase 2 - Core Auth** (iterations 3-4)
   - Implemented token generation
   - Added token validation middleware
   - Integrated with database

### In Progress 🔄
3. **Phase 3 - Testing** (iteration 5)
   - Writing unit tests for token generation
   - Testing OAuth2 flow
   - Security audit in progress

### Not Started ⏳
4. Phase 4 - Documentation
5. Phase 5 - Integration with existing modules

---

## Iteration Log

### Iteration 1-2 (Completed)
**Task**: Design auth architecture
**Approach**: JWT tokens + OAuth2
**Result**: PASS (design approved by lead)

### Iteration 3-4 (Completed)
**Task**: Implement core auth module
**Time**: 2 contexts
**Ralph Verdict**: PASS
**Tests**: 15/15 passing

### Iteration 5 (Current)
**Task**: Write unit tests
**Started**: 2026-02-07 10:30:00Z
**Agent Output**:
```
Created test_auth.py with coverage:
- test_token_generation: PASS
- test_token_validation: PASS
- test_token_expiry: FAIL (need refresh logic)
- test_oauth_callback: PASS
```
**Verdict**: RETRY_NEEDED (1 test failing)

---

## Code Artifacts

### auth/tokens.py
[Summary of changes: 127 lines added, JWT implementation]

### auth/middleware.py
[Summary of changes: 85 lines added, token validation]

### tests/test_auth.py
[Summary of changes: 234 lines added, 15 tests]

---

## Decision Log

| Iteration | Decision | Value | Reasoning |
|-----------|----------|-------|-----------|
| 1 | APPROACH | JWT + OAuth2 | Balance of security & simplicity |
| 3 | REFACTOR_TRIGGER | No major refactoring | Design solid, incremental improvement OK |
| 5 | NEXT_FOCUS | Fix token refresh | Failing test blocks progress |

---

## Current Blockers

None - on track for completion

---

## Next Steps (Resume from iteration 6)

1. ✅ **Fix token refresh logic** in `auth/tokens.py:refresh_token()`
2. ✅ **Re-run test_token_expiry** - expect PASS
3. ⏳ **Full test suite** - expect 16/16 PASS
4. ⏳ **Integration tests** - test with web portal
5. ⏳ **Security review** - HIPAA compliance check

---

## Context Window History

| Window | Iterations | Token Usage | Status |
|--------|-----------|-------------|--------|
| 1 | 1-2 | 3,200 | Completed |
| 2 | 3-4 | 3,800 | Completed |
| 3 | 5-N | 2,100+ | In Progress |

---

## Meta Information

- **Checkpointed At**: 2026-02-07T10:35:42Z
- **Checkpoint Reason**: After iteration 5, test failure detected
- **Can Resume**: Yes (RETRY_NEEDED status)
- **Estimated Remaining**: 2-3 iterations
- **Knowledge Objects Referenced**: [KO-cm-001, KO-cm-005]

```
```

**Key Features**:
- YAML frontmatter for structured data
- Human-readable markdown body
- Clear progress tracking
- Next steps for resumption
- Iteration log for reference
- Decision history for audit

---

### 3. Integration with IterationLoop

**File to modify**: `orchestration/iteration_loop.py`

**Changes** (~50 lines):

```python
from orchestration.session_state import SessionState

class IterationLoop:
    def __init__(self, ...):
        self.session = None
        ...

    def run(
        self,
        task_id: str,
        task_description: str,
        starting_iteration: int = 0
    ):
        """Run iteration loop with session management"""

        # Initialize session
        self.session = SessionState(task_id, self.project)

        # Load existing session if resuming
        if starting_iteration > 0:
            session_data = self.session.load(task_id)
            self.current_iteration = session_data['iteration_count']
        else:
            self.current_iteration = 0

        # Main loop
        while self.current_iteration < self.max_iterations:
            self.current_iteration += 1

            # Run iteration
            result = self.agent.execute(task_description)

            # Checkpoint after EVERY iteration
            self._checkpoint(result)

            # Check completion
            if result.verdict == "PASS":
                self.session.archive()  # Move to archive
                return result
            elif result.verdict == "BLOCKED":
                # Don't advance, wait for human decision
                return result

        return result

    def _checkpoint(self, result):
        """Save session state after iteration"""

        self.session.save({
            'iteration_count': self.current_iteration,
            'checkpoint_number': self.current_iteration,
            'phase': self._current_phase(),
            'status': 'in_progress' if result.verdict != 'PASS' else 'completed',
            'last_output': self._summarize_output(result),
            'next_steps': self._extract_next_steps(result),
            'markdown_content': self._format_markdown(result),
            'error': result.error if result.verdict == 'BLOCKED' else None
        })
```

---

### 4. Integration with AutonomousLoop

**File to modify**: `autonomous_loop.py`

**Changes** (~30 lines):

```python
from orchestration.session_state import SessionState

class AutonomousLoop:
    def run_iteration(self):
        """Process one task from queue"""

        # Get next ready task
        task = self.work_queue.get_next_ready()
        if not task:
            return False

        # Check if resuming
        if task.session_ref:
            # This is a continuing task
            print(f"Resuming {task.id} (iteration {task.iteration_count})")
            starting_iter = task.iteration_count
        else:
            starting_iter = 0

        # Run iteration loop
        try:
            result = self.iteration_loop.run(
                task_id=task.id,
                task_description=task.description,
                starting_iteration=starting_iter
            )

            # Update task status based on result
            if result.verdict == "PASS":
                self.work_queue.mark_complete(task.id)
            elif result.verdict == "BLOCKED":
                self.work_queue.mark_blocked(task.id)
            else:
                # RETRY - will resume next iteration
                pass

            return True

        except Exception as e:
            # Save error state for debugging
            session = SessionState(task.id, self.project)
            session.update(error=str(e))
            print(f"Error in {task.id}: {e}")
            return False
```

---

### 5. Tests: `tests/test_session_state.py`

**Size**: ~200 lines

**Test Cases**:

```python
import pytest
from orchestration.session_state import SessionState
from pathlib import Path
import json

class TestSessionStateBasics:
    """Basic save/load functionality"""

    def test_save_creates_file(self, tmp_path):
        """Session.save() creates markdown file"""
        session = SessionState("TASK-1", "credentialmate")

        session.save({
            'iteration_count': 1,
            'phase': 'feature_build',
            'status': 'in_progress',
            'markdown_content': '## Test\nContent here'
        })

        assert Path('.aibrain/session-TASK-1.md').exists()

    def test_save_includes_frontmatter(self):
        """Saved file includes YAML frontmatter"""
        session = SessionState("TASK-2", "credentialmate")
        session.save({'iteration_count': 5, 'phase': 'testing', ...})

        content = Path('.aibrain/session-TASK-2.md').read_text()
        assert '---' in content
        assert 'iteration_count' in content
        assert 'TASK-2' in content

    def test_load_returns_all_data(self):
        """Session.load() returns all saved data"""
        session = SessionState("TASK-3", "credentialmate")
        original = {
            'iteration_count': 8,
            'phase': 'complete',
            'status': 'completed',
            'markdown_content': 'Done!'
        }
        session.save(original)

        loaded = SessionState.load("TASK-3")
        assert loaded['iteration_count'] == 8
        assert loaded['markdown_content'] == 'Done!'

    def test_load_parses_frontmatter_correctly(self):
        """Load correctly parses JSON frontmatter"""
        session = SessionState("TASK-4", "credentialmate")
        session.save({
            'iteration_count': 12,
            'phase': 'testing',
            'tags': ['auth', 'jwt'],
            'nested': {'a': 1, 'b': 2},
            'markdown_content': ''
        })

        loaded = SessionState.load("TASK-4")
        assert loaded['iteration_count'] == 12
        assert loaded['tags'] == ['auth', 'jwt']
        assert loaded['nested']['b'] == 2


class TestSessionStateResume:
    """Resume capability"""

    def test_resume_continues_iteration_count(self):
        """Resuming task continues iteration count"""
        session = SessionState("TASK-5", "credentialmate")

        # First save
        session.save({'iteration_count': 5, 'phase': 'build', ...})

        # Load and update
        session.update(iteration_count=6)

        # Verify
        loaded = SessionState.load("TASK-5")
        assert loaded['iteration_count'] == 6

    def test_resume_preserves_progress(self):
        """Resuming preserves previous progress"""
        session = SessionState("TASK-6", "credentialmate")

        session.save({
            'iteration_count': 3,
            'markdown_content': '## Progress\n✅ Phase 1\n✅ Phase 2\n🔄 Phase 3'
        })

        loaded = SessionState.load("TASK-6")
        assert '✅ Phase 1' in loaded['markdown_content']

    def test_multiple_checkpoints_overwrite_previous(self):
        """Multiple saves overwrite previous (not append)"""
        session = SessionState("TASK-7", "credentialmate")

        session.save({'iteration_count': 1, 'phase': 'build'})
        session.save({'iteration_count': 2, 'phase': 'test'})

        loaded = SessionState.load("TASK-7")
        # Should have iteration 2, not 1
        assert loaded['iteration_count'] == 2


class TestSessionStateIntegration:
    """Integration with other systems"""

    async def test_checkpoint_in_iteration_loop(self):
        """IterationLoop.checkpoint() saves session"""
        # This test requires mocking IterationLoop
        # Verify that checkpoint calls session.save()
        pass

    async def test_resume_in_autonomous_loop(self):
        """AutonomousLoop resumes from session"""
        # Create a session with iteration_count=5
        # Run autonomous loop
        # Verify it continues from iteration 6
        pass

    def test_archived_session_not_loaded_again(self):
        """Completed sessions moved to archive"""
        session = SessionState("TASK-8", "credentialmate")
        session.save({'iteration_count': 50, 'status': 'completed'})
        session.archive()

        # Original should be gone
        assert not Path('.aibrain/session-TASK-8.md').exists()

        # Should be in archive
        archive_path = Path('.aibrain/sessions/archive/session-TASK-8.md')
        assert archive_path.exists()


class TestSessionStateEdgeCases:
    """Edge cases and error handling"""

    def test_load_nonexistent_raises_error(self):
        """Loading non-existent session raises error"""
        with pytest.raises(FileNotFoundError):
            SessionState.load("NONEXISTENT")

    def test_malformed_frontmatter_raises_error(self):
        """Malformed JSON frontmatter raises error"""
        # Create file with bad JSON
        Path('.aibrain/session-BAD.md').write_text("---\nNOT JSON\n---\nContent")

        with pytest.raises(json.JSONDecodeError):
            SessionState.load("BAD")

    def test_large_session_file_handled(self):
        """Large session files (100KB+) handled correctly"""
        session = SessionState("TASK-9", "credentialmate")

        # Create large content
        large_content = "x" * (100 * 1024)  # 100KB

        session.save({
            'iteration_count': 100,
            'markdown_content': large_content
        })

        loaded = SessionState.load("TASK-9")
        assert len(loaded['markdown_content']) == 100 * 1024

    def test_special_chars_in_content(self):
        """Special characters, JSON escaping handled"""
        session = SessionState("TASK-10", "credentialmate")

        session.save({
            'iteration_count': 1,
            'last_output': 'Error: "quotes" and \'apostrophes\' and \n newlines',
            'markdown_content': '# Title\n```json\n{"key": "value"}\n```'
        })

        loaded = SessionState.load("TASK-10")
        assert '"quotes"' in loaded['last_output']
```

---

## Implementation Checklist

### Week 1, Day 1-2: Core Implementation
- [ ] Create `orchestration/session_state.py` with SessionState class
- [ ] Implement `save()` method
- [ ] Implement `load()` classmethod
- [ ] Write 20+ unit tests
- [ ] Create `.aibrain/` directory structure

### Week 1, Day 3: IterationLoop Integration
- [ ] Modify `orchestration/iteration_loop.py`
- [ ] Add session initialization in `run()`
- [ ] Add checkpoint call after each iteration
- [ ] Test with simple task
- [ ] Verify session files created

### Week 1, Day 4: AutonomousLoop Integration
- [ ] Modify `autonomous_loop.py`
- [ ] Add session resumption logic
- [ ] Test resuming interrupted task
- [ ] Verify work queue updated correctly

### Week 1, Day 5: Testing & Documentation
- [ ] Write integration tests (5+)
- [ ] Test context reset scenario
- [ ] Test long-running task spanning 3+ contexts
- [ ] Update documentation
- [ ] Manual testing with credentialmate

---

## Success Criteria

| Criterion | How to Verify |
|-----------|---------------|
| **Session files created** | `.aibrain/session-{task_id}.md` exists after iteration |
| **Data persists** | Load session, verify all data intact |
| **Resume works** | Stop mid-iteration, resume, continue correctly |
| **Markdown readable** | Open file in editor, can understand progress |
| **Tests passing** | 20+ unit tests + integration tests all green |
| **Performance** | Save/load < 100ms per iteration |
| **Archival works** | Completed tasks moved to `.aibrain/sessions/archive/` |

---

## Code Review Checklist

Before merging, verify:
- [ ] All tests passing (20+ unit + 5+ integration)
- [ ] Session files human-readable
- [ ] Error handling for file I/O issues
- [ ] Performance acceptable (<100ms per checkpoint)
- [ ] Documentation complete
- [ ] Works with both IterationLoop and AutonomousLoop
- [ ] No hardcoded paths (use Path objects)
- [ ] Thread-safe for concurrent tasks

---

## Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| Save session | <100ms | TBD |
| Load session | <50ms | TBD |
| Update session | <75ms | TBD |
| Checkpoint in loop | <200ms overhead | TBD |

---

## Next Phase Dependencies

Phase 2 (Work Queue) depends on:
- ✅ Session files working
- ✅ Resume capability verified
- ✅ Tests passing

Once Phase 1 complete, Phase 2 can start immediately.

---

**Estimated Timeline**: 5 days (40 hours)
**Complexity**: Medium
**Risk**: Low (isolated, no breaking changes)

