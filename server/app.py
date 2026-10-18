"""Slipstream F1 Fantasy League — FastAPI application entry point.

Run locally:
    cd server && uv run uvicorn app:app --port 3001 --reload
"""

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import settings
from routes import auth

# Docs live under /api so they're reachable through the Vercel /api rewrite.
app = FastAPI(
    title="Slipstream F1 Fantasy League API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Every non-2xx response uses the contract's {"error": "..."} shape
# (docs/api-contracts.md), not FastAPI's default {"detail": ...}.
@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        {"error": str(exc.detail)}, status_code=exc.status_code, headers=exc.headers
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", ())[1:])
    msg = first.get("msg", "Invalid request").removeprefix("Value error, ")
    message = f"{field}: {msg}" if field else msg
    return JSONResponse({"error": message}, status_code=422)


# All API routes are mounted under /api.
api = APIRouter(prefix="/api")


@api.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


api.include_router(auth.router)

app.include_router(api)
