"""Quick test of Kimi API authentication."""

import os
import asyncio
from openai import AsyncOpenAI

async def test_kimi_auth():
    api_key = os.getenv("KIMI_API_KEY")

    if not api_key:
        print("❌ KIMI_API_KEY not found in environment")
        return False

    print(f"✓ KIMI_API_KEY found ({len(api_key)} chars)")
    print(f"  Prefix: {api_key[:10]}...")

    # Test with moonshot API
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.ai/v1"  # Updated endpoint (.ai not .cn)
    )

    print("\nTesting API authentication...")
    try:
        response = await client.chat.completions.create(
            model="moonshot-v1-8k",  # Try basic model first
            messages=[{"role": "user", "content": "Say 'API works'"}],
            max_tokens=10
        )
        print(f"✓ API authentication successful!")
        print(f"  Response: {response.choices[0].message.content}")
        print(f"  Model: {response.model}")
        return True

    except Exception as e:
        print(f"❌ API authentication failed: {e}")

        # Try to parse the error
        if "401" in str(e):
            print("\n401 Unauthorized - Possible causes:")
            print("  1. API key is invalid or expired")
            print("  2. API key needs to be regenerated at https://platform.moonshot.cn")
            print("  3. Account may need credits/balance")
        elif "403" in str(e):
            print("\n403 Forbidden - Account may be suspended or need verification")
        elif "404" in str(e):
            print("\n404 Not Found - API endpoint may have changed")

        return False

if __name__ == "__main__":
    success = asyncio.run(test_kimi_auth())
    exit(0 if success else 1)
