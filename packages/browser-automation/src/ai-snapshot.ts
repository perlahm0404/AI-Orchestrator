/**
 * AI Snapshot Generator
 * Converts DOM to LLM-friendly text representation using accessibility tree
 */

import type { Page } from 'playwright';
import type { PageSnapshot, InteractiveElement, FormField, Landmark, PageMetadata } from './types.js';

/**
 * Generate stable selector for element
 * Priority: data-testid > id > aria-label > unique CSS
 */
function generateSelector(element: any, index: number): string {
  // Try data-testid first
  if (element.getAttribute && element.getAttribute('data-testid')) {
    return `[data-testid="${element.getAttribute('data-testid')}"]`;
  }

  // Try id
  if (element.id) {
    return `#${element.id}`;
  }

  // Try aria-label
  if (element.getAttribute && element.getAttribute('aria-label')) {
    return `[aria-label="${element.getAttribute('aria-label')}"]`;
  }

  // Fallback to role + index
  const role = element.role || element.tagName?.toLowerCase();
  return `${role}-${index}`;
}

/**
 * Get accessible name for element
 * Follows ARIA accessible name calculation algorithm (simplified)
 */
function getAccessibleName(element: any): string {
  // 1. aria-labelledby
  if (element.getAttribute && element.getAttribute('aria-labelledby')) {
    return `[aria-labelledby=${element.getAttribute('aria-labelledby')}]`;
  }

  // 2. aria-label
  if (element.getAttribute && element.getAttribute('aria-label')) {
    return element.getAttribute('aria-label');
  }

  // 3. Associated label (for inputs)
  if (element.labels && element.labels.length > 0) {
    return element.labels[0].textContent?.trim() || '';
  }

  // 4. placeholder (for inputs)
  if (element.placeholder) {
    return element.placeholder;
  }

  // 5. text content
  if (element.textContent) {
    return element.textContent.trim().slice(0, 100); // Limit to 100 chars
  }

  // 6. alt text (for images)
  if (element.alt) {
    return element.alt;
  }

  // 7. title
  if (element.title) {
    return element.title;
  }

  return '';
}

/**
 * Get surrounding context for element
 * Finds nearest heading or landmark
 */
async function getContext(page: Page, selector: string): Promise<string> {
  try {
    const context = await page.evaluate((sel) => {
      const element = document.querySelector(sel);
      if (!element) return '';

      // Find nearest heading
      let current: Element | null = element;
      while (current && current !== document.body) {
        const heading = current.querySelector('h1, h2, h3, h4, h5, h6');
        if (heading) {
          return heading.textContent?.trim() || '';
        }
        current = current.parentElement;
      }

      // Find nearest landmark
      const landmarks = ['main', 'nav', 'aside', 'footer', 'header', 'section'];
      current = element;
      while (current && current !== document.body) {
        if (landmarks.includes(current.tagName.toLowerCase())) {
          const label = current.getAttribute('aria-label') || current.tagName.toLowerCase();
          return label;
        }
        current = current.parentElement;
      }

      return '';
    }, selector);

    return context || '';
  } catch {
    return '';
  }
}

/**
 * Generate page snapshot for LLM consumption
 */
export async function generateSnapshot(page: Page): Promise<PageSnapshot> {
  const url = page.url();
  const title = await page.title();
  const timestamp = new Date().toISOString();

  // Get viewport size
  const viewport = page.viewportSize() || { width: 1280, height: 720 };

  // Extract interactive elements
  const interactiveElements = await extractInteractiveElements(page);

  // Extract form fields
  const formFields = await extractFormFields(page);

  // Extract landmarks
  const landmarks = await extractLandmarks(page);

  // Check for modals/dialogs
  const hasModals = await page.evaluate(() => {
    return document.querySelectorAll('[role="dialog"], [role="alertdialog"], .modal').length > 0;
  });

  const hasDialogs = await page.evaluate(() => {
    return document.querySelectorAll('dialog[open]').length > 0;
  });

  const metadata: PageMetadata = {
    viewport,
    hasModals,
    hasDialogs,
  };

  return {
    url,
    title,
    timestamp,
    interactiveElements,
    formFields,
    landmarks,
    metadata,
  };
}

/**
 * Extract interactive elements from page
 */
