/**
 * Tests for AI snapshot generator
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { chromium, type Browser, type Page } from 'playwright';
import { generateSnapshot, formatSnapshotForLLM } from '../src/ai-snapshot.js';

describe('AI Snapshot', () => {
  let browser: Browser;
  let page: Page;

  beforeEach(async () => {
    browser = await chromium.launch({ headless: true });
    page = await browser.newPage();
  });

  afterEach(async () => {
    await browser.close();
  });

  it('should generate snapshot for simple page', async () => {
    await page.setContent(`
      <html>
        <head><title>Test Page</title></head>
        <body>
          <h1>Welcome</h1>
          <button>Click me</button>
          <a href="/test">Link</a>
        </body>
      </html>
    `);

    const snapshot = await generateSnapshot(page);

    expect(snapshot.title).toBe('Test Page');
    expect(snapshot.url).toContain('about:blank');
    expect(snapshot.interactiveElements.length).toBeGreaterThan(0);
  });

  it('should extract interactive elements', async () => {
    await page.setContent(`
      <html>
        <body>
          <button>Submit</button>
          <a href="/test">Link</a>
          <div role="button">Custom Button</div>
        </body>
      </html>
    `);

    const snapshot = await generateSnapshot(page);

    expect(snapshot.interactiveElements).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          type: 'button',
          label: expect.stringContaining('Submit'),
        }),
        expect.objectContaining({
          type: 'link',
        }),
      ])
    );
  });

  it('should extract form fields', async () => {
    await page.setContent(`
      <html>
        <body>
          <form>
            <input type="text" id="username" placeholder="Enter username" required />
            <input type="password" id="password" placeholder="Enter password" />
            <textarea id="bio" placeholder="Your bio"></textarea>
          </form>
        </body>
      </html>
    `);

    const snapshot = await generateSnapshot(page);

    expect(snapshot.formFields.length).toBe(3);
    expect(snapshot.formFields[0]).toMatchObject({
      type: 'text',
      placeholder: 'Enter username',
      required: true,
    });
  });

  it('should detect modals', async () => {
    await page.setContent(`
      <html>
        <body>
          <div role="dialog">Modal content</div>
        </body>
      </html>
    `);

    const snapshot = await generateSnapshot(page);

    expect(snapshot.metadata.hasModals).toBe(true);
  });

  it('should format snapshot as LLM-friendly text', async () => {
    await page.setContent(`
      <html>
        <head><title>Test Page</title></head>
        <body>
          <main>
            <h1>Welcome</h1>
            <button>Click</button>
          </main>
        </body>
      </html>
    `);

    const snapshot = await generateSnapshot(page);
    const formatted = formatSnapshotForLLM(snapshot);

    expect(formatted).toContain('# Page: Test Page');
    expect(formatted).toContain('## Interactive Elements');
    expect(formatted).toContain('button');
  });
});
