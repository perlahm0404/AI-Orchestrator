# Product Requirements Document (PRD)

> **Purpose**: This file defines tasks for the Real Ralph loop.
> Each task has a checkbox, description, and acceptance criteria.
> Ralph will work through tasks top-to-bottom, marking checkboxes as complete.

---

## How to Use This File

1. Add tasks as checkbox items: `- [ ] Task description`
2. Include clear acceptance criteria for each task
3. Run `./ralph.sh` to start the loop
4. Ralph marks `- [x]` when tasks are complete
5. Check `progress.md` for iteration history

---

## Tasks

### Example Section: Code Quality Improvements

- [x] Fix unused import warnings in `ralph/engine.py`
  - **Acceptance Criteria**: `ruff check ralph/engine.py` returns 0 warnings
  - **Files**: `ralph/engine.py`

- [ ] Add type hints to the `Verdict` class methods
  - **Acceptance Criteria**: `mypy ralph/verdict.py` passes with no errors
  - **Files**: `ralph/verdict.py`

- [ ] Write a unit test for `count_incomplete_tasks` function in ralph.sh
  - **Acceptance Criteria**: Test file exists and validates grep pattern matching
  - **Files**: `tests/test_ralph_loop.sh`

### Example Section: Documentation

- [ ] Update README.md with Real Ralph usage instructions
  - **Acceptance Criteria**: README includes `./ralph.sh` command examples
  - **Files**: `README.md`

---

## Completed Tasks

> Move completed tasks here for reference.

<!-- Example:
- [x] Initial PRD.md setup
  - **Completed**: 2024-01-15
  - **Notes**: Created template structure
-->

---

## Notes

- Tasks should be atomic (one clear deliverable per task)
- Order tasks by priority (Ralph works top-to-bottom)
- Include file paths to help Claude navigate the codebase
- Add acceptance criteria that can be verified programmatically when possible
