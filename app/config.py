"""
Central configuration — all environment variables are read here and nowhere else.
Import `settings` from this module throughout the app.
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Logging — configured once at import time so every module gets the same format
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)


class Settings:
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Email
    email_smtp_host: str = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    email_smtp_port: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    email_sender: str = os.getenv("EMAIL_SENDER", "")
    email_password: str = os.getenv("EMAIL_PASSWORD", "")
    email_recipient: str = os.getenv("EMAIL_RECIPIENT", "")

    # API security
    chatbot_api_key: str | None = os.getenv("CHATBOT_API_KEY", "").strip() or None

    # CORS
    cors_origins: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")
    ]

    # Profile
    profile_content: str = os.getenv("PROFILE_CONTENT", "").strip()
    profile_file: str = os.getenv("PROFILE_FILE", "profile.txt")

    # Langfuse — env vars are also read directly by the langfuse SDK
    langfuse_enabled: bool = bool(os.getenv("LANGFUSE_SECRET_KEY", "").strip())


settings = Settings()
