from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .api.episodes import router as episodes_router
from .api.shows import router as shows_router

app = FastAPI(
    title="Private Podcast Archive Copilot API",
    version="0.1.0",
    description="M2 Show/Episode UI + M3/M4 transcript/ingestion (built on M0/M1 foundations). See PRODUCT_SPEC.md.",
)

# CORS - allow the web dev server
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    """Exact response required by PRODUCT_SPEC.md §14.1."""
    return {
        "status": "ok",
        "version": "0.1.0",
    }


# M2 routers (shows + episodes CRUD)
app.include_router(shows_router, prefix="/api")
app.include_router(episodes_router, prefix="/api")

# Future:
# from .api import search, chat, exports, jobs
# app.include_router(...)
