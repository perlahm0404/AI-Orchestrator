"""
Claude Code CLI integration module

Provides clean Python interface to Claude Code CLI with:
- Error handling
- Timeout management
- Output parsing
- Session management
- Smart prompt generation
"""

from .cli_wrapper import ClaudeCliWrapper, ClaudeResult
from .prompts import (
    generate_bugfix_prompt,
    generate_quality_prompt,
    generate_feature_prompt,
    generate_smart_prompt,
    detect_task_type,
    detect_quality_issue_type
)

__all__ = [
    "ClaudeCliWrapper",
    "ClaudeResult",
    "generate_bugfix_prompt",
    "generate_quality_prompt",
    "generate_feature_prompt",
    "generate_smart_prompt",
    "detect_task_type",
    "detect_quality_issue_type"
]
