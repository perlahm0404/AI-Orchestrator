"""
Claude Code CLI Wrapper - Subprocess interface to claude command

Provides clean Python interface to Claude Code CLI with:
- Error handling
- Timeout management
- Output parsing
- Session management
"""

import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List
import time


@dataclass
class ClaudeResult:
    """Result from Claude Code CLI execution"""
    success: bool
    output: str
    error: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)
    duration_ms: int = 0


class ClaudeError(Exception):
    """Base exception for Claude CLI errors"""
    pass


class ClaudeTimeoutError(ClaudeError):
    """Raised when Claude CLI times out"""
    pass


class ClaudeAuthError(ClaudeError):
    """Raised when Claude CLI auth fails"""
    pass


class ClaudeNotInstalledError(ClaudeError):
    """Raised when Claude CLI is not installed"""
    pass


class ClaudeCliWrapper:
    """Wrapper for Claude Code CLI subprocess calls"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def execute_task(
        self,
        prompt: str,
        files: Optional[List[str]] = None,
        timeout: int = 300  # 5 minutes
    ) -> ClaudeResult:
        """
        Execute a task via Claude Code CLI

        Args:
            prompt: Task description
            files: Optional list of files to focus on
            timeout: Max execution time in seconds

        Returns:
            ClaudeResult with execution details
        """
        start = time.time()

        # Build command
        cmd = ["claude"]

        # Add print mode for non-interactive execution (runs in background)
        cmd.append("--print")

        # Add flags for automation
        cmd.append("--dangerously-skip-permissions")

        # ENABLE session persistence so sessions can be viewed in UI later
        # Sessions will be saved to ~/.claude/sessions/
        # You can view them with: claude sessions list
        # cmd.append("--no-session-persistence")  # Commented out to enable sessions

        # Add files if specified (as context via system prompt)
        if files:
            file_context = "\n\nFocus on these files:\n" + "\n".join(f"- {f}" for f in files)
            prompt = prompt + file_context

        # Add prompt as final argument
        cmd.append(prompt)

        try:
            # Execute
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            duration = int((time.time() - start) * 1000)

            # Parse output
            files_changed = self._parse_changed_files(result.stdout)

            if result.returncode == 0:
                return ClaudeResult(
                    success=True,
                    output=result.stdout,
                    files_changed=files_changed,
                    duration_ms=duration
                )
            else:
                return ClaudeResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr,
                    duration_ms=duration
                )

        except subprocess.TimeoutExpired:
            duration = int((time.time() - start) * 1000)
            return ClaudeResult(
                success=False,
                output="",
                error=f"Timeout after {timeout} seconds",
                duration_ms=duration
            )
        except FileNotFoundError:
            duration = int((time.time() - start) * 1000)
            return ClaudeResult(
                success=False,
                output="",
                error="Claude CLI not found in PATH - is it installed?",
                duration_ms=duration
            )
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            return ClaudeResult(
                success=False,
                output="",
                error=str(e),
                duration_ms=duration
            )

    def execute_task_with_retry(
        self,
        prompt: str,
        files: Optional[List[str]] = None,
        max_retries: int = 3
    ) -> ClaudeResult:
        """Execute task with automatic retry on transient failures"""

        for attempt in range(max_retries):
            result = self.execute_task(prompt, files)

            if result.success:
                return result

            # Check if error is retryable
            if result.error and "timeout" in result.error.lower():
                # Retryable - try again with longer timeout
                continue
            elif result.error and "rate limit" in result.error.lower():
                # Retryable - wait and retry
                time.sleep(60)
                continue
            else:
                # Non-retryable - fail fast
                return result

        return result

    def _parse_changed_files(self, output: str) -> List[str]:
        """
        Parse changed files from Claude output

        Look for patterns like:
        - "Modified: src/foo.ts"
        - "Created: src/bar.ts"
        - "Updated: src/baz.ts"
        """
        files = []
        for line in output.split('\n'):
            line_stripped = line.strip()
            if line_stripped.startswith(('Modified:', 'Created:', 'Updated:')):
                # Extract filename
                parts = line_stripped.split(':', 1)
                if len(parts) == 2:
                    files.append(parts[1].strip())
        return files

    @staticmethod
    def check_cli_available() -> bool:
        """
        Check if Claude CLI is installed and authenticated

        Returns:
            True if CLI is ready to use

        Raises:
            ClaudeNotInstalledError: If CLI is not installed
            ClaudeAuthError: If CLI is not authenticated
        """
        try:
            # Check if CLI is installed
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise ClaudeNotInstalledError("Claude CLI not installed")

            # Check auth status
            result = subprocess.run(
                ["claude", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "authenticated" not in result.stdout.lower():
                raise ClaudeAuthError(
                    "Claude CLI not authenticated. Run: claude auth login"
                )

            return True

        except FileNotFoundError:
            raise ClaudeNotInstalledError(
                "Claude CLI not found in PATH. Install from: https://claude.com/code"
            )
        except subprocess.TimeoutExpired:
            raise ClaudeError("Claude CLI command timed out")
