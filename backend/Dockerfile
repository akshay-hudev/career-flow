FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy "psycopg[binary]" pydantic pydantic-settings python-multipart httpx redis pdfplumber spacy sentence-transformers google-generativeai python-dotenv alembic langgraph langchain-core "pydantic[email]" email-validator

RUN python -m spacy download en_core_web_sm

COPY . .

EXPOSE 8000

CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}