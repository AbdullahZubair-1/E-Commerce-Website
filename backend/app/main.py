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
