"""
Improved email classification rules based on manual review.

This module contains explicit rules for categorizing emails into:
- Personal: Actual human correspondence
- Business: Work-related, professional emails, invoices
- Other: Newsletters, automated notifications, marketing
"""

from typing import Tuple


def should_be_other(from_addr: str, subject: str, snippet: str) -> Tuple[bool, str]:
    """
    Check if email should definitely be classified as 'Other'.

    Returns: (is_other, reason)
    """
    from_lower = from_addr.lower()
    subject_lower = subject.lower()
    snippet_lower = snippet.lower()

    # EXCEPTIONS: Business-critical automated emails that should NOT be Other
    # Therathrive: Lead notification system (business emails despite noreply@ sender)
    if 'therathrive' in from_lower or 'therathrive' in subject_lower or 'therathrive' in snippet_lower:
        return False, ""  # Not Other, will be caught by Business rules

    if ('acct-mgmt.com' in from_lower or 'msgsndr' in from_lower) and 'new lead' in subject_lower:
        return False, ""  # Not Other, will be caught by Business rules

    # Automated senders (no-reply, notifications, etc.)
    automated_patterns = [
        'noreply', 'no-reply', 'donotreply', 'do-not-reply',
        'notifications@', 'notification@', 'calendar-notification@',
        'auto@', 'automated@', 'robot@', 'bot@',
        'alerts@', 'updates@', 'newsletter@',
        'marketing@', 'videos@', 'support@', 'hello@',
        'offers@', 'success@', 'mail@', 'email@'
    ]

    for pattern in automated_patterns:
        if pattern in from_lower:
            return True, f"Automated sender: {pattern}"

    # Travel & Booking services
    travel_domains = [
        'southwest.com', 'americanairlines', 'united.com', 'delta.com',
        'booking.com', 'expedia.com', 'tripadvisor.com', 'airbnb.com',
        'hotels.com', 'tripit.com', 'kayak.com', 'priceline.com',
        'vrbo.com', 'eg.vrbo.com', 'alaskaair.com', 'omnihotels.com'
    ]

    for domain in travel_domains:
        if domain in from_lower:
            return True, f"Travel/booking service: {domain}"

    # Job/Recruiting platforms
    recruiting_domains = [
        'weatherbyhealthcare', 'indeed.com', 'linkedin.com', 'glassdoor.com',
        'ziprecruiter.com', 'monster.com', 'careerbuilder.com',
        'legalmatch.net', 'practicematch.com'
    ]

    for domain in recruiting_domains:
        if domain in from_lower:
            return True, f"Recruiting/job platform: {domain}"

    # Tech platforms & services
    tech_platforms = [
        'github.com', 'gitlab.com', 'bitbucket.org',
        'vercel.com', 'netlify.com', 'heroku.com',
        'kaggle.com', 'medium.com', 'substack.com',
        'fiverr.com', 'upwork.com', 'freelancer.com',
        'birdeye.com', 'vumedi.com', 'doximity.com',
        'nutanix.com', 'emeritus.org', 'medscapelive.org',
        'wellreceived.com', 'dominos.com', 'e-offers.dominos.com',
        'tebra.com'  # Healthcare practice management platform
    ]

    for platform in tech_platforms:
        if platform in from_lower:
            return True, f"Tech platform: {platform}"

    # Newsletters & Media
    newsletter_indicators = [
        'ycombinator.com', 'techcrunch.com', 'wired.com',
        'startuphealth.com', 'newsletter', 'digest',
        'hbr.org', 'substack'
    ]

    for indicator in newsletter_indicators:
        if indicator in from_lower or indicator in subject_lower:
            return True, f"Newsletter/media: {indicator}"

    # Marketing & Promotional
    marketing_keywords = [
        'unsubscribe', 'promo', 'deal', 'discount', 'sale',
        'limited time', 'act now', 'click here', 'shop now',
        'exclusive offer'
    ]

    marketing_count = sum(1 for keyword in marketing_keywords if keyword in snippet_lower)
    if marketing_count >= 2:
        return True, "Marketing email (multiple promo keywords)"

    # Calendar & scheduling (Google Calendar, Calendly, etc.)
    if 'calendar-notification' in from_lower or 'calendar.google.com' in from_lower:
        return True, "Automated calendar notification"

    return False, ""


