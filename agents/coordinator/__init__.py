"""
Coordinator Agent Package
Version: 3.0
Part of: AI Team (AI-TEAM-SPEC-V3)
"""

from .coordinator import Coordinator, CoordinatorConfig
from .task_manager import TaskManager, Task, TaskStatus, TaskType
from .project_hq import ProjectHQManager
from .handoff import HandoffGenerator

__all__ = [
    "Coordinator",
    "CoordinatorConfig",
    "TaskManager",
    "Task",
    "TaskStatus",
    "TaskType",
    "ProjectHQManager",
    "HandoffGenerator",
]
