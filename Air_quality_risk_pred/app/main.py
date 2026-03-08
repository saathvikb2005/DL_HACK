"""Air Quality Health Risk Predictor — FastAPI application."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.routes.prediction import router as prediction_router
from app.services.prediction_service import load_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup & shutdown lifecycle.

    Loads ML models when the API starts so predictions are fast.
    """
    print("🔄 Loading AI models...")
    load_models()
    print("✅ Models loaded successfully")

    yield

    print("🛑 Shutting down API...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered Air Quality Health Risk Predictor. "
        "Forecasts AQI for the next 24–48 hours and provides "
        "health warnings and safety recommendations."
    ),
    lifespan=lifespan,
    contact={
        "name": "AI Health Hub",
        "url": "https://github.com",
    },
)

# ---------------------------------------------------
# CORS (allow frontend apps like React / MERN)
# ---------------------------------------------------
# Production: Set ALLOWED_ORIGINS env var to specific domains
# Development: Defaults to localhost
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# API Routes
# ---------------------------------------------------
app.include_router(prediction_router)


# ---------------------------------------------------
# Root Endpoint
# ---------------------------------------------------
@app.get("/", tags=["System"])
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------
# Health Check
# ---------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """
    Used by monitoring systems to verify API status.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }