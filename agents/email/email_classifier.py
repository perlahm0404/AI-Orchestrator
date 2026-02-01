"""
Email classification engine with AI-powered categorization and pattern learning.

Analyzes emails and learns patterns to enable bulk labeling operations.
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from agents.email.gmail_client import GmailClient
from agents.email.classification_rules import classify_email

# Default path for pattern persistence
PATTERNS_FILE = Path.home() / '.aibrain' / 'gmail_patterns.json'


class EmailClassifier:
    """AI-powered email classifier with pattern learning."""

    CATEGORIES = ['Personal', 'Business', 'Other']

    def __init__(self, gmail_client: GmailClient):
        """
        Initialize classifier.

        Args:
            gmail_client: Authenticated GmailClient instance
        """
        self.client = gmail_client
        self.patterns: Dict[str, Dict[str, Set[str]]] = {
            'Personal': {'domains': set(), 'keywords': set(), 'senders': set()},
            'Business': {'domains': set(), 'keywords': set(), 'senders': set()},
            'Other': {'domains': set(), 'keywords': set(), 'senders': set()}
        }
        self.classifications: List[Dict[str, Any]] = []  # Training data

    def save_patterns(self, path: Optional[Path] = None) -> None:
        """
        Save learned patterns to JSON file.

        Args:
            path: Path to save patterns (default: ~/.aibrain/gmail_patterns.json)
        """
        save_path = path or PATTERNS_FILE
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert sets to lists for JSON serialization
        patterns_data = {
            category: {
                'domains': sorted(patterns['domains']),
                'senders': sorted(patterns['senders']),
                'keywords': sorted(patterns['keywords'])
            }
            for category, patterns in self.patterns.items()
        }

        # Build final data structure with metadata
        data = {
            'patterns': patterns_data,
            'metadata': {
                'version': 1,
                'total_classifications': len(self.classifications),
                'categories': list(self.CATEGORIES)
            }
        }

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load_patterns(self, path: Optional[Path] = None, merge: bool = True) -> bool:
        """
        Load patterns from JSON file.

        Args:
            path: Path to load patterns from (default: ~/.aibrain/gmail_patterns.json)
            merge: If True, merge with existing patterns. If False, replace them.

        Returns:
            True if patterns were loaded successfully, False if file doesn't exist
        """
        load_path = path or PATTERNS_FILE

        if not load_path.exists():
            return False

        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle both old format (categories at root) and new format (nested under 'patterns')
            patterns_data = data.get('patterns', data)

            # Load patterns for each category
            for category in self.CATEGORIES:
                if category in patterns_data:
                    category_data = patterns_data[category]
                    if merge:
                        # Merge with existing patterns
                        self.patterns[category]['domains'].update(category_data.get('domains', []))
                        self.patterns[category]['senders'].update(category_data.get('senders', []))
                        self.patterns[category]['keywords'].update(category_data.get('keywords', []))
                    else:
                        # Replace existing patterns
                        self.patterns[category]['domains'] = set(category_data.get('domains', []))
                        self.patterns[category]['senders'] = set(category_data.get('senders', []))
                        self.patterns[category]['keywords'] = set(category_data.get('keywords', []))

            return True

        except (json.JSONDecodeError, KeyError):
            # Corrupted file - return False but don't crash
            return False

    def extract_email_metadata(self, message: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract relevant metadata from a Gmail message.

        Args:
            message: Gmail message object

        Returns:
            Dictionary with 'from', 'subject', 'snippet', 'message_id' keys
        """
        headers = message.get('payload', {}).get('headers', [])

        # Extract headers
        from_header = next((h['value'] for h in headers if h['name'] == 'From'), '')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')

        # Extract email address and domain
        email_match = re.search(r'<(.+?)>|(\S+@\S+)', from_header)
        email_address = email_match.group(1) or email_match.group(2) if email_match else from_header
        domain = email_address.split('@')[-1] if '@' in email_address else ''

        return {
            'message_id': message['id'],
            'from': email_address,
            'from_display': from_header,
            'domain': domain,
            'subject': subject,
            'snippet': message.get('snippet', '')
        }

    def suggest_category(self, metadata: Dict[str, str]) -> Tuple[str, str]:
        """
        Suggest a category for an email using learned patterns.

        Args:
            metadata: Email metadata from extract_email_metadata()

        Returns:
            Tuple of (category, reason)
        """
        from_addr = metadata['from'].lower()
        domain = metadata['domain'].lower()
        subject = metadata['subject'].lower()
        snippet = metadata['snippet'].lower()

        # FIRST: Apply refined classification rules (highest priority)
        # These are based on manual review of 22,000+ emails
        rule_category, rule_reason = classify_email(
            metadata['from'],  # Original case
            metadata['subject'],
            metadata['snippet']
        )

        # If the rules have a confident match (not the default), use it
        if rule_reason != 'No clear indicators, defaulting to Other':
            return rule_category, f"Rule-based: {rule_reason}"

        # Check exact sender matches from learned patterns (second priority)
        for category in self.CATEGORIES:
            if from_addr in self.patterns[category]['senders']:
                return category, f"Known sender for {category}"

        # Check domain patterns
        for category in self.CATEGORIES:
            for pattern_domain in self.patterns[category]['domains']:
                if domain.endswith(pattern_domain):
                    return category, f"Domain matches {category} pattern"

        # Check keyword patterns
        text = f"{subject} {snippet}"
        for category in self.CATEGORIES:
            for keyword in self.patterns[category]['keywords']:
                if keyword in text:
                    return category, f"Keyword '{keyword}' matches {category}"

        # Heuristic-based fallback suggestions
        business_indicators = [
            'invoice', 'meeting', 'contract', 'proposal', 'quotation',
            'conference', 'webinar', 'appointment', 'calendar', 'client',
            'vendor', 'purchase order', 'p.o.', 'regards,', 'sincerely,'
        ]

        personal_indicators = [
            'hi ', 'hey ', 'hello ', 'how are you', 'family', 'friend',
            'birthday', 'wedding', 'vacation', 'party', 'dinner'
        ]

        other_indicators = [
            'unsubscribe', 'newsletter', 'promo', 'deal', 'offer',
            'discount', 'sale', 'marketing', 'notification', 'no-reply',
            'noreply', 'do not reply'
        ]

        business_score = sum(1 for ind in business_indicators if ind in text)
        personal_score = sum(1 for ind in personal_indicators if ind in text)
        other_score = sum(1 for ind in other_indicators if ind in text)

        scores = {
            'Business': business_score,
            'Personal': personal_score,
            'Other': other_score
        }

        if max(scores.values()) > 0:
            suggested = max(scores, key=lambda k: scores[k])
            return suggested, f"Heuristic analysis suggests {suggested}"

        return 'Other', 'No clear indicators, defaulting to Other'

    def record_classification(
        self,
        metadata: Dict[str, str],
        category: str,
        user_confirmed: bool = False
    ) -> None:
        """
        Record a classification for pattern learning.

        Args:
            metadata: Email metadata
            category: Chosen category
            user_confirmed: Whether user explicitly confirmed this classification
        """
        self.classifications.append({
            'metadata': metadata,
            'category': category,
            'confirmed': user_confirmed
        })

        # Update patterns if user confirmed
        if user_confirmed:
            self._update_patterns(metadata, category)

    def _update_patterns(self, metadata: Dict[str, str], category: str) -> None:
        """
        Update learned patterns based on a confirmed classification.

        Args:
            metadata: Email metadata
            category: Category to update patterns for
        """
        from_addr = metadata['from'].lower()
        domain = metadata['domain'].lower()

        # Add domain if not too generic
        if domain and domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']:
            self.patterns[category]['domains'].add(domain)

        # Add specific sender for known correspondents
        if from_addr:
            self.patterns[category]['senders'].add(from_addr)

        # Extract potential keywords from subject
        subject_lower = metadata['subject'].lower()
        # Common business keywords
        if category == 'Business':
            business_keywords = [
                'invoice', 'meeting', 'contract', 'proposal', 'client',
                'vendor', 'project', 'deadline', 'report'
            ]
            for keyword in business_keywords:
                if keyword in subject_lower:
                    self.patterns[category]['keywords'].add(keyword)

        # Newsletter/marketing indicators
        if category == 'Other':
            if 'unsubscribe' in metadata['snippet'].lower():
                self.patterns[category]['keywords'].add('unsubscribe')
            if 'newsletter' in subject_lower:
                self.patterns[category]['keywords'].add('newsletter')

    def generate_search_queries(self) -> Dict[str, List[str]]:
        """
        Generate Gmail search queries from learned patterns.

        Returns:
            Dictionary mapping category to list of search queries
        """
        queries: Dict[str, List[str]] = {cat: [] for cat in self.CATEGORIES}

        for category in self.CATEGORIES:
            # Domain-based queries
            for domain in self.patterns[category]['domains']:
                queries[category].append(f"from:@{domain}")

            # Sender-based queries
            for sender in self.patterns[category]['senders']:
                queries[category].append(f"from:{sender}")

            # Keyword-based queries (only for strong signals)
            strong_keywords = ['invoice', 'unsubscribe', 'newsletter']
            for keyword in self.patterns[category]['keywords']:
                if keyword in strong_keywords:
                    queries[category].append(f"subject:{keyword}")

        return queries

    def get_pattern_summary(self) -> Dict[str, Dict[str, int]]:
        """
        Get a summary of learned patterns.

        Returns:
            Dictionary with pattern counts per category
        """
        summary = {}
        for category in self.CATEGORIES:
            summary[category] = {
                'domains': len(self.patterns[category]['domains']),
                'senders': len(self.patterns[category]['senders']),
                'keywords': len(self.patterns[category]['keywords'])
            }
        return summary

    def estimate_coverage(self, total_emails: int) -> Dict[str, int]:
        """
        Estimate how many emails each category's patterns would match.

        This is an approximation based on classification history.

        Args:
            total_emails: Total number of emails in the mailbox

        Returns:
            Dictionary mapping category to estimated email count
        """
        if not self.classifications:
            return {cat: 0 for cat in self.CATEGORIES}

        # Calculate category distribution from training data
        category_counts: Dict[str, int] = defaultdict(int)
        for classification in self.classifications:
            category_counts[classification['category']] += 1

        total_classified = len(self.classifications)
        estimates = {}

        for category in self.CATEGORIES:
            proportion = category_counts[category] / total_classified
            estimates[category] = int(total_emails * proportion)

        return estimates


def format_email_for_display(metadata: Dict[str, str], index: int, total: int) -> str:
    """
    Format email metadata for user display.

    Args:
        metadata: Email metadata dictionary
        index: Current email index (1-based)
        total: Total number of emails

    Returns:
        Formatted string for display
    """
    from_display = metadata['from_display'][:50]  # Truncate long names
    subject = metadata['subject'][:60] if metadata['subject'] else '(no subject)'

    return (
        f"[{index}/{total}] From: {from_display}\n"
        f"         Subject: {subject}\n"
        f"         Preview: {metadata['snippet'][:80]}..."
    )
