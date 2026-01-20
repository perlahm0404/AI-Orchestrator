/**
 * Shared TypeScript types for browser automation
 */

/**
 * Session configuration for browser automation
 */
export interface SessionConfig {
  sessionId: string;
  credentialVaultPath?: string;
  auditLogPath?: string;
  screenshotDir?: string;
  maxSessionDuration?: number;
  headless?: boolean;
}

/**
 * Encrypted credential stored in vault
 */
export interface Credential {
  id: string;
  service: string;
  username: string;
  password: string;
  otpSecret?: string;
  metadata?: Record<string, string>;
}

/**
 * Audit log entry for tracking actions
 */
export interface AuditEntry {
  timestamp: string;
  sessionId: string;
  action: string;
  url: string;
  elementSelector?: string;
  success: boolean;
  errorMessage?: string;
  metadata?: Record<string, string>;
}

/**
 * Page snapshot for LLM consumption
 */
export interface PageSnapshot {
  url: string;
  title: string;
  timestamp: string;
  interactiveElements: InteractiveElement[];
  formFields: FormField[];
  landmarks: Landmark[];
  metadata: PageMetadata;
}

/**
 * Interactive element in page snapshot
 */
export interface InteractiveElement {
  id: string;
  type: 'button' | 'link' | 'input' | 'select' | 'textarea';
  label: string;
  selector: string;
  coordinates?: { x: number; y: number };
  isVisible: boolean;
  context: string;
}

/**
 * Form field in page snapshot
 */
export interface FormField {
  id: string;
  type: string;
  label: string;
  value?: string;
  placeholder?: string;
  required: boolean;
  selector: string;
}

/**
 * Landmark (major section) in page snapshot
 */
export interface Landmark {
  role: string;
  label?: string;
  selector: string;
}

/**
 * Page metadata in snapshot
 */
export interface PageMetadata {
  language?: string;
  viewport: { width: number; height: number };
  hasModals: boolean;
  hasDialogs: boolean;
}

/**
 * Options for finding elements semantically
 */
export interface FindElementOptions {
  role?: string;
  label?: string;
  text?: string;
  placeholder?: string;
  context?: string;
  fuzzyMatch?: boolean;
}

/**
 * Extraction query for LLM-powered data extraction
 */
export interface ExtractionQuery {
  target: string;
  context?: string;
  schema?: Record<string, unknown>;
}

/**
 * Extracted data with confidence score
 */
export interface ExtractedData {
  value: unknown;
  confidence: number;
  source: string;
  rawText: string;
}

/**
 * License information extracted from portal
 */
export interface LicenseInfo {
  licenseNumber: string;
  status: 'active' | 'inactive' | 'expired' | 'suspended' | 'revoked';
  holderName: string;
  licenseType: string;
  issueDate?: string;
  expirationDate?: string;
  disciplinaryActions?: DisciplinaryAction[];
  metadata?: Record<string, unknown>;
}

/**
 * Disciplinary action on license
 */
export interface DisciplinaryAction {
  date: string;
  type: string;
  description: string;
  status: 'active' | 'resolved';
}

/**
 * Portal adapter interface
 */
export interface PortalAdapter {
  name: string;
  baseUrl: string;
  login(credential: Credential): Promise<void>;
  logout(): Promise<void>;
  extractLicenseInfo(licenseNumber: string): Promise<LicenseInfo>;
  isSessionValid(): Promise<boolean>;
}
