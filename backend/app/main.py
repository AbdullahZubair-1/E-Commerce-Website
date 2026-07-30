from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
from pathlib import Path

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.seed import seed_sites_and_owners
from app.api.v1.router import api_router
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A modern e-commerce platform for chemistry supplies.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Static files for uploads
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
(upload_dir / "products").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# Include API router
app.include_router(api_router)


@app.on_event("startup")
async def on_startup():
    # Creates each known site (chemisto, chemisto-food) and its owner
    # account if they don't already exist. Safe to run every time the
    # backend starts -- it's a no-op once everything's already set up.
    await seed_sites_and_owners()


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "success": True,
        "message": "CHEMISTO's Store API is running.",
        "data": {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        },
    }

# ---- Serve the built frontend (single-container deployment) ----
frontend_dist = Path(__file__).resolve().parent.parent / "static_frontend"
if frontend_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        """SPA fallback: any path that isn't an API route, /uploads, /docs,
        or a real static asset gets index.html, so React Router can handle
        client-side routing (e.g. a direct visit to /products/some-slug).

        Critically excludes anything starting with these reserved prefixes
        -- without this, this catch-all "matches" API paths too (like
        /api/v1/products, requested without its real trailing slash) and
        steals them before FastAPI's own built-in trailing-slash redirect
        ever gets a chance to run, silently returning index.html instead of
        real API data or a proper redirect."""
        from fastapi.responses import FileResponse
        from fastapi import HTTPException

        reserved_prefixes = ("api/", "uploads/", "docs", "redoc", "openapi.json", "health")
        if full_path.startswith(reserved_prefixes):
            raise HTTPException(status_code=404)

        candidate = frontend_dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(frontend_dist / "index.html")