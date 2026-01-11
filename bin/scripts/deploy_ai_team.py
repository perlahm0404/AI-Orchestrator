#!/usr/bin/env python3
"""
AI Team Deployment Script
Version: 3.0
Part of: AI Team (AI-TEAM-SPEC-V3)

Deploys AI Team structure to target repositories.
Creates necessary folders, templates, and configuration files.

Usage:
    python scripts/deploy_ai_team.py <target_repo> [--project-name NAME]

Example:
    python scripts/deploy_ai_team.py /Users/tmac/karematch --project-name karematch
"""

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

ORCHESTRATOR_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = ORCHESTRATOR_ROOT / "templates"

# Directories to create
DIRECTORIES = [
    "AI-Team-Plans",
    "AI-Team-Plans/decisions",
    "AI-Team-Plans/tasks",
    "AI-Team-Plans/sessions",
    "AI-Team-Plans/events",
    "AI-Team-Plans/events/current",
    "AI-Team-Plans/events/archive",
    "AI-Team-Plans/retrospectives",
    "AI-Team-Plans/knowledge",
    "AI-Team-Plans/knowledge/approved",
    "AI-Team-Plans/knowledge/drafts",
]


# ═══════════════════════════════════════════════════════════════════════════════
# DEPLOYMENT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_directories(target: Path) -> None:
    """Create required directory structure."""
    print("📁 Creating directory structure...")

    for dir_path in DIRECTORIES:
        full_path = target / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {dir_path}")


def copy_templates(target: Path, project_name: str) -> None:
    """Copy and customize templates."""
    print("\n📄 Copying templates...")

    templates_source = TEMPLATES_DIR / "AI-Team-Plans"

    if not templates_source.exists():
        print(f"   ⚠ Templates not found at {templates_source}")
        return

    # Copy PROJECT_HQ.md
    if (templates_source / "PROJECT_HQ.md").exists():
        content = (templates_source / "PROJECT_HQ.md").read_text()
        content = content.replace("{{PROJECT_NAME}}", project_name)
        content = content.replace("{{TIMESTAMP}}", utc_now().strftime("%Y-%m-%d %H:%M:%S"))
        (target / "AI-Team-Plans" / "PROJECT_HQ.md").write_text(content)
        print("   ✓ PROJECT_HQ.md")

    # Copy ADR template
    adr_template = templates_source / "decisions" / "ADR-TEMPLATE.md"
    if adr_template.exists():
        shutil.copy(adr_template, target / "AI-Team-Plans" / "decisions" / "ADR-TEMPLATE.md")
        print("   ✓ decisions/ADR-TEMPLATE.md")

    # Copy decisions index
    index_template = templates_source / "decisions" / "index.md"
    if index_template.exists():
        content = index_template.read_text()
        content = content.replace("{{PROJECT_NAME}}", project_name)
        (target / "AI-Team-Plans" / "decisions" / "index.md").write_text(content)
        print("   ✓ decisions/index.md")

    # Copy handoff template
    handoff_template = templates_source / "sessions" / "HANDOFF-TEMPLATE.md"
    if handoff_template.exists():
        shutil.copy(handoff_template, target / "AI-Team-Plans" / "sessions" / "HANDOFF-TEMPLATE.md")
        print("   ✓ sessions/HANDOFF-TEMPLATE.md")

    # Copy retrospective template
    retro_template = templates_source / "retrospectives" / "RETROSPECTIVE-TEMPLATE.md"
    if retro_template.exists():
        shutil.copy(retro_template, target / "AI-Team-Plans" / "retrospectives" / "RETROSPECTIVE-TEMPLATE.md")
        print("   ✓ retrospectives/RETROSPECTIVE-TEMPLATE.md")


