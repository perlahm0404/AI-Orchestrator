/**
 * Keyword Validator - Validate content against SEO keyword strategy
 */

import * as fs from 'fs';
import * as yaml from 'js-yaml';

/**
 * Keyword strategy loaded from YAML
 */
export interface KeywordStrategy {
  primary_keywords: Record<string, string[]>;
  secondary_keywords: Record<string, string[]>;
  long_tail_keywords: Record<string, string[]>;
  lsi_terms: Record<string, string[]>;
  content_guidelines: {
    keyword_density: {
      primary_keyword: { min: number; max: number; target: number };
      secondary_keywords: { min: number; max: number };
    };
    keyword_placement: {
      required: string[];
      recommended: string[];
    };
  };
}

/**
 * Keyword analysis for a single keyword
 */
export interface KeywordAnalysis {
  primaryKeyword: string;
  density: number;  // Percentage
  inTitle: boolean;
  inH1: boolean;
  inFirstParagraph: boolean;
  count: number;
}

/**
 * Content validation report
 */
export interface ValidationReport {
  passed: boolean;
  seoScore: number;  // 0-100
  issues: string[];
  suggestions: string[];
  keywordAnalysis: KeywordAnalysis;
}

/**
 * Validates content against keyword strategy
 *
 * Features:
 * - Keyword density checking
 * - Placement validation (title, H1, first paragraph)
 * - Structure analysis (headings, word count)
 * - LSI term coverage
 */
export class KeywordValidator {
  private strategy: KeywordStrategy;

  /**
   * Create validator with keyword strategy
   *
   * @param strategyPath - Path to keyword-strategy.yaml
   */
  constructor(strategyPath: string) {
    const content = fs.readFileSync(strategyPath, 'utf8');
    this.strategy = yaml.load(content) as KeywordStrategy;
  }

