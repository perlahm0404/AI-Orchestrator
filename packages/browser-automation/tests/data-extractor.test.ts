/**
 * Tests for data extractor
 * Note: These tests mock the LLM API
 */

import { describe, it, expect } from 'vitest';
import { buildExtractionPrompt, buildLicenseExtractionPrompt } from '../src/prompts.js';

describe('Data Extractor', () => {
  it('should build extraction prompt', () => {
    const snapshot = '# Page: Test\n## Interactive Elements\n- button: Submit';
    const query = 'Extract the submit button text';

    const prompt = buildExtractionPrompt(snapshot, query);

    expect(prompt).toContain('Extract the following information');
    expect(prompt).toContain(query);
    expect(prompt).toContain(snapshot);
  });

  it('should build license extraction prompt', () => {
    const snapshot = '# Page: License Verification';
    const licenseNumber = 'A12345';

    const prompt = buildLicenseExtractionPrompt(snapshot, licenseNumber);

    expect(prompt).toContain(licenseNumber);
    expect(prompt).toContain('License information');
    expect(prompt).toContain('disciplinary actions');
  });

  it('should include context in prompt', () => {
    const snapshot = '# Page: Test';
    const query = 'Find the price';
    const context = 'Look in the pricing section';

    const prompt = buildExtractionPrompt(snapshot, query, context);

    expect(prompt).toContain('# Context');
    expect(prompt).toContain(context);
  });
});
