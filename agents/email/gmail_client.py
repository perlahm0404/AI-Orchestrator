"""
Gmail API client with OAuth 2.0 authentication.

Provides secure access to Gmail for email classification and labeling operations.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Gmail API scopes required for read, modify, and filter management
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.settings.basic'
]

# Token storage location
TOKEN_DIR = Path.home() / '.aibrain'
TOKEN_FILE = TOKEN_DIR / 'gmail_token.json'


class GmailClient:
    """Gmail API client with OAuth authentication and label management."""

    def __init__(self, credentials_json: Optional[str] = None):
        """
        Initialize Gmail client.

        Args:
            credentials_json: Path to OAuth client credentials JSON file.
                             If None, looks for GMAIL_OAUTH_CREDENTIALS env var.
        """
        self.credentials_json = credentials_json or os.getenv('GMAIL_OAUTH_CREDENTIALS')
        self.service = None
        self._labels_cache: Dict[str, str] = {}  # name -> label_id mapping

    def authenticate(self) -> None:
        """
        Authenticate with Gmail API using OAuth 2.0.

        Opens browser for first-time consent, then saves refresh token
        for subsequent use.

        Raises:
            ValueError: If credentials JSON is not provided or found
            HttpError: If authentication fails
        """
        creds = None

        # Load existing token if available
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        # If no valid credentials, initiate OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh expired token
                creds.refresh(Request())
            else:
                # First-time OAuth flow
                if not self.credentials_json:
                    raise ValueError(
                        "Gmail OAuth credentials required. Set GMAIL_OAUTH_CREDENTIALS "
                        "environment variable or pass credentials_json parameter."
                    )

                if not os.path.exists(self.credentials_json):
                    raise ValueError(f"Credentials file not found: {self.credentials_json}")

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_json, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for future use
            TOKEN_DIR.mkdir(parents=True, exist_ok=True)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        # Build Gmail service
        self.service = build('gmail', 'v1', credentials=creds)

        # Pre-load labels cache
        self._refresh_labels_cache()

    def _refresh_labels_cache(self) -> None:
        """Refresh the internal labels cache."""
        if not self.service:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")

        try:
            response = self.service.users().labels().list(userId='me').execute()
            labels = response.get('labels', [])
            self._labels_cache = {label['name']: label['id'] for label in labels}
        except HttpError as e:
            raise RuntimeError(f"Failed to fetch labels: {e}")

    def list_labels(self) -> List[Dict[str, Any]]:
        """
        List all Gmail labels.

        Returns:
            List of label dictionaries with 'id' and 'name' keys
        """
        if not self.service:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")

        try:
            response = self.service.users().labels().list(userId='me').execute()
            return response.get('labels', [])
        except HttpError as e:
            raise RuntimeError(f"Failed to list labels: {e}")

    def create_label(self, name: str) -> str:
        """
        Create a new Gmail label.

        Args:
            name: Label name to create

        Returns:
            Label ID of the created label
        """
        if not self.service:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")

        # Check if label already exists
        if name in self._labels_cache:
            return self._labels_cache[name]

        try:
            label_object = {
                'name': name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            created = self.service.users().labels().create(
                userId='me', body=label_object
            ).execute()

            label_id = created['id']
            self._labels_cache[name] = label_id
            return label_id
        except HttpError as e:
            raise RuntimeError(f"Failed to create label '{name}': {e}")

    def get_label_id(self, name: str) -> Optional[str]:
        """
        Get label ID by name.

        Args:
            name: Label name to lookup

        Returns:
            Label ID if found, None otherwise
        """
        return self._labels_cache.get(name)

    def ensure_labels(self, label_names: List[str]) -> Dict[str, str]:
        """
        Ensure labels exist, creating them if necessary.

        Args:
            label_names: List of label names to ensure exist

        Returns:
            Dictionary mapping label name to label ID
        """
        result = {}
        for name in label_names:
            label_id = self.get_label_id(name)
            if not label_id:
                label_id = self.create_label(name)
            result[name] = label_id
        return result

    def fetch_messages(
        self,
        max_results: int = 100,
        query: str = '',
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch email messages.

        Args:
            max_results: Maximum number of messages to return (1-500)
            query: Gmail search query (e.g., 'from:example.com')
            page_token: Token for pagination

        Returns:
            Dictionary with 'messages' list and optional 'nextPageToken'
        """
        if not self.service:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")

        try:
            response = self.service.users().messages().list(
                userId='me',
                maxResults=min(max_results, 500),
                q=query,
                pageToken=page_token
            ).execute()
            return response
        except HttpError as e:
            raise RuntimeError(f"Failed to fetch messages: {e}")

    def get_message(self, message_id: str, format: str = 'metadata') -> Dict[str, Any]:
        """
        Get a single email message.

        Args:
            message_id: Gmail message ID
            format: Response format ('minimal', 'metadata', 'full', 'raw')

        Returns:
            Message dictionary
        """
        if not self.service:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")

        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format=format,
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            return message
        except HttpError as e:
            raise RuntimeError(f"Failed to get message {message_id}: {e}")

    def batch_modify_labels(
        self,
        message_ids: List[str],
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None
    ) -> None:
        """
        Batch modify labels on messages (up to 1000 per call).

        Args:
            message_ids: List of message IDs to modify (max 1000)
            add_label_ids: List of label IDs to add
            remove_label_ids: List of label IDs to remove
        """
        if not self.service:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")

        if len(message_ids) > 1000:
            raise ValueError("Cannot modify more than 1000 messages per batch")

        if not add_label_ids and not remove_label_ids:
            return  # Nothing to do

        body = {'ids': message_ids}
        if add_label_ids:
            body['addLabelIds'] = add_label_ids
        if remove_label_ids:
            body['removeLabelIds'] = remove_label_ids

        try:
            self.service.users().messages().batchModify(userId='me', body=body).execute()
        except HttpError as e:
            raise RuntimeError(f"Failed to batch modify labels: {e}")

    def create_filter(
        self,
        criteria: Dict[str, Any],
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a Gmail filter.

        Args:
            criteria: Filter criteria (e.g., {'from': 'example.com'})
            add_label_ids: List of label IDs to add when filter matches
            remove_label_ids: List of label IDs to remove when filter matches

        Returns:
            Created filter object
        """
        if not self.service:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")

        action = {}
        if add_label_ids:
            action['addLabelIds'] = add_label_ids
        if remove_label_ids:
            action['removeLabelIds'] = remove_label_ids

        if not action:
            raise ValueError("Filter must have at least one action")

        filter_body = {
            'criteria': criteria,
            'action': action
        }

        try:
            created = self.service.users().settings().filters().create(
                userId='me', body=filter_body
            ).execute()
            return created
        except HttpError as e:
            raise RuntimeError(f"Failed to create filter: {e}")

    def get_label_stats(self, label_id: str) -> Dict[str, int]:
        """
        Get statistics for a label.

        Args:
            label_id: Label ID to get stats for

        Returns:
            Dictionary with 'messagesTotal' and 'messagesUnread' counts
        """
        if not self.service:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")

        try:
            label = self.service.users().labels().get(userId='me', id=label_id).execute()
            return {
                'messagesTotal': label.get('messagesTotal', 0),
                'messagesUnread': label.get('messagesUnread', 0)
            }
        except HttpError as e:
            raise RuntimeError(f"Failed to get label stats: {e}")