  /**
   * Validate markdown content against keyword strategy
   *
   * @param markdown - Markdown content to validate
   * @param targetKeywords - Target keywords (primary first)
   * @returns Validation report with SEO score
   */
  validateContent(markdown: string, targetKeywords: string[]): ValidationReport {
    const report: ValidationReport = {
      passed: false,
      seoScore: 0,
      issues: [],
      suggestions: [],
      keywordAnalysis: {
        primaryKeyword: '',
        density: 0,
        inTitle: false,
        inH1: false,
        inFirstParagraph: false,
        count: 0
      }
    };

    if (targetKeywords.length === 0) {
      report.issues.push('No target keywords provided');
      return report;
    }

    // Parse markdown
    const { title, h1, firstParagraph, body } = this._parseMarkdown(markdown);
    const wordCount = body.split(/\s+/).filter(w => w.length > 0).length;

    const primaryKeyword = targetKeywords[0].toLowerCase();

    // Count keyword occurrences
    const keywordCount = this._countKeywordOccurrences(body, primaryKeyword);
    const density = wordCount > 0 ? (keywordCount / wordCount) * 100 : 0;

    // Check placement
    const inTitle = title.toLowerCase().includes(primaryKeyword);
    const inH1 = h1.toLowerCase().includes(primaryKeyword);
    const inFirstPara = firstParagraph.toLowerCase().includes(primaryKeyword);

    // Build keyword analysis
    report.keywordAnalysis = {
      primaryKeyword,
      density,
      inTitle,
      inH1,
      inFirstParagraph: inFirstPara,
      count: keywordCount
    };

    // Calculate score
    let score = 0;

    // === DENSITY (40 points) ===
    const minDensity = this.strategy.content_guidelines.keyword_density.primary_keyword.min;
    const maxDensity = this.strategy.content_guidelines.keyword_density.primary_keyword.max;

    if (density >= minDensity && density <= maxDensity) {
      score += 40;
    } else if (keywordCount > 0) {
      score += 20;
      if (density < minDensity) {
        report.issues.push(`Keyword density ${density.toFixed(2)}% below minimum ${minDensity}%`);
      } else {
        report.issues.push(`Keyword density ${density.toFixed(2)}% above maximum ${maxDensity}%`);
      }
    } else {
      report.issues.push('Primary keyword not found in content');
    }

    // === PLACEMENT (30 points) ===
    if (inTitle) {
      score += 10;
    } else {
      report.issues.push('Primary keyword not in title');
    }

    if (inH1) {
      score += 10;
    } else {
      report.issues.push('Primary keyword not in H1');
    }

    if (inFirstPara) {
      score += 10;
    } else {
      report.issues.push('Primary keyword not in first paragraph');
    }

    // === STRUCTURE (30 points) ===
    const h2Count = (markdown.match(/^## /gm) || []).length;
    const h3Count = (markdown.match(/^### /gm) || []).length;

    if (h2Count >= 3 && h3Count >= 2) {
      score += 30;
    } else if (h2Count >= 2) {
      score += 20;
      report.suggestions.push('Add more subheadings (H2/H3) for better structure');
    } else {
      score += 10;
      report.issues.push('Insufficient heading structure (need at least 3 H2 and 2 H3)');
    }

    // Final score and pass/fail
    report.seoScore = Math.round(score);
    report.passed = report.seoScore >= 50;

    // Add suggestions
    if (wordCount < 1000) {
      report.suggestions.push('Consider adding more content (target: 1500-2500 words)');
    }

    if (keywordCount === 0) {
      report.suggestions.push(`Add "${primaryKeyword}" to your content`);
    }

    return report;
  }

  /**
   * Check keyword density for a specific keyword
   *
   * @param text - Text content
   * @param keyword - Keyword to check
   * @returns Density as percentage
   */
  checkKeywordDensity(text: string, keyword: string): number {
    const words = text.split(/\s+/).filter(w => w.length > 0).length;
    if (words === 0) return 0;

    const count = this._countKeywordOccurrences(text, keyword);
    return (count / words) * 100;
  }

  /**
   * Validate keyword placement in specific locations
   *
   * @param markdown - Markdown content
   * @param keyword - Keyword to check
   * @returns Placement validation result
   */
  validatePlacement(markdown: string, keyword: string): {
    inTitle: boolean;
    inH1: boolean;
    inFirstParagraph: boolean;
  } {
    const { title, h1, firstParagraph } = this._parseMarkdown(markdown);
    const keywordLower = keyword.toLowerCase();

    return {
      inTitle: title.toLowerCase().includes(keywordLower),
      inH1: h1.toLowerCase().includes(keywordLower),
      inFirstParagraph: firstParagraph.toLowerCase().includes(keywordLower)
    };
  }

  // ===== Private helpers =====

  /**
   * Parse markdown into components
   */
  private _parseMarkdown(markdown: string): {
    title: string;
    h1: string;
    firstParagraph: string;
    body: string;
  } {
    const lines = markdown.split('\n');
    let h1 = '';
    let firstParagraph = '';

    // Skip frontmatter
    let inFrontmatter = false;
    let bodyStart = 0;

    for (let i = 0; i < lines.length; i++) {
      if (lines[i] === '---') {
        if (!inFrontmatter) {
          inFrontmatter = true;
        } else {
          bodyStart = i + 1;
          break;
        }
      }
    }

    const bodyLines = lines.slice(bodyStart);

    // Find H1
    for (const line of bodyLines) {
      if (line.startsWith('# ')) {
        h1 = line.substring(2).trim();
        break;
      }
    }

    // Find first non-heading paragraph
    for (const line of bodyLines) {
      if (line.trim() && !line.startsWith('#')) {
        firstParagraph = line.trim();
        break;
      }
    }

    return {
      title: h1,  // Use H1 as title
      h1,
      firstParagraph,
      body: bodyLines.join(' ')
    };
  }

  /**
   * Count keyword occurrences (case-insensitive)
   */
  private _countKeywordOccurrences(text: string, keyword: string): number {
    // Escape special regex characters
    const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(escapedKeyword, 'gi');
    return (text.match(regex) || []).length;
  }
}
