# Governance Overhaul: Unified System

**Date**: 2026-01-09
**Status**: Design Phase

---

## Problem Statement

Three repos, three governance models:

| Repo | Current Model | Issues |
|------|---------------|--------|
| AI_Orchestrator | YAML contracts | No golden paths, no graduated autonomy |
| CredentialMate | Contracts + HIPAA | Synced but fragmented |
| KareMatch | Golden paths + RIS | No contracts, manual enforcement |

**Result**: Inconsistent enforcement, confusion, potential conflicts with new agents.

---

## Unified Governance Model

### Single Source: `governance/unified/`

```
governance/
├── unified/
│   ├── governance.yaml       # Master config
│   ├── golden-paths.yaml     # Protected files (all repos)
│   └── guardrails.yaml       # Safety rules (all repos)
│
├── contracts/
│   ├── advisor.yaml          # All Advisors
│   ├── coordinator.yaml      # Coordinator
│   ├── qa-team.yaml          # BugFix, CodeQuality
│   ├── dev-team.yaml         # FeatureBuilder, TestWriter
│   └── infra-team.yaml       # Infrastructure
│
└── extensions/
    ├── hipaa.yaml            # HIPAA additions (CredentialMate)
    └── healthcare.yaml       # Healthcare additions (KareMatch)
```

---

## Governance.yaml (Master Config)

```yaml
# governance/unified/governance.yaml

version: "2.0"
name: "AI Team Governance"

# Autonomy Levels (unified from KareMatch L0-L4 + AI_Orch L1-L2)
autonomy_levels:
  L0:
    name: "Observer"
    allowed: [read_file, search_codebase, analyze]
    forbidden: [write_file, run_commands, modify]

  L1:
    name: "Contributor"
    allowed: [read_file, write_file, run_tests]
    forbidden: [modify_migrations, modify_ci, deploy]
    requires_approval: [merge_pr]

  L2:
    name: "Maintainer"
    allowed: [read_file, write_file, run_tests, create_branch]
    forbidden: [modify_migrations, deploy]
    requires_approval: [merge_to_main]

  L3:
    name: "Architect"
    allowed: [read_file, write_file, analyze, propose_changes]
    forbidden: [implement_without_approval]
    requires_approval: [every_decision]

  L4:
    name: "Admin"
    allowed: [all_except_forbidden]
    forbidden: [bypass_ralph, hard_delete, deploy_without_approval]
    requires_approval: [deploy, schema_changes]

# Agent Mode Mapping
agent_modes:
  dialogue:
    autonomy: L3
    agents: [data-advisor, app-advisor, uiux-advisor]
    behavior: "Present options, wait for decision, document"

  autonomous:
    autonomy: L1-L2
    agents: [coordinator, feature-builder, bug-fixer, test-writer, code-quality]
    behavior: "Execute within contract, escalate on BLOCKED"

# Verification
verification:
  engine: ralph
  timing:
    advisors: none          # Advisors don't write code
    coordinator: none       # Coordinator orchestrates, doesn't write code
    qa_team: every_commit   # Strict
    dev_team: on_pr         # Relaxed for iteration speed

# Human Touch Points
human_required:
  - BLOCKED verdict
  - Every Advisor decision
  - Merge to main
  - Deploy
  - Schema changes (HIPAA/Healthcare)
```

---

## Golden Paths (Protected Files)

```yaml
# governance/unified/golden-paths.yaml

version: "1.0"

protection_levels:
  BLOCK_AND_ASK:
    description: "Cannot modify without explicit human approval"
    files:
      - "CLAUDE.md"
      - ".claude/instructions.md"
      - "governance/**/*.yaml"
      - "PROJECT_HQ.md"

  VALIDATE_FIRST:
    description: "Must pass validation before modification"
    files:
      - "**/migrations/**"
      - "**/alembic/versions/**"
      - "package.json"
      - "requirements.txt"
    validation: "schema_validator"

  WARN_AND_LOG:
    description: "Allow but log modification"
    files:
      - "Dockerfile*"
      - "docker-compose*.yml"
      - ".env*"
      - "*.config.js"
      - "*.config.ts"

  SECURITY_REVIEW:
    description: "Requires security check"
    files:
      - "**/auth/**"
      - "**/encryption/**"
      - "**/middleware/auth*"

  BLOCK_MODIFICATION:
    description: "Frozen - never modify"
    files:
      - "decisions/ADR-*.md"  # Immutable once approved

# Per-Project Extensions
project_extensions:
  credentialmate:
    BLOCK_AND_ASK:
      - "ralph/hipaa_*.py"
      - "ralph/hipaa_*.yaml"
    SECURITY_REVIEW:
      - "**/models/patient*.py"
      - "**/models/credential*.py"

  karematch:
    BLOCK_AND_ASK:
      - ".claude/golden-paths.json"
      - "docs/06-ris/**"
    VALIDATE_FIRST:
      - "services/matching/**"
```

