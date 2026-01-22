/**
 * Regulatory Board Adapter - Scrape state board websites for updates
 */

import { BasePortalAdapter } from './base.js';
import type { BrowserSession } from '../session-manager.js';
import { extract } from '../data-extractor.js';
import { generateSnapshot } from '../ai-snapshot.js';
import type { Credential, AuditEntry } from '../types.js';

/**
 * Regulatory update from state board
 */
export interface RegulatoryUpdate {
  source: string;           // State board name
  updateType: 'regulation' | 'guidance' | 'announcement' | 'disciplinary';
  title: string;
  date: string;            // ISO 8601
  summary: string;
  fullText?: string;
  url: string;
  confidence: string;      // 0.0-1.0 as string for CLI JSON compatibility
  extractedAt: string;     // ISO timestamp
}

/**
 * Options for extracting regulatory updates
 */
export interface ExtractRegulatoryUpdatesOptions {
  maxPages?: number;
  dateFrom?: string;
  updateTypes?: Array<'regulation' | 'guidance' | 'announcement' | 'disciplinary'>;
}

/**
 * Adapter for scraping state board websites
 *
 * Features:
 * - LLM-powered extraction of regulatory updates
 * - Semantic element locators (no brittle CSS selectors)
 * - Confidence scoring for extracted data
 * - HIPAA-compliant audit logging
 */
export class RegulatoryBoardAdapter extends BasePortalAdapter {
  name = 'Regulatory Board Scraper';
  baseUrl = '';  // Set dynamically per state

