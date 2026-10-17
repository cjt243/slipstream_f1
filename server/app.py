"""Slipstream F1 Fantasy League — FastAPI application entry point.

Run locally:
    cd server && uv run uvicorn app:app --port 3001 --reload
"""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

app = FastAPI(title="Slipstream F1 Fantasy League API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All API routes are mounted under /api.
api = APIRouter(prefix="/api")


@api.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# Feature routers are registered here as later issues add them, e.g.:
#   from routes import auth, contracts, races, scores, leaderboard, admin
#   api.include_router(auth.router)
#   ...

app.include_router(api)