---

## Guardrails (Safety Rules)

```yaml
# governance/unified/guardrails.yaml

version: "1.0"

# Forbidden Patterns (Ralph will BLOCK)
forbidden_patterns:
  typescript:
    - pattern: "@ts-ignore"
      message: "Fix the type error instead of ignoring"
    - pattern: "@ts-nocheck"
      message: "Type checking must remain enabled"
    - pattern: "@ts-expect-error"
      message: "Fix the underlying issue"

  eslint:
    - pattern: "eslint-disable"
      message: "Fix the lint error instead of disabling"

  testing:
    - pattern: ".skip("
      message: "Do not skip tests"
    - pattern: ".only("
      message: "Do not focus tests"
    - pattern: "test.todo("
      message: "Implement the test"

  git:
    - pattern: "--no-verify"
      message: "Never bypass pre-commit hooks"
    - pattern: "-n"
      context: "git commit"
      message: "Never bypass verification"

  python:
    - pattern: "# noqa"
      message: "Fix the lint issue"
    - pattern: "# type: ignore"
      message: "Fix the type error"
    - pattern: "@pytest.mark.skip"
      message: "Do not skip tests"

# Behavioral Rules
behavioral_rules:
  qa_team:
    - rule: "test_count_unchanged"
      message: "QA team cannot change test count"
    - rule: "no_new_files"
      message: "QA team cannot create new files"
    - rule: "behavior_preserved"
      message: "Must not change application behavior"

  dev_team:
    - rule: "tests_required"
      message: "New code must have tests"
    - rule: "coverage_minimum"
      value: 80
      message: "Minimum 80% coverage on new files"

  advisors:
    - rule: "no_implementation"
      message: "Advisors cannot implement, only advise"
    - rule: "must_present_options"
      message: "Must present 2+ options"
    - rule: "must_wait_for_decision"
      message: "Cannot proceed without human decision"

  coordinator:
    - rule: "no_code_changes"
      message: "Coordinator orchestrates, doesn't code"
    - rule: "must_update_project_hq"
      message: "Every action must update PROJECT_HQ"

# HIPAA Extension (CredentialMate only)
hipaa_rules:
  enabled_for: [credentialmate]
  patterns:
    - pattern: "patient"
      context: "hardcoded string"
      message: "No hardcoded PHI"
    - pattern: "ssn"
      context: "hardcoded string"
      message: "No hardcoded SSN"
    - pattern: "medical"
      context: "hardcoded string"
      message: "No hardcoded medical data"
  sensitive_paths:
    - "**/models/patient*"
    - "**/models/credential*"
    - "**/api/health*"
```

---

## Contract Updates

### Advisor Contract

```yaml
# governance/contracts/advisor.yaml

name: advisor
version: "2.0"
mode: dialogue
autonomy_level: L3

applies_to:
  - data-advisor
  - app-advisor
  - uiux-advisor

allowed_actions:
  - read_file
  - search_codebase
  - analyze_schema
  - analyze_architecture
  - analyze_components
  - create_adr
  - update_project_hq_roadmap

forbidden_actions:
  - write_code
  - modify_source_files
  - run_commands
  - implement_changes
  - make_autonomous_decisions
  - approve_own_recommendations

requires_approval:
  - every_recommendation

behaviors:
  must_present_options: true
  min_options: 2
  max_options: 4
  must_explain_tradeoffs: true
  must_use_plain_language: true
  must_wait_for_decision: true
  must_document_decision: true
  must_handoff_to_coordinator: true

output_artifacts:
  required:
    - decisions/ADR-*.md
  optional:
    - diagrams/
    - wireframes/

on_violation: halt
```

### Coordinator Contract

