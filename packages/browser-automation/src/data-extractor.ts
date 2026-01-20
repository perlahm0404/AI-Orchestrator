/**
 * LLM-powered data extraction from web pages
 */

import type { Page } from 'playwright';
import { generateSnapshot, formatSnapshotForLLM } from './ai-snapshot.js';
import { callClaude } from './llm-client.js';
import { buildExtractionPrompt } from './prompts.js';
import type { ExtractionQuery, ExtractedData } from './types.js';

/**
 * Extract structured data from page using LLM
 */
export async function extract(page: Page, query: ExtractionQuery): Promise<ExtractedData> {
  // Generate page snapshot
  const snapshot = await generateSnapshot(page);
  const snapshotText = formatSnapshotForLLM(snapshot);

  // Build extraction prompt
  const prompt = buildExtractionPrompt(snapshotText, query.target, query.context);

  // Call LLM
  const rawResponse = await callClaude(prompt, query.schema);

  // Parse response
  let value: unknown;
  let confidence = 0.8; // Default confidence

  try {
    value = JSON.parse(rawResponse);

    // Check if extraction failed
    if (typeof value === 'object' && value !== null && 'found' in value) {
      const found = (value as { found: boolean }).found;
      if (!found) {
        confidence = 0.0;
      }
    }
  } catch {
    // If not JSON, use raw text
    value = rawResponse;
    confidence = 0.5; // Lower confidence for non-structured response
  }

  // Validate against schema if provided
  if (query.schema && typeof value === 'object') {
    const isValid = validateSchema(value, query.schema);
    if (!isValid) {
      confidence *= 0.5; // Reduce confidence if schema validation fails
    }
  }

  return {
    value,
    confidence,
    source: 'llm-extraction',
    rawText: rawResponse,
  };
}

/**
 * Simple schema validation
 */
function validateSchema(data: unknown, schema: Record<string, unknown>): boolean {
  if (typeof data !== 'object' || data === null) {
    return false;
  }

  const dataObj = data as Record<string, unknown>;

  // Check if all required fields are present
  for (const key of Object.keys(schema)) {
    if (!(key in dataObj)) {
      return false;
    }
  }

  return true;
}