def create_work_queue(target: Path, project_name: str) -> None:
    """Create initial work queue."""
    print("\n📋 Creating work queue...")

    queue = {
        "version": "3.0",
        "project": project_name,
        "generated_at": utc_now().isoformat(),
        "sequence": 0,
        "stats": {
            "total": 0,
            "by_status": {
                "pending": 0,
                "assigned": 0,
                "in_progress": 0,
                "blocked": 0,
                "completed": 0,
                "cancelled": 0,
            },
            "by_type": {},
        },
        "tasks": [],
    }

    queue_path = target / "AI-Team-Plans" / "tasks" / "work_queue.json"
    with open(queue_path, "w") as f:
        json.dump(queue, f, indent=2)

    print("   ✓ tasks/work_queue.json")


def create_metrics(target: Path, project_name: str) -> None:
    """Create initial metrics file."""
    print("\n📊 Creating metrics...")

    metrics = {
        "version": "3.0",
        "project": project_name,
        "period": utc_now().strftime("%Y-%m-%d"),
        "generated_at": utc_now().isoformat(),
        "totals": {
            "events_total": 0,
            "events_logged_detail": 0,
            "events_counted_only": 0,
        },
        "by_agent": {},
        "ralph_verdicts": {
            "pass": 0,
            "fail": 0,
            "blocked": 0,
        },
        "escalations": {
            "to_human": 0,
            "scope_triggers": 0,
            "adr_conflicts": 0,
            "low_confidence": 0,
            "strategic_domain": 0,
        },
        "phase_progress": {
            "current_phase": 1,
            "tasks_in_phase": 0,
            "tasks_completed": 0,
            "tasks_blocked": 0,
            "tasks_pending": 0,
        },
        "daily_counts": [],
    }

    metrics_path = target / "AI-Team-Plans" / "events" / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print("   ✓ events/metrics.json")


def create_patterns(target: Path) -> None:
    """Create initial patterns file."""
    print("\n🔍 Creating patterns registry...")

    patterns = {
        "version": "3.0",
        "generated_at": utc_now().isoformat(),
        "patterns": [],
    }

    patterns_path = target / "AI-Team-Plans" / "retrospectives" / "patterns.json"
    with open(patterns_path, "w") as f:
        json.dump(patterns, f, indent=2)

    print("   ✓ retrospectives/patterns.json")


def create_gitignore(target: Path) -> None:
    """Create or update .gitignore for AI-Team files."""
    print("\n🔒 Updating .gitignore...")

    gitignore_path = target / ".gitignore"
    ai_team_ignores = """
# AI Team Plans - Ephemeral files
AI-Team-Plans/events/current/*.md
AI-Team-Plans/sessions/*-handoff.md
!AI-Team-Plans/sessions/HANDOFF-TEMPLATE.md

# Keep these tracked
!AI-Team-Plans/decisions/**
!AI-Team-Plans/retrospectives/**
!AI-Team-Plans/PROJECT_HQ.md
"""

    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if "AI Team Plans" not in content:
            content += ai_team_ignores
            gitignore_path.write_text(content)
            print("   ✓ Added AI Team entries to .gitignore")
        else:
            print("   ✓ .gitignore already configured")
    else:
        gitignore_path.write_text(ai_team_ignores.strip())
        print("   ✓ Created .gitignore")


