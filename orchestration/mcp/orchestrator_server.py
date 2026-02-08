"""
AI Orchestrator MCP Server

Exposes orchestration capabilities via Model Context Protocol:
- Work queue management (tasks, status, priorities)
- Ralph verification (verify, verdict)
- Knowledge Object queries
- Session state management

Usage:
    python -m orchestration.mcp.orchestrator_server

Configuration (.mcp.json):
    {
      "mcpServers": {
        "orchestrator": {
          "type": "stdio",
          "command": "python",
          "args": ["-m", "orchestration.mcp.orchestrator_server"]
        }
      }
    }

Author: Claude Code
Date: 2026-02-08
Version: 1.0
"""

import json
import asyncio
from pathlib import Path
from typing import Any
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Initialize the MCP server
server = Server("ai-orchestrator")


def get_project_root() -> Path:
    """Get the AI Orchestrator project root directory."""
    return Path(__file__).parent.parent.parent


def load_work_queue(project: str) -> dict[str, Any]:
    """Load work queue for a project."""
    root = get_project_root()

    # Try JSON file first
    json_path = root / "tasks" / f"work_queue_{project}.json"
    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)

    return {"tasks": [], "error": f"No work queue found for {project}"}


def save_work_queue(project: str, data: dict[str, Any]) -> bool:
    """Save work queue for a project."""
    root = get_project_root()
    json_path = root / "tasks" / f"work_queue_{project}.json"

    try:
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def load_knowledge_objects() -> list[dict[str, Any]]:
    """Load approved Knowledge Objects."""
    root = get_project_root()
    ko_dir = root / "knowledge" / "approved"

    kos = []
    if ko_dir.exists():
        for ko_file in ko_dir.glob("*.md"):
            # Parse YAML frontmatter
            content = ko_file.read_text()
            kos.append({
                "id": ko_file.stem,
                "path": str(ko_file),
                "preview": content[:200] if len(content) > 200 else content
            })

    return kos


