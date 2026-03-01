from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings
from app.database import Base, engine
from app.routers import (
    upload,
    intersections,
    timing,
    conversion,
    master_list,
    migration,
    export,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Migrate column sizes for PostgreSQL (safe to run multiple times)
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE intersections ALTER COLUMN section TYPE VARCHAR(255)"))
            conn.commit()
        except Exception:
            conn.rollback()
    yield


app = FastAPI(
    title="BiTrans → SEPAC Migration API",
    version="1.0.0",
    lifespan=lifespan,
)

# Build allowed origins: explicit list + any Vercel preview URL
_allowed_origins = settings.get_cors_origins()
_vercel_suffix = ".vercel.app"


def _is_origin_allowed(origin: str) -> bool:
    """Check if origin is in explicit list or is a Vercel preview deployment."""
    if origin in _allowed_origins:
        return True
    # Allow any *.vercel.app subdomain (preview deployments)
    if origin.endswith(_vercel_suffix) and origin.startswith("https://"):
        return True
    return False


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """CORS middleware that dynamically allows Vercel preview URLs."""

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")

        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS" and origin and _is_origin_allowed(origin):
            from starlette.responses import Response
            return Response(status_code=200, headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "86400",
            })

        response = await call_next(request)
        if origin and _is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response


# Use dynamic CORS for Vercel preview support
app.add_middleware(DynamicCORSMiddleware)

app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(intersections.router, prefix="/api/intersections", tags=["Intersections"])
app.include_router(timing.router, prefix="/api/timing", tags=["Timing"])
app.include_router(conversion.router, prefix="/api/conversion", tags=["Conversion"])
app.include_router(master_list.router, prefix="/api/master-list", tags=["Master List"])
app.include_router(migration.router, prefix="/api/migration", tags=["Migration"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
