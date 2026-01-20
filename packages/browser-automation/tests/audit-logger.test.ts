/**
 * Tests for audit logger
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs/promises';
import path from 'path';
import { AuditLogger } from '../src/audit-logger.js';
import type { AuditEntry } from '../src/types.js';

describe('AuditLogger', () => {
  const testLogPath = path.join(__dirname, 'test-audit.jsonl');
  let logger: AuditLogger;

  beforeEach(async () => {
    logger = new AuditLogger(testLogPath);
  });

  afterEach(async () => {
    // Clean up test logs
    try {
      await fs.unlink(testLogPath);
    } catch {
      // Ignore if doesn't exist
    }
  });

  it('should log actions to file', async () => {
    const entry: AuditEntry = {
      timestamp: new Date().toISOString(),
      sessionId: 'test-session-001',
      action: 'navigate',
      url: 'https://example.com',
      success: true,
    };

    await logger.log(entry);

    const logs = await logger.query('test-session-001');
    expect(logs).toHaveLength(1);
    expect(logs[0]).toEqual(entry);
  });

  it('should append logs in JSON lines format', async () => {
    await logger.log({
      timestamp: '2024-01-01T00:00:00Z',
      sessionId: 'test-001',
      action: 'action1',
      url: 'https://example.com',
      success: true,
    });

    await logger.log({
      timestamp: '2024-01-01T00:00:01Z',
      sessionId: 'test-001',
      action: 'action2',
      url: 'https://example.com',
      success: true,
    });

    const fileContent = await fs.readFile(testLogPath, 'utf-8');
    const lines = fileContent.trim().split('\n');

    expect(lines).toHaveLength(2);
    expect(JSON.parse(lines[0]).action).toBe('action1');
    expect(JSON.parse(lines[1]).action).toBe('action2');
  });

  it('should scrub SSN from logs', async () => {
    const entry: AuditEntry = {
      timestamp: new Date().toISOString(),
      sessionId: 'test-002',
      action: 'fill',
      url: 'https://example.com?ssn=123-45-6789',
      success: true,
      metadata: { field: 'SSN: 123-45-6789' },
    };

    await logger.log(entry);

    const logs = await logger.query('test-002');
    expect(logs[0].url).not.toContain('123-45-6789');
    expect(logs[0].url).toContain('[SSN-REDACTED]');
    expect(logs[0].metadata?.field).toContain('[SSN-REDACTED]');
  });

  it('should scrub email addresses from logs', async () => {
    const entry: AuditEntry = {
      timestamp: new Date().toISOString(),
      sessionId: 'test-003',
      action: 'fill',
      url: 'https://example.com',
      success: true,
      elementSelector: 'input[value="patient@example.com"]',
    };

    await logger.log(entry);

    const logs = await logger.query('test-003');
    expect(logs[0].elementSelector).not.toContain('patient@example.com');
    expect(logs[0].elementSelector).toContain('[EMAIL-REDACTED]');
  });

  it('should scrub phone numbers from logs', async () => {
    const entry: AuditEntry = {
      timestamp: new Date().toISOString(),
      sessionId: 'test-004',
      action: 'fill',
      url: 'https://example.com',
      success: true,
      errorMessage: 'Invalid phone: (555) 123-4567',
    };

    await logger.log(entry);

    const logs = await logger.query('test-004');
    expect(logs[0].errorMessage).not.toContain('555) 123-4567');
    expect(logs[0].errorMessage).toContain('[PHONE-REDACTED]');
  });

  it('should scrub dates of birth from logs', async () => {
    const entry: AuditEntry = {
      timestamp: new Date().toISOString(),
      sessionId: 'test-005',
      action: 'extract',
      url: 'https://example.com',
      success: true,
      metadata: { dob: '01/15/1980' },
    };

    await logger.log(entry);

    const logs = await logger.query('test-005');
    expect(logs[0].metadata?.dob).not.toContain('01/15/1980');
    expect(logs[0].metadata?.dob).toContain('[DOB-REDACTED]');
  });

  it('should query logs by session ID', async () => {
    await logger.log({
      timestamp: '2024-01-01T00:00:00Z',
      sessionId: 'session-1',
      action: 'action1',
      url: 'https://example.com',
      success: true,
    });

    await logger.log({
      timestamp: '2024-01-01T00:00:01Z',
      sessionId: 'session-2',
      action: 'action2',
      url: 'https://example.com',
      success: true,
    });

    await logger.log({
      timestamp: '2024-01-01T00:00:02Z',
      sessionId: 'session-1',
      action: 'action3',
      url: 'https://example.com',
      success: true,
    });

    const session1Logs = await logger.query('session-1');
    expect(session1Logs).toHaveLength(2);
    expect(session1Logs[0].action).toBe('action1');
    expect(session1Logs[1].action).toBe('action3');

    const session2Logs = await logger.query('session-2');
    expect(session2Logs).toHaveLength(1);
    expect(session2Logs[0].action).toBe('action2');
  });

  it('should return empty array for nonexistent session', async () => {
    const logs = await logger.query('nonexistent');
    expect(logs).toEqual([]);
  });

  it('should get all logs', async () => {
    await logger.log({
      timestamp: '2024-01-01T00:00:00Z',
      sessionId: 'session-1',
      action: 'action1',
      url: 'https://example.com',
      success: true,
    });

    await logger.log({
      timestamp: '2024-01-01T00:00:01Z',
      sessionId: 'session-2',
      action: 'action2',
      url: 'https://example.com',
      success: true,
    });

    const allLogs = await logger.getAll();
    expect(allLogs).toHaveLength(2);
  });

  it('should clear logs', async () => {
    await logger.log({
      timestamp: new Date().toISOString(),
      sessionId: 'test-006',
      action: 'test',
      url: 'https://example.com',
      success: true,
    });

    await logger.clear();

    const logs = await logger.getAll();
    expect(logs).toEqual([]);
  });
});
