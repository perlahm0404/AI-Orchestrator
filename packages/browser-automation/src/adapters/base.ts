/**
 * Base portal adapter interface
 */

import type { BrowserSession } from '../session-manager.js';
import type { Credential, LicenseInfo } from '../types.js';

/**
 * Abstract base class for portal adapters
 */
export abstract class BasePortalAdapter {
  abstract name: string;
  abstract baseUrl: string;

  protected session: BrowserSession | null = null;

  /**
   * Set browser session
   */
  setSession(session: BrowserSession): void {
    this.session = session;
  }

  /**
   * Get current session (throws if not set)
   */
  protected getSession(): BrowserSession {
    if (!this.session) {
      throw new Error('Browser session not set');
    }
    return this.session;
  }

  /**
   * Login to portal
   */
  abstract login(credential: Credential): Promise<void>;

  /**
   * Logout from portal
   */
  abstract logout(): Promise<void>;

  /**
   * Extract license information
   */
  abstract extractLicenseInfo(licenseNumber: string): Promise<LicenseInfo>;

  /**
   * Check if session is still valid
   */
  abstract isSessionValid(): Promise<boolean>;
}
