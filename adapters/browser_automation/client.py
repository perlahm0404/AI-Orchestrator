"""
Python client for browser automation package.

Spawns Node.js process and communicates via JSON over stdin/stdout.
"""

import subprocess
import json
from pathlib import Path
from typing import Any, Dict, Optional


class BrowserAutomationClient:
    """
    Client for browser automation TypeScript package.

    Usage:
        client = BrowserAutomationClient()
        session_id = client.create_session({
            "sessionId": "my-session",
            "auditLogPath": "/tmp/audit.jsonl"
        })

        result = client.extract_license_info(
            session_id=session_id,
            adapter="california-medical-board",
            license_number="A12345"
        )

        client.cleanup_session(session_id)
    """

    def __init__(self, package_path: Optional[str] = None):
        """
        Initialize browser automation client.

        Args:
            package_path: Path to browser-automation package.
                         Defaults to packages/browser-automation relative to this file.
        """
        if package_path is None:
            # Default: packages/browser-automation relative to repo root
            this_dir = Path(__file__).parent
            repo_root = this_dir.parent.parent
            package_path = str(repo_root / "packages" / "browser-automation")

        self.package_path = Path(package_path)
        self.cli_path = self.package_path / "dist" / "index.js"

        if not self.cli_path.exists():
            raise RuntimeError(
                f"Browser automation CLI not found at {self.cli_path}. "
                f"Run: cd {self.package_path} && npm run build"
            )

    def _execute_command(self, command: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute command via Node.js subprocess.

        Args:
            command: Command name (e.g., "create-session")
            **kwargs: Command parameters

        Returns:
            Command result as dict

        Raises:
            RuntimeError: If command fails
        """
        cmd = ["node", str(self.cli_path)]

        # Add command and params to JSON
        input_data = {"command": command, **kwargs}
        input_json = json.dumps(input_data)

        # Execute subprocess
        proc_result = subprocess.run(
            cmd,
            input=input_json,
            capture_output=True,
            text=True,
            check=False,
        )

        # Parse output
        try:
            output = json.loads(proc_result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Failed to parse output: {proc_result.stdout}\n"
                f"Stderr: {proc_result.stderr}"
            ) from e

        # Check for errors
        if not output.get("success"):
            error = output.get("error", "Unknown error")
            raise RuntimeError(f"Command failed: {error}")

        result: Dict[str, Any] = output.get("result", {})
        return result

    def create_session(self, config: Dict[str, Any]) -> str:
        """
        Create browser session.

        Args:
            config: Session configuration with keys:
                   - sessionId (str, required)
                   - auditLogPath (str, optional)
                   - credentialVaultPath (str, optional)
                   - screenshotDir (str, optional)
                   - maxSessionDuration (int, optional)
                   - headless (bool, optional)

        Returns:
            Session ID

        Example:
            session_id = client.create_session({
                "sessionId": "test-session",
                "headless": True
            })
        """
        result = self._execute_command("create-session", **config)
        session_id: str = result["sessionId"]
        return session_id

    def extract_license_info(
        self,
        session_id: str,
        adapter: str,
        license_number: str,
        credential: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extract license info using adapter.

        Args:
            session_id: Active session ID
            adapter: Adapter name (e.g., "california-medical-board")
            license_number: License number to lookup
            credential: Optional credential for login

        Returns:
            License information dict

        Example:
            info = client.extract_license_info(
                session_id="test",
                adapter="california-medical-board",
                license_number="A12345"
            )
        """
        params: Dict[str, Any] = {
            "sessionId": session_id,
            "adapter": adapter,
            "licenseNumber": license_number,
        }

        if credential:
            params["credential"] = credential

        return self._execute_command("extract-license-info", **params)

    def cleanup_session(self, session_id: str) -> None:
        """
        Cleanup browser session.

        Args:
            session_id: Session ID to cleanup

        Example:
            client.cleanup_session("test-session")
        """
        self._execute_command("cleanup-session", sessionId=session_id)
