FROM python:3.11-slim

WORKDIR /app

# Build context is the REPO ROOT (see docker-compose.yml `context: .` and
# railway.toml `dockerfilePath = "backend/Dockerfile"`). The app imports
# `backend.*`, so the code must live under /app/backend for uvicorn to resolve it.
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/

EXPOSE 8000

CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
