"""Script to verify NanoGPT API connectivity and key format.

Tests authentication and retrieves available models from the configured endpoints.
"""

import json
import os
import sys
import urllib.error
import urllib.request


def check_api_connection(api_key: str, base_url: str) -> bool:
    """Verifies connection to the NanoGPT API by listing models.

    Args:
        api_key: The NanoGPT API key.
        base_url: The configured base API URL.

    Returns:
        True if connection and authentication succeed, False otherwise.
    """
    endpoint = f"{base_url}/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(endpoint, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                models = [m.get("id") for m in data.get("data", [])]
                print(f"SUCCESS: Connected to NanoGPT API at {base_url}.")
                print(f"Retrieved {len(models)} models.")
                return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"ERROR: HTTP {e.code} received from {endpoint}.")
        print(f"Response: {body}")
    except Exception as e:
        print(f"ERROR: Failed to connect to {endpoint}. Detail: {e}")

    return False


def check_chat_completion(api_key: str, base_url: str) -> bool:
    """Verifies chat completions functionality.

    Args:
        api_key: The NanoGPT API key.
        base_url: The configured base API URL.

    Returns:
        True if chat completion succeeds, False otherwise.
    """
    endpoint = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, headers=headers, data=data, method="POST")

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print(f"SUCCESS: Chat completions functional at {base_url}.")
                return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"ERROR: Chat completions failed (HTTP {e.code}) at {endpoint}.")
        print(f"Response: {body}")
    except Exception as e:
        print(f"ERROR: Failed to call chat completions at {endpoint}. Detail: {e}")

    return False


def main() -> None:
    """Main entry point to execute diagnostic checks."""
    api_key = os.getenv("NANOGPT_API_KEY")
    if not api_key:
        print("ERROR: NANOGPT_API_KEY environment variable is not set.")
        sys.exit(1)

    print("Testing API key format...")
    import re

    uuid_pattern = (
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )
    if api_key.startswith("sk-nano-"):
        uuid_part = api_key[len("sk-nano-") :]
        if not re.match(uuid_pattern, uuid_part):
            print(
                "WARNING: API key prefix 'sk-nano-' detected but suffix is not a UUID."
            )
    elif not re.match(uuid_pattern, api_key):
        print("WARNING: API key does not match expected UUID formats.")

    # Test subscription URL (which was failing)
    sub_url = "https://nano-gpt.com/api/subscription/v1"
    print(f"\n1. Testing subscription endpoint: {sub_url}")
    check_api_connection(api_key, sub_url)
    check_chat_completion(api_key, sub_url)

    # Test standard URL
    std_url = "https://nano-gpt.com/api/v1"
    print(f"\n2. Testing standard endpoint: {std_url}")
    check_api_connection(api_key, std_url)
    success = check_chat_completion(api_key, std_url)

    if success:
        print("\nAll checks completed. The standard endpoint is functional.")
        sys.exit(0)
    else:
        print("\nDiagnostic checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
