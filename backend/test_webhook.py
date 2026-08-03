import asyncio
import json
import os
from app.webhooks.validator import verify_signature
from app.webhooks.parser import parse_webhook_payload
from app.webhooks.router import route_webhook

# A minimal fake webhook body (just enough fields)
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

# Encode as bytes (like the HTTP request body)
body_bytes = json.dumps(fake_body).encode()

# Simulate headers GitHub sends
headers = {
    "X-GitHub-Event": "pull_request",
    "X-GitHub-Delivery": "delivery-123",
    "X-Hub-Signature-256": None  # We'll compute it
}

# Compute HMAC using the same secret
import hmac, hashlib
from app.core.config import get_settings

secret = get_settings().github_webhook_secret

# Compute signature
mac = hmac.new(secret.encode(), msg=body_bytes, digestmod=hashlib.sha256)
headers["X-Hub-Signature-256"] = "sha256=" + mac.hexdigest()

# 1. Validate
try:
    valid = verify_signature(body_bytes, headers["X-Hub-Signature-256"])
    print("✅ Signature valid")
except Exception as e:
    print(f"❌ Validation failed: {e}")

# 2. Parse
try:
    payload = parse_webhook_payload(fake_body, headers["X-GitHub-Event"], headers["X-GitHub-Delivery"])
    print(f"✅ Parsed: PR #{payload.pull_request.number} - {payload.pull_request.title}")
except Exception as e:
    print(f"❌ Parsing failed: {e}")

# 3. Route (will try to enqueue a job; needs Redis running)
# You need Upstash Redis online for this to work.
async def test_route():
    try:
        job_id = await route_webhook(payload)
        print(f"✅ Enqueued job: {job_id}")
    except Exception as e:
        print(f"❌ Routing failed (is Redis up?): {e}")

if __name__ == "__main__":
    asyncio.run(test_route())