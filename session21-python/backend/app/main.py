from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .routes import router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Customer support ticketing API for the Session 21 DevOps capstone.",
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])
# Schema is owned by Alembic (run before Uvicorn in the container), not created here.
Instrumentator(excluded_handlers=["/metrics", "/health", "/ready"]).instrument(app).expose(
    app, endpoint="/metrics", include_in_schema=False
)
app.include_router(router)


@app.get("/")
def root():
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}


@app.get("/health")
def health():
    """Liveness: the process is up and serving requests."""
    return {"status": "UP"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    """Readiness: the database is reachable, so this pod can take traffic."""
    db.execute(text("SELECT 1"))
    return {"status": "READY"}
