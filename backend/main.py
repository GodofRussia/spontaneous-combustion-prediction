import sys
import os

# Добавляем корневую директорию проекта в PYTHONPATH
# This allows running the app from the 'backend' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""
FastAPI main application entry point.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime

from backend.api.routes import router
from backend.api.models import ErrorResponse
from backend.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## Coal Fire Prediction API

    This API provides endpoints for predicting coal self-ignition in stockpiles.

    ### Features:
    - **Upload CSV data** (supplies, temperature, weather, fires)
    - **Generate predictions** with configurable forecast horizon
    - **Evaluate model performance** against reference data
    - **Get model information** and health status

    ### Workflow:
    1. Upload required data files (supplies.csv, temperature.csv, weather.csv)
    2. Call `/api/predict` to generate fire predictions
    3. Optionally upload fires.csv and call `/api/evaluate` for metrics

    ### Requirements:
    - Model accuracy: ≥70% within ±2 days
    - Forecast horizon: ≥3 days
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Validation Error",
            message="Invalid request data",
            details=exc.errors(),
            timestamp=datetime.utcnow()
        ).dict()
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    """Handle file not found errors."""
    logger.error(f"File not found: {exc}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error="File Not Found",
            message=str(exc),
            timestamp=datetime.utcnow()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred. Please try again later.",
            timestamp=datetime.utcnow()
        ).dict()
    )


# Include API router
app.include_router(router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
        "description": "Coal Fire Prediction API - Predicts self-ignition dates for coal stockpiles"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"API prefix: {settings.API_V1_PREFIX}")
    logger.info(f"Model path: {settings.MODEL_PATH}")

    try:
        # Initialize prediction service (loads model)
        from backend.services.prediction_service import get_prediction_service
        service = get_prediction_service()
        logger.info("Prediction service initialized successfully")

        # Log model info
        info = service.get_model_info()
        logger.info(f"Model type: {info['model_type']}")
        logger.info(f"Features: {info['feature_count']}")
        logger.info(f"MAE: {info['metrics'].get('mae', 'N/A')}")
        logger.info(f"Accuracy ±2 days: {info['metrics'].get('accuracy_pm2', 'N/A')}")

    except Exception as e:
        logger.error(f"Failed to initialize prediction service: {e}")
        logger.warning("API will start but predictions may not work")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )