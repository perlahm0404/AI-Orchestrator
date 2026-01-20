# Browser Automation Agent

Autonomous agent for HIPAA-compliant credentialing portal verification using browser automation.

## Overview

The BrowserAutomationAgent provides autonomous license verification capabilities across multiple credentialing portals (state medical boards, DEA, CME providers). It integrates with Wiggum for iteration control and Ralph for data validation.

**Autonomy Level**: L2 (Code + Schema)

## Features

- **Browser Automation**: Playwright-based navigation and extraction
- **HIPAA Compliance**: Encrypted credentials, audit trails, PHI scrubbing
- **Retry Logic**: Automatic retry with exponential backoff (Wiggum integration)
- **Data Validation**: Ralph-based validation of extracted data
- **Multi-Portal Support**: Extensible adapter pattern for different portals

## Usage

### From Python

```python
from agents.browser_automation import BrowserAutomationAgent
from agents.base import AgentConfig
from adapters import get_adapter

# Get project adapter
adapter = get_adapter("karematch")

# Create agent config
config = AgentConfig(
    project_name="karematch",
    agent_name="browser_automation",
    expected_completion_signal="VERIFICATION_COMPLETE",
    max_iterations=5
)

# Initialize agent
agent = BrowserAutomationAgent(adapter, config)

# Execute verification task
result = agent.execute("verify-license-california-medical-board-A12345")

print(f"Status: {result['status']}")
print(f"Output: {result['output']}")
print(f"Evidence: {result['evidence']}")
```

### With Wiggum (Iteration Loop)

```python
from orchestration.iteration_loop import IterationLoop
from agents.browser_automation import BrowserAutomationAgent
from adapters import get_adapter

adapter = get_adapter("karematch")
agent = BrowserAutomationAgent(adapter)

loop = IterationLoop(agent, adapter.get_context())

result = loop.run(
    task_id="verify-license-california-medical-board-A12345",
    task_description="Verify medical license A12345 via CA Medical Board",
    max_iterations=5
)

print(f"Completed in {result.iterations} iterations")
print(f"Final status: {result.status}")
```

## Task Format

Tasks must follow this format:

```
verify-license-<adapter-name>-<license-number>
```

**Examples**:
- `verify-license-california-medical-board-A12345`
- `verify-license-texas-medical-board-TX67890`
- `verify-license-dea-DEA123456`

**Parts**:
1. `verify-license`: Fixed prefix
2. `<adapter-name>`: Portal adapter name (may contain hyphens)
3. `<license-number>`: License number to verify

## Contract (Governance)

See `contract.yaml` for full governance rules.

**Key Constraints**:
- Max 5 iterations per task
- 30 minute session timeout (HIPAA requirement)
- Exponential backoff retry (1s, 2s, 4s, 8s, 16s)
- Escalate to human on: CAPTCHA, auth failure, portal unavailable

**Permissions**:
- ✅ Navigate, click, type, extract, screenshot
- ❌ Financial transactions, persistent state, credential storage without audit

**Compliance**:
- HIPAA: Encryption at rest/transit, audit logging, PHI scrubbing
- Security: Credential vault required, no credential persistence

## Integration

### Wiggum (Iteration Control)

Automatic retry on navigation failures:

```python
# Wiggum automatically retries on:
- navigation_timeout
- element_not_found
- network_error

# Escalates to human on:
- captcha_detected
- authentication_failed
- portal_unavailable (after 3 retries)
```

### Ralph (Verification)

Data validation checks:

```python
# Required fields:
- licenseNumber
- status
- holderName
- licenseType

# Valid statuses:
- active, inactive, expired, suspended, revoked

# Checks:
- All required fields present
- Status is valid
- License found in portal (metadata.found != false)
```

## Supported Portals

**Phase 1**:
- California Medical Board (POC)

**Planned**:
- Texas Medical Board
- DEA (Drug Enforcement Administration)
- State nursing boards
- CME providers

## Architecture

```
agents/browser-automation/
├── __init__.py          # Agent exports
├── browser_agent.py     # BrowserAutomationAgent class
├── contract.yaml        # Governance contract (L2 autonomy)
└── README.md            # This file
```

**Dependencies**:
- `packages/browser-automation/` - TypeScript package (browser automation core)
- `adapters/browser_automation/` - Python client (subprocess IPC)
- `agents/base.py` - BaseAgent interface
- `ralph/` - Verification engine
- `orchestration/iteration_loop.py` - Wiggum integration

## Error Handling

**CAPTCHA Detected**:
- Action: Escalate to human
- Reason: Requires manual intervention

**Authentication Failed**:
- Action: Escalate to human
- Reason: Credential issue

**Portal Unavailable**:
- Action: Retry 3 times with backoff
- Then: Escalate to human

**Extraction Failure**:
- Action: Retry 5 times with backoff
- Then: Mark for manual verification

## HIPAA Compliance

**Encryption**:
- Credentials: AES-256-GCM at rest
- Transport: HTTPS only

**Audit Logging**:
- All actions logged: timestamp, sessionId, action, url, success
- PHI scrubbed: SSN, DOB, phone, email patterns removed

**Session Management**:
- 30 minute timeout (configurable)
- Browser state cleared on exit (cookies, storage, cache)
- No credential persistence across sessions

## Testing

```bash
# Unit tests (future)
pytest tests/agents/browser_automation/

# Integration tests with browser automation package
cd packages/browser-automation
npm test
```

## Troubleshooting

**Error**: `Browser automation CLI not found`

**Solution**: Build TypeScript package first:
```bash
cd packages/browser-automation && npm run build
```

**Error**: `Session timeout exceeded`

**Solution**: Increase timeout in contract.yaml or optimize portal adapter

**Error**: `CAPTCHA detected`

**Solution**: Manual verification required - escalate to human operator

## Development

### Adding New Portal Adapters

1. Implement adapter in `packages/browser-automation/src/adapters/`
2. Follow `BasePortalAdapter` interface
3. Add tests in `packages/browser-automation/tests/adapters/`
4. Update CLI in `packages/browser-automation/src/cli.ts`
5. Test with agent: `agent.execute("verify-license-<new-adapter>-<license-num>")`

### Extending Agent Capabilities

To add new capabilities:

1. Update `contract.yaml` permissions
2. Modify `execute()` method in `browser_agent.py`
3. Add validation in `_validate_extraction()`
4. Update documentation

## License

UNLICENSED - Internal use only for AI_Orchestrator project
