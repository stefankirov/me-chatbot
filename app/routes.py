"""API route handlers."""

import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.models import ChatRequest, ChatResponse
from app.security import limiter, verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", tags=["ops"])
def health() -> dict:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
@limiter.limit("30/minute")
def chat(request: Request, req: ChatRequest) -> ChatResponse:
    verify_api_key(request)

    if not req.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    # Import here to avoid circular imports with the app factory
    from app.chatbot import Me
    me: Me = request.app.state.me

    try:
        response_text = me.chat(req.message, req.history)
        return ChatResponse(response=response_text)
    except Exception as exc:
        logger.error("Unhandled error in /chat: %s", exc)
        return ChatResponse(response="Something went wrong. Please try again.")
