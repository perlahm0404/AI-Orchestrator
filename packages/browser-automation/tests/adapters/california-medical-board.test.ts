/**
 * Tests for California Medical Board adapter
 * Note: These are basic tests. Full integration tests would require test credentials.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { CaliforniaMedicalBoardAdapter } from '../../src/adapters/california-medical-board.js';
import { BrowserSession } from '../../src/session-manager.js';
import type { SessionConfig } from '../../src/types.js';

describe('CaliforniaMedicalBoardAdapter', () => {
  let adapter: CaliforniaMedicalBoardAdapter;
  let session: BrowserSession;

  beforeEach(async () => {
    process.env.BROWSER_AUTOMATION_KEY = 'test-key-for-encryption-32bytes';

    const config: SessionConfig = {
      sessionId: 'test-ca-adapter',
      headless: true,
    };

    session = new BrowserSession(config);
    await session.initialize();

    adapter = new CaliforniaMedicalBoardAdapter();
    adapter.setSession(session);
  });

  afterEach(async () => {
    await session.cleanup();
  });

  it('should have correct name and base URL', () => {
    expect(adapter.name).toBe('California Medical Board');
    expect(adapter.baseUrl).toContain('mbc.ca.gov');
  });

  it('should throw error if session not set', () => {
    const newAdapter = new CaliforniaMedicalBoardAdapter();

    expect(() => newAdapter.isSessionValid()).rejects.toThrow('Browser session not set');
  });

  // Note: Skip actual portal tests since we don't have test credentials
  it.skip('should navigate to portal', async () => {
    await session.navigate(adapter.baseUrl);
    const url = await session.currentUrl();
    expect(url).toContain('mbc.ca.gov');
  });
});