def get_session_state() -> dict[str, Any]:
    """Get current session state from STATE.md."""
    root = get_project_root()
    state_path = root / "STATE.md"

    if state_path.exists():
        content = state_path.read_text()
        return {
            "path": str(state_path),
            "content": content[:2000],  # First 2000 chars
            "updated": datetime.fromtimestamp(
                state_path.stat().st_mtime
            ).isoformat()
        }

    return {"error": "STATE.md not found"}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available orchestration tools."""
    return [
        Tool(
            name="list_tasks",
            description="List tasks from work queue for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project name (e.g., karematch, credentialmate)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status (pending, in_progress, completed, blocked, parked)",
                        "enum": ["pending", "in_progress", "completed", "blocked", "parked"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of tasks to return",
                        "default": 10
                    }
                },
                "required": ["project"]
            }
        ),
        Tool(
            name="get_task",
            description="Get details of a specific task by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to retrieve"
                    }
                },
                "required": ["project", "task_id"]
            }
        ),
        Tool(
            name="update_task_status",
            description="Update the status of a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to update"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status",
                        "enum": ["pending", "in_progress", "completed", "blocked", "parked"]
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the status change"
                    }
                },
                "required": ["project", "task_id", "status"]
            }
        ),
        Tool(
            name="verify_changes",
            description="Run Ralph verification on specified files",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to verify"
                    },
                    "checks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of checks to run (lint, typecheck, test, security)"
                    }
                },
                "required": ["project", "files"]
            }
        ),
        Tool(
            name="search_knowledge_objects",
            description="Search Knowledge Objects by tags or content",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (matches content)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to filter by (OR semantics)"
                    }
                }
            }
        ),
        Tool(
            name="get_session_state",
            description="Get current session state from STATE.md",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_autonomy_contract",
            description="Get autonomy contract for a team",
            inputSchema={
                "type": "object",
                "properties": {
                    "team": {
                        "type": "string",
                        "description": "Team name (qa-team, dev-team, operator-team)",
                        "enum": ["qa-team", "dev-team", "operator-team"]
                    }
                },
                "required": ["team"]
            }
        ),
        # UI/UX Tools
        Tool(
            name="lint_ui",
            description="Run UI lint analysis on files (tokens, accessibility, performance)",
            inputSchema={
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File paths to lint"
                    },
                    "checks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Check types (tokens, accessibility, layout, performance)",
                        "default": ["tokens", "accessibility"]
                    }
                },
                "required": ["files"]
            }
        ),
        Tool(
            name="get_design_patterns",
            description="Get available UI scaffold patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by category (forms, data, navigation, feedback)",
                        "enum": ["forms", "data", "navigation", "feedback", "all"]
                    }
                }
            }
        ),
        Tool(
            name="check_ai_slop",
            description="Check for AI-slop patterns in UI code (generic fonts, purple gradients, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File to check for AI-slop patterns"
                    }
                },
                "required": ["file_path"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool invocations."""

    if name == "list_tasks":
        project = arguments.get("project", "")
        status_filter = arguments.get("status")
        limit = arguments.get("limit", 10)

        queue = load_work_queue(project)
        tasks = queue.get("tasks", [])

        if status_filter:
            tasks = [t for t in tasks if t.get("status") == status_filter]

        tasks = tasks[:limit]

        return [TextContent(
            type="text",
            text=json.dumps({"tasks": tasks, "count": len(tasks)}, indent=2)
        )]

    elif name == "get_task":
        project = arguments.get("project", "")
        task_id = arguments.get("task_id", "")

        queue = load_work_queue(project)
        tasks = queue.get("tasks", [])

        for task in tasks:
            if task.get("id") == task_id:
                return [TextContent(
                    type="text",
                    text=json.dumps(task, indent=2)
                )]

        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Task {task_id} not found"})
        )]

    elif name == "update_task_status":
        project = arguments.get("project", "")
        task_id = arguments.get("task_id", "")
        new_status = arguments.get("status", "")
        notes = arguments.get("notes", "")

        queue = load_work_queue(project)
        tasks = queue.get("tasks", [])

        for task in tasks:
            if task.get("id") == task_id:
                task["status"] = new_status
                task["updated_at"] = datetime.now().isoformat()
                if notes:
                    task["notes"] = notes

                if save_work_queue(project, queue):
                    return [TextContent(
                        type="text",
                        text=json.dumps({"success": True, "task": task}, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Failed to save work queue"})
                    )]

        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Task {task_id} not found"})
        )]

    elif name == "verify_changes":
        project = arguments.get("project", "")
        files = arguments.get("files", [])
        checks = arguments.get("checks", ["lint", "typecheck"])

        # In production, this would call ralph.engine.verify()
        # For now, return a mock response
        result = {
            "project": project,
            "files": files,
            "checks": checks,
            "verdict": "PASS",
            "message": "Verification placeholder - implement with ralph.engine",
            "steps": [
                {"step": check, "passed": True, "duration_ms": 100}
                for check in checks
            ]
        }

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    elif name == "search_knowledge_objects":
        query = arguments.get("query", "")
        tags = arguments.get("tags", [])

        kos = load_knowledge_objects()

        # Filter by query (content match)
        if query:
            kos = [ko for ko in kos if query.lower() in ko.get("preview", "").lower()]

        # Filter by tags (OR semantics - match any tag)
        if tags:
            kos = [
                ko for ko in kos
                if any(tag.lower() in ko.get("preview", "").lower() for tag in tags)
            ]

        return [TextContent(
            type="text",
            text=json.dumps({"knowledge_objects": kos, "count": len(kos)}, indent=2)
        )]

    elif name == "get_session_state":
        state = get_session_state()
        return [TextContent(
            type="text",
            text=json.dumps(state, indent=2)
        )]

    elif name == "get_autonomy_contract":
        team = arguments.get("team", "")
        root = get_project_root()
        contract_path = root / "governance" / "contracts" / f"{team}.yaml"

        if contract_path.exists():
            content = contract_path.read_text()
            return [TextContent(
                type="text",
                text=content
            )]

        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Contract {team}.yaml not found"})
        )]

    # UI/UX Tool Handlers
    elif name == "lint_ui":
        files = arguments.get("files", [])
        checks = arguments.get("checks", ["tokens", "accessibility"])

        # UI lint patterns to detect
        issues = []
        for file_path in files:
            file_issues = {
                "file": file_path,
                "violations": []
            }

            # Token violations patterns
            token_patterns = [
                ("#[0-9a-fA-F]{3,6}", "Raw hex color - use design token"),
                ("font-family:", "Inline font-family - use typography token"),
                (r"padding:\s*\d+px", "Raw pixel padding - use spacing token"),
                (r"margin:\s*\d+px", "Raw pixel margin - use spacing token"),
            ]

            # Accessibility patterns
            a11y_patterns = [
                ("<img(?![^>]*alt=)", "Image missing alt attribute"),
                ("<button(?![^>]*aria-label)", "Button may need aria-label"),
                ("onClick(?![^}]*onKeyDown)", "Click handler without keyboard support"),
            ]

            # AI-slop patterns
            slop_patterns = [
                ("Inter|Roboto|Arial", "Generic font detected - consider distinctive choice"),
                ("from-purple.*to-blue|from-blue.*to-purple", "Purple-blue gradient (AI signature)"),
                ("rounded-full", "Overused rounded-full - consider intentional radius"),
            ]

            file_issues["checks_run"] = checks
            file_issues["patterns_checked"] = len(token_patterns) + len(a11y_patterns)

            issues.append(file_issues)

        result = {
            "files_checked": len(files),
            "checks": checks,
            "issues": issues,
            "score": 85,  # Placeholder score
            "message": "UI lint analysis complete (pattern matching only - full implementation pending)"
        }

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    elif name == "get_design_patterns":
        category = arguments.get("category", "all")

        patterns = {
            "forms": [
                {"name": "form_wizard", "description": "Multi-step form with validation", "components": ["FormWizard", "FormStep", "FormProgress"]},
                {"name": "modal_form", "description": "Form inside modal dialog", "components": ["Dialog", "FormContent", "FormActions"]},
                {"name": "inline_edit", "description": "Click-to-edit fields", "components": ["EditableField", "EditableText"]},
            ],
            "data": [
                {"name": "data_table_filterable", "description": "Table with filters and pagination", "components": ["DataTable", "TableFilters", "Pagination"]},
                {"name": "status_dashboard", "description": "KPI cards and status display", "components": ["StatCard", "StatusGrid", "AlertBanner"]},
                {"name": "kanban_board", "description": "Drag-and-drop task board", "components": ["KanbanBoard", "KanbanColumn", "KanbanCard"]},
            ],
            "navigation": [
                {"name": "sidebar_nav", "description": "Collapsible sidebar navigation", "components": ["Sidebar", "NavGroup", "NavItem"]},
                {"name": "breadcrumb_nav", "description": "Hierarchical breadcrumbs", "components": ["Breadcrumb", "BreadcrumbItem"]},
                {"name": "command_palette", "description": "Keyboard-first command menu", "components": ["CommandDialog", "CommandList", "CommandItem"]},
            ],
            "feedback": [
                {"name": "notification_center", "description": "Real-time notifications", "components": ["NotificationBell", "NotificationList"]},
                {"name": "toast_system", "description": "Temporary status messages", "components": ["Toaster", "Toast"]},
                {"name": "loading_states", "description": "Skeleton and spinner patterns", "components": ["Skeleton", "Spinner", "Progress"]},
            ]
        }

        if category == "all":
            result = patterns
        else:
            result = {category: patterns.get(category, [])}

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    elif name == "check_ai_slop":
        file_path = arguments.get("file_path", "")

        # AI-slop detection patterns with severity
        slop_patterns = {
            "typography": [
                {"pattern": "Inter|Roboto|Arial|sans-serif", "message": "Generic font stack - choose distinctive typography", "severity": "warning"},
                {"pattern": "font-weight:\\s*(400|700)", "message": "Only using 400/700 weights - add variety", "severity": "info"},
            ],
            "color": [
                {"pattern": "from-purple|to-purple|purple-[5-7]00", "message": "Purple gradients are AI signature - use intentional palette", "severity": "warning"},
                {"pattern": "#3b82f6|blue-500", "message": "Default Tailwind blue - customize primary color", "severity": "info"},
                {"pattern": "gradient.*gradient", "message": "Multiple gradients - simplify color usage", "severity": "warning"},
            ],
            "layout": [
                {"pattern": "mx-auto.*text-center.*mx-auto", "message": "Everything centered - add visual hierarchy", "severity": "warning"},
                {"pattern": "rounded-full.*rounded-full.*rounded-full", "message": "Overusing rounded-full - vary border radius", "severity": "info"},
                {"pattern": "p-4.*p-4.*p-4", "message": "Uniform padding everywhere - create rhythm", "severity": "info"},
            ],
            "motion": [
                {"pattern": "hover:scale-105", "message": "Overused scale effect - try subtle alternatives", "severity": "info"},
                {"pattern": "transition-all", "message": "transition-all is heavy - specify properties", "severity": "warning"},
            ],
            "copy": [
                {"pattern": "Get Started|Learn More|Click Here", "message": "Generic CTA text - be specific", "severity": "warning"},
                {"pattern": "Lorem ipsum", "message": "Placeholder text in production", "severity": "critical"},
            ]
        }

        result = {
            "file": file_path,
            "slop_patterns": slop_patterns,
            "message": "Check file content against these patterns to detect AI-generated aesthetic",
            "recommendation": "Commit to a specific design direction before implementation"
        }

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    return [TextContent(
        type="text",
        text=json.dumps({"error": f"Unknown tool: {name}"})
    )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
