"""
CLI commands for SQLite work queue management.

Provides commands for managing work queue via command line:
- list: View tasks with optional hierarchy
- add-epic/add-feature/add-task: Create hierarchy items
- progress: View completion stats
- migrate: Run schema migrations
- export: SQLite → JSON snapshot

Reference: KO-aio-002 (SQLite persistence), KO-aio-004 (Feature hierarchy)
"""

import click
from pathlib import Path
from orchestration.queue_manager import WorkQueueManager
from orchestration.models import Epic, Feature, Task


@click.command("list")
@click.option("--project", required=True, help="Project name")
@click.option("--hierarchy", is_flag=True, help="Show hierarchical tree view")
def queue_list(project: str, hierarchy: bool):
    """List all tasks in work queue."""
    manager = WorkQueueManager(project=project, use_db=True)

    if hierarchy:
        _print_hierarchy(manager)
    else:
        _print_flat_list(manager)


def _print_flat_list(manager: WorkQueueManager):
    """Print flat list of tasks."""
    tasks = manager.get_all_tasks()

    if not tasks:
        click.echo("No tasks found in queue.")
        return

    click.echo(f"\n{'ID':<15} {'Description':<50} {'Status':<15}")
    click.echo("-" * 80)

    for task in tasks:
        click.echo(
            f"{task['id']:<15} {task['description'][:48]:<50} {task['status']:<15}"
        )

    click.echo(f"\nTotal: {len(tasks)} tasks")


def _print_hierarchy(manager: WorkQueueManager):
    """Print hierarchical tree view of epics → features → tasks."""
    with manager._get_session() as session:
        epics = session.query(Epic).all()

        if not epics:
            click.echo("No epics found in queue (empty).")
            return

        for epic in epics:
            # Print epic
            click.echo(f"\n📦 {epic.name} ({epic.status})")
            if epic.description:
                click.echo(f"   {epic.description}")

            # Print features
            features = session.query(Feature).filter_by(epic_id=epic.id).all()
            for i, feature in enumerate(features):
                is_last_feature = (i == len(features) - 1)
                prefix = "└──" if is_last_feature else "├──"

                click.echo(f"  {prefix} 📂 {feature.name} (P{feature.priority}, {feature.status})")

                # Print tasks
                tasks = session.query(Task).filter_by(feature_id=feature.id).all()
                for j, task in enumerate(tasks):
                    is_last_task = (j == len(tasks) - 1)
                    task_prefix = "└──" if is_last_task else "├──"
                    indent = "      " if is_last_feature else "  │   "

                    click.echo(
                        f"{indent}{task_prefix} ✓ {task.description[:50]} ({task.status})"
                    )


@click.command("add-epic")
@click.option("--project", required=True, help="Project name")
@click.option("--name", required=True, help="Epic name")
@click.option("--description", help="Epic description")
def queue_add_epic(project: str, name: str, description: str = None):
    """Add new epic to work queue."""
    manager = WorkQueueManager(project=project, use_db=True)

    epic_id = manager.add_epic(name=name, description=description)

    click.echo(f"✅ Epic created: {epic_id}")
    click.echo(f"   Name: {name}")
    if description:
        click.echo(f"   Description: {description}")


@click.command("add-feature")
@click.option("--project", required=True, help="Project name")
@click.option("--epic", required=True, help="Parent epic ID")
@click.option("--name", required=True, help="Feature name")
@click.option("--description", help="Feature description")
@click.option("--priority", type=int, default=2, help="Priority (0=P0, 1=P1, 2=P2)")
def queue_add_feature(
    project: str,
    epic: str,
    name: str,
    description: str = None,
    priority: int = 2
):
    """Add new feature to work queue."""
    manager = WorkQueueManager(project=project, use_db=True)

    feature_id = manager.add_feature(
        epic_id=epic,
        name=name,
        description=description,
        priority=priority
    )

    click.echo(f"✅ Feature created: {feature_id}")
    click.echo(f"   Name: {name}")
    click.echo(f"   Epic: {epic}")
    click.echo(f"   Priority: P{priority}")


@click.command("add-task")
@click.option("--project", required=True, help="Project name")
@click.option("--feature", required=True, help="Parent feature ID")
@click.option("--description", required=True, help="Task description")
@click.option("--priority", type=int, default=2, help="Priority (0=P0, 1=P1, 2=P2)")
def queue_add_task(
    project: str,
    feature: str,
    description: str,
    priority: int = 2
):
    """Add new task to work queue."""
    manager = WorkQueueManager(project=project, use_db=True)

    task_id = manager.add_task(
        feature_id=feature,
        description=description,
        priority=priority
    )

    click.echo(f"✅ Task created: {task_id}")
    click.echo(f"   Description: {description}")
    click.echo(f"   Feature: {feature}")
    click.echo(f"   Priority: P{priority}")


