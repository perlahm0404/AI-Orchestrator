"""
CLI commands for Gmail email labeling and classification.

Usage:
    aibrain email setup                    # Initial OAuth setup
    aibrain email classify --batch 100     # Learn patterns from emails
    aibrain email apply                    # Apply learned patterns (bulk label)
    aibrain email status                   # Show label statistics
"""

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.email import EmailClassifier, GmailClient, format_email_for_display


def email_setup_command(args: Any) -> int:
    """Set up Gmail API OAuth authentication."""
    print("\n" + "="*70)
    print("🔐 Gmail API OAuth Setup")
    print("="*70)

    credentials_path = args.credentials
    if not credentials_path:
        print("\n❌ Error: OAuth credentials JSON file required")
        print("\nSteps to get credentials:")
        print("1. Go to Google Cloud Console: https://console.cloud.google.com")
        print("2. Create a new project or select existing project")
        print("3. Enable Gmail API for the project")
        print("4. Create OAuth 2.0 Client ID (Desktop app)")
        print("5. Download credentials JSON")
        print("\nThen run:")
        print("  aibrain email setup --credentials /path/to/credentials.json")
        return 1

    if not Path(credentials_path).exists():
        print(f"\n❌ Credentials file not found: {credentials_path}")
        return 1

    try:
        client = GmailClient(credentials_json=credentials_path)
        print("\n📧 Opening browser for OAuth consent...")
        print("   (This only needs to be done once)")

        client.authenticate()

        print("\n✅ Authentication successful!")
        print(f"   Token saved to: {client.__class__.__module__}")
        print("\nYou can now use:")
        print("  aibrain email classify  # Start classifying emails")
        return 0

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return 1