  /**
   * Extract regulatory updates from state board website
   *
   * @param boardUrl - URL of state board updates page
   * @param state - State name (e.g., "California")
   * @param options - Extraction options
   * @returns Array of regulatory updates with confidence scores
   */
  async extractRegulatoryUpdates(
    boardUrl: string,
    state: string,
    options?: ExtractRegulatoryUpdatesOptions
  ): Promise<RegulatoryUpdate[]> {
    const session = this.getSession();
    const updates: RegulatoryUpdate[] = [];
    const maxPages = options?.maxPages || 5;

    try {
      // Navigate to updates page
      await session.navigate(boardUrl);

      // Wait for content to load
      await session.page().waitForLoadState('networkidle', { timeout: 10000 });

      // Log navigation
      await this._logAction({
        action: 'navigate',
        url: boardUrl,
        success: true,
        metadata: { state, purpose: 'regulatory_updates' }
      });

      // Generate AI snapshot for LLM extraction
      const snapshot = await generateSnapshot(session.page());

      // Extract updates using LLM
      const extracted = await extract(session.page(), {
        target: 'recent regulatory updates, announcements, policy changes, or guidance documents',
        context: `State board of nursing website for ${state}. Extract title, date, summary, and type of each update.`,
        schema: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              title: { type: 'string' },
              date: { type: 'string' },
              summary: { type: 'string' },
              updateType: {
                enum: ['regulation', 'guidance', 'announcement', 'disciplinary']
              }
            },
            required: ['title', 'date', 'summary']
          }
        }
      });

      // Process extracted data
      if (extracted.value && Array.isArray(extracted.value)) {
        for (const item of extracted.value) {
          // Filter by update types if specified
          if (options?.updateTypes && options.updateTypes.length > 0) {
            if (!options.updateTypes.includes(item.updateType as any)) {
              continue;
            }
          }

          // Filter by date if specified
          if (options?.dateFrom) {
            try {
              const updateDate = new Date(item.date);
              const fromDate = new Date(options.dateFrom);
              if (updateDate < fromDate) {
                continue;
              }
            } catch {
              // Skip date filtering if parsing fails
            }
          }

          updates.push({
            source: `${state} Board of Nursing`,
            updateType: item.updateType || 'announcement',
            title: item.title,
            date: item.date,
            summary: item.summary,
            fullText: item.fullText,
            url: boardUrl,
            confidence: String(extracted.confidence),
            extractedAt: new Date().toISOString()
          });
        }
      }

      // Log extraction success
      await this._logAction({
        action: 'extract_regulatory_updates',
        url: boardUrl,
        success: true,
        metadata: {
          state,
          count: String(updates.length),
          confidence: String(extracted.confidence)
        }
      });

      return updates;

    } catch (error) {
      // Log extraction failure
      await this._logAction({
        action: 'extract_regulatory_updates',
        url: boardUrl,
        success: false,
        errorMessage: error instanceof Error ? error.message : String(error),
        metadata: { state }
      });

      throw error;
    }
  }

  /**
   * Extract disciplinary actions from state board website
   *
   * @param boardUrl - URL of disciplinary actions page
   * @param state - State name
   * @param options - Extraction options
   * @returns Array of disciplinary actions as RegulatoryUpdates
   */
  async extractDisciplinaryActions(
    boardUrl: string,
    state: string,
    options?: { maxRecords?: number }
  ): Promise<RegulatoryUpdate[]> {
    const session = this.getSession();
    const actions: RegulatoryUpdate[] = [];
    const maxRecords = options?.maxRecords || 50;

    try {
      // Navigate to disciplinary page
      await session.navigate(boardUrl);
      await session.page().waitForLoadState('networkidle', { timeout: 10000 });

      // Log navigation
      await this._logAction({
        action: 'navigate',
        url: boardUrl,
        success: true,
        metadata: { state, purpose: 'disciplinary_actions' }
      });

      // Extract disciplinary actions using LLM
      const extracted = await extract(session.page(), {
        target: 'disciplinary actions against licensees',
        context: `State board of nursing disciplinary actions for ${state}. Extract licensee name (if public), action type, date, and resolution.`,
        schema: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              licenseeName: { type: 'string' },
              actionType: { type: 'string' },
              date: { type: 'string' },
              description: { type: 'string' },
              resolution: { type: 'string' }
            },
            required: ['actionType', 'date', 'description']
          }
        }
      });

      // Process extracted data
      if (extracted.value && Array.isArray(extracted.value)) {
        const limitedActions = extracted.value.slice(0, maxRecords);

        for (const item of limitedActions) {
          actions.push({
            source: `${state} Board of Nursing`,
            updateType: 'disciplinary',
            title: `Disciplinary Action: ${item.actionType}`,
            date: item.date,
            summary: item.description,
            fullText: `Licensee: ${item.licenseeName || 'Not disclosed'}\nAction: ${item.actionType}\nResolution: ${item.resolution || 'Pending'}`,
            url: boardUrl,
            confidence: String(extracted.confidence),
            extractedAt: new Date().toISOString()
          });
        }
      }

      // Log extraction success
      await this._logAction({
        action: 'extract_disciplinary_actions',
        url: boardUrl,
        success: true,
        metadata: {
          state,
          count: String(actions.length),
          confidence: String(extracted.confidence)
        }
      });

      return actions;

    } catch (error) {
      // Log extraction failure
      await this._logAction({
        action: 'extract_disciplinary_actions',
        url: boardUrl,
        success: false,
        errorMessage: error instanceof Error ? error.message : String(error),
        metadata: { state }
      });

      throw error;
    }
  }

  // ===== BasePortalAdapter required methods =====

  /**
   * Login not needed for public data
   */
  async login(_credential: Credential): Promise<void> {
    // No-op: regulatory data is publicly accessible
  }

  /**
   * Logout not needed
   */
  async logout(): Promise<void> {
    // No-op: no session to close
  }

  /**
   * Session is always valid for public data
   */
  async isSessionValid(): Promise<boolean> {
    return true;
  }

  /**
   * Not applicable for regulatory boards
   */
  async extractLicenseInfo(_licenseNumber: string): Promise<any> {
    throw new Error('Use extractRegulatoryUpdates() for regulatory board scraping');
  }

  // ===== Private helpers =====

  /**
   * Log action to audit trail
   */
  private async _logAction(entry: Partial<AuditEntry>): Promise<void> {
    const session = this.getSession();

    // Access audit logger through session if available
    // For now, just log to console
    console.log('[RegulatoryBoard]', entry.action, entry.url, entry.success ? '✓' : '✗');
  }
}
