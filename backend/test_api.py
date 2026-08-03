"""
Test the webhook endpoint with proper HMAC signature.
"""
import requests
import json
import hmac
import hashlib
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get the secret from .env
secret = os.getenv("GITHUB_WEBHOOK_SECRET")
if not secret:
    print("❌ GITHUB_WEBHOOK_SECRET not found in .env file!")
    exit(1)

print(f"Using secret: {secret[:4]}...")

url = "http://localhost:8000/webhook"

# Fake GitHub webhook payload
fake_body = {
    "action": "opened",
    "repository": {
        "full_name": "test/repo",
        "owner": {"login": "testowner"},
        "name": "repo",
        "clone_url": "https://github.com/test/repo.git",
        "default_branch": "main"
    },
    "pull_request": {
        "number": 1,
        "title": "Test PR",
        "body": None,
        "state": "open",
        "html_url": "https://github.com/test/repo/pull/1",
        "diff_url": "https://github.com/test/repo/pull/1.diff",
        "base": {"ref": "main", "sha": "abc123"},
        "head": {"ref": "feature", "sha": "def456"},
        "user": {"login": "dev"}
    }
}

body_bytes = json.dumps(fake_body).encode()

sig = hmac.new(
    secret.encode(),
    msg=body_bytes,
    digestmod=hashlib.sha256
).hexdigest()

headers = {
    "X-Hub-Signature-256": f"sha256={sig}",
    "X-GitHub-Event": "pull_request",
    "X-GitHub-Delivery": "test-delivery-001",
    "Content-Type": "application/json"
}

print(f"\nSending request to {url}...")
response = requests.post(url, data=body_bytes, headers=headers)

print(f"Status: {response.status_code}")

# Try to parse JSON, but handle the case where body is empty
if response.text:
    try:
        print(f"Body: {json.dumps(response.json(), indent=2)}")
    except json.JSONDecodeError:
        print(f"Raw response: {response.text}")
else:
    print("Body: (empty)")