"""FastAPI application factory."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.routes import router
from app.security import limiter
from app.config import settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Stefan Kirov — Personal Chatbot API",
        docs_url=None,   # disable Swagger UI in production
        redoc_url=None,
    )

    # ── Rate limiting ──────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── CORS ───────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────
    app.include_router(router)

    # ── Startup / shutdown ────────────────────────────────────────────────
    @app.on_event("startup")
    def startup() -> None:
        from app.chatbot import Me
        try:
            app.state.me = Me()
            logger.info("Chatbot initialised successfully.")
        except Exception as exc:
            logger.critical("Failed to initialise chatbot: %s", exc)
            raise

    @app.on_event("shutdown")
    def shutdown() -> None:
        logger.info("Chatbot shutting down.")

    return app


app = create_app()
