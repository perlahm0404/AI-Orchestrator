/**
 * CLI commands for browser automation
 * Communicates via JSON over stdin/stdout for Python subprocess integration
 */

import { BrowserSession } from './session-manager.js';
import { CaliforniaMedicalBoardAdapter } from './adapters/california-medical-board.js';
import { RegulatoryBoardAdapter } from './adapters/regulatory-boards.js';
import { CompetitorBlogAdapter } from './adapters/competitor-blogs.js';
import { KeywordValidator } from './seo/keyword-validator.js';
import type { SessionConfig, Credential, LicenseInfo } from './types.js';
import type { RegulatoryUpdate } from './adapters/regulatory-boards.js';
import type { BlogPost } from './adapters/competitor-blogs.js';
import type { ValidationReport } from './seo/keyword-validator.js';

// Active sessions (in-memory)
const activeSessions = new Map<string, BrowserSession>();

/**
 * Create a new browser session
 */
export async function createSession(config: SessionConfig): Promise<{ sessionId: string }> {
  const session = new BrowserSession(config);
  await session.initialize();

  activeSessions.set(config.sessionId, session);

  return { sessionId: config.sessionId };
}

/**
 * Extract license info using adapter
 */
export async function extractLicenseInfo(params: {
  sessionId: string;
  adapter: string;
  licenseNumber: string;
  credential?: Credential;
}): Promise<LicenseInfo> {
  const session = activeSessions.get(params.sessionId);

  if (!session) {
    throw new Error(`Session ${params.sessionId} not found`);
  }

  // Create adapter based on type
  let adapter;

  switch (params.adapter) {
    case 'california-medical-board':
      adapter = new CaliforniaMedicalBoardAdapter();
      break;
    default:
      throw new Error(`Unknown adapter: ${params.adapter}`);
  }

  adapter.setSession(session);

  // Login if credentials provided
  if (params.credential) {
    await adapter.login(params.credential);
  }

  // Extract license info
  const licenseInfo = await adapter.extractLicenseInfo(params.licenseNumber);

  return licenseInfo;
}

/**
 * Cleanup session
 */
export async function cleanupSession(params: { sessionId: string }): Promise<{ success: boolean }> {
  const session = activeSessions.get(params.sessionId);

  if (!session) {
    throw new Error(`Session ${params.sessionId} not found`);
  }

  await session.cleanup();
  activeSessions.delete(params.sessionId);

  return { success: true };
}

/**
 * Scrape regulatory updates from state board
 */
export async function scrapeRegulatoryUpdates(params: {
  sessionId: string;
  boardUrl: string;
  state: string;
  maxPages?: number;
}): Promise<RegulatoryUpdate[]> {
  const session = activeSessions.get(params.sessionId);

  if (!session) {
    throw new Error(`Session ${params.sessionId} not found`);
  }

  const adapter = new RegulatoryBoardAdapter();
  adapter.setSession(session);

  return await adapter.extractRegulatoryUpdates(
    params.boardUrl,
    params.state,
    { maxPages: params.maxPages || 5 }
  );
}

/**
 * Analyze competitor blog post
 */
export async function analyzeCompetitorBlog(params: {
  sessionId: string;
  url: string;
}): Promise<BlogPost> {
  const session = activeSessions.get(params.sessionId);

  if (!session) {
    throw new Error(`Session ${params.sessionId} not found`);
  }

  const adapter = new CompetitorBlogAdapter();
  adapter.setSession(session);

  return await adapter.extractBlogPost(params.url);
}

/**
 * Validate content against keyword strategy
 */
export async function validateKeywords(params: {
  content: string;
  keywords: string[];
  strategyPath: string;
}): Promise<ValidationReport> {
  const validator = new KeywordValidator(params.strategyPath);
  return validator.validateContent(params.content, params.keywords);
}

/**
 * Execute CLI command
 */
export async function executeCommand(command: string, params: Record<string, unknown>): Promise<unknown> {
  switch (command) {
    case 'create-session':
      return await createSession(params as unknown as SessionConfig);

    case 'extract-license-info':
      return await extractLicenseInfo(params as unknown as Parameters<typeof extractLicenseInfo>[0]);

    case 'cleanup-session':
      return await cleanupSession(params as unknown as Parameters<typeof cleanupSession>[0]);

    case 'scrape-regulatory-updates':
      return await scrapeRegulatoryUpdates(params as unknown as Parameters<typeof scrapeRegulatoryUpdates>[0]);

    case 'analyze-competitor-blog':
      return await analyzeCompetitorBlog(params as unknown as Parameters<typeof analyzeCompetitorBlog>[0]);

    case 'validate-keywords':
      return await validateKeywords(params as unknown as Parameters<typeof validateKeywords>[0]);

    default:
      throw new Error(`Unknown command: ${command}`);
  }
}
