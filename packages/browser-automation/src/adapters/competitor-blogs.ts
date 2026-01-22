/**
 * Competitor Blog Adapter - Analyze competitor content for SEO intelligence
 */

import { BasePortalAdapter } from './base.js';
import type { BrowserSession } from '../session-manager.js';
import { extract } from '../data-extractor.js';
import type { Credential, AuditEntry } from '../types.js';

/**
 * Blog post analysis result
 */
export interface BlogPost {
  url: string;
  title: string;
  metaDescription?: string;
  headings: {
    level: number;  // 1-6
    text: string;
  }[];
  keywords: string[];
  wordCount: string;  // String for CLI JSON compatibility
  readabilityScore?: string;
  readabilityGrade?: string;
  internalLinks: string;
  externalLinks: string;
  images: string;
  publishDate?: string;
  author?: string;
  confidence: number;
  extractedAt: string;
}

/**
 * SEO metadata from page
 */
export interface SEOMetadata {
  title: string;
  description?: string;
  keywords: string[];
  ogTags: Record<string, string>;
  canonicalUrl?: string;
  robots?: string;
  language?: string;
}

/**
 * Link analysis result
 */
interface LinkAnalysis {
  internal: number;
  external: number;
  broken: number;
}

/**
 * Adapter for analyzing competitor blog posts
 *
 * Features:
 * - SEO metadata extraction
 * - Content structure analysis (headings, word count)
 * - Readability scoring (Flesch-Kincaid)
 * - Link profile analysis
 * - Keyword extraction
 */
export class CompetitorBlogAdapter extends BasePortalAdapter {
  name = 'Competitor Blog Analyzer';
  baseUrl = '';  // Set dynamically per competitor

