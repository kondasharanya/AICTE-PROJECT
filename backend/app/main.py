"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import setup_logging
from app.api.routes import startups, grants, proposals
from app.services.grant_service import grant_service
from app.core.database import SessionLocal

# ── Startup / Shutdown lifecycle ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = logging.getLogger("grant_finder")
    logger.info("🚀 Starting AICTE AI Grant & Funding Finder...")

    # Create all DB tables
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created/verified")

    # Seed initial grant data
    db = SessionLocal()
    try:
        count = await grant_service.seed_grants(db)
        logger.info(f"✅ Grant database ready with {count} grants")
    finally:
        db.close()

    yield

    logger.info("👋 Shutting down AICTE Grant Finder...")


# ── App Factory ────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="AICTE AI Grant & Funding Finder for Startups",
        description=(
            "An AI-powered platform that discovers, matches, and generates proposals "
            "for grants and funding opportunities for Indian and global startups. "
            "Powered by IBM Granite (watsonx.ai)."
        ),
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ───────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── API Routers ────────────────────────────────────────────────────────────
    app.include_router(startups.router, prefix="/api/v1")
    app.include_router(grants.router, prefix="/api/v1")
    app.include_router(proposals.router, prefix="/api/v1")

    # ── Health check ───────────────────────────────────────────────────────────
    @app.get("/api/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "AICTE AI Grant Finder",
            "version": "1.0.0",
            "ibm_granite_model": settings.ibm_granite_model_id,
            "environment": settings.app_env,
        }

    # ── Serve frontend static files ────────────────────────────────────────────
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "dist")
    if os.path.exists(frontend_path):
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

    return app


app = create_app()
