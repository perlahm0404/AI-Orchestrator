#!/usr/bin/env python3
"""
Example: Extract license information from California Medical Board.

Usage:
    python examples/extract-license.py A12345
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from adapters.browser_automation import BrowserAutomationClient


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python extract-license.py <license-number>")
        sys.exit(1)

    license_number = sys.argv[1]

    # Create client
    client = BrowserAutomationClient()

    try:
        # Create session
        print(f"Creating browser session...")
        session_id = client.create_session({
            "sessionId": f"extract-{license_number}",
            "headless": True,
        })
        print(f"Session created: {session_id}")

        # Extract license info
        print(f"Extracting license info for {license_number}...")
        info = client.extract_license_info(
            session_id=session_id,
            adapter="california-medical-board",
            license_number=license_number,
        )

        # Display results
        print("\nLicense Information:")
        print(f"  License Number: {info['licenseNumber']}")
        print(f"  Status: {info['status']}")
        print(f"  Holder: {info['holderName']}")
        print(f"  Type: {info['licenseType']}")

        if info.get('expirationDate'):
            print(f"  Expiration: {info['expirationDate']}")

        if info.get('disciplinaryActions'):
            print(f"  Disciplinary Actions: {len(info['disciplinaryActions'])}")

        # Cleanup
        print("\nCleaning up session...")
        client.cleanup_session(session_id)
        print("Done!")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
