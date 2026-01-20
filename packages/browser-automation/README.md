# Browser Automation Package

HIPAA-compliant browser automation for credentialing portal verification.

## Overview

This package provides secure, auditable browser automation for extracting data from credentialing portals (state medical boards, DEA, CME providers). It uses Playwright for browser control and implements HIPAA-compliant security measures including credential encryption and comprehensive audit logging.

**Status**: Phase 1 Complete ✓

## Features

- **AI Snapshots**: Convert web pages to LLM-friendly text representations using accessibility tree
- **Semantic Element Finding**: Locate elements using accessible names and roles (not brittle CSS selectors)
- **HIPAA-Compliant Sessions**: AES-256-GCM encrypted credentials, audit trails, automatic cleanup
- **LLM-Powered Extraction**: Extract structured data with Claude Haiku and confidence scoring
- **Portal Adapters**: Extensible pattern for supporting multiple portals (CA Medical Board POC included)
- **Python Integration**: Subprocess-based client for AI_Orchestrator agents

## Installation

### 1. Install Dependencies

```bash
cd packages/browser-automation
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

Generate encryption key:

```bash
openssl rand -hex 32
```

Edit `.env.local`:

```bash
BROWSER_AUTOMATION_KEY=your-32-byte-hex-key-here
ANTHROPIC_API_KEY=sk-ant-your-api-key-here  # Optional, for LLM extraction
```

### 3. Build

```bash
npm run build
```

### 4. Verify

```bash
npm test
```

Expected: All tests pass with 80%+ coverage

## Development

```bash
npm run dev        # Watch mode with automatic rebuild
npm test           # Run all tests
npm run check      # Type check without building
npm run coverage   # Generate test coverage report
```

## Usage

### From Python (Recommended)

```python
from adapters.browser_automation import BrowserAutomationClient

# Initialize client
client = BrowserAutomationClient()

# Create session
session_id = client.create_session({
    "sessionId": "my-session",
    "headless": True,
    "auditLogPath": "./audit-logs/session.jsonl"
})

# Extract license info using adapter
result = client.extract_license_info(
    session_id=session_id,
    adapter="california-medical-board",
    license_number="A12345"
)

print(f"Status: {result['status']}")
print(f"Holder: {result['holderName']}")

# Cleanup (REQUIRED)
client.cleanup_session(session_id)
```

See `examples/extract-license.py` for complete example.

### From TypeScript/Node.js

```typescript
import { BrowserSession, CaliforniaMedicalBoardAdapter } from '@ai-orchestrator/browser-automation';

const session = new BrowserSession({
  sessionId: 'test-session',
  headless: true,
});

await session.initialize();

const adapter = new CaliforniaMedicalBoardAdapter();
adapter.setSession(session);

const licenseInfo = await adapter.extractLicenseInfo('A12345');

await session.cleanup();
```

### CLI Interface

```bash
# Create session
echo '{"command": "create-session", "sessionId": "test", "headless": true}' \
  | node dist/index.js

# Extract license info
echo '{
  "command": "extract-license-info",
  "sessionId": "test",
  "adapter": "california-medical-board",
  "licenseNumber": "A12345"
}' | node dist/index.js

# Cleanup
echo '{"command": "cleanup-session", "sessionId": "test"}' \
  | node dist/index.js
```

## Security & HIPAA Compliance

### Encryption

- **Algorithm**: AES-256-GCM (FIPS 140-2 compliant)
- **Key Derivation**: PBKDF2 with 100,000 iterations
- **Format**: `IV:AuthTag:EncryptedData` (hex encoded)
- **Storage**: Credentials encrypted at rest in vault file

### Audit Trail

- **Format**: JSON Lines (one entry per line)
- **Fields**: timestamp, sessionId, action, url, success, errorMessage
- **PHI Scrubbing**: Automatic removal of SSN, DOB, phone, email patterns
- **Immutability**: Append-only log file

### Session Security

- **Isolation**: Each session uses isolated browser context
- **Timeout**: Automatic termination after 30 minutes (configurable)
- **Cleanup**: Browser state (cookies, storage, cache) cleared on exit
- **No Persistence**: Credentials loaded fresh each session

### Compliance Checklist

✅ Encryption at Rest (AES-256-GCM)
✅ Encryption in Transit (HTTPS only)
✅ Access Logging (all actions audited)
✅ PHI Scrubbing (automatic in logs)
✅ Session Cleanup (no credential leakage)
✅ Timeout Enforcement (30min default)
✅ No Persistent State (stateless design)
✅ Key Management (env vars only)

## Architecture

### Package Structure

```
src/
├── index.ts                    # CLI entry point + exports
├── cli.ts                      # Command execution logic
├── types.ts                    # Shared TypeScript types
├── credential-vault.ts         # AES-256-GCM encryption
├── audit-logger.ts             # JSON Lines audit trail
├── session-manager.ts          # Playwright session wrapper
├── ai-snapshot.ts              # DOM → accessibility tree → text
├── element-finder.ts           # Semantic element location
├── data-extractor.ts           # LLM-powered extraction
├── llm-client.ts               # Claude API integration
├── prompts.ts                  # Extraction prompt templates
└── adapters/
    ├── base.ts                 # Abstract portal adapter
    ├── california-medical-board.ts  # POC implementation
    └── index.ts                # Adapter exports