```yaml
# governance/contracts/coordinator.yaml

name: coordinator
version: "2.0"
mode: autonomous
autonomy_level: L2

allowed_actions:
  - read_adr
  - read_codebase
  - create_task
  - assign_task
  - update_project_hq
  - create_handoff
  - manage_work_queue

forbidden_actions:
  - write_code
  - modify_source_files
  - make_architectural_decisions
  - modify_adr
  - bypass_ralph
  - hard_delete

requires_approval:
  - delete_task
  - change_priority
  - reassign_blocked_task

limits:
  max_concurrent_tasks: 3
  max_queue_size: 50
  max_iterations: 100

behaviors:
  auto_break_down_adrs: true
  auto_assign_tasks: true
  auto_update_project_hq: true
  auto_create_handoffs: true
  respect_dependencies: true
  escalate_on_blocked: true

triggers:
  - adr_approved
  - task_complete
  - task_blocked
  - session_start
  - session_end

on_violation: halt
```

---

## Sync Strategy

### What Syncs to Projects

```yaml
sync_manifest:
  syncable:
    # Core governance (sync to all projects)
    - governance/unified/governance.yaml
    - governance/unified/golden-paths.yaml
    - governance/unified/guardrails.yaml
    - governance/contracts/advisor.yaml
    - governance/contracts/coordinator.yaml
    - governance/contracts/qa-team.yaml
    - governance/contracts/dev-team.yaml

    # Core agents (sync to all projects)
    - agents/base/base_advisor.py
    - agents/base/base_coordinator.py
    - agents/base/*.py

  protected:
    # Project-specific (never sync)
    - governance/extensions/*.yaml
    - ralph/hipaa_*.py
    - ralph/hipaa_*.yaml
    - PROJECT_HQ.md
    - tasks/work_queue.json
    - decisions/*.md

  merge_strategy:
    # Need careful merging
    - agents/factory.py: preserve_local_extensions
```

---

## Migration Path

### Phase 1: AI_Orchestrator

1. Create `governance/unified/` folder
2. Consolidate existing contracts
3. Add golden-paths.yaml
4. Add guardrails.yaml
5. Test with existing agents

### Phase 2: CredentialMate

1. Sync unified governance
2. Add HIPAA extension (`governance/extensions/hipaa.yaml`)
3. Update sync-manifest.yaml
4. Verify HIPAA rules still enforced

### Phase 3: KareMatch

1. Migrate from `.claude/golden-paths.json` to `governance/unified/`
2. Adopt contract-based governance
3. Keep domain skills as-is
4. Add healthcare extension

---

## Enforcement Points

### Pre-Write Hook

```python
def pre_write_hook(agent, file_path, content):
    """
    Runs before any file write.
    """
    # 1. Check golden paths
    protection = golden_paths.check(file_path)
    if protection == BLOCK_AND_ASK:
        raise NeedsApproval(f"Cannot modify {file_path}")
    if protection == VALIDATE_FIRST:
        validate(file_path, content)

    # 2. Check guardrails
    violations = guardrails.scan(content)
    if violations:
        raise GuardrailViolation(violations)

    # 3. Check contract
    if not agent.contract.allows('write_file'):
        raise ContractViolation("Agent cannot write files")

    return ALLOW
```

### Pre-Commit Hook

```python
def pre_commit_hook(agent, changes):
    """
    Runs before any commit.
    """
    # 1. Run Ralph verification
    verdict = ralph.verify(changes)

    if verdict == BLOCKED:
        raise RalphBlocked(verdict.reason)

    # 2. Check behavioral rules
    for rule in agent.contract.behavioral_rules:
        if not rule.check(changes):
            raise BehaviorViolation(rule.message)

    return ALLOW
```

---

## Conflict Resolution

### When Contracts Conflict

```yaml
conflict_resolution:
  priority:
    1. Safety guardrails (always win)
    2. Golden paths protection
    3. Project extensions (HIPAA, healthcare)
    4. Base contracts

  example:
    # If base contract allows write_file but HIPAA extension
    # blocks writes to patient models:
    # → HIPAA extension wins (more specific)
```

### Agent Mode Conflicts

```yaml
mode_conflicts:
  # Advisor tries to implement
  scenario: "data-advisor attempts to write code"
  resolution: "Contract blocks, agent halts"

  # Coordinator tries to make decisions
  scenario: "coordinator attempts architectural decision"
  resolution: "Contract blocks, escalates to Advisor"

  # Builder tries to modify golden path
  scenario: "feature-builder tries to edit CLAUDE.md"
  resolution: "Golden paths block, requires human approval"
```
