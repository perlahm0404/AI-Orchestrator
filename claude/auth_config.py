"""
Claude Authentication Configuration

Supports multiple authentication methods for Claude API access:
1. API Key (ANTHROPIC_API_KEY) - Direct API access
2. OAuth Token (ANTHROPIC_AUTH_TOKEN) - Claude.ai OAuth access
3. OAuth Client Credentials - For programmatic OAuth flow

OAuth Setup for Claude.ai:
1. Get OAuth token from Claude.ai settings
2. Set ANTHROPIC_AUTH_TOKEN environment variable
   Or configure in ~/.config/ai-orchestrator/auth.yaml

Usage:
    from claude.auth_config import get_anthropic_client, AuthConfig

    # Auto-detect authentication method
    client = get_anthropic_client()

    # Or explicitly configure
    config = AuthConfig(auth_token="your-oauth-token")
    client = config.create_client()
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
import json


@dataclass
class AuthConfig:
    """
    Authentication configuration for Anthropic Claude API.

    Supports:
    - api_key: Direct API key authentication
    - auth_token: OAuth access token (from claude.ai)
    - oauth_client_id/secret: For programmatic OAuth flows

    Priority order:
    1. Explicit parameters
    2. Environment variables
    3. Config file (~/.config/ai-orchestrator/auth.yaml)
    """
    api_key: Optional[str] = None
    auth_token: Optional[str] = None
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    base_url: Optional[str] = None  # Custom API endpoint

    # OAuth settings
    oauth_redirect_uri: str = "http://localhost:8080/callback"
    oauth_scopes: list = field(default_factory=lambda: ["read", "write"])

    def __post_init__(self):
        """Load from environment if not explicitly set."""
        if self.api_key is None:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")

        if self.auth_token is None:
            self.auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")

        if self.oauth_client_id is None:
            self.oauth_client_id = os.environ.get("ANTHROPIC_OAUTH_CLIENT_ID")

        if self.oauth_client_secret is None:
            self.oauth_client_secret = os.environ.get("ANTHROPIC_OAUTH_CLIENT_SECRET")

        if self.base_url is None:
            self.base_url = os.environ.get("ANTHROPIC_BASE_URL")

        # Try loading from config file if still not set
        if not self.api_key and not self.auth_token:
            self._load_from_config_file()

    def _load_from_config_file(self) -> None:
        """Load credentials from config file."""
        # First, try Claude Code's credentials (OAuth from claude.ai)
        claude_creds = Path.home() / ".claude" / ".credentials.json"
        if claude_creds.exists():
            try:
                content = claude_creds.read_text()
                creds = json.loads(content)
                if "claudeAiOauth" in creds:
                    oauth = creds["claudeAiOauth"]
                    if "accessToken" in oauth:
                        self.auth_token = oauth["accessToken"]
                        return  # Found OAuth token, done
            except Exception:
                pass

        # Fallback to other config files
        config_paths = [
            Path.home() / ".config" / "ai-orchestrator" / "auth.yaml",
            Path.home() / ".config" / "ai-orchestrator" / "auth.json",
            Path.home() / ".anthropic" / "credentials",
        ]

        for path in config_paths:
            if path.exists():
                try:
                    content = path.read_text()
                    if path.suffix == ".yaml":
                        import yaml
                        config = yaml.safe_load(content)
                    else:
                        config = json.loads(content)

                    self.api_key = config.get("api_key", self.api_key)
                    self.auth_token = config.get("auth_token", self.auth_token)
                    self.oauth_client_id = config.get("oauth_client_id", self.oauth_client_id)
                    self.oauth_client_secret = config.get("oauth_client_secret", self.oauth_client_secret)
                    break
                except Exception:
                    continue

    @property
    def auth_method(self) -> str:
        """Determine which authentication method is configured."""
        if self.auth_token:
            return "oauth"
        elif self.api_key:
            return "api_key"
        elif self.oauth_client_id and self.oauth_client_secret:
            return "oauth_client"
        else:
            return "none"

    @property
    def is_configured(self) -> bool:
        """Check if any authentication is configured."""
        return self.auth_method != "none"

    def create_client(self, **kwargs) -> Any:
        """
        Create an Anthropic client with configured authentication.

        Note: The Anthropic API requires an API key. OAuth tokens from
        Claude.ai are for the web interface only and won't work with
        the API.

        Args:
            **kwargs: Additional arguments to pass to the Anthropic client

        Returns:
            anthropic.Anthropic client instance

        Raises:
            ImportError: If anthropic package not installed
            ValueError: If no API key configured
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        # API key is required for API access
        # OAuth tokens from claude.ai don't work with the API
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. OAuth tokens from Claude.ai "
                "don't work with the API.\n\n"
                "Get an API key from: https://console.anthropic.com/\n"
                "Then set: ANTHROPIC_API_KEY=sk-ant-api03-..."
            )

        client_kwargs = {"api_key": self.api_key}

        # Set base URL if configured
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        # Merge additional kwargs
        client_kwargs.update(kwargs)

        return anthropic.Anthropic(**client_kwargs)

    def create_async_client(self, **kwargs) -> Any:
        """
        Create an async Anthropic client with configured authentication.

        Returns:
            anthropic.AsyncAnthropic client instance
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. OAuth tokens from Claude.ai "
                "don't work with the API.\n\n"
                "Get an API key from: https://console.anthropic.com/\n"
                "Then set: ANTHROPIC_API_KEY=sk-ant-api03-..."
            )

        client_kwargs = {"api_key": self.api_key}

        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        client_kwargs.update(kwargs)

        return anthropic.AsyncAnthropic(**client_kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excludes secrets)."""
        return {
            "auth_method": self.auth_method,
            "is_configured": self.is_configured,
            "has_api_key": bool(self.api_key),
            "has_auth_token": bool(self.auth_token),
            "has_oauth_client": bool(self.oauth_client_id),
            "base_url": self.base_url,
        }


