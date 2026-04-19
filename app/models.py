"""Pydantic request and response models for the API."""

from pydantic import BaseModel, field_validator

# Hard cap on incoming message length — defence against prompt-stuffing
_MAX_MESSAGE_LENGTH = 1000
# Keep only the last N messages from history to limit token usage
_MAX_HISTORY_MESSAGES = 20


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    session_id: str | None = None

    model_config = {"str_strip_whitespace": True}

    @field_validator("message")
    @classmethod
    def truncate_message(cls, v: str) -> str:
        return v[:_MAX_MESSAGE_LENGTH]

    @field_validator("history")
    @classmethod
    def trim_history(cls, v: list[dict]) -> list[dict]:
        return v[-_MAX_HISTORY_MESSAGES:]


class ChatResponse(BaseModel):
    response: str