def should_be_business(from_addr: str, subject: str, snippet: str) -> Tuple[bool, str]:
    """
    Check if email should definitely be classified as 'Business'.

    Returns: (is_business, reason)
    """
    from_lower = from_addr.lower()
    subject_lower = subject.lower()
    snippet_lower = snippet.lower()

    # Special business exceptions (checked first before automated sender rules)
    # Therathrive: Lead notification system (business-critical)
    if 'therathrive' in from_lower or 'therathrive' in subject_lower or 'therathrive' in snippet_lower:
        return True, "Business notification system: Therathrive"

    # Also check for specific Therathrive domains
    if 'acct-mgmt.com' in from_lower or 'msgsndr' in from_lower:
        if 'new lead' in subject_lower or 'therathrive' in snippet_lower:
            return True, "Business notification system: Therathrive"

    # Invoices & billing
    billing_keywords = ['invoice', 'payment', 'receipt', 'billing', 'statement']
    for keyword in billing_keywords:
        if keyword in subject_lower or keyword in from_lower:
            return True, f"Billing/invoice: {keyword}"

    # Professional organizations & consulting firms
    professional_orgs = [
        'himss.org', 'hospitalmedicine.org', 'medscape.com',
        'nejm.org', 'jama', 'acponline.org', 'shm.org',
        'guidepointglobal.com'
    ]

    for org in professional_orgs:
        if org in from_lower:
            return True, f"Professional organization: {org}"

    # Corporate domains (non-automated)
    # Only if it's from an actual person (has a name-like local part)
    # BUT exclude personal email providers (Gmail, Yahoo, etc.)
    personal_providers = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com', 'msn.com']

    if '@' in from_addr and not any(provider in from_lower for provider in personal_providers):
        local_part = from_addr.split('@')[0].lower()
        # Check if it looks like a person's email (firstname.lastname or similar)
        if '.' in local_part and not any(x in local_part for x in ['noreply', 'notification', 'info', 'support']):
            # Common business TLDs
            if any(tld in from_lower for tld in ['.com', '.org', '.edu', '.gov']):
                return True, "Professional email from named person"

    # Meeting-related (but not automated calendar)
    meeting_keywords = ['meeting invite', 'conference call', 'zoom link', 'teams meeting']
    for keyword in meeting_keywords:
        if keyword in subject_lower and 'calendar-notification' not in from_lower:
            return True, f"Meeting invitation: {keyword}"

    return False, ""


def should_be_personal(from_addr: str, subject: str, snippet: str) -> Tuple[bool, str]:
    """
    Check if email should definitely be classified as 'Personal'.

    Returns: (is_personal, reason)
    """
    from_lower = from_addr.lower()

    # Personal email providers (Gmail, Yahoo, Hotmail, etc.)
    personal_domains = ['@gmail.com', '@yahoo.com', '@hotmail.com', '@outlook.com', '@aol.com', '@msn.com']

    if any(domain in from_lower for domain in personal_domains):
        # Make sure it's not automated
        automated_prefixes = [
            'noreply', 'no-reply', 'notification', 'donotreply', 'do-not-reply',
            'automated', 'info@', 'support@', 'team@', 'hello@',
            'updates@', 'newsletter@', 'alerts@', 'admin@', 'contact@'
        ]

        if not any(prefix in from_lower for prefix in automated_prefixes):
            return True, "Personal email from Gmail/Yahoo/Hotmail (non-automated)"

    return False, ""


def classify_email(from_addr: str, subject: str, snippet: str) -> Tuple[str, str]:
    """
    Apply refined classification logic.

    Order of precedence:
    1. Check if it should be Other (automated, marketing, newsletters)
    2. Check if it should be Business (invoices, professional orgs, work emails)
    3. Check if it should be Personal (known contacts, personal email providers)
    4. Default to Other if uncertain

    Returns: (category, reason)
    """
    # First check if it's clearly Other (most common)
    is_other, other_reason = should_be_other(from_addr, subject, snippet)
    if is_other:
        return 'Other', other_reason

    # Then check if it's Business
    is_business, business_reason = should_be_business(from_addr, subject, snippet)
    if is_business:
        return 'Business', business_reason

    # Then check if it's Personal
    is_personal, personal_reason = should_be_personal(from_addr, subject, snippet)
    if is_personal:
        return 'Personal', personal_reason

    # Default to Other for anything uncertain
    return 'Other', 'No clear indicators, defaulting to Other'
