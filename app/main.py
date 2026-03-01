from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    yield


app = FastAPI(
    title="BiTrans → SEPAC Migration API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