def create_claude_md(target: Path, project_name: str) -> None:
    """Create or update CLAUDE.md with AI Team section."""
    print("\n📝 Updating CLAUDE.md...")

    claude_md_path = target / "CLAUDE.md"

    ai_team_section = f"""
## AI Team Integration

This project uses the AI Team orchestration system for governed AI-assisted development.

### Key Files

| File | Purpose |
|------|---------|
| `AI-Team-Plans/PROJECT_HQ.md` | Central dashboard for project status |
| `AI-Team-Plans/decisions/` | Architecture Decision Records (ADRs) |
| `AI-Team-Plans/tasks/work_queue.json` | Current work queue |
| `AI-Team-Plans/events/metrics.json` | Event metrics and statistics |

### Invoking Advisors

- `@data-advisor` - Database, schema, data modeling questions
- `@app-advisor` - Architecture, API, design pattern questions
- `@uiux-advisor` - Component, accessibility, UX questions

### Session Protocol

1. Read `AI-Team-Plans/PROJECT_HQ.md` for current status
2. Check `AI-Team-Plans/tasks/work_queue.json` for pending work
3. Review recent `AI-Team-Plans/sessions/*-handoff.md` for context
4. At session end, handoffs are auto-generated

### Governance

- Scope limit: 5 files per task (escalates to advisor if exceeded)
- ADR alignment: Recommendations checked against existing decisions
- Confidence threshold: 85% for auto-approval
- Strategic domains (migrations, auth, etc.) always require human approval
"""

    if claude_md_path.exists():
        content = claude_md_path.read_text()
        if "AI Team Integration" not in content:
            content += "\n" + ai_team_section
            claude_md_path.write_text(content)
            print("   ✓ Added AI Team section to CLAUDE.md")
        else:
            print("   ✓ CLAUDE.md already has AI Team section")
    else:
        header = f"# {project_name}\n\n"
        claude_md_path.write_text(header + ai_team_section)
        print("   ✓ Created CLAUDE.md")


def verify_deployment(target: Path) -> bool:
    """Verify deployment was successful."""
    print("\n✅ Verifying deployment...")

    required_files = [
        "AI-Team-Plans/PROJECT_HQ.md",
        "AI-Team-Plans/tasks/work_queue.json",
        "AI-Team-Plans/events/metrics.json",
        "AI-Team-Plans/decisions/index.md",
        "AI-Team-Plans/retrospectives/patterns.json",
    ]

    all_present = True
    for file_path in required_files:
        full_path = target / file_path
        if full_path.exists():
            print(f"   ✓ {file_path}")
        else:
            print(f"   ✗ {file_path} MISSING")
            all_present = False

    return all_present


def deploy(target: Path, project_name: str) -> bool:
    """
    Deploy AI Team structure to target repository.

    Args:
        target: Path to target repository
        project_name: Name of the project

    Returns:
        True if deployment successful
    """
    print(f"\n{'='*60}")
    print(f"🚀 Deploying AI Team to: {target}")
    print(f"   Project: {project_name}")
    print(f"{'='*60}")

    # Validate target
    if not target.exists():
        print(f"\n❌ Error: Target directory does not exist: {target}")
        return False

    if not (target / ".git").exists():
        print(f"\n⚠ Warning: Target is not a git repository")

    # Run deployment steps
    create_directories(target)
    copy_templates(target, project_name)
    create_work_queue(target, project_name)
    create_metrics(target, project_name)
    create_patterns(target)
    create_gitignore(target)
    create_claude_md(target, project_name)

    # Verify
    success = verify_deployment(target)

    print(f"\n{'='*60}")
    if success:
        print("✅ Deployment complete!")
        print(f"\nNext steps:")
        print(f"  1. Review AI-Team-Plans/PROJECT_HQ.md")
        print(f"  2. Create your first ADR in AI-Team-Plans/decisions/")
        print(f"  3. Start using @data-advisor, @app-advisor, @uiux-advisor")
    else:
        print("❌ Deployment incomplete - some files missing")
    print(f"{'='*60}\n")

    return success


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Deploy AI Team structure to a target repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s /Users/tmac/karematch
    %(prog)s /Users/tmac/credentialmate --project-name CredentialMate
    %(prog)s . --project-name MyProject
        """,
    )

    parser.add_argument(
        "target",
        type=Path,
        help="Path to target repository",
    )

    parser.add_argument(
        "--project-name",
        type=str,
        default=None,
        help="Project name (defaults to directory name)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without making changes",
    )

    args = parser.parse_args()

    target = args.target.resolve()
    project_name = args.project_name or target.name

    if args.dry_run:
        print(f"Dry run - would deploy to: {target}")
        print(f"Project name: {project_name}")
        print(f"\nDirectories to create:")
        for d in DIRECTORIES:
            print(f"  - {d}")
        return 0

    success = deploy(target, project_name)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
