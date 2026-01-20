/**
 * Tests for credential vault
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs/promises';
import path from 'path';
import { CredentialVault } from '../src/credential-vault.js';
import type { Credential } from '../src/types.js';

describe('CredentialVault', () => {
  const testVaultPath = path.join(__dirname, 'test-vault.json');
  let vault: CredentialVault;

  beforeEach(async () => {
    // Set encryption key for tests
    process.env.BROWSER_AUTOMATION_KEY = 'test-key-for-encryption-32bytes';
    vault = new CredentialVault(testVaultPath);
  });

  afterEach(async () => {
    // Clean up test vault
    try {
      await fs.unlink(testVaultPath);
    } catch {
      // Ignore if doesn't exist
    }
  });

  it('should store and retrieve credentials', async () => {
    const credential: Credential = {
      id: 'test-001',
      service: 'california-medical-board',
      username: 'test@example.com',
      password: 'secretpassword123',
      metadata: { region: 'CA' },
    };

    await vault.store(credential);

    const retrieved = await vault.retrieve('test-001');

    expect(retrieved).toEqual(credential);
  });

  it('should encrypt passwords', async () => {
    const credential: Credential = {
      id: 'test-002',
      service: 'test-service',
      username: 'user',
      password: 'plaintextpassword',
    };

    await vault.store(credential);

    // Read raw vault file
    const vaultData = await fs.readFile(testVaultPath, 'utf-8');
    const parsed = JSON.parse(vaultData);

    // Password should be encrypted (contains colons for iv:authTag:data)
    expect(parsed.credentials[0].encryptedPassword).toContain(':');
    expect(parsed.credentials[0].encryptedPassword).not.toContain('plaintextpassword');
  });

  it('should encrypt OTP secrets', async () => {
    const credential: Credential = {
      id: 'test-003',
      service: 'test-service',
      username: 'user',
      password: 'password',
      otpSecret: 'JBSWY3DPEHPK3PXP',
    };

    await vault.store(credential);

    const retrieved = await vault.retrieve('test-003');

    expect(retrieved.otpSecret).toBe('JBSWY3DPEHPK3PXP');

    // Check encryption in raw file
    const vaultData = await fs.readFile(testVaultPath, 'utf-8');
    const parsed = JSON.parse(vaultData);
    expect(parsed.credentials[0].encryptedOtpSecret).toContain(':');
  });

  it('should list credentials without sensitive data', async () => {
    const credential: Credential = {
      id: 'test-004',
      service: 'test-service',
      username: 'user@example.com',
      password: 'secret',
    };

    await vault.store(credential);

    const list = await vault.list();

    expect(list).toHaveLength(1);
    expect(list[0]).toEqual({
      id: 'test-004',
      service: 'test-service',
      username: 'user@example.com',
      metadata: undefined,
    });
    expect(list[0]).not.toHaveProperty('password');
    expect(list[0]).not.toHaveProperty('otpSecret');
  });

  it('should delete credentials', async () => {
    const credential: Credential = {
      id: 'test-005',
      service: 'test-service',
      username: 'user',
      password: 'password',
    };

    await vault.store(credential);
    await vault.delete('test-005');

    await expect(vault.retrieve('test-005')).rejects.toThrow('not found');
  });

  it('should check if credential exists', async () => {
    const credential: Credential = {
      id: 'test-006',
      service: 'test-service',
      username: 'user',
      password: 'password',
    };

    await vault.store(credential);

    expect(await vault.exists('test-006')).toBe(true);
    expect(await vault.exists('nonexistent')).toBe(false);
  });

  it('should update existing credentials', async () => {
    const credential: Credential = {
      id: 'test-007',
      service: 'test-service',
      username: 'user',
      password: 'oldpassword',
    };

    await vault.store(credential);

    const updated: Credential = {
      id: 'test-007',
      service: 'test-service',
      username: 'user',
      password: 'newpassword',
    };

    await vault.store(updated);

    const retrieved = await vault.retrieve('test-007');
    expect(retrieved.password).toBe('newpassword');

    const list = await vault.list();
    expect(list).toHaveLength(1); // Should not duplicate
  });

  it('should throw error when encryption key is missing', async () => {
    delete process.env.BROWSER_AUTOMATION_KEY;

    const credential: Credential = {
      id: 'test-008',
      service: 'test-service',
      username: 'user',
      password: 'password',
    };

    await expect(vault.store(credential)).rejects.toThrow('BROWSER_AUTOMATION_KEY');
  });
});
