/**
 * HIPAA-compliant audit logger
 * Logs all browser automation actions with PHI scrubbing
 */

import fs from 'fs/promises';
import path from 'path';
import type { AuditEntry } from './types.js';

/**
 * PHI patterns to scrub from logs
 * Based on HIPAA guidelines
 */
const PHI_PATTERNS = [
  // Social Security Numbers
  { pattern: /\b\d{3}-\d{2}-\d{4}\b/g, replacement: '[SSN-REDACTED]' },
  { pattern: /\b\d{9}\b/g, replacement: '[SSN-REDACTED]' },

  // Dates of Birth (various formats)
  { pattern: /\b(0?[1-9]|1[0-2])[\/\-](0?[1-9]|[12]\d|3[01])[\/\-](19|20)\d{2}\b/g, replacement: '[DOB-REDACTED]' },

  // Medical Record Numbers (generic pattern)
  { pattern: /\b(MRN|mrn|medical.?record.?number)[:\s]+[\w\d-]+/gi, replacement: '[MRN-REDACTED]' },

  // Email addresses (potential PHI)
  { pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, replacement: '[EMAIL-REDACTED]' },

  // Phone numbers
  { pattern: /\b(\+?1[-.]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g, replacement: '[PHONE-REDACTED]' },
];

/**
 * Scrub PHI from text
 */
function scrubPHI(text: string): string {
  let scrubbed = text;

  for (const { pattern, replacement } of PHI_PATTERNS) {
    scrubbed = scrubbed.replace(pattern, replacement);
  }

  return scrubbed;
}

/**
 * Audit logger for tracking all browser automation actions
 */
export class AuditLogger {
  private logPath: string;

  constructor(logPath: string = './audit-logs/audit.jsonl') {
    this.logPath = path.resolve(logPath);
  }

  /**
   * Ensure log directory exists
   */
  private async ensureLogDirectory(): Promise<void> {
    const dir = path.dirname(this.logPath);
    await fs.mkdir(dir, { recursive: true });
  }

  /**
   * Log an action to the audit trail
   */
  async log(entry: AuditEntry): Promise<void> {
    await this.ensureLogDirectory();

    // Scrub PHI from all text fields
    const scrubbedEntry: AuditEntry = {
      ...entry,
      url: scrubPHI(entry.url),
      elementSelector: entry.elementSelector ? scrubPHI(entry.elementSelector) : undefined,
      errorMessage: entry.errorMessage ? scrubPHI(entry.errorMessage) : undefined,
      metadata: entry.metadata ? this.scrubMetadata(entry.metadata) : undefined,
    };

    // Append as JSON line (one entry per line)
    const line = JSON.stringify(scrubbedEntry) + '\n';
    await fs.appendFile(this.logPath, line, 'utf-8');
  }

  /**
   * Scrub PHI from metadata object
   */
  private scrubMetadata(metadata: Record<string, string>): Record<string, string> {
    const scrubbed: Record<string, string> = {};

    for (const [key, value] of Object.entries(metadata)) {
      scrubbed[key] = scrubPHI(value);
    }

    return scrubbed;
  }

  /**
   * Query audit logs by session ID
   */
  async query(sessionId: string): Promise<AuditEntry[]> {
    try {
      const data = await fs.readFile(this.logPath, 'utf-8');
      const lines = data.trim().split('\n').filter((line) => line.length > 0);

      const entries: AuditEntry[] = [];

      for (const line of lines) {
        try {
          const entry = JSON.parse(line) as AuditEntry;
          if (entry.sessionId === sessionId) {
            entries.push(entry);
          }
        } catch (parseError) {
          // Skip malformed lines
          console.error('Failed to parse audit log line:', parseError);
        }
      }

      return entries;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        return []; // Log file doesn't exist yet
      }
      throw error;
    }
  }

  /**
   * Get all audit logs (for debugging, use carefully)
   */
  async getAll(): Promise<AuditEntry[]> {
    try {
      const data = await fs.readFile(this.logPath, 'utf-8');
      const lines = data.trim().split('\n').filter((line) => line.length > 0);

      const entries: AuditEntry[] = [];

      for (const line of lines) {
        try {
          entries.push(JSON.parse(line) as AuditEntry);
        } catch (parseError) {
          console.error('Failed to parse audit log line:', parseError);
        }
      }

      return entries;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        return [];
      }
      throw error;
    }
  }

  /**
   * Clear audit logs (for testing only)
   */
  async clear(): Promise<void> {
    try {
      await fs.unlink(this.logPath);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') {
        throw error;
      }
    }
  }
}
