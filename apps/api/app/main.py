from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Private Podcast Archive Copilot API",
    version="0.1.0",
    description="M0 foundations only. See PRODUCT_SPEC.md for full design.",
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
    """Exact response required by PRODUCT_SPEC.md §14.1 for M0."""
    return {
        "status": "ok",
        "version": "0.1.0",
    }


# Future routers (M1+):
# from .api import shows, episodes, search, chat, exports, jobs
# app.include_router(...)
