/**
 * CLI commands for browser automation
 * Communicates via JSON over stdin/stdout for Python subprocess integration
 */

import { BrowserSession } from './session-manager.js';
import { CaliforniaMedicalBoardAdapter } from './adapters/california-medical-board.js';
import type { SessionConfig, Credential, LicenseInfo } from './types.js';

// Active sessions (in-memory)
const activeSessions = new Map<string, BrowserSession>();

/**
 * Create a new browser session
 */
export async function createSession(config: SessionConfig): Promise<{ sessionId: string }> {
  const session = new BrowserSession(config);
  await session.initialize();

  activeSessions.set(config.sessionId, session);

  return { sessionId: config.sessionId };
}

/**
 * Extract license info using adapter
 */
export async function extractLicenseInfo(params: {
  sessionId: string;
  adapter: string;
  licenseNumber: string;
  credential?: Credential;
}): Promise<LicenseInfo> {
  const session = activeSessions.get(params.sessionId);

  if (!session) {
    throw new Error(`Session ${params.sessionId} not found`);
  }

  // Create adapter based on type
  let adapter;

  switch (params.adapter) {
    case 'california-medical-board':
      adapter = new CaliforniaMedicalBoardAdapter();
      break;
    default:
      throw new Error(`Unknown adapter: ${params.adapter}`);
  }

  adapter.setSession(session);

  // Login if credentials provided
  if (params.credential) {
    await adapter.login(params.credential);
  }

  // Extract license info
  const licenseInfo = await adapter.extractLicenseInfo(params.licenseNumber);

  return licenseInfo;
}

/**
 * Cleanup session
 */
export async function cleanupSession(params: { sessionId: string }): Promise<{ success: boolean }> {
  const session = activeSessions.get(params.sessionId);

  if (!session) {
    throw new Error(`Session ${params.sessionId} not found`);
  }

  await session.cleanup();
  activeSessions.delete(params.sessionId);

  return { success: true };
}

/**
 * Execute CLI command
 */
export async function executeCommand(command: string, params: Record<string, unknown>): Promise<unknown> {
  switch (command) {
    case 'create-session':
      return await createSession(params as unknown as SessionConfig);

    case 'extract-license-info':
      return await extractLicenseInfo(params as unknown as Parameters<typeof extractLicenseInfo>[0]);

    case 'cleanup-session':
      return await cleanupSession(params as unknown as Parameters<typeof cleanupSession>[0]);

    default:
      throw new Error(`Unknown command: ${command}`);
  }
}