# Global config instance (lazy initialized)
_global_config: Optional[AuthConfig] = None


def get_auth_config() -> AuthConfig:
    """
    Get the global authentication configuration.

    Creates a new AuthConfig if not already initialized.
    Loads from environment variables and config files.
    """
    global _global_config
    if _global_config is None:
        _global_config = AuthConfig()
    return _global_config


def get_anthropic_client(**kwargs) -> Any:
    """
    Get an Anthropic client with auto-detected authentication.

    This is the recommended way to get a client instance.
    Supports both API key and OAuth authentication.

    Args:
        **kwargs: Additional arguments for the client

    Returns:
        anthropic.Anthropic client instance

    Example:
        client = get_anthropic_client()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """
    config = get_auth_config()
    return config.create_client(**kwargs)


def get_async_anthropic_client(**kwargs) -> Any:
    """
    Get an async Anthropic client with auto-detected authentication.

    Returns:
        anthropic.AsyncAnthropic client instance
    """
    config = get_auth_config()
    return config.create_async_client(**kwargs)


def configure_oauth(auth_token: str) -> None:
    """
    Configure OAuth authentication with the given token.

    Args:
        auth_token: OAuth access token from Claude.ai
    """
    global _global_config
    _global_config = AuthConfig(auth_token=auth_token)


def configure_api_key(api_key: str) -> None:
    """
    Configure API key authentication.

    Args:
        api_key: Anthropic API key
    """
    global _global_config
    _global_config = AuthConfig(api_key=api_key)


def save_auth_config(
    auth_token: Optional[str] = None,
    api_key: Optional[str] = None,
    path: Optional[Path] = None
) -> Path:
    """
    Save authentication configuration to file.

    Args:
        auth_token: OAuth token to save
        api_key: API key to save
        path: Custom path (defaults to ~/.config/ai-orchestrator/auth.yaml)

    Returns:
        Path where config was saved
    """
    if path is None:
        path = Path.home() / ".config" / "ai-orchestrator" / "auth.yaml"

    path.parent.mkdir(parents=True, exist_ok=True)

    config = {}
    if auth_token:
        config["auth_token"] = auth_token
    if api_key:
        config["api_key"] = api_key

    try:
        import yaml
        content = yaml.dump(config, default_flow_style=False)
    except ImportError:
        content = json.dumps(config, indent=2)
        path = path.with_suffix(".json")

    path.write_text(content)

    # Set restrictive permissions
    path.chmod(0o600)

    return path


def print_auth_status() -> None:
    """Print current authentication status."""
    config = get_auth_config()
    info = config.to_dict()

    print("Claude Authentication Status:")
    print(f"  Configured: {info['is_configured']}")
    if info['has_api_key']:
        print("  ✓ API Key configured (required for API calls)")
    else:
        print("  ✗ API Key NOT configured")
        print("    Get one from: https://console.anthropic.com/")
        print("    Set: ANTHROPIC_API_KEY=sk-ant-api03-...")
    if info['has_auth_token']:
        print("  ℹ OAuth Token found (Claude.ai web only, not for API)")
    if info['base_url']:
        print(f"  Base URL: {info['base_url']}")


__all__ = [
    "AuthConfig",
    "get_auth_config",
    "get_anthropic_client",
    "get_async_anthropic_client",
    "configure_oauth",
    "configure_api_key",
    "save_auth_config",
    "print_auth_status",
]
