/**
 * Semantic element finder
 * Locates elements using accessible names and roles instead of brittle selectors
 */

import type { Page, Locator } from 'playwright';
import type { FindElementOptions } from './types.js';

/**
 * Calculate Levenshtein distance for fuzzy text matching
 */
function levenshteinDistance(a: string, b: string): number {
  const matrix: number[][] = [];

  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i];
  }

  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j;
  }

  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1, // substitution
          matrix[i][j - 1] + 1, // insertion
          matrix[i - 1][j] + 1 // deletion
        );
      }
    }
  }

  return matrix[b.length][a.length];
}

/**
 * Check if text matches with fuzzy matching
 */
function fuzzyMatch(text: string, query: string, threshold: number = 0.3): boolean {
  const textLower = text.toLowerCase();
  const queryLower = query.toLowerCase();

  // Exact match
  if (textLower === queryLower) return true;

  // Contains match
  if (textLower.includes(queryLower)) return true;

  // Fuzzy match with Levenshtein distance
  const distance = levenshteinDistance(textLower, queryLower);
  const maxLength = Math.max(text.length, query.length);
  const similarity = 1 - distance / maxLength;

  return similarity >= 1 - threshold;
}

/**
 * Find element using semantic options
 */
export async function findElement(page: Page, options: FindElementOptions): Promise<Locator | null> {
  // Try semantic locators first
  let locator: Locator | null = null;

  // 1. Try by role
  if (options.role) {
    if (options.label) {
      locator = page.getByRole(options.role as any, { name: options.label, exact: !options.fuzzyMatch });
    } else {
      locator = page.getByRole(options.role as any);
    }

    if (await locator.count() > 0) {
      return locator.first();
    }
  }

  // 2. Try by label
  if (options.label) {
    locator = page.getByLabel(options.label, { exact: !options.fuzzyMatch });

    if (await locator.count() > 0) {
      return locator.first();
    }
  }

  // 3. Try by text
  if (options.text) {
    locator = page.getByText(options.text, { exact: !options.fuzzyMatch });

    if (await locator.count() > 0) {
      return locator.first();
    }
  }

  // 4. Try by placeholder
  if (options.placeholder) {
    locator = page.getByPlaceholder(options.placeholder, { exact: !options.fuzzyMatch });

    if (await locator.count() > 0) {
      return locator.first();
    }
  }

  // 5. Fuzzy search fallback
  if (options.fuzzyMatch && (options.label || options.text)) {
    const query = options.label || options.text || '';
    locator = await fuzzyFindElement(page, query);

    if (locator) {
      return locator;
    }
  }

  return null;
}

/**
 * Fuzzy find element by text content
 */
async function fuzzyFindElement(page: Page, query: string): Promise<Locator | null> {
  // Get all interactive elements
  const candidates = await page.evaluate(() => {
    const elements = Array.from(
      document.querySelectorAll('button, a, input, select, textarea, [role="button"], [role="link"]')
    );

    const results: Array<{ text: string; index: number }> = [];

    elements.forEach((el, index) => {
      const input = el as HTMLInputElement;
      const text = (
        el.getAttribute('aria-label') ||
        el.textContent ||
        input.placeholder ||
        ''
      ).trim();

      if (text) {
        results.push({ text, index });
      }
    });

    return results;
  });

  // Find best match
  let bestMatch: { text: string; index: number } | null = null;
  let bestScore = 0;

  for (const candidate of candidates) {
    if (fuzzyMatch(candidate.text, query)) {
      const distance = levenshteinDistance(candidate.text.toLowerCase(), query.toLowerCase());
      const score = 1 - distance / Math.max(candidate.text.length, query.length);

      if (score > bestScore) {
        bestScore = score;
        bestMatch = candidate;
      }
    }
  }

  if (bestMatch) {
    // Return nth element
    const allElements = page.locator('button, a, input, select, textarea, [role="button"], [role="link"]');
    return allElements.nth(bestMatch.index);
  }

  return null;
}

/**
 * Find multiple elements matching criteria
 */
export async function findElements(page: Page, options: FindElementOptions): Promise<Locator[]> {
  const locators: Locator[] = [];

  // Try semantic locators
  let locator: Locator | null = null;

  if (options.role) {
    if (options.label) {
      locator = page.getByRole(options.role as any, { name: options.label, exact: !options.fuzzyMatch });
    } else {
      locator = page.getByRole(options.role as any);
    }
  } else if (options.label) {
    locator = page.getByLabel(options.label, { exact: !options.fuzzyMatch });
  } else if (options.text) {
    locator = page.getByText(options.text, { exact: !options.fuzzyMatch });
  } else if (options.placeholder) {
    locator = page.getByPlaceholder(options.placeholder, { exact: !options.fuzzyMatch });
  }

  if (locator) {
    const count = await locator.count();
    for (let i = 0; i < count; i++) {
      locators.push(locator.nth(i));
    }
  }

  return locators;
}

/**
 * Wait for element to appear
 */
export async function waitForElement(
  page: Page,
  options: FindElementOptions,
  timeout: number = 30000
): Promise<Locator | null> {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const element = await findElement(page, options);

    if (element && (await element.count()) > 0) {
      return element;
    }

    await page.waitForTimeout(500); // Wait 500ms before retrying
  }

  return null;
}

/**
 * Check if element exists
 */
export async function elementExists(page: Page, options: FindElementOptions): Promise<boolean> {
  const element = await findElement(page, options);
  return element !== null && (await element.count()) > 0;
}
