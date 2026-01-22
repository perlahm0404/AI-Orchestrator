# Gmail Email Labeling Agent

AI-powered email classification and bulk labeling system using the Gmail API.

## Overview

The Gmail Email Labeling Agent enables automated organization of Gmail emails into three categories:
- **Personal** - Personal correspondence, family, friends
- **Business** - Work-related, professional contacts
- **Other** - Newsletters, promotional content, automated notifications

## Features

- **OAuth 2.0 Authentication** - Secure Gmail API access
- **AI-Powered Classification** - Pattern learning from user feedback
- **Bulk Labeling** - Batch operations for efficient processing (up to 1000 emails/second)
- **Pattern Learning** - Automatically identifies domains, senders, and keywords
- **Gmail Filters** - Create filters for automated future labeling

## Installation

### 1. Install Dependencies

Dependencies are already included in `pyproject.toml`:
```bash
pip install -e .
```

### 2. Set Up Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Name it (e.g., "AI Orchestrator Gmail Agent")
   - Download the credentials JSON file
5. Save the credentials file somewhere secure (e.g., `~/.aibrain/gmail_credentials.json`)

### 3. Run OAuth Setup

```bash
aibrain email setup --credentials /path/to/credentials.json
```

This will:
- Open your browser for Google OAuth consent
- Save a refresh token to `~/.aibrain/gmail_token.json`
- Grant the agent access to your Gmail (read, modify labels, create filters)

**Required Scopes:**
- `gmail.readonly` - Read email metadata
- `gmail.modify` - Add/remove labels
- `gmail.settings.basic` - Create Gmail filters

## Usage

### Quick Start

```bash
# 1. Classify first 100 emails (learn patterns)
aibrain email classify --batch 100

# 2. Check label statistics
aibrain email status

# 3. Apply learned patterns (bulk labeling)
aibrain email apply
```

### Commands

#### `aibrain email setup`

Initial OAuth authentication setup.

**Options:**
- `--credentials PATH` - Path to OAuth credentials JSON file

**Example:**
```bash
aibrain email setup --credentials ~/.aibrain/gmail_credentials.json
```

#### `aibrain email classify`

Classify emails interactively and learn patterns.

**Options:**
- `--batch N` - Number of emails to classify (default: 100)

**Interactive Process:**
1. Fetches N emails from your mailbox
2. For each email:
   - Displays: From, Subject, Preview
   - AI suggests a category based on learned patterns
   - You confirm or override the suggestion
3. Records patterns from your confirmed classifications

**User Input:**
- `A` - Accept AI suggestion
- `P` - Override to Personal
- `B` - Override to Business
- `O` - Override to Other
- `S` - Skip this email

**Example:**
```bash
aibrain email classify --batch 50
```

**Output Example:**
```
[1/50] From: john@acme.com
       Subject: Q4 Project Update
       Preview: Hi team, here's the quarterly update on our project...
       AI suggests: Business (Domain matches Business pattern)
       Your choice [P]ersonal / [B]usiness / [O]ther / [A]ccept / [S]kip? A
       ✓ Recorded as Business

[2/50] From: mom@gmail.com
       Subject: Weekend plans
       Preview: Hi honey, what are your plans for this weekend?
       AI suggests: Personal (Heuristic analysis suggests Personal)
       Your choice [P]ersonal / [B]usiness / [O]ther / [A]ccept / [S]kip? A
       ✓ Recorded as Personal
```

#### `aibrain email status`

Show Gmail label statistics.

**Example:**
```bash
aibrain email status
```

**Output:**
```
====================================================================
📊 Gmail Label Statistics
====================================================================

Label statistics:

  Personal        123 total  (5 unread)
  Business        456 total  (12 unread)
  Other           789 total  (0 unread)

Searching for unlabeled emails...
  ⚠️  Found unlabeled emails (showing 1 of possibly many)
```

#### `aibrain email apply`

Apply learned patterns to bulk-label emails (coming soon).

**Note:** Currently requires pattern persistence to be implemented. Will enable:
- Bulk labeling based on learned patterns
- Query generation from patterns
- Batch API operations (1000s of emails in seconds)

### Pattern Learning

The classifier learns from your confirmed classifications:

**Domain Patterns:**
- If 80%+ emails from `@company.com` are marked Business, future emails from that domain are auto-suggested as Business
- Generic domains (gmail.com, yahoo.com) are not used as patterns

**Sender Patterns:**
- Specific email addresses you classify are remembered
- Future emails from the same sender get the same suggestion

