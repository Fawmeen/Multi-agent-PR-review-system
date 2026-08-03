"""
HMAC signature validation for GitHub webhooks.
"""
import hmac
import hashlib
from app.core.config import get_settings
from app.core.exceptions import InvalidSignatureError

settings = get_settings()


def verify_signature(payload_body: bytes, signature_header: str | None) -> bool:
    """
    Verify that the webhook was sent by GitHub.

    GitHub sends a header: X-Hub-Signature-256 = sha256=<HMAC hex>
    We compute the HMAC of the raw body with our secret and compare.

    Args:
        payload_body: Raw bytes of the request body (must be exactly as received).
        signature_header: Value of the X-Hub-Signature-256 header, e.g., "sha256=abc123..."
    """
    if not signature_header:
        raise InvalidSignatureError("Missing signature header")

    # Extract the signature part after 'sha256='
    try:
        sha_name, signature = signature_header.split("=")
    except ValueError:
        raise InvalidSignatureError("Invalid signature format")

    if sha_name != "sha256":
        raise InvalidSignatureError("Unsupported hash algorithm")

    # Compute our own signature
    secret = settings.github_webhook_secret.encode()
    mac = hmac.new(secret, msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = mac.hexdigest()

    # Constant‑time comparison to prevent timing attacks
    if not hmac.compare_digest(expected_signature, signature):
        raise InvalidSignatureError("Signatures do not match")

    return True