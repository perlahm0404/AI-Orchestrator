#!/usr/bin/env node

/**
 * Browser Automation Package
 * CLI entry point for JSON stdin/stdout communication
 */

import { executeCommand } from './cli.js';

// Export types and modules for programmatic usage
export * from './types.js';
export * from './session-manager.js';
export * from './credential-vault.js';
export * from './audit-logger.js';
export * from './ai-snapshot.js';
export * from './element-finder.js';
export * from './data-extractor.js';
export * from './adapters/index.js';

export const version = '0.1.0';

/**
 * CLI mode: Read JSON from stdin, execute command, write result to stdout
 */
async function cli() {
  try {
    // Read input from stdin
    const input = await readStdin();
    const data = JSON.parse(input);

    const { command, ...params } = data;

    if (!command) {
      throw new Error('Command is required');
    }

    // Execute command
    const result = await executeCommand(command, params);

    // Write result to stdout as JSON
    process.stdout.write(JSON.stringify({ success: true, result }));
    process.exit(0);
  } catch (error) {
    // Write error to stdout as JSON
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    process.stdout.write(JSON.stringify({ success: false, error: errorMessage }));
    process.exit(1);
  }
}

/**
 * Read all data from stdin
 */
function readStdin(): Promise<string> {
  return new Promise((resolve) => {
    const chunks: string[] = [];

    process.stdin.setEncoding('utf8');

    process.stdin.on('data', (chunk: string) => {
      chunks.push(chunk);
    });

    process.stdin.on('end', () => {
      resolve(chunks.join(''));
    });
  });
}

// Run CLI if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  cli();
}