**Keyword Patterns:**
- Common keywords in subjects/bodies are tracked
- Strong indicators: "invoice", "meeting", "unsubscribe", "newsletter"

**Example Pattern Summary:**
```
📊 Learned patterns:
   Business:
      - 12 domains
      - 45 specific senders
      - 8 keywords
   Personal:
      - 0 domains (generic only)
      - 23 specific senders
      - 2 keywords
   Other:
      - 34 domains
      - 5 specific senders
      - 15 keywords
```

## Architecture

### Modules

**`gmail_client.py`** - Gmail API wrapper
- OAuth 2.0 authentication flow
- Token storage and refresh
- Label management (create, list, get stats)
- Email fetching with pagination
- Batch label operations (up to 1000 emails)
- Filter creation

**`email_classifier.py`** - AI classification engine
- Email metadata extraction
- Pattern-based categorization
- Heuristic analysis fallback
- Pattern learning from user feedback
- Query generation for bulk operations

**`cli/commands/email.py`** - CLI interface
- Interactive classification workflow
- OAuth setup wizard
- Status reporting
- Bulk operations (future)

### Data Flow

```
┌─────────────────┐
│  Gmail API      │
│  (OAuth 2.0)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GmailClient    │ ◄──── Fetch emails, manage labels
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ EmailClassifier │ ◄──── Extract metadata, suggest category
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  User Review    │ ◄──── Confirm/override suggestions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Pattern Store   │ ◄──── Record patterns for bulk operations
└─────────────────┘
```

## Security & Privacy

**Token Storage:**
- Refresh tokens are stored in `~/.aibrain/gmail_token.json`
- This file contains sensitive credentials - keep it secure
- Never commit this file to version control

**OAuth Scopes:**
- `gmail.readonly` - Cannot modify or delete emails
- `gmail.modify` - Can only add/remove labels (cannot delete emails)
- `gmail.settings.basic` - Can create filters (cannot modify security settings)

**Data Access:**
- Only email metadata is read (From, Subject, snippet)
- Email bodies are NOT accessed
- No data is sent to external services (except Google for authentication)

## Limitations

**Current Implementation:**
- Pattern persistence not yet implemented (patterns lost after session ends)
- Bulk labeling requires pattern persistence
- No undo functionality (manually remove labels via Gmail UI if needed)

**Gmail API Limits:**
- 250 quota units per user per second
- 1 billion quota units per day
- Batch modify: max 1000 messages per call

**Future Enhancements:**
- Pattern persistence (JSON/database storage)
- Bulk labeling implementation
- Undo/rollback functionality
- Advanced filters (date ranges, attachment types)
- Multi-category labeling
- Export/import patterns for sharing

## Troubleshooting

### "Not authenticated" Error

Run the setup command:
```bash
aibrain email setup --credentials /path/to/credentials.json
```

### Token Expired

Delete the token file and re-authenticate:
```bash
rm ~/.aibrain/gmail_token.json
aibrain email setup --credentials /path/to/credentials.json
```

### Import Errors

Ensure dependencies are installed:
```bash
pip install google-auth-oauthlib google-api-python-client
```

### OAuth Consent Screen Warnings

If you see "This app isn't verified":
1. This is normal for personal OAuth apps
2. Click "Advanced" > "Go to [App Name] (unsafe)"
3. This is safe if you created the OAuth credentials yourself

## Examples

### Complete Workflow

```bash
# 1. Initial setup (one-time)
aibrain email setup --credentials ~/.aibrain/gmail_credentials.json

# 2. Classify a small batch to learn patterns
aibrain email classify --batch 50

# 3. Review the learned patterns
aibrain email status

# 4. Classify more emails to refine patterns
aibrain email classify --batch 100

# 5. Once patterns are good, apply to all emails
aibrain email apply  # Coming soon - requires pattern persistence
```

### Pattern Learning Example

After classifying 100 emails:
```
Business pattern learned:
- @acme.com, @company.com, @vendor.io domains
- Keywords: "invoice", "meeting", "contract"

Personal pattern learned:
- mom@gmail.com, friend@email.com, family@example.com senders

Other pattern learned:
- @newsletter.com, @marketing.io domains
- Keywords: "unsubscribe", "promotional"
```

Future emails automatically suggested based on these patterns.

## Contributing

This module is part of the AI Orchestrator project. See the main README for contribution guidelines.

## License

MIT License - See LICENSE file in repository root
