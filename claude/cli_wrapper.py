"""
Claude Code CLI Wrapper - Subprocess interface to claude command

Provides clean Python interface to Claude Code CLI with:
- Error handling
- Timeout management
- Output parsing
- Session management
"""

import os
import selectors
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
        timeout: int = 300,  # 5 minutes
        allow_dangerous_permissions: Optional[bool] = None
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

        # Add flags for automation (opt-in)
        if self._allow_dangerous_permissions(allow_dangerous_permissions):
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
            # Execute with streaming output for real-time visibility
            process = subprocess.Popen(
                cmd,
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                bufsize=0
            )

            # Stream output in real-time without blocking on newline flush
            output_chunks: list[bytes] = []
            error_chunks: list[bytes] = []

            import sys
            selector = selectors.DefaultSelector()
            if process.stdout:
                selector.register(process.stdout, selectors.EVENT_READ, data="stdout")
            if process.stderr:
                selector.register(process.stderr, selectors.EVENT_READ, data="stderr")

            start_time = time.time()
            timed_out = False
            while selector.get_map():
                if time.time() - start_time > timeout:
                    process.kill()
                    try:
                        process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        pass
                    timed_out = True
                    break

                events = selector.select(timeout=0.1)
                if not events:
                    if process.poll() is not None:
                        break
                    continue

                for key, _ in events:
                    fileobj = key.fileobj
                    fd = fileobj if isinstance(fileobj, int) else fileobj.fileno()
                    data = os.read(fd, 4096)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue

                    text = data.decode(errors="replace")
                    if key.data == "stdout":
                        print(text, end="", flush=True)
                        output_chunks.append(data)
                    else:
                        print(text, end="", file=sys.stderr, flush=True)
                        error_chunks.append(data)

            duration = int((time.time() - start) * 1000)
            output = b"".join(output_chunks).decode(errors="replace")
            error = b"".join(error_chunks).decode(errors="replace") if error_chunks else None

            # Parse output
            files_changed = self._parse_changed_files(output)

            if timed_out:
                return ClaudeResult(
                    success=False,
                    output=output,
                    error=f"Timeout after {timeout} seconds",
                    duration_ms=duration
                )

            returncode = process.poll()
            if returncode == 0:
                return ClaudeResult(
                    success=True,
                    output=output,
                    files_changed=files_changed,
                    duration_ms=duration
                )
            else:
                return ClaudeResult(
                    success=False,
                    output=output,
                    error=error,
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
        result: Optional[ClaudeResult] = None

        for _ in range(max_retries):
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

        # Return last result or error if no retries attempted
        if result is None:
            return ClaudeResult(success=False, output="", error="No retries attempted (max_retries=0)")
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
    def _allow_dangerous_permissions(override: Optional[bool]) -> bool:
        if override is not None:
            return override
        env_value = os.environ.get("AI_ORCHESTRATOR_CLAUDE_SKIP_PERMISSIONS", "")
        return env_value.strip().lower() in ("1", "true", "yes")

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
