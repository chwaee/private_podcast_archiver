FROM python:3.12-slim

WORKDIR /app

# System dependencies for building psycopg etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies for M0 foundations + M1 models (includes pgvector for Vector columns)
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        fastapi \
        "uvicorn[standard]" \
        pydantic \
        python-dotenv \
        sqlalchemy \
        alembic \
        "psycopg[binary]" \
        pgvector \
        httpx \  # for embedding provider (M4)
        python-multipart  # required by FastAPI for UploadFile / multipart form data (M3 transcript upload)

# Copy the rest of the app (volume mount will override in dev)
COPY . .

# Entrypoint that runs migrations + seed automatically (for `docker compose up -d --build` only workflow)
RUN chmod +x entrypoint.sh || true

EXPOSE 8000

CMD ["./entrypoint.sh"]
