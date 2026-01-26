# OAuth API Authentication Research

**Date**: 2025-01-25
**Status**: Complete
**Topic**: Claude OAuth tokens and API access

## Problem Statement

When testing API calls with the OAuth token from `~/.claude/.credentials.json`, we received:
```
anthropic.AuthenticationError: Error code: 401 - {'type': 'error', 'error':
{'type': 'authentication_error', 'message': 'OAuth authentication is currently not supported.'}}
```

The OAuth token (`sk-ant-oat01-...`) is for Claude.ai web interface only - the Anthropic Messages API requires an API key (`sk-ant-api03-...`).

## Key Finding: Intentional Restriction

**As of January 2026, Anthropic intentionally blocks OAuth tokens from being used for direct API calls.**

### Why This Was Done
- OAuth tokens from Claude Pro/Max subscriptions ($200/month) provided unlimited token usage
- Third-party tools were using these tokens to access the API, bypassing per-token pricing
- Anthropic deployed technical safeguards on January 9, 2026 to close this arbitrage

### Token Types
| Token Type | Prefix | Purpose |
|------------|--------|---------|
| OAuth Access Token | `sk-ant-oat01-` | Claude.ai web, Claude Code only |
| OAuth Refresh Token | `sk-ant-ort01-` | Refresh access tokens |
| API Key | `sk-ant-api03-` | Direct API calls via SDK |

## Solutions

### Option 1: Use API Key (Recommended for SDK calls)
```bash
# Get from https://console.anthropic.com/api-keys
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

This works with:
- `anthropic.Anthropic()` SDK
- REST API calls
- Any third-party tools

### Option 2: Use Claude Code CLI
```bash
# This uses OAuth tokens internally
claude "Your prompt here"
```

Claude Code handles OAuth authentication internally - you don't need to manage tokens.

### Option 3: Use Claude Agent SDK
```python
from claude_agent_sdk import query, ClaudeAgentOptions

# SDK still requires API key (ANTHROPIC_API_KEY env var)
async for msg in query(prompt="...", options=ClaudeAgentOptions(...)):
    ...
```

**Note**: Despite using the "Claude Code" branding, the Agent SDK still requires an API key, not OAuth tokens.

## Files Updated

1. **claude/auth_config.py** - Updated docstring to explain OAuth limitations
2. **claude/sdk_adapter.py** - Updated to:
   - Use correct package name (`claude-agent-sdk`)
   - Use correct class name (`ClaudeAgentOptions`)
   - Add explicit API key check with helpful error message

## OAuth Token Scopes (Reference)

The token in `~/.claude/.credentials.json` has these scopes:
- `user:inference` - API inference calls (blocked for external use)
- `user:profile` - User profile access
- `user:sessions:claude_code` - Claude Code session management

Despite having `user:inference` scope, external API access is blocked by Anthropic's technical controls.

## Recommendations

For AI Orchestrator:
1. **Require API key** for direct SDK/API usage
2. **Use Claude Code CLI** via subprocess for tasks that benefit from OAuth/subscription
3. **Document clearly** that OAuth tokens won't work

## Sources

- [GitHub Issue #6058](https://github.com/anthropics/claude-code/issues/6058) - OAuth authentication error
- [AI Checker Article](https://ai-checker.webcoda.com.au/articles/anthropic-blocks-claude-code-subscriptions-third-party-tools-2026)
- [Claude Agent SDK Docs](https://platform.claude.com/docs/en/agent-sdk/overview)
