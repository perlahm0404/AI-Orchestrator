/**
 * California Medical Board portal adapter
 * POC implementation for license verification
 */

import { BasePortalAdapter } from './base.js';
import type { Credential, LicenseInfo } from '../types.js';

/**
 * California Medical Board adapter
 * Note: This is a simplified POC. Real implementation would need to handle:
 * - CAPTCHA
 * - Multi-step forms
 * - Dynamic selectors
 */
export class CaliforniaMedicalBoardAdapter extends BasePortalAdapter {
  name = 'California Medical Board';
  baseUrl = 'https://www.mbc.ca.gov/breeze/';

  /**
   * Login to portal (if required)
   * Note: Public license lookup may not require login
   */
  async login(credential: Credential): Promise<void> {
    const session = this.getSession();

    await session.navigate(`${this.baseUrl}login`);

    // Check if login is required
    const hasLoginForm = await session.hasElement({ role: 'textbox', label: 'Username' });

    if (hasLoginForm) {
      await session.fill({ label: 'Username' }, credential.username);
      await session.fill({ label: 'Password' }, credential.password);
      await session.click({ role: 'button', text: 'Sign In' });

      // Wait for navigation
      await session.waitForNavigation();

      // Handle 2FA if present
      if (credential.otpSecret) {
        const has2FA = await session.hasElement({ text: 'verification code' });
        if (has2FA) {
          // Note: OTP generation would be implemented here
          // For POC, we skip this step
          console.warn('2FA required but not implemented in POC');
        }
      }
    }
  }

  /**
   * Logout from portal
   */
  async logout(): Promise<void> {
    const session = this.getSession();

    const hasLogout = await session.hasElement({ role: 'button', text: 'Logout' });

    if (hasLogout) {
      await session.click({ role: 'button', text: 'Logout' });
    }
  }

  /**
   * Extract license information by license number
   */
  async extractLicenseInfo(licenseNumber: string): Promise<LicenseInfo> {
    const session = this.getSession();

    // Navigate to public license lookup
    await session.navigate(`${this.baseUrl}lookup`);

    // Fill in license number
    await session.fill({ label: 'License Number' }, licenseNumber);

    // Submit search
    await session.click({ role: 'button', text: 'Search' });

    // Wait for results
    await session.waitForNavigation();

    // Check if license was found
    const notFound = await session.hasElement({ text: 'No records found' });

    if (notFound) {
      return {
        licenseNumber,
        status: 'inactive',
        holderName: 'Unknown',
        licenseType: 'Unknown',
        metadata: { found: false },
      };
    }

    // Extract license data using snapshot
    // In a real implementation, this would use the LLM data extractor
    // For POC, we use simple element finding

    let status: LicenseInfo['status'] = 'active';
    let holderName = 'Unknown';
    let licenseType = 'Physician';
    let expirationDate: string | undefined;

    try {
      // Try to find status
      const statusElement = await session.hasElement({ text: 'Active' });
      if (!statusElement) {
        const expired = await session.hasElement({ text: 'Expired' });
        if (expired) status = 'expired';
      }

      // Try to find holder name
      const nameText = await session.getText({ role: 'heading' });
      if (nameText) {
        holderName = nameText;
      }
    } catch (error) {
      console.warn('Error extracting license details:', error);
    }

    return {
      licenseNumber,
      status,
      holderName,
      licenseType,
      expirationDate,
      disciplinaryActions: [],
    };
  }

  /**
   * Check if session is valid
   */
  async isSessionValid(): Promise<boolean> {
    const session = this.getSession();

    try {
      const url = await session.currentUrl();

      // If we're on a login page, session is invalid
      if (url.includes('/login')) {
        return false;
      }

      // Check for session timeout message
      const hasTimeout = await session.hasElement({ text: 'session expired' });
      return !hasTimeout;
    } catch {
      return false;
    }
  }
}
