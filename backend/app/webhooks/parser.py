"""
Parse raw GitHub webhook JSON into our domain models.
"""
from typing import Any
from app.models.webhook import WebhookPayload, RepositoryInfo, PullRequestInfo
from app.models.enums import WebhookEventType
from app.core.exceptions import InvalidPayloadError


def parse_webhook_payload(
    body: dict[str, Any],
    event_type: str,        # from X-GitHub-Event header
    delivery_id: str | None, # from X-GitHub-Delivery header
) -> WebhookPayload:
    """
    Convert raw webhook JSON into a validated WebhookPayload.

    Raises InvalidPayloadError if required fields are missing.
    """
    try:
        # Map event type string to enum (e.g., "pull_request" -> PULL_REQUEST)
        event_enum = WebhookEventType(event_type)

        # Build repository info
        repo_data = body.get("repository", {})
        repository = RepositoryInfo(
            full_name=repo_data.get("full_name", ""),
            owner=repo_data["owner"]["login"] if "owner" in repo_data else "",
            name=repo_data.get("name", ""),
            clone_url=repo_data.get("clone_url"),
            default_branch=repo_data.get("default_branch", "main"),
        )

        # Build PR info if present
        pr_data = body.get("pull_request")
        pull_request = None
        if pr_data:
            pull_request = PullRequestInfo(
                number=pr_data["number"],
                title=pr_data["title"],
                body=pr_data.get("body"),
                state=pr_data.get("state", "open"),
                html_url=pr_data["html_url"],
                diff_url=pr_data["diff_url"],
                base_ref=pr_data["base"]["ref"],
                head_ref=pr_data["head"]["ref"],
                base_sha=pr_data["base"]["sha"],
                head_sha=pr_data["head"]["sha"],
                user_login=pr_data["user"]["login"],
            )

        # Determine action (e.g., "opened", "synchronize")
        action = body.get("action", "")

        return WebhookPayload(
            event_type=event_enum,
            action=action,
            repository=repository,
            pull_request=pull_request,
            delivery_id=delivery_id,
            raw_payload=body,
        )
    except (KeyError, TypeError, ValueError) as e:
        raise InvalidPayloadError(f"Invalid webhook payload: {e}") from e