"""Send a Meta-style webhook verification request to a callback URL."""

from __future__ import annotations

import sys
from urllib.parse import urlencode

import httpx


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m scripts.test_webhook <callback_url> <verify_token>")
        print("Example: python -m scripts.test_webhook https://abcd.ngrok-free.app/webhook zana_verify_token_123")
        return 1

    callback_url = sys.argv[1].rstrip("/")
    verify_token = sys.argv[2]
    params = urlencode(
        {
            "hub.mode": "subscribe",
            "hub.challenge": "123456789",
            "hub.verify_token": verify_token,
        }
    )
    url = f"{callback_url}?{params}"

    try:
        response = httpx.get(url, timeout=15)
    except Exception as exc:
        print(f"Request failed: {exc}")
        return 1

    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
    return 0 if response.status_code == 200 and response.text == "123456789" else 2


if __name__ == "__main__":
    raise SystemExit(main())
