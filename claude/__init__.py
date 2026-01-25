"""
Claude Code CLI integration module

Provides clean Python interface to Claude Code CLI with:
- Error handling
- Timeout management
- Output parsing
- Session management
- Smart prompt generation
- Authentication (API key and OAuth)
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
from .auth_config import (
    AuthConfig,
    get_auth_config,
    get_anthropic_client,
    get_async_anthropic_client,
    configure_oauth,
    configure_api_key,
    save_auth_config,
    print_auth_status,
)

__all__ = [
    # CLI Wrapper
    "ClaudeCliWrapper",
    "ClaudeResult",
    # Prompts
    "generate_bugfix_prompt",
    "generate_quality_prompt",
    "generate_feature_prompt",
    "generate_smart_prompt",
    "detect_task_type",
    "detect_quality_issue_type",
    # Authentication
    "AuthConfig",
    "get_auth_config",
    "get_anthropic_client",
    "get_async_anthropic_client",
    "configure_oauth",
    "configure_api_key",
    "save_auth_config",
    "print_auth_status",
]
