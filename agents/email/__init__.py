"""
Email agent package for Gmail integration and automated classification.

Provides Gmail API access, OAuth authentication, and AI-powered email
categorization with pattern learning.
"""

from agents.email.email_classifier import EmailClassifier, format_email_for_display
from agents.email.gmail_client import GmailClient

__all__ = ['GmailClient', 'EmailClassifier', 'format_email_for_display']
