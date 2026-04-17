# Root-level ASGI entry point for gunicorn.
# Using this file avoids naming collisions between the `app` package
# and gunicorn's `app:app` module resolution on Azure App Service.
from app.main import app  # noqa: F401
