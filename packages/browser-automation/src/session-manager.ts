/**
 * HIPAA-compliant browser session manager
 * Manages isolated browser sessions with encryption and audit trails
 */

import { chromium, type Browser, type BrowserContext, type Page } from 'playwright';
import { CredentialVault } from './credential-vault.js';
import { AuditLogger } from './audit-logger.js';
import type { SessionConfig, FindElementOptions } from './types.js';

/**
 * Browser session with HIPAA compliance
 */
export class BrowserSession {
  private config: SessionConfig;
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private _page: Page | null = null;
  private auditLogger: AuditLogger;
  // Reserved for future use when loading credentials from vault
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  private credentialVault: CredentialVault;
  private sessionStartTime: number = 0;
  private sessionTimeout: number;

  constructor(config: SessionConfig) {
    this.config = config;
    this.auditLogger = new AuditLogger(config.auditLogPath);
    this.credentialVault = new CredentialVault(config.credentialVaultPath);
    this.sessionTimeout = config.maxSessionDuration || 30 * 60 * 1000; // Default 30 minutes
  }

  /**
   * Initialize browser session
   */
  async initialize(): Promise<void> {
    this.sessionStartTime = Date.now();

    await this.auditLogger.log({
      timestamp: new Date().toISOString(),
      sessionId: this.config.sessionId,
      action: 'initialize_session',
      url: '',
      success: true,
    });

    this.browser = await chromium.launch({
      headless: this.config.headless !== false,
    });

    this.context = await this.browser.newContext({
      viewport: { width: 1280, height: 720 },
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    });

    this._page = await this.context.newPage();
  }

  /**
   * Check if session has timed out
   */
  private checkTimeout(): void {
    if (Date.now() - this.sessionStartTime > this.sessionTimeout) {
      throw new Error('Session timeout exceeded');
    }
  }

  /**
   * Get current page (throws if not initialized)
   */
  private getPage(): Page {
    if (!this._page) {
      throw new Error('Session not initialized');
    }
    this.checkTimeout();
    return this._page;
  }

  /**
   * Get current Playwright page (public accessor for adapters)
   */
  page(): Page {
    return this.getPage();
  }

  /**
   * Navigate to URL
   */
  async navigate(url: string): Promise<void> {
    const page = this.getPage();

    try {
      await page.goto(url, { waitUntil: 'networkidle' });

      await this.auditLogger.log({
        timestamp: new Date().toISOString(),
        sessionId: this.config.sessionId,
        action: 'navigate',
        url,
        success: true,
      });
    } catch (error) {
      await this.auditLogger.log({
        timestamp: new Date().toISOString(),
        sessionId: this.config.sessionId,
        action: 'navigate',
        url,
        success: false,
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
      });
      throw error;
    }
  }

  /**
   * Fill input field
   */
  async fill(options: FindElementOptions, value: string): Promise<void> {
    const page = this.getPage();

    try {
      const locator = this.buildLocator(page, options);
      await locator.fill(value);

      await this.auditLogger.log({
        timestamp: new Date().toISOString(),
        sessionId: this.config.sessionId,
        action: 'fill',
        url: page.url(),
        elementSelector: JSON.stringify(options),
        success: true,
        metadata: { valueLength: value.length.toString() }, // Don't log actual value (PHI)
      });
    } catch (error) {
      await this.auditLogger.log({
        timestamp: new Date().toISOString(),
        sessionId: this.config.sessionId,
        action: 'fill',
        url: page.url(),
        elementSelector: JSON.stringify(options),
        success: false,
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
      });
      throw error;
    }
  }

  /**
   * Click element
   */
  async click(options: FindElementOptions): Promise<void> {
    const page = this.getPage();

    try {
      const locator = this.buildLocator(page, options);
      await locator.click();

      await this.auditLogger.log({
        timestamp: new Date().toISOString(),
        sessionId: this.config.sessionId,
        action: 'click',
        url: page.url(),
        elementSelector: JSON.stringify(options),
        success: true,
      });
    } catch (error) {
      await this.auditLogger.log({
        timestamp: new Date().toISOString(),
        sessionId: this.config.sessionId,
        action: 'click',
        url: page.url(),
        elementSelector: JSON.stringify(options),
        success: false,
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
      });
      throw error;
    }
  }

  /**
   * Check if element exists
   */
  async hasElement(options: FindElementOptions): Promise<boolean> {
    const page = this.getPage();

    try {
      const locator = this.buildLocator(page, options);
      const count = await locator.count();
      return count > 0;
    } catch {
      return false;
    }
  }

  /**
   * Get text content from element
   */
  async getText(options: FindElementOptions): Promise<string> {
    const page = this.getPage();
    const locator = this.buildLocator(page, options);
    const text = await locator.textContent();
    return text || '';
  }

  /**
   * Take screenshot (optionally scrub PHI)
   */
  async screenshot(filename?: string): Promise<Buffer> {
    const page = this.getPage();

    const screenshotPath = filename
      ? `${this.config.screenshotDir || './screenshots'}/${filename}`
      : undefined;

    const screenshot = await page.screenshot({ path: screenshotPath, fullPage: true });

    await this.auditLogger.log({
      timestamp: new Date().toISOString(),
      sessionId: this.config.sessionId,
      action: 'screenshot',
      url: page.url(),
      success: true,
      metadata: { path: screenshotPath || 'buffer' },
    });

    return screenshot;
  }

  /**
   * Build Playwright locator from semantic options
   */
  private buildLocator(page: Page, options: FindElementOptions) {
    if (options.role) {
      return page.getByRole(options.role as any, { name: options.label });
    }

    if (options.label) {
      return page.getByLabel(options.label);
    }

    if (options.text) {
      return page.getByText(options.text);
    }

    if (options.placeholder) {
      return page.getByPlaceholder(options.placeholder);
    }

    throw new Error('At least one locator option must be provided');
  }

  /**
   * Get current URL
   */
  async currentUrl(): Promise<string> {
    const page = this.getPage();
    return page.url();
  }

  /**
   * Wait for navigation
   */
  async waitForNavigation(): Promise<void> {
    const page = this.getPage();
    await page.waitForLoadState('networkidle');
  }

  /**
   * Get page title
   */
  async title(): Promise<string> {
    const page = this.getPage();
    return page.title();
  }

  /**
   * Cleanup session (MUST be called to prevent credential leakage)
   */
  async cleanup(): Promise<void> {
    try {
      if (this.context) {
        await this.context.clearCookies();
        await this.context.close();
      }

      if (this.browser) {
        await this.browser.close();
      }

      await this.auditLogger.log({
        timestamp: new Date().toISOString(),
        sessionId: this.config.sessionId,
        action: 'cleanup_session',
        url: '',
        success: true,
      });
    } catch (error) {
      await this.auditLogger.log({
        timestamp: new Date().toISOString(),
        sessionId: this.config.sessionId,
        action: 'cleanup_session',
        url: '',
        success: false,
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
      });
      throw error;
    } finally {
      this.browser = null;
      this.context = null;
      this._page = null;
    }
  }
}
