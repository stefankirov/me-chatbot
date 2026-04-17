# Re-export app so both `app:app` and `app.main:app` resolve correctly.
# Azure App Service / Oryx sometimes resolves the package instead of the module.
from app.main import app  # noqa: F401
