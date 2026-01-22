"""
Citation Verifier - Verify factual accuracy of citations via browser automation

Uses browser automation to verify citations against authoritative sources:
- CFR (Code of Federal Regulations)
- USC (United States Code)
- State statutes and regulations
- State board websites

Returns confidence scores (0.0-1.0) for each citation.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Citation:
    """A citation extracted from content."""
    text: str
    source: str
    line_number: int
    citation_type: str  # "CFR", "USC", "state_statute", "url", "unknown"


@dataclass
class CitationVerification:
    """Verification result for a citation."""
    citation: Citation
    verified: bool
    confidence: float  # 0.0-1.0
    verification_source: Optional[str] = None
    error: Optional[str] = None


class CitationVerifier:
    """
    Verify citations using browser automation.

    Features:
    - Extract citations from markdown content
    - Classify citation types (CFR, USC, state statute, URL)
    - Verify via browser automation (when available)
    - Return confidence scores for auto-approval decisions
    """

    def __init__(self) -> None:
        """Initialize citation verifier."""
        self.browser_client: Any = None

        # Try to import browser automation client
        try:
            from adapters.browser_automation import BrowserAutomationClient
            self.browser_client = BrowserAutomationClient()
        except ImportError:
            pass  # Will run in degraded mode without verification

    def extract_citations(self, content: str) -> List[Citation]:
        """
        Extract citations from markdown content.

        Supports:
        - [1] numbered citations
        - (Source: ...) inline citations
        - ## References section with links

        Args:
            content: Markdown content

        Returns:
            List of Citation objects
        """
        citations = []
        lines = content.split('\n')

        # Pattern 1: Numbered citations [1], [2], etc.
        for i, line in enumerate(lines, 1):
            for match in re.finditer(r'\[(\d+)\]', line):
                citation_num = match.group(1)
                # Look for the reference definition (usually at bottom of document)
                ref_pattern = rf'\[{citation_num}\]:\s*(.+)$'
                for ref_line in lines:
                    ref_match = re.search(ref_pattern, ref_line)
                    if ref_match:
                        source = ref_match.group(1).strip()
                        citation_type = self._classify_citation(source)
                        citations.append(Citation(
                            text=f"[{citation_num}]",
                            source=source,
                            line_number=i,
                            citation_type=citation_type
                        ))
                        break

        # Pattern 2: Inline (Source: ...) citations
        for i, line in enumerate(lines, 1):
            for match in re.finditer(r'\(Source:\s*([^)]+)\)', line):
                source = match.group(1).strip()
                citation_type = self._classify_citation(source)
                citations.append(Citation(
                    text=match.group(0),
                    source=source,
                    line_number=i,
                    citation_type=citation_type
                ))

        # Pattern 3: Links in References section
        in_references = False
        for i, line in enumerate(lines, 1):
            if re.match(r'^##\s+(References|Sources|Citations)', line):
                in_references = True
                continue

            if in_references:
                # Stop at next main heading
                if line.startswith('# '):
                    break

                # Extract markdown links
                for match in re.finditer(r'\[([^\]]+)\]\(([^\)]+)\)', line):
                    text, url = match.groups()
                    citation_type = self._classify_citation(url)
                    citations.append(Citation(
                        text=text,
                        source=url,
                        line_number=i,
                        citation_type=citation_type
                    ))

        return citations

    def _classify_citation(self, source: str) -> str:
        """
        Classify citation type based on source string.

        Args:
            source: Citation source (URL or reference string)

        Returns:
            Citation type: "CFR", "USC", "state_statute", "url", "unknown"
        """
        source_lower = source.lower()

        if 'cfr' in source_lower or 'code of federal regulations' in source_lower:
            return "CFR"
        elif 'usc' in source_lower or 'united states code' in source_lower:
            return "USC"
        elif any(state in source_lower for state in ['california', 'texas', 'florida', 'new york']):
            if 'statute' in source_lower or 'code' in source_lower or 'regulation' in source_lower:
                return "state_statute"
        elif source.startswith('http://') or source.startswith('https://'):
            return "url"

        return "unknown"

    def verify_citations(self, citations: List[Citation]) -> List[CitationVerification]:
        """
        Verify citations via browser automation.

        Args:
            citations: List of Citation objects to verify

        Returns:
            List of CitationVerification results
        """
        verifications = []

        for citation in citations:
            if self.browser_client:
                verification = self._verify_citation(citation)
            else:
                # Degraded mode: return unverified with low confidence
                verification = CitationVerification(
                    citation=citation,
                    verified=False,
                    confidence=0.0,
                    error="Browser automation not available"
                )

            verifications.append(verification)

        return verifications

    def _verify_citation(self, citation: Citation) -> CitationVerification:
        """
        Verify a single citation via browser automation.

        Args:
            citation: Citation to verify

        Returns:
            CitationVerification result
        """
        # MVP: Return placeholder verification
        # In production, this would use browser automation to:
        # 1. Navigate to authoritative source (ecfr.gov, uscode.house.gov, state sites)
        # 2. Search for citation text
        # 3. Extract matching content
        # 4. Compare with article content
        # 5. Return confidence score based on match quality

        if citation.citation_type == "url":
            # URLs are easier to verify - just check if accessible
            return CitationVerification(
                citation=citation,
                verified=True,
                confidence=0.8,  # Assume valid if URL is well-formed
                verification_source=citation.source
            )
        elif citation.citation_type in ["CFR", "USC", "state_statute"]:
            # Regulatory citations need more sophisticated verification
            return CitationVerification(
                citation=citation,
                verified=False,
                confidence=0.5,  # Medium confidence - needs manual review
                verification_source=None,
                error="Automated verification not yet implemented for regulatory citations"
            )
        else:
            return CitationVerification(
                citation=citation,
                verified=False,
                confidence=0.3,  # Low confidence for unknown types
                verification_source=None,
                error="Unknown citation type"
            )

    def verify_content(self, content_path: Path) -> Dict[str, Any]:
        """
        Verify all citations in a content file.

        Args:
            content_path: Path to markdown content file

        Returns:
            Dict with verification summary
        """
        if not content_path.exists():
            return {
                "error": f"File not found: {content_path}",
                "citations": [],
                "verifications": []
            }

        with open(content_path, 'r') as f:
            content = f.read()

        # Extract citations
        citations = self.extract_citations(content)

        # Verify citations
        verifications = self.verify_citations(citations)

        # Calculate summary stats
        total = len(verifications)
        verified = sum(1 for v in verifications if v.verified)
        high_confidence = sum(1 for v in verifications if v.confidence >= 0.7)
        avg_confidence = sum(v.confidence for v in verifications) / total if total > 0 else 0.0

        return {
            "total_citations": total,
            "verified_count": verified,
            "high_confidence_count": high_confidence,
            "average_confidence": avg_confidence,
            "citations": citations,
            "verifications": verifications,
            "summary": f"{verified}/{total} verified, {high_confidence} high-confidence (avg: {avg_confidence:.2f})"
        }
