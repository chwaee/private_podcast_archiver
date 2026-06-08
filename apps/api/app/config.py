"""M0 config loader. Environment driven. No secrets in code."""
import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV: str = os.getenv("APP_ENV", "development")
APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
DEV_AUTH_BYPASS: bool = os.getenv("DEV_AUTH_BYPASS", "true").lower() in ("1", "true", "yes")

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/podcast_copilot",
)

UPLOADS_DIR: str = os.getenv("UPLOADS_DIR", "/app/data/uploads")
EXPORTS_DIR: str = os.getenv("EXPORTS_DIR", "/app/data/exports")

AI_CHAT_PROVIDER: str = os.getenv("AI_CHAT_PROVIDER", "openai_compatible")
AI_EMBEDDING_PROVIDER: str = os.getenv("AI_EMBEDDING_PROVIDER", "openai_compatible")
AI_EMBEDDING_DIMENSIONS: int = int(os.getenv("AI_EMBEDDING_DIMENSIONS", "1024"))
