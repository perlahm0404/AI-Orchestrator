#!/usr/bin/env python3
"""
State Sync Utility for Cross-Repo Memory Continuity

Synchronizes STATE.md files across AI_Orchestrator, KareMatch, and CredentialMate
to enable cross-repo context awareness.

Usage:
    from utils.state_sync import sync_state_to_global_cache, pull_global_state

    # On STATE.md update:
    sync_state_to_global_cache('ai_orchestrator')

    # On session start:
    other_states = pull_global_state('ai_orchestrator')
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Repo paths mapping
REPO_MAP = {
    'ai_orchestrator': '/Users/tmac/1_REPOS/AI_Orchestrator',
    'karematch': '/Users/tmac/1_REPOS/karematch',
    'credentialmate': '/Users/tmac/1_REPOS/credentialmate'
}


def sync_state_to_global_cache(current_repo: str) -> None:
    """
    Sync this repo's STATE.md to other repos' global-state-cache.md

    Args:
        current_repo: Name of current repo ('ai_orchestrator', 'karematch', 'credentialmate')
    """
    if current_repo not in REPO_MAP:
        print(f"[state_sync] Unknown repo: {current_repo}")
        return

    state_file = Path(REPO_MAP[current_repo]) / 'STATE.md'

    if not state_file.exists():
        print(f"[state_sync] STATE.md not found in {current_repo}")
        return

    state_content = state_file.read_text()
    timestamp = datetime.now().isoformat()

    # Write to other repos' global cache
    for repo, repo_path in REPO_MAP.items():
        if repo == current_repo:
            continue

        cache_file = Path(repo_path) / '.aibrain' / 'global-state-cache.md'
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Read existing cache
        existing = ""
        if cache_file.exists():
            existing = cache_file.read_text()
            # Remove old section for this repo
            existing = _remove_section(existing, current_repo.upper())

        # Append new section
        new_section = f"""
## {current_repo.upper()} State

**Last Synced**: {timestamp}

{state_content}

---
"""

        # Write merged content
        merged = _merge_cache(existing, new_section)
        cache_file.write_text(merged)

        print(f"[state_sync] Synced {current_repo} STATE.md -> {repo}/.aibrain/global-state-cache.md")


def pull_global_state(current_repo: str) -> Dict[str, str]:
    """
    Read global-state-cache.md and return state from other repos

    Args:
        current_repo: Name of current repo ('ai_orchestrator', 'karematch', 'credentialmate')

    Returns:
        Dict mapping repo names to their state content
    """
    if current_repo not in REPO_MAP:
        return {}

    cache_file = Path(REPO_MAP[current_repo]) / '.aibrain' / 'global-state-cache.md'

    if not cache_file.exists():
        return {}

    cache_content = cache_file.read_text()

    # Parse sections
    states = {}
    for repo in REPO_MAP.keys():
        if repo == current_repo:
            continue
        section = _extract_section(cache_content, repo.upper())
        if section:
            states[repo] = section

    return states


def _remove_section(content: str, section_name: str) -> str:
    """Remove a section from markdown content"""
    lines = content.split('\n')
    result = []
    in_section = False

    for line in lines:
        if line.startswith(f'## {section_name}'):
            in_section = True
            continue
        if in_section and line.startswith('##'):
            in_section = False
        if not in_section:
            result.append(line)

    return '\n'.join(result)


def _extract_section(content: str, section_name: str) -> Optional[str]:
    """Extract a section from markdown content"""
    lines = content.split('\n')
    result = []
    in_section = False

    for line in lines:
        if line.startswith(f'## {section_name}'):
            in_section = True
            continue
        if in_section and line.startswith('##'):
            break
        if in_section:
            result.append(line)

    section_text = '\n'.join(result).strip()
    return section_text if section_text else None


def _merge_cache(existing: str, new_section: str) -> str:
    """Merge new section into existing cache content"""
    # Remove header if present in existing
    lines = existing.split('\n')
    filtered = []
    for line in lines:
        if not line.startswith('# Global State Cache'):
            filtered.append(line)

    existing_clean = '\n'.join(filtered).strip()

    # Build full cache
    header = f"""# Global State Cache

**Purpose**: Cached state from other repos for cross-repo context awareness.

**Last Updated**: {datetime.now().isoformat()}

---
"""

    return header + new_section + '\n' + existing_clean


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python state_sync.py <sync|pull> <repo_name>")
        print("  sync: Sync this repo's STATE.md to others")
        print("  pull: Pull state from other repos")
        print("  repo_name: ai_orchestrator | karematch | credentialmate")
        sys.exit(1)

    action = sys.argv[1]
    repo = sys.argv[2]

    if action == 'sync':
        sync_state_to_global_cache(repo)
    elif action == 'pull':
        states = pull_global_state(repo)
        for repo_name, state in states.items():
            print(f"\n{'='*60}")
            print(f"{repo_name.upper()} STATE:")
            print(f"{'='*60}")
            print(state[:500] + '...' if len(state) > 500 else state)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