def email_classify_command(args: Any) -> int:
    """Classify emails and learn patterns."""
    print("\n" + "="*70)
    print("🤖 Email Classification - Pattern Learning Mode")
    print("="*70)

    batch_size = args.batch
    auto_mode = getattr(args, 'auto', False)
    csv_output = getattr(args, 'csv', None)

    try:
        client = GmailClient()
        client.authenticate()

        # Ensure labels exist
        print("\n📋 Setting up labels...")
        labels = client.ensure_labels(['Personal', 'Business', 'Other'])
        print(f"   ✓ Labels ready: {', '.join(labels.keys())}")

        # Initialize classifier
        classifier = EmailClassifier(client)

        # Fetch emails for classification (excluding already labeled)
        print(f"\n📨 Fetching {batch_size} unlabeled emails...")
        query = "-label:Personal -label:Business -label:Other"
        response = client.fetch_messages(max_results=batch_size, query=query)
        messages = response.get('messages', [])

        if not messages:
            print("   No emails found!")
            return 1

        print(f"   Found {len(messages)} emails\n")

        if auto_mode:
            print("🤖 Auto-mode enabled: AI will classify all emails automatically")
            print("   Progress will be shown every 50 emails\n")

        # Setup CSV logging if requested
        csv_file = None
        csv_writer = None
        if csv_output:
            csv_file = open(csv_output, 'a', newline='', encoding='utf-8')
            csv_writer = csv.writer(csv_file)

            # Write header if file is new/empty
            if Path(csv_output).stat().st_size == 0:
                csv_writer.writerow([
                    'Timestamp', 'From', 'Subject', 'Category',
                    'AI Suggested', 'Reason', 'User Confirmed'
                ])

            print(f"📝 Logging to CSV: {csv_output}\n")

        # Classification loop
        classified_count = 0
        for i, msg_info in enumerate(messages, 1):
            message = client.get_message(msg_info['id'])
            metadata = classifier.extract_email_metadata(message)

            # Rate limiting: sleep to avoid quota exceeded errors
            # Gmail API limit: ~250-450 queries/minute
            # 0.5s delay = ~120 emails/minute (very safe margin)
            time.sleep(0.5)

            # Get AI suggestion
            suggested, reason = classifier.suggest_category(metadata)

            if auto_mode:
                # Auto mode: accept AI suggestion without prompting
                category = suggested
                confirmed = False  # Auto-classified, not user-confirmed

                # Show progress every 50 emails
                if i % 50 == 0 or i == len(messages):
                    print(f"   Progress: {i}/{len(messages)} emails classified...")
            else:
                # Interactive mode: prompt user
                print(format_email_for_display(metadata, i, len(messages)))
                print(f"         AI suggests: {suggested} ({reason})")

                # Get user input
                user_response = input("         Your choice [P]ersonal / [B]usiness / [O]ther / [A]ccept / [S]kip? ").strip().upper()

                if user_response == 'S':
                    print("         → Skipped\n")
                    continue

                # Determine final category
                if user_response == 'A':
                    category = suggested
                    confirmed = True
                elif user_response == 'P':
                    category = 'Personal'
                    confirmed = True
                elif user_response == 'B':
                    category = 'Business'
                    confirmed = True
                elif user_response == 'O':
                    category = 'Other'
                    confirmed = True
                else:
                    print(f"         → Invalid input, using suggestion: {suggested}\n")
                    category = suggested
                    confirmed = False

            # Record classification
            classifier.record_classification(metadata, category, confirmed)
            classified_count += 1

            # Apply label to Gmail
            label_id = labels[category]
            try:
                client.batch_modify_labels([metadata['message_id']], add_label_ids=[label_id])
                if not auto_mode:
                    # Only show individual confirmations in interactive mode
                    if confirmed:
                        print(f"         ✓ Labeled as {category}\n")
                    else:
                        print(f"         → Labeled as {category} (not confirmed)\n")
            except Exception as e:
                if not auto_mode:
                    print(f"         ⚠️  Failed to apply label: {e}\n")

            # Log to CSV if enabled
            if csv_writer:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                csv_writer.writerow([
                    timestamp,
                    metadata['from'],
                    metadata['subject'],
                    category,
                    suggested,
                    reason,
                    'Yes' if confirmed else 'No'
                ])
                if csv_file:
                    csv_file.flush()  # Ensure data is written immediately

        # Show pattern summary
        print("="*70)
        print(f"✅ Classification complete: {classified_count} emails processed\n")

        # Show category distribution
        category_counts = {'Personal': 0, 'Business': 0, 'Other': 0}
        for classification in classifier.classifications:
            category_counts[classification['category']] += 1

        print("📧 Labeled emails:")
        for category, count in category_counts.items():
            if count > 0:
                print(f"   {category}: {count} emails")
        print()

        summary = classifier.get_pattern_summary()
        print("📊 Learned patterns:")
        for category, counts in summary.items():
            print(f"   {category}:")
            print(f"      - {counts['domains']} domains")
            print(f"      - {counts['senders']} specific senders")
            print(f"      - {counts['keywords']} keywords")

        # Save patterns for later use
        from agents.email.email_classifier import PATTERNS_FILE
        classifier.save_patterns()
        print(f"\n💾 Patterns saved to: {PATTERNS_FILE}")
        print("   Run 'aibrain email apply' to bulk-label based on these patterns")

        # Close CSV file if opened
        if csv_file:
            csv_file.close()
            print(f"\n📝 CSV log saved: {csv_output}")

        return 0

    except RuntimeError as e:
        if "not authenticated" in str(e).lower():
            print("\n❌ Not authenticated. Run 'aibrain email setup' first")
        else:
            print(f"\n❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


def email_apply_command(args: Any) -> int:
    """Apply learned patterns to bulk-label emails."""
    print("\n" + "="*70)
    print("⚡ Bulk Email Labeling - Applying Patterns")
    print("="*70)

    dry_run = getattr(args, 'dry_run', False)

    try:
        client = GmailClient()
        client.authenticate()

        # Initialize classifier and load patterns
        classifier = EmailClassifier(client)

        from agents.email.email_classifier import PATTERNS_FILE
        if not classifier.load_patterns():
            print(f"\n❌ No patterns found at: {PATTERNS_FILE}")
            print("   Run 'aibrain email classify' first to learn patterns")
            return 1

        # Show loaded patterns
        summary = classifier.get_pattern_summary()
        total_patterns = sum(
            counts['domains'] + counts['senders'] + counts['keywords']
            for counts in summary.values()
        )

        if total_patterns == 0:
            print("\n❌ No patterns loaded (file may be empty)")
            print("   Run 'aibrain email classify' to learn patterns")
            return 1

        print(f"\n✓ Loaded {total_patterns} patterns from {PATTERNS_FILE}")
        for category, counts in summary.items():
            if counts['domains'] + counts['senders'] + counts['keywords'] > 0:
                print(f"   {category}: {counts['domains']} domains, {counts['senders']} senders, {counts['keywords']} keywords")

        # Ensure labels exist
        labels = client.ensure_labels(['Personal', 'Business', 'Other'])

        # Generate search queries from patterns
        queries = classifier.generate_search_queries()

        # Process each category
        total_labeled = 0
        for category in ['Personal', 'Business', 'Other']:
            category_queries = queries.get(category, [])
            if not category_queries:
                continue

            label_id = labels[category]

            print(f"\n{'='*50}")
            print(f"📧 Processing {category} emails...")
            print(f"   {len(category_queries)} search patterns")

            # Combine queries with OR and exclude already-labeled emails
            combined_query = f"({' OR '.join(category_queries)}) -label:{category}"

            # Count matching emails
            print(f"   Searching...")
            all_message_ids = []
            page_token = None
            while True:
                response = client.fetch_messages(
                    max_results=500,
                    query=combined_query,
                    page_token=page_token
                )
                messages = response.get('messages', [])
                all_message_ids.extend([m['id'] for m in messages])
                page_token = response.get('nextPageToken')
                if not page_token:
                    break

            if not all_message_ids:
                print(f"   No unlabeled emails match {category} patterns")
                continue

            print(f"   Found {len(all_message_ids)} emails to label as {category}")

            if dry_run:
                print(f"   [DRY RUN] Would label {len(all_message_ids)} emails")
                continue

            # Confirm before bulk operation
            response_text = input(f"   Apply {category} label to {len(all_message_ids)} emails? [y/N]: ").strip().lower()
            if response_text != 'y':
                print(f"   Skipped {category}")
                continue

            # Batch apply labels (Gmail API allows up to 1000 per call)
            batch_size = 1000
            labeled = 0
            for i in range(0, len(all_message_ids), batch_size):
                batch = all_message_ids[i:i + batch_size]
                try:
                    client.batch_modify_labels(batch, add_label_ids=[label_id])
                    labeled += len(batch)
                    print(f"   Labeled {labeled}/{len(all_message_ids)}...")
                except Exception as e:
                    print(f"   ⚠️  Batch failed: {e}")

            total_labeled += labeled
            print(f"   ✓ Labeled {labeled} emails as {category}")

        print("\n" + "="*70)
        if dry_run:
            print(f"✓ Dry run complete")
        else:
            print(f"✅ Complete! Labeled {total_labeled} emails total")
        return 0

    except RuntimeError as e:
        if "not authenticated" in str(e).lower():
            print("\n❌ Not authenticated. Run 'aibrain email setup' first")
        else:
            print(f"\n❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


def email_status_command(args: Any) -> int:
    """Show Gmail label statistics."""
    print("\n" + "="*70)
    print("📊 Gmail Label Statistics")
    print("="*70)

    try:
        client = GmailClient()
        client.authenticate()

        # Get label stats
        labels = client.ensure_labels(['Personal', 'Business', 'Other'])

        print("\nLabel statistics:\n")
        for name, label_id in labels.items():
            stats = client.get_label_stats(label_id)
            total = stats['messagesTotal']
            unread = stats['messagesUnread']
            print(f"  {name:12} {total:5} total  ({unread} unread)")

        # Show unlabeled count
        print("\nSearching for unlabeled emails...")
        unlabeled = client.fetch_messages(
            max_results=1,
            query="-label:Personal -label:Business -label:Other"
        )
        unlabeled_count = len(unlabeled.get('messages', []))

        if unlabeled_count > 0:
            print(f"  ⚠️  Found unlabeled emails (showing 1 of possibly many)")
        else:
            print(f"  ✅ All emails are labeled!")

        return 0

    except RuntimeError as e:
        if "not authenticated" in str(e).lower():
            print("\n❌ Not authenticated. Run 'aibrain email setup' first")
        else:
            print(f"\n❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


def setup_parser(subparsers: Any) -> None:
    """Setup argparse for email commands."""
    email_parser = subparsers.add_parser(
        'email',
        help='Gmail email labeling and classification',
        description='Manage Gmail labels with AI-powered classification'
    )
    email_subparsers = email_parser.add_subparsers(dest='email_command')

    # Setup command
    setup_parser = email_subparsers.add_parser(
        'setup',
        help='Set up Gmail API OAuth authentication'
    )
    setup_parser.add_argument(
        '--credentials',
        type=str,
        help='Path to OAuth credentials JSON file'
    )
    setup_parser.set_defaults(func=email_setup_command)

    # Classify command
    classify_parser = email_subparsers.add_parser(
        'classify',
        help='Classify emails and learn patterns'
    )
    classify_parser.add_argument(
        '--batch',
        type=int,
        default=100,
        help='Number of emails to classify (default: 100)'
    )
    classify_parser.add_argument(
        '--auto',
        action='store_true',
        help='Auto-mode: accept all AI suggestions without prompting (for bulk processing)'
    )
    classify_parser.add_argument(
        '--csv',
        type=str,
        help='CSV file path to log all classifications (appends if exists)'
    )
    classify_parser.set_defaults(func=email_classify_command)

    # Apply command
    apply_parser = email_subparsers.add_parser(
        'apply',
        help='Apply learned patterns to bulk-label emails'
    )
    apply_parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Preview only, do not apply labels'
    )
    apply_parser.set_defaults(func=email_apply_command)

    # Status command
    status_parser = email_subparsers.add_parser(
        'status',
        help='Show Gmail label statistics'
    )
    status_parser.set_defaults(func=email_status_command)