@click.command("progress")
@click.option("--project", required=True, help="Project name")
@click.option("--epic", help="Epic ID to show progress for")
@click.option("--feature", help="Feature ID to show progress for")
def queue_progress(project: str, epic: str = None, feature: str = None):
    """Show progress statistics for epic or feature."""
    if not epic and not feature:
        click.echo("❌ Error: Must specify --epic or --feature", err=True)
        raise click.Abort()

    manager = WorkQueueManager(project=project, use_db=True)

    with manager._get_session() as session:
        if epic:
            _show_epic_progress(session, epic)
        elif feature:
            _show_feature_progress(session, feature)


def _show_epic_progress(session, epic_id: str):
    """Show progress for an epic."""
    epic = session.query(Epic).filter_by(id=epic_id).first()
    if not epic:
        click.echo(f"❌ Epic not found: {epic_id}", err=True)
        raise click.Abort()

    click.echo(f"\n📦 Epic: {epic.name} ({epic.status})")

    # Get all features
    features = session.query(Feature).filter_by(epic_id=epic_id).all()
    total_features = len(features)
    completed_features = sum(1 for f in features if f.status == "completed")

    # Get all tasks across all features
    total_tasks = 0
    completed_tasks = 0
    for feature in features:
        tasks = session.query(Task).filter_by(feature_id=feature.id).all()
        total_tasks += len(tasks)
        completed_tasks += sum(1 for t in tasks if t.status == "completed")

    click.echo(f"\n   Features: {completed_features}/{total_features} completed")
    if total_features > 0:
        feat_pct = (completed_features / total_features) * 100
        click.echo(f"   Progress: {feat_pct:.1f}%")

    click.echo(f"\n   Tasks: {completed_tasks}/{total_tasks} completed")
    if total_tasks > 0:
        task_pct = (completed_tasks / total_tasks) * 100
        click.echo(f"   Progress: {task_pct:.1f}%")


def _show_feature_progress(session, feature_id: str):
    """Show progress for a feature."""
    feature = session.query(Feature).filter_by(id=feature_id).first()
    if not feature:
        click.echo(f"❌ Feature not found: {feature_id}", err=True)
        raise click.Abort()

    click.echo(f"\n📂 Feature: {feature.name} (P{feature.priority}, {feature.status})")

    # Get all tasks
    tasks = session.query(Task).filter_by(feature_id=feature_id).all()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "completed")
    pending_tasks = sum(1 for t in tasks if t.status == "pending")
    in_progress_tasks = sum(1 for t in tasks if t.status == "in_progress")

    click.echo(f"\n   Total tasks: {total_tasks}")
    click.echo(f"   Completed: {completed_tasks}")
    click.echo(f"   In progress: {in_progress_tasks}")
    click.echo(f"   Pending: {pending_tasks}")

    if total_tasks > 0:
        pct = (completed_tasks / total_tasks) * 100
        click.echo(f"\n   Progress: {pct:.1f}%")


@click.command("migrate")
@click.option("--project", required=True, help="Project name")
def queue_migrate(project: str):
    """Run database schema migrations."""
    manager = WorkQueueManager(project=project, use_db=True)

    current_version = manager.get_schema_version()
    click.echo(f"Current schema version: {current_version}")

    # Run migrations
    manager.migrate()

    new_version = manager.get_schema_version()
    if new_version > current_version:
        click.echo(f"✅ Migrated to version {new_version}")
    else:
        click.echo("✅ Database is up to date (no migrations needed)")


@click.command("export")
@click.option("--project", required=True, help="Project name")
@click.option("--output", help="Custom output path (default: work_queue_{project}_snapshot.json)")
def queue_export(project: str, output: str = None):
    """Export SQLite work queue to JSON snapshot."""
    manager = WorkQueueManager(project=project, use_db=True)

    # Export to default or custom path
    if output:
        # Custom path - need to manually save
        snapshot_path = manager.export_snapshot()

        # Read and write to custom location
        import shutil
        custom_path = Path(output)
        shutil.copy(snapshot_path, custom_path)

        click.echo(f"✅ Work queue exported to: {custom_path}")
    else:
        snapshot_path = manager.export_snapshot()
        click.echo(f"✅ Work queue exported to: {snapshot_path}")

    # Show summary
    import json
    with open(snapshot_path if not output else custom_path) as f:
        data = json.load(f)

    task_count = len(data.get("tasks", []))
    click.echo(f"   Exported {task_count} tasks")
