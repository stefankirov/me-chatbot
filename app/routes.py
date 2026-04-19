"""API route handlers."""

import json
import logging

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

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
        response_text = me.chat(req.message, req.history, session_id=req.session_id)
        return ChatResponse(response=response_text)
    except Exception as exc:
        logger.error("Unhandled error in /chat: %s", exc)
        return ChatResponse(response="Something went wrong. Please try again.")


@router.post("/chat/stream", tags=["chat"])
@limiter.limit("30/minute")
def chat_stream(request: Request, req: ChatRequest) -> StreamingResponse:
    verify_api_key(request)

    if not req.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    from app.chatbot import Me
    me: Me = request.app.state.me

    def generate():
        try:
            for token in me.stream_chat(req.message, req.history, session_id=req.session_id):
                yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as exc:
            logger.error("Streaming error: %s", exc)
            yield f"data: {json.dumps({'token': 'Sorry, something went wrong. Please try again.'})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
