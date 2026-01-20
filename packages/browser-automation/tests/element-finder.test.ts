/**
 * Tests for element finder
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { chromium, type Browser, type Page } from 'playwright';
import { findElement, findElements, waitForElement, elementExists } from '../src/element-finder.js';

describe('Element Finder', () => {
  let browser: Browser;
  let page: Page;

  beforeEach(async () => {
    browser = await chromium.launch({ headless: true });
    page = await browser.newPage();
  });

  afterEach(async () => {
    await browser.close();
  });

  it('should find element by role', async () => {
    await page.setContent(`
      <html>
        <body>
          <button>Click me</button>
        </body>
      </html>
    `);

    const element = await findElement(page, { role: 'button' });

    expect(element).not.toBeNull();
    expect(await element?.textContent()).toContain('Click me');
  });

  it('should find element by label', async () => {
    await page.setContent(`
      <html>
        <body>
          <label for="username">Username</label>
          <input id="username" />
        </body>
      </html>
    `);

    const element = await findElement(page, { label: 'Username' });

    expect(element).not.toBeNull();
  });

  it('should find element by text', async () => {
    await page.setContent(`
      <html>
        <body>
          <a href="/test">Click here</a>
        </body>
      </html>
    `);

    const element = await findElement(page, { text: 'Click here' });

    expect(element).not.toBeNull();
    expect(await element?.textContent()).toBe('Click here');
  });

  it('should find element by placeholder', async () => {
    await page.setContent(`
      <html>
        <body>
          <input placeholder="Enter your email" />
        </body>
      </html>
    `);

    const element = await findElement(page, { placeholder: 'Enter your email' });

    expect(element).not.toBeNull();
  });

  it('should find multiple elements', async () => {
    await page.setContent(`
      <html>
        <body>
          <button>Button 1</button>
          <button>Button 2</button>
          <button>Button 3</button>
        </body>
      </html>
    `);

    const elements = await findElements(page, { role: 'button' });

    expect(elements.length).toBe(3);
  });

  it('should check if element exists', async () => {
    await page.setContent(`
      <html>
        <body>
          <button>Exists</button>
        </body>
      </html>
    `);

    const exists = await elementExists(page, { role: 'button', text: 'Exists' });
    const notExists = await elementExists(page, { text: 'Does not exist' });

    expect(exists).toBe(true);
    expect(notExists).toBe(false);
  });

  it('should wait for element to appear', async () => {
    await page.setContent('<html><body></body></html>');

    // Add element after 1 second
    setTimeout(async () => {
      await page.evaluate(() => {
        const button = document.createElement('button');
        button.textContent = 'Delayed Button';
        document.body.appendChild(button);
      });
    }, 1000);

    const element = await waitForElement(page, { text: 'Delayed Button' }, 5000);

    expect(element).not.toBeNull();
  });

  it('should support fuzzy matching', async () => {
    await page.setContent(`
      <html>
        <body>
          <button>Submit Form</button>
        </body>
      </html>
    `);

    // Fuzzy match: partial text should match
    const element = await findElement(page, { text: 'Submit', fuzzyMatch: true });

    expect(element).not.toBeNull();
  });
});