async function extractInteractiveElements(page: Page): Promise<InteractiveElement[]> {
  const elements = await page.evaluate(() => {
    const interactive = Array.from(
      document.querySelectorAll('button, a[href], [role="button"], [role="link"]')
    );

    return interactive
      .filter((el) => {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0; // Only visible elements
      })
      .map((el, index) => {
        const rect = el.getBoundingClientRect();
        return {
          index,
          tagName: el.tagName.toLowerCase(),
          role: el.getAttribute('role') || (el.tagName.toLowerCase() === 'a' ? 'link' : 'button'),
          ariaLabel: el.getAttribute('aria-label') || '',
          textContent: el.textContent?.trim().slice(0, 100) || '',
          id: el.id || '',
          testId: el.getAttribute('data-testid') || '',
          coordinates: { x: Math.round(rect.left), y: Math.round(rect.top) },
        };
      });
  });

  const result: InteractiveElement[] = [];

  for (const el of elements) {
    const label = el.ariaLabel || el.textContent;
    const selector = el.testId
      ? `[data-testid="${el.testId}"]`
      : el.id
        ? `#${el.id}`
        : `${el.role}-${el.index}`;

    const context = await getContext(page, selector);

    result.push({
      id: `${el.role}-${el.index}`,
      type: el.role === 'link' ? 'link' : 'button',
      label,
      selector,
      coordinates: el.coordinates,
      isVisible: true,
      context,
    });
  }

  return result;
}

/**
 * Extract form fields from page
 */
async function extractFormFields(page: Page): Promise<FormField[]> {
  const fields = await page.evaluate(() => {
    const inputs = Array.from(document.querySelectorAll('input, textarea, select'));

    return inputs
      .filter((el) => {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      })
      .map((el, index) => {
        const input = el as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
        return {
          index,
          type: input.type || 'text',
          id: input.id || '',
          name: input.name || '',
          placeholder: (input as HTMLInputElement).placeholder || '',
          required: input.required,
          ariaLabel: input.getAttribute('aria-label') || '',
          testId: input.getAttribute('data-testid') || '',
          value: input.value || '',
        };
      });
  });

  const result: FormField[] = [];

  for (const field of fields) {
    const label = field.ariaLabel || field.placeholder || field.name;
    const selector = field.testId
      ? `[data-testid="${field.testId}"]`
      : field.id
        ? `#${field.id}`
        : `input[name="${field.name}"]`;

    result.push({
      id: `input-${field.index}`,
      type: field.type,
      label,
      value: field.value,
      placeholder: field.placeholder,
      required: field.required,
      selector,
    });
  }

  return result;
}

/**
 * Extract landmarks (major page sections)
 */
async function extractLandmarks(page: Page): Promise<Landmark[]> {
  return page.evaluate(() => {
    const landmarks = Array.from(
      document.querySelectorAll('[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"], [role="complementary"], main, nav, header, footer, aside')
    );

    return landmarks.map((el) => {
      const role = el.getAttribute('role') || el.tagName.toLowerCase();
      const ariaLabel = el.getAttribute('aria-label') || '';
      const id = el.id || '';

      const selector = id ? `#${id}` : `[role="${role}"]`;

      return {
        role,
        label: ariaLabel,
        selector,
      };
    });
  });
}

/**
 * Format snapshot as LLM-friendly text
 */
export function formatSnapshotForLLM(snapshot: PageSnapshot): string {
  const lines: string[] = [];

  lines.push(`# Page: ${snapshot.title}`);
  lines.push(`URL: ${snapshot.url}`);
  lines.push(`Timestamp: ${snapshot.timestamp}`);
  lines.push('');

  // Landmarks
  if (snapshot.landmarks.length > 0) {
    lines.push('## Page Structure');
    for (const landmark of snapshot.landmarks) {
      const label = landmark.label ? ` - ${landmark.label}` : '';
      lines.push(`- ${landmark.role}${label}`);
    }
    lines.push('');
  }

  // Interactive elements
  if (snapshot.interactiveElements.length > 0) {
    lines.push('## Interactive Elements');
    for (const el of snapshot.interactiveElements) {
      const context = el.context ? ` (in ${el.context})` : '';
      lines.push(`- [${el.id}] ${el.type}: "${el.label}"${context}`);
    }
    lines.push('');
  }

  // Form fields
  if (snapshot.formFields.length > 0) {
    lines.push('## Form Fields');
    for (const field of snapshot.formFields) {
      const required = field.required ? ' *' : '';
      const value = field.value ? ` = "${field.value}"` : '';
      lines.push(`- [${field.id}] ${field.type}: "${field.label}"${required}${value}`);
    }
    lines.push('');
  }

  // Metadata
  if (snapshot.metadata.hasModals || snapshot.metadata.hasDialogs) {
    lines.push('## Alerts');
    if (snapshot.metadata.hasModals) lines.push('- Modal dialog is open');
    if (snapshot.metadata.hasDialogs) lines.push('- Dialog is open');
    lines.push('');
  }

  return lines.join('\n');
}
