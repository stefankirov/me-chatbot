#!/bin/bash
# Azure App Service startup script for FastAPI + Gunicorn
# Set this as the Startup Command in Azure, or point the startup command here: bash startup.sh

set -e

echo "Starting chatbot API..."
echo "Python: $(python3 --version)"
echo "Working dir: $(pwd)"
echo "Files: $(ls)"

# Azure sets PORT env var; fall back to 8000
PORT="${PORT:-8000}"

exec gunicorn \
  -w 2 \
  -k uvicorn.workers.UvicornWorker \
  app.main:app \
  --timeout 120 \
  --bind "0.0.0.0:${PORT}" \
  --access-logfile - \
  --error-logfile - \
  --log-level info
