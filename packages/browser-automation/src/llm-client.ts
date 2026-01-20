/**
 * LLM client for Claude API
 */

/**
 * Claude API response
 */
export interface ClaudeResponse {
  content: Array<{
    type: string;
    text: string;
  }>;
  role: string;
  model: string;
}

/**
 * Call Claude API for structured extraction
 */
export async function callClaude(prompt: string, schema?: Record<string, unknown>): Promise<string> {
  const apiKey = process.env.ANTHROPIC_API_KEY;

  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY environment variable is required');
  }

  const systemPrompt = schema
    ? `You are a data extraction assistant. Extract the requested information and return it as valid JSON matching this schema: ${JSON.stringify(schema)}`
    : 'You are a helpful assistant that extracts structured data from web pages.';

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: 'claude-3-haiku-20240307',
      max_tokens: 1024,
      system: systemPrompt,
      messages: [
        {
          role: 'user',
          content: prompt,
        },
      ],
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Claude API error: ${response.status} - ${error}`);
  }

  const data = (await response.json()) as ClaudeResponse;

  return data.content[0]?.text || '';
}
