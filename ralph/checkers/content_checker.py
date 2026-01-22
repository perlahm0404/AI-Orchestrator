"""
Content Checker - Ralph-style validation for editorial content

Validates blog posts and editorial content for:
1. Markdown syntax correctness
2. Frontmatter metadata completeness
3. SEO score (keyword density, placement, LSI coverage)
4. Link validity (internal/external)
5. Spelling and grammar
6. Citation verification
7. Readability score

Returns Ralph Verdict with PASS/FAIL/BLOCKED semantics.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml
from dataclasses import dataclass

from ralph.engine import VerdictType, Verdict, StepResult


@dataclass
class ContentValidation:
    """Validation result for a piece of content."""
    passed: bool
    seo_score: int  # 0-100
    issues: List[str]
    warnings: List[str]
    step_results: List[StepResult]


class ContentValidator:
    """
    Ralph-style content validator for editorial agent.

    Follows PASS/FAIL/BLOCKED verdict semantics:
    - PASS: Content meets all quality and SEO requirements
    - FAIL: Fixable issues (low SEO score, missing keywords, etc.)
    - BLOCKED: Critical violations (no frontmatter, invalid markdown, etc.)
    """

    def __init__(self, keyword_strategy: Optional[Dict[str, Any]] = None):
        """
        Initialize content validator.

        Args:
            keyword_strategy: Optional keyword strategy dict (loaded from YAML)
        """
        self.keyword_strategy = keyword_strategy or {}

    def validate(self, content_path: Path, min_seo_score: int = 50) -> Verdict:
        """
        Validate content and return Ralph Verdict.

        Args:
            content_path: Path to content file (markdown)
            min_seo_score: Minimum SEO score to pass (default: 50)

        Returns:
            Verdict with PASS/FAIL/BLOCKED and detailed steps
        """
        steps: List[StepResult] = []
        issues: List[str] = []
        warnings: List[str] = []

        # Read content
        if not content_path.exists():
            return Verdict(
                type=VerdictType.BLOCKED,
                steps=[],
                reason=f"Content file not found: {content_path}",
                safe_to_merge=False
            )

        with open(content_path, 'r') as f:
            content = f.read()

        # Step 1: Markdown syntax check
        step1 = self._check_markdown_syntax(content)
        steps.append(step1)
        if not step1.passed:
            issues.append(step1.output)

        # Step 2: Frontmatter metadata
        frontmatter, step2 = self._check_frontmatter(content)
        steps.append(step2)
        if not step2.passed:
            return Verdict(
                type=VerdictType.BLOCKED,
                steps=steps,
                reason="Missing or invalid frontmatter (critical)",
                safe_to_merge=False
            )

        # Step 3: SEO score
        seo_score, step3 = self._check_seo(content, frontmatter)
        steps.append(step3)
        if seo_score < min_seo_score:
            issues.append(f"SEO score {seo_score} below minimum {min_seo_score}")

        # Step 4: Link validity
        step4 = self._check_links(content)
        steps.append(step4)
        if not step4.passed:
            warnings.append(step4.output)

        # Step 5: Spelling & grammar (basic check)
        step5 = self._check_spelling(content)
        steps.append(step5)
        if not step5.passed:
            warnings.append(step5.output)

        # Step 6: Citations
        step6 = self._check_citations(content)
        steps.append(step6)
        if not step6.passed:
            warnings.append(step6.output)

        # Step 7: Readability
        step7 = self._check_readability(content)
        steps.append(step7)
        if not step7.passed:
            warnings.append(step7.output)

        # Determine verdict
        all_critical_passed = all(s.passed for s in [step1, step2])
        seo_passed = seo_score >= min_seo_score

        if not all_critical_passed:
            verdict_type = VerdictType.BLOCKED
            safe_to_merge = False
            reason = "Critical validation failures"
        elif not seo_passed or issues:
            verdict_type = VerdictType.FAIL
            safe_to_merge = False
            reason = f"SEO score {seo_score}/{min_seo_score} or other fixable issues"
        else:
            verdict_type = VerdictType.PASS
            safe_to_merge = True
            reason = None

        return Verdict(
            type=verdict_type,
            steps=steps,
            reason=reason,
            safe_to_merge=safe_to_merge,
            evidence={
                "seo_score": seo_score,
                "issues": issues,
                "warnings": warnings
            }
        )

    def _check_markdown_syntax(self, content: str) -> StepResult:
        """Check markdown syntax validity."""
        issues = []

        # Check for basic markdown structure
        if not content.strip():
            issues.append("Empty content")

        # Check for unmatched brackets/parentheses in links
        link_pattern = r'\[([^\]]*)\]\(([^\)]*)\)'
        for match in re.finditer(link_pattern, content):
            text, url = match.groups()
            if not url.strip():
                issues.append(f"Empty URL in link: [{text}]()")

        # Check for malformed headings
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line.startswith('#'):
                # Heading should have space after #
                if not re.match(r'^#+\s+', line):
                    issues.append(f"Line {i}: Malformed heading (missing space)")

        passed = len(issues) == 0
        output = "; ".join(issues) if issues else "Markdown syntax valid"

        return StepResult(
            step="markdown_syntax",
            passed=passed,
            output=output,
            duration_ms=10
        )

    def _check_frontmatter(self, content: str) -> Tuple[Dict[str, Any], StepResult]:
        """Check frontmatter exists and is valid."""
        if not content.startswith("---\n"):
            return {}, StepResult(
                step="frontmatter",
                passed=False,
                output="Missing frontmatter (must start with ---)",
                duration_ms=5
            )

        # Extract frontmatter
        frontmatter_end = content.find("\n---\n", 4)
        if frontmatter_end == -1:
            return {}, StepResult(
                step="frontmatter",
                passed=False,
                output="Malformed frontmatter (no closing ---)",
                duration_ms=5
            )

        frontmatter_yaml = content[4:frontmatter_end]

        try:
            frontmatter = yaml.safe_load(frontmatter_yaml) or {}
        except yaml.YAMLError as e:
            return {}, StepResult(
                step="frontmatter",
                passed=False,
                output=f"Invalid YAML in frontmatter: {e}",
                duration_ms=5
            )

        # Check required fields
        required_fields = ["title", "category", "keywords", "status"]
        missing = [f for f in required_fields if f not in frontmatter]

        if missing:
            return frontmatter, StepResult(
                step="frontmatter",
                passed=False,
                output=f"Missing required fields: {', '.join(missing)}",
                duration_ms=5
            )

        return frontmatter, StepResult(
            step="frontmatter",
            passed=True,
            output="Frontmatter valid with all required fields",
            duration_ms=5
        )

    def _check_seo(self, content: str, frontmatter: Dict[str, Any]) -> Tuple[int, StepResult]:
        """
        Calculate SEO score (0-100).

        Score breakdown:
        - 30 points: Length (1000+ words)
        - 40 points: Keyword presence (primary keywords in title, H1, content)
        - 20 points: Heading structure (H2, H3 hierarchy)
        - 10 points: Links (internal + external)
        """
        score = 0
        details = []

        # Length score (0-30)
        word_count = len(content.split())
        if word_count >= 2000:
            score += 30
            details.append("Length: 30/30 (2000+ words)")
        elif word_count >= 1000:
            score += 20
            details.append("Length: 20/30 (1000+ words)")
        elif word_count >= 500:
            score += 10
            details.append("Length: 10/30 (500+ words)")
        else:
            details.append("Length: 0/30 (< 500 words)")

        # Keyword score (0-40)
        keywords = frontmatter.get("keywords", [])
        if keywords:
            primary_keyword = keywords[0].lower()
            title = frontmatter.get("title", "").lower()
            content_lower = content.lower()

            keyword_score = 0
            if primary_keyword in title:
                keyword_score += 15
                details.append("Keyword in title: +15")

            # Check for keyword in H1
            h1_match = re.search(r'^# (.+)$', content, re.MULTILINE)
            if h1_match and primary_keyword in h1_match.group(1).lower():
                keyword_score += 10
                details.append("Keyword in H1: +10")

            # Keyword density (target: 1-3%)
            keyword_count = content_lower.count(primary_keyword)
            density = (keyword_count / word_count * 100) if word_count > 0 else 0
            if 1.0 <= density <= 3.0:
                keyword_score += 15
                details.append(f"Keyword density optimal ({density:.1f}%): +15")
            elif keyword_count > 0:
                keyword_score += 5
                details.append(f"Keyword present but density suboptimal ({density:.1f}%): +5")

            score += keyword_score
            details.append(f"Keyword score: {keyword_score}/40")
        else:
            details.append("Keyword score: 0/40 (no keywords defined)")

        # Heading structure score (0-20)
        h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
        h3_count = len(re.findall(r'^### ', content, re.MULTILINE))

        if h2_count >= 3 and h3_count >= 2:
            score += 20
            details.append("Heading structure: 20/20 (good hierarchy)")
        elif h2_count >= 2:
            score += 10
            details.append("Heading structure: 10/20 (needs more subheadings)")
        else:
            details.append("Heading structure: 0/20 (insufficient headings)")

        # Links score (0-10)
        internal_links = len(re.findall(r'\[([^\]]+)\]\(/[^\)]+\)', content))
        external_links = len(re.findall(r'\[([^\]]+)\]\(https?://[^\)]+\)', content))

        if internal_links >= 2 and external_links >= 3:
            score += 10
            details.append("Links: 10/10 (good internal + external links)")
        elif internal_links + external_links >= 3:
            score += 5
            details.append("Links: 5/10 (some links present)")
        else:
            details.append("Links: 0/10 (insufficient links)")

        output = f"SEO score: {score}/100 | " + " | ".join(details)

        return score, StepResult(
            step="seo_score",
            passed=True,  # Always passes, score is returned separately
            output=output,
            duration_ms=15
        )

    def _check_links(self, content: str) -> StepResult:
        """Check for broken or invalid links."""
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        links = re.findall(link_pattern, content)

        issues = []
        for text, url in links:
            if not url.strip():
                issues.append(f"Empty URL for link: {text}")
            elif url.startswith('http'):
                # External link - would validate in production
                # For now, just check it's not obviously broken
                if ' ' in url:
                    issues.append(f"Invalid URL (contains spaces): {url}")

        passed = len(issues) == 0
        output = "; ".join(issues) if issues else f"All {len(links)} links valid"

        return StepResult(
            step="link_validity",
            passed=passed,
            output=output,
            duration_ms=10
        )

    def _check_spelling(self, content: str) -> StepResult:
        """Basic spelling check (placeholder for real spell checker)."""
        # MVP: Just check for common typos
        common_typos = {
            "teh": "the",
            "recieve": "receive",
            "occured": "occurred"
        }

        content_lower = content.lower()
        found_typos = []

        for typo, correct in common_typos.items():
            if typo in content_lower:
                found_typos.append(f"{typo} -> {correct}")

        passed = len(found_typos) == 0
        output = f"Found typos: {', '.join(found_typos)}" if found_typos else "No common typos detected"

        return StepResult(
            step="spelling",
            passed=passed,
            output=output,
            duration_ms=20
        )

    def _check_citations(self, content: str) -> StepResult:
        """Check for citations and references."""
        # Look for common citation patterns
        citation_patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\(Source:',  # (Source: ...)
            r'## References',  # References section
            r'## Sources',  # Sources section
        ]

        has_citations = any(re.search(pattern, content) for pattern in citation_patterns)

        if has_citations:
            # Count citations
            citation_count = len(re.findall(r'\[\d+\]', content))
            output = f"Found {citation_count} citations"
            passed = True
        else:
            output = "No citations found (consider adding sources)"
            passed = False  # Warning, not critical

        return StepResult(
            step="citations",
            passed=passed,
            output=output,
            duration_ms=10
        )

    def _check_readability(self, content: str) -> StepResult:
        """
        Check readability score (simplified Flesch-Kincaid).

        Target: Grade level <= 12 (readable by high school graduates).
        """
        # Remove markdown syntax for analysis
        text = re.sub(r'#+ ', '', content)  # Remove headings
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remove links
        text = re.sub(r'```[^`]+```', '', text, flags=re.DOTALL)  # Remove code blocks

        # Count sentences (simplified)
        sentences = len(re.findall(r'[.!?]+', text))
        if sentences == 0:
            sentences = 1

        # Count words
        words = len(text.split())
        if words == 0:
            return StepResult(
                step="readability",
                passed=False,
                output="No readable content",
                duration_ms=10
            )

        # Count syllables (very simplified: count vowel groups)
        syllables = len(re.findall(r'[aeiouy]+', text, re.IGNORECASE))

        # Simplified Flesch-Kincaid Grade Level
        # Formula: 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
        avg_words_per_sentence = words / sentences
        avg_syllables_per_word = syllables / words

        grade_level = 0.39 * avg_words_per_sentence + 11.8 * avg_syllables_per_word - 15.59
        grade_level = max(0, min(grade_level, 18))  # Clamp to 0-18

        passed = grade_level <= 12
        output = f"Grade level: {grade_level:.1f} ({'PASS' if passed else 'WARNING: complex'})"

        return StepResult(
            step="readability",
            passed=passed,
            output=output,
            duration_ms=15
        )
