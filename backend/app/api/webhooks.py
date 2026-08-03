"""
Webhook receiver endpoint.
"""
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from app.webhooks.validator import verify_signature
from app.webhooks.parser import parse_webhook_payload
from app.webhooks.router import route_webhook
from app.core.exceptions import InvalidSignatureError, InvalidPayloadError, WebhookError

router = APIRouter(tags=["webhooks"])


@router.post("/webhook", status_code=202)
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
    x_github_delivery: str = Header(None, alias="X-GitHub-Delivery"),
):
    """
    Receives GitHub webhook events.

    - Validates HMAC signature to ensure authenticity.
    - Parses payload into a clean domain model.
    - Enqueues a background job for async processing.
    - Returns 202 Accepted immediately (before the review runs).
    """
    # 1. Read raw body bytes (must be exactly as received)
    body_bytes = await request.body()

    # 2. Verify signature (raises InvalidSignatureError if fails)
    try:
        verify_signature(body_bytes, x_hub_signature_256)
    except InvalidSignatureError as e:
        raise HTTPException(status_code=401, detail=str(e))

    # 3. Parse JSON
    try:
        body_dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # 4. Build domain model (raises InvalidPayloadError)
    try:
        payload = parse_webhook_payload(body_dict, x_github_event, x_github_delivery)
    except InvalidPayloadError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 5. Route to background queue (raises WebhookError if unsupported)
    try:
        job_id = await route_webhook(payload)
    except WebhookError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 6. Return acknowledgement (the review will be processed later)
    return {
        "status": "accepted",
        "message": "Review queued for processing",
        "job_id": job_id,
        "pr_number": payload.pull_request.number if payload.pull_request else None,
    }