  /**
   * Extract and analyze a blog post
   *
   * @param url - Blog post URL
   * @returns Complete blog post analysis
   */
  async extractBlogPost(url: string): Promise<BlogPost> {
    const session = this.getSession();

    try {
      // Navigate to blog post
      await session.navigate(url);
      await session.page().waitForLoadState('networkidle', { timeout: 10000 });

      // Log navigation
      await this._logAction({
        action: 'navigate',
        url,
        success: true,
        metadata: { purpose: 'competitor_analysis' }
      });

      // Extract main content using LLM
      const contentExtraction = await extract(session.page(), {
        target: 'main article content, headings, and metadata',
        context: 'Blog post or article page. Extract title, headings (H1-H6), word count estimate, and main content.',
        schema: {
          type: 'object',
          properties: {
            title: { type: 'string' },
            headings: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  level: { type: 'number' },
                  text: { type: 'string' }
                }
              }
            },
            wordCount: { type: 'number' },
            author: { type: 'string' },
            publishDate: { type: 'string' }
          },
          required: ['title']
        }
      });

      const extracted = contentExtraction.value as any;

      // Extract SEO metadata
      const metadata = await this._extractSEOMetadata();

      // Analyze links
      const linkAnalysis = await this._analyzeLinkStructure(url);

      // Extract main text for readability analysis
      const mainText = await this._extractMainText();

      // Calculate readability
      const readability = this._calculateReadability(mainText);

      // Count images
      const imageCount = await session.page().locator('img').count();

      // Build result
      const result: BlogPost = {
        url,
        title: extracted.title || metadata.title,
        metaDescription: metadata.description,
        headings: extracted.headings || [],
        keywords: metadata.keywords,
        wordCount: String(extracted.wordCount || this._countWords(mainText)),
        readabilityScore: readability.score !== undefined ? String(readability.score) : undefined,
        readabilityGrade: readability.grade !== undefined ? String(readability.grade) : undefined,
        internalLinks: String(linkAnalysis.internal),
        externalLinks: String(linkAnalysis.external),
        images: String(imageCount),
        publishDate: extracted.publishDate,
        author: extracted.author,
        confidence: contentExtraction.confidence,
        extractedAt: new Date().toISOString()
      };

      // Log extraction success
      await this._logAction({
        action: 'extract_blog_post',
        url,
        success: true,
        metadata: {
          wordCount: result.wordCount,
          readabilityScore: result.readabilityScore || 'N/A',
          confidence: String(result.confidence)
        }
      });

      return result;

    } catch (error) {
      // Log extraction failure
      await this._logAction({
        action: 'extract_blog_post',
        url,
        success: false,
        errorMessage: error instanceof Error ? error.message : String(error)
      });

      throw error;
    }
  }

  /**
   * Extract SEO metadata from page
   *
   * @returns SEO metadata
   */
  async analyzeSEOMetadata(url?: string): Promise<SEOMetadata> {
    const session = this.getSession();

    if (url) {
      await session.navigate(url);
      await session.page().waitForLoadState('networkidle', { timeout: 10000 });
    }

    return await this._extractSEOMetadata();
  }

  /**
   * Extract sitemap URLs from website
   *
   * @param baseUrl - Website base URL
   * @returns Array of blog post URLs found in sitemap
   */
  async extractSiteMap(baseUrl: string): Promise<string[]> {
    const session = this.getSession();
    const urls: string[] = [];

    try {
      // Try common sitemap locations
      const sitemapUrls = [
        `${baseUrl}/sitemap.xml`,
        `${baseUrl}/sitemap_index.xml`,
        `${baseUrl}/blog-sitemap.xml`,
        `${baseUrl}/post-sitemap.xml`
      ];

      for (const sitemapUrl of sitemapUrls) {
        try {
          await session.navigate(sitemapUrl);
          await session.page().waitForLoadState('networkidle', { timeout: 5000 });

          // Extract URLs from XML
          const pageContent = await session.page().content();

          // Simple regex to extract <loc> tags
          const locMatches = pageContent.matchAll(/<loc>(.*?)<\/loc>/g);

          for (const match of locMatches) {
            const url = match[1];
            if (url && url.includes('/blog') || url.includes('/post')) {
              urls.push(url);
            }
          }

          if (urls.length > 0) {
            // Found URLs, stop searching
            break;
          }
        } catch {
          // Try next sitemap location
          continue;
        }
      }

      // Log extraction
      await this._logAction({
        action: 'extract_sitemap',
        url: baseUrl,
        success: true,
        metadata: { urlCount: String(urls.length) }
      });

      return urls;

    } catch (error) {
      await this._logAction({
        action: 'extract_sitemap',
        url: baseUrl,
        success: false,
        errorMessage: error instanceof Error ? error.message : String(error)
      });

      return [];  // Return empty array on failure
    }
  }

  // ===== BasePortalAdapter required methods =====

  async login(_credential: Credential): Promise<void> {
    // No-op: public blog content
  }

  async logout(): Promise<void> {
    // No-op
  }

  async isSessionValid(): Promise<boolean> {
    return true;
  }

  async extractLicenseInfo(_licenseNumber: string): Promise<any> {
    throw new Error('Use extractBlogPost() for competitor blog analysis');
  }

  // ===== Private helpers =====

  /**
   * Extract SEO metadata from current page
   */
  private async _extractSEOMetadata(): Promise<SEOMetadata> {
    const session = this.getSession();

    const metadata = await session.page().evaluate(() => {
      const getMeta = (name: string): string | undefined => {
        const element = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
        return element?.getAttribute('content') || undefined;
      };

      const ogTags: Record<string, string> = {};
      document.querySelectorAll('meta[property^="og:"]').forEach((el) => {
        const property = el.getAttribute('property');
        const content = el.getAttribute('content');
        if (property && content) {
          ogTags[property] = content;
        }
      });

      return {
        title: document.title,
        description: getMeta('description'),
        keywords: getMeta('keywords')?.split(',').map(k => k.trim()) || [],
        ogTags,
        canonicalUrl: document.querySelector('link[rel="canonical"]')?.getAttribute('href') || undefined,
        robots: getMeta('robots'),
        language: document.documentElement.lang || undefined
      };
    });

    return metadata;
  }

  /**
   * Analyze link structure (internal vs external)
   */
  private async _analyzeLinkStructure(currentUrl: string): Promise<LinkAnalysis> {
    const session = this.getSession();

    const analysis = await session.page().evaluate((url) => {
      const currentDomain = new URL(url).hostname;
      let internal = 0;
      let external = 0;
      let broken = 0;

      document.querySelectorAll('a[href]').forEach((link) => {
        const href = link.getAttribute('href');
        if (!href) return;

        try {
          if (href.startsWith('/') || href.startsWith('#')) {
            internal++;
          } else {
            const linkUrl = new URL(href, url);
            if (linkUrl.hostname === currentDomain) {
              internal++;
            } else {
              external++;
            }
          }
        } catch {
          broken++;
        }
      });

      return { internal, external, broken };
    }, currentUrl);

    return analysis;
  }

  /**
   * Extract main text content for readability analysis
   */
  private async _extractMainText(): Promise<string> {
    const session = this.getSession();

    // Try to find main content area
    const mainText = await session.page().evaluate(() => {
      // Try common content selectors
      const selectors = [
        'article',
        'main',
        '[role="main"]',
        '.post-content',
        '.entry-content',
        '.article-content',
        '.content'
      ];

      for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element && element.textContent) {
          return element.textContent.trim();
        }
      }

      // Fallback: use body text
      return document.body.textContent?.trim() || '';
    });

    return mainText;
  }

  /**
   * Calculate readability score using Flesch-Kincaid
   */
  private _calculateReadability(text: string): { score: number; grade: number } {
    const words = text.split(/\s+/).filter(w => w.length > 0).length;
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0).length;
    const syllables = this._countSyllables(text);

    if (words === 0 || sentences === 0) {
      return { score: 0, grade: 0 };
    }

    const avgWordsPerSentence = words / sentences;
    const avgSyllablesPerWord = syllables / words;

    // Flesch Reading Ease
    const score = Math.max(
      0,
      Math.min(100, 206.835 - 1.015 * avgWordsPerSentence - 84.6 * avgSyllablesPerWord)
    );

    // Flesch-Kincaid Grade Level
    const grade = Math.max(
      0,
      Math.min(18, 0.39 * avgWordsPerSentence + 11.8 * avgSyllablesPerWord - 15.59)
    );

    return {
      score: Math.round(score * 10) / 10,
      grade: Math.round(grade * 10) / 10
    };
  }

  /**
   * Count syllables in text (approximate)
   */
  private _countSyllables(text: string): number {
    const words = text.toLowerCase().split(/\s+/);
    let syllableCount = 0;

    for (const word of words) {
      if (word.length === 0) continue;

      // Simple syllable counting heuristic
      const matches = word.match(/[aeiouy]+/g);
      let count = matches ? matches.length : 0;

      // Adjust for silent 'e'
      if (word.endsWith('e')) {
        count--;
      }

      // Ensure at least 1 syllable per word
      syllableCount += Math.max(1, count);
    }

    return syllableCount;
  }

  /**
   * Count words in text
   */
  private _countWords(text: string): number {
    return text.split(/\s+/).filter(w => w.length > 0).length;
  }

  /**
   * Log action to audit trail
   */
  private async _logAction(entry: Partial<AuditEntry>): Promise<void> {
    console.log('[CompetitorBlog]', entry.action, entry.url, entry.success ? '✓' : '✗');
  }
}
