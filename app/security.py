"""API key verification and rate limiting."""

import logging

from fastapi import HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

logger = logging.getLogger(__name__)

# Shared limiter instance — imported by routes and registered on the app in main.py
limiter = Limiter(key_func=get_remote_address)


def verify_api_key(request: Request) -> None:
    """
    Raise HTTP 401 if CHATBOT_API_KEY is configured and the request
    doesn't supply a matching X-API-Key header.

    When CHATBOT_API_KEY is not set the endpoint is open — useful for local dev.
    """
    if settings.chatbot_api_key is None:
        return

    provided = request.headers.get("X-API-Key", "")
    if provided != settings.chatbot_api_key:
        logger.warning("Rejected request with invalid API key from %s", request.client.host)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
