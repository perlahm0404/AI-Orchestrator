"""
Knowledge Object System Configuration

Centralized configuration for KO system behavior.

Settings can be customized per-project or globally.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json


@dataclass
class KOConfig:
    """Configuration for Knowledge Object system."""

    # Auto-approval thresholds
    auto_approve_enabled: bool = True
    auto_approve_min_iterations: int = 2  # Minimum iterations for auto-approval
    auto_approve_max_iterations: int = 10  # Maximum iterations for auto-approval
    auto_approve_require_pass: bool = True  # Only auto-approve PASS verdicts

    # Cache settings
    cache_expiry_seconds: int = 300  # 5 minutes

    # Consultation settings
    min_tags_for_match: int = 1  # Minimum matching tags (1 = OR semantics)

    # Metrics settings
    metrics_enabled: bool = True

    @classmethod
    def load(cls, project_name: Optional[str] = None) -> 'KOConfig':
        """
        Load configuration from file or use defaults.

        Priority:
        1. Project-specific config: knowledge/config/{project_name}.json
        2. Global config: knowledge/config/global.json
        3. Default values

        Args:
            project_name: Optional project name for project-specific config

        Returns:
            KOConfig instance
        """
        config_dir = Path(__file__).parent / "config"

        # Try project-specific config first
        if project_name:
            project_config_file = config_dir / f"{project_name}.json"
            if project_config_file.exists():
                return cls._load_from_file(project_config_file)

        # Try global config
        global_config_file = config_dir / "global.json"
        if global_config_file.exists():
            return cls._load_from_file(global_config_file)

        # Use defaults
        return cls()

    @classmethod
    def _load_from_file(cls, config_file: Path) -> 'KOConfig':
        """Load config from JSON file."""
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
                return cls(**data)
        except (json.JSONDecodeError, FileNotFoundError, TypeError):
            # Fallback to defaults on error
            return cls()

    def save(self, project_name: Optional[str] = None):
        """
        Save configuration to file.

        Args:
            project_name: Optional project name (saves to project-specific config)
                         If None, saves to global config
        """
        config_dir = Path(__file__).parent / "config"
        config_dir.mkdir(exist_ok=True)

        if project_name:
            config_file = config_dir / f"{project_name}.json"
        else:
            config_file = config_dir / "global.json"

        data = {
            'auto_approve_enabled': self.auto_approve_enabled,
            'auto_approve_min_iterations': self.auto_approve_min_iterations,
            'auto_approve_max_iterations': self.auto_approve_max_iterations,
            'auto_approve_require_pass': self.auto_approve_require_pass,
            'cache_expiry_seconds': self.cache_expiry_seconds,
            'min_tags_for_match': self.min_tags_for_match,
            'metrics_enabled': self.metrics_enabled
        }

        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)


# Global default config (can be overridden)
_default_config = KOConfig()


def get_config(project_name: Optional[str] = None) -> KOConfig:
    """
    Get configuration for KO system.

    Args:
        project_name: Optional project name

    Returns:
        KOConfig instance
    """
    return KOConfig.load(project_name)


def set_default_config(config: KOConfig):
    """
    Set global default configuration.

    Args:
        config: KOConfig instance to use as default
    """
    global _default_config
    _default_config = config
