"""
AI tool definitions — both the callable implementations and their OpenAI JSON schemas.

Adding a new tool:
  1. Write the function below.
  2. Add its schema to TOOL_SCHEMAS.
  3. Register it in TOOL_REGISTRY.
"""

import logging

from app.email import send_email

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------

def record_user_details(email: str, name: str = "Name not provided", notes: str = "not provided") -> dict:
    logger.info("Recording user: name=%s email=%s", name, email)
    send_email(
        subject="Chatbot: New visitor contact",
        body=f"Name: {name}\nEmail: {email}\nNotes: {notes}",
    )
    return {"recorded": "ok"}


def record_unknown_question(question: str) -> dict:
    logger.info("Recording unknown question: %s", question)
    send_email(subject="Chatbot: Unknown question", body=question)
    return {"recorded": "ok"}


# ---------------------------------------------------------------------------
# Registry — used by the chatbot to dispatch tool calls by name
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, callable] = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
}

# ---------------------------------------------------------------------------
# OpenAI schemas
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "record_user_details",
            "description": (
                "Use this tool to record that a visitor is interested in getting in touch "
                "and has provided their email address."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "The visitor's email address.",
                    },
                    "name": {
                        "type": "string",
                        "description": "The visitor's name, if they provided it.",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Brief context about the conversation — what they're looking for.",
                    },
                },
                "required": ["email"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_unknown_question",
            "description": (
                "Use this tool when a visitor asks a relevant question about Stefan "
                "that you couldn't answer from your profile information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question that couldn't be answered.",
                    },
                },
                "required": ["question"],
                "additionalProperties": False,
            },
        },
    },
]
