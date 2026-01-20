/**
 * Prompt templates for LLM extraction
 */

/**
 * Build extraction prompt from page snapshot
 */
export function buildExtractionPrompt(
  pageSnapshot: string,
  query: string,
  context?: string
): string {
  const parts: string[] = [];

  parts.push('# Task');
  parts.push(`Extract the following information from the web page: ${query}`);
  parts.push('');

  if (context) {
    parts.push('# Context');
    parts.push(context);
    parts.push('');
  }

  parts.push('# Page Content');
  parts.push(pageSnapshot);
  parts.push('');

  parts.push('# Instructions');
  parts.push('- Extract only the requested information');
  parts.push('- Return the data in JSON format');
  parts.push('- If the information is not found, return {"found": false}');
  parts.push('- Be precise and accurate');
  parts.push('');

  return parts.join('\n');
}

/**
 * Build license extraction prompt
 */
export function buildLicenseExtractionPrompt(pageSnapshot: string, licenseNumber: string): string {
  return buildExtractionPrompt(
    pageSnapshot,
    `License information for license number ${licenseNumber}`,
    'Look for license status, expiration date, holder name, and any disciplinary actions'
  );
}
