/**
 * HIPAA-compliant credential vault
 * Encrypts credentials using AES-256-GCM
 */

import crypto from 'crypto';
import fs from 'fs/promises';
import path from 'path';
import type { Credential } from './types.js';

const ALGORITHM = 'aes-256-gcm';
const IV_LENGTH = 16;

/**
 * Get encryption key from environment variable
 */
function getEncryptionKey(): Buffer {
  const key = process.env.BROWSER_AUTOMATION_KEY;

  if (!key) {
    throw new Error('BROWSER_AUTOMATION_KEY environment variable is required');
  }

  // Derive a 32-byte key using PBKDF2
  return crypto.pbkdf2Sync(key, 'browser-automation-salt', 100000, 32, 'sha256');
}

/**
 * Encrypt a string using AES-256-GCM
 */
function encrypt(text: string): string {
  if (!text) {
    throw new Error('Text to encrypt cannot be empty');
  }

  const key = getEncryptionKey();
  const iv = crypto.randomBytes(IV_LENGTH);

  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);

  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');

  const authTag = cipher.getAuthTag();

  // Return format: iv:authTag:encryptedData (all hex encoded)
  return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
}

/**
 * Decrypt a string encrypted with encrypt()
 */
function decrypt(encryptedText: string): string {
  if (!encryptedText) {
    throw new Error('Encrypted text cannot be empty');
  }

  const parts = encryptedText.split(':');

  if (parts.length !== 3) {
    throw new Error('Invalid encrypted text format');
  }

  const [ivHex, authTagHex, encryptedData] = parts;

  const key = getEncryptionKey();
  const iv = Buffer.from(ivHex, 'hex');
  const authTag = Buffer.from(authTagHex, 'hex');

  const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
  decipher.setAuthTag(authTag);

  let decrypted = decipher.update(encryptedData, 'hex', 'utf8');
  decrypted += decipher.final('utf8');

  return decrypted;
}

interface StoredCredential {
  id: string;
  service: string;
  username: string;
  encryptedPassword: string;
  encryptedOtpSecret?: string;
  metadata?: Record<string, string>;
}

/**
 * Credential vault for encrypted storage
 */
export class CredentialVault {
  private vaultPath: string;

  constructor(vaultPath: string = './credential-vault.json') {
    this.vaultPath = path.resolve(vaultPath);
  }

  /**
   * Initialize vault file if it doesn't exist
   */
  private async ensureVault(): Promise<void> {
    try {
      await fs.access(this.vaultPath);
    } catch {
      await fs.writeFile(this.vaultPath, JSON.stringify({ credentials: [] }, null, 2));
    }
  }

  /**
   * Read all credentials from vault
   */
  private async readVault(): Promise<StoredCredential[]> {
    await this.ensureVault();
    const data = await fs.readFile(this.vaultPath, 'utf-8');
    const parsed = JSON.parse(data);
    return parsed.credentials || [];
  }

  /**
   * Write credentials to vault
   */
  private async writeVault(credentials: StoredCredential[]): Promise<void> {
    await fs.writeFile(
      this.vaultPath,
      JSON.stringify({ credentials }, null, 2)
    );
  }

  /**
   * Store a credential in the vault
   */
  async store(credential: Credential): Promise<void> {
    const credentials = await this.readVault();

    // Remove existing credential with same ID
    const filtered = credentials.filter((c) => c.id !== credential.id);

    // Encrypt sensitive fields
    const stored: StoredCredential = {
      id: credential.id,
      service: credential.service,
      username: credential.username,
      encryptedPassword: encrypt(credential.password),
      encryptedOtpSecret: credential.otpSecret ? encrypt(credential.otpSecret) : undefined,
      metadata: credential.metadata,
    };

    filtered.push(stored);
    await this.writeVault(filtered);
  }

  /**
   * Retrieve a credential from the vault
   */
  async retrieve(id: string): Promise<Credential> {
    const credentials = await this.readVault();
    const stored = credentials.find((c) => c.id === id);

    if (!stored) {
      throw new Error(`Credential with ID "${id}" not found`);
    }

    // Decrypt sensitive fields
    const credential: Credential = {
      id: stored.id,
      service: stored.service,
      username: stored.username,
      password: decrypt(stored.encryptedPassword),
      otpSecret: stored.encryptedOtpSecret ? decrypt(stored.encryptedOtpSecret) : undefined,
      metadata: stored.metadata,
    };

    return credential;
  }

  /**
   * List all credentials (metadata only, no passwords)
   */
  async list(): Promise<Array<Omit<Credential, 'password' | 'otpSecret'>>> {
    const credentials = await this.readVault();

    return credentials.map((c) => ({
      id: c.id,
      service: c.service,
      username: c.username,
      metadata: c.metadata,
    }));
  }

  /**
   * Delete a credential from the vault
   */
  async delete(id: string): Promise<void> {
    const credentials = await this.readVault();
    const filtered = credentials.filter((c) => c.id !== id);

    if (filtered.length === credentials.length) {
      throw new Error(`Credential with ID "${id}" not found`);
    }

    await this.writeVault(filtered);
  }

  /**
   * Check if a credential exists
   */
  async exists(id: string): Promise<boolean> {
    const credentials = await this.readVault();
    return credentials.some((c) => c.id === id);
  }
}