```

### Key Components

#### AI Snapshot Generator

Converts DOM to LLM-readable format:

1. Traverse accessibility tree
2. Extract interactive elements (buttons, links, inputs)
3. Generate stable selectors (data-testid > id > aria-label)
4. Include semantic context (nearest heading/landmark)
5. Output as formatted text (not HTML)

Example output:

```
# Page: License Verification
URL: https://mbc.ca.gov/breeze/lookup

## Interactive Elements
- [button-0] button: "Search" (in License Lookup)
- [input-0] text: "License Number" *

## Form Fields
- [input-0] text: "License Number" (required)
```

#### Element Finder

Semantic element location with fuzzy matching:

1. Try Playwright semantic locators (getByRole, getByLabel, getByText)
2. Fallback to placeholder matching
3. Last resort: fuzzy text matching with Levenshtein distance
4. Return first match or null

#### Session Manager

HIPAA-compliant browser session:

- Isolated Playwright browser context
- Credential vault integration
- Audit logger for all actions
- Automatic cleanup on timeout or exit
- No PHI in logs (scrubbed)

#### Portal Adapters

Extensible pattern for portal-specific logic:

```typescript
export abstract class BasePortalAdapter {
  abstract name: string;
  abstract baseUrl: string;
  abstract login(credential: Credential): Promise<void>;
  abstract logout(): Promise<void>;
  abstract extractLicenseInfo(licenseNumber: string): Promise<LicenseInfo>;
  abstract isSessionValid(): Promise<boolean>;
}
```

## Testing

### Test Coverage

```bash
npm test
```

**Current Status**: 44/44 tests passing, 80%+ coverage

### Test Categories

1. **Unit Tests** (Vitest)
   - Credential vault: encryption/decryption, key derivation
   - Audit logger: log writing, PHI scrubbing, querying
   - Session manager: lifecycle, cleanup, timeout
   - AI snapshot: element extraction, context
   - Element finder: semantic location, fuzzy matching
   - Data extractor: prompt building, validation

2. **Integration Tests** (Vitest + Playwright)
   - Session manager: real browser navigation, element interaction
   - Element finder: live page element finding
   - AI snapshot: full page snapshot generation

3. **Adapter Tests**
   - California Medical Board: basic structure (full tests require credentials)

### Running Tests

```bash
npm test              # All tests
npm run test:watch    # Watch mode
npm run test:coverage # Coverage report (view in coverage/index.html)
```

## Examples

### Example 1: Extract License Info

```python
# examples/extract-license.py
python examples/extract-license.py A12345
```

### Example 2: Verify Multiple Licenses

```python
from adapters.browser_automation import BrowserAutomationClient

client = BrowserAutomationClient()
licenses = ["A12345", "B67890", "C11111"]

session_id = client.create_session({
    "sessionId": "batch-verify",
    "headless": True
})

for license_num in licenses:
    try:
        info = client.extract_license_info(
            session_id=session_id,
            adapter="california-medical-board",
            license_number=license_num
        )
        print(f"{license_num}: {info['status']}")
    except Exception as e:
        print(f"{license_num}: ERROR - {e}")

client.cleanup_session(session_id)
```

## Troubleshooting

### Build Errors

**Error**: `tsc --build` fails with module errors

**Solution**: Ensure TypeScript 5.3+ installed: `npm install -D typescript@latest`

### Test Failures

**Error**: Browser tests timeout

**Solution**: Increase timeout in `vitest.config.ts`: `testTimeout: 60000`

### Import Errors

**Error**: Python can't find `adapters.browser_automation`

**Solution**: Build TypeScript first: `cd packages/browser-automation && npm run build`

### CLI Errors

**Error**: `BROWSER_AUTOMATION_KEY environment variable is required`

**Solution**: Create `.env.local` with encryption key (see Configuration above)

## Future Enhancements

### Phase 2 (Planned)

- Additional portal adapters (Texas Medical Board, DEA, etc.)
- Headless mode with screenshot verification
- Parallel session support
- Credential rotation automation
- Web-based credential management UI

### Phase 3 (Planned)

- Auto-retry on transient errors
- Session recording/playback for debugging
- Performance metrics (time per portal, success rates)
- Integration with Wiggum (iteration control)
- Integration with Ralph (verification)
- MCP server for Claude Desktop

## Contributing

### Adding New Portal Adapters

1. Extend `BasePortalAdapter` in `src/adapters/`
2. Implement required methods: `login()`, `logout()`, `extractLicenseInfo()`, `isSessionValid()`
3. Add tests in `tests/adapters/`
4. Update CLI command handler in `src/cli.ts`
5. Document in README

Example adapter structure:

```typescript
export class MyPortalAdapter extends BasePortalAdapter {
  name = 'My Portal';
  baseUrl = 'https://myportal.com';

  async login(credential: Credential): Promise<void> {
    const session = this.getSession();
    await session.navigate(`${this.baseUrl}/login`);
    // ...
  }

  async extractLicenseInfo(licenseNumber: string): Promise<LicenseInfo> {
    // ...
  }
}
```

## License

UNLICENSED - Internal use only for AI_Orchestrator project

## Support

For issues and questions:
- GitHub Issues: [AI_Orchestrator/issues](https://github.com/mylaiviet/AI_Orchestrator/issues)
- Internal docs: `docs/04-operations/browser-automation/`
