"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    get_tts_engine_manager,
    get_database_manager,
    get_tts_engine,
)
from app.api.routes import health, tts
from app.core.config import settings
from app.core.exceptions import TTSAPIException
from app.core.logging import setup_logging, get_logger
from app.models.schemas import ErrorResponse

# Setup logging
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    try:
        # Setup logging
        setup_logging()
        logger.info("Logging system initialized successfully")

        # Initialize database manager
        db_manager = get_database_manager()
        logger.info("Database manager initialized successfully")

        # Initialize TTS service
        tts_engine = get_tts_engine()
        tts_engine.initialize()
        logger.info("TTS engine service initialized successfully")

        # Initialize tts engine manager
        tts_engine_manager = get_tts_engine_manager()
        tts_engine_manager.start_monitoring()
        logger.info("TTS engine manager initialized successfully")

        logger.info("All API services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # Shutdown
    try:
        # Shutdown tts engine manager
        try:
            tts_engine_manager = get_tts_engine_manager()
            tts_engine_manager.stop_monitoring()
            logger.info("TTS engine manager shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down TTS engine manager: {e}")

        # Shutdown TTS service
        tts_engine = get_tts_engine()
        tts_engine.shutdown()
        logger.info("TTS engine service shut down successfully")

        # Shutdown database manager
        db_manager = get_database_manager()
        db_manager.close()
        logger.info("Database manager shut down successfully")

        logger.info("All API services shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url=settings.docs_url if not settings.disable_docs else None,
    redoc_url=settings.redoc_url if not settings.disable_docs else None,
    openapi_url=settings.openapi_url if not settings.disable_docs else None,
    lifespan=lifespan,
)


# Add CORS middleware
def get_cors_origins():
    """Parse CORS origins from comma-separated string."""
    if settings.cors_origins == "*":
        return ["*"]
    return [
        origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()
    ]


def get_cors_methods():
    """Parse CORS methods from comma-separated string."""
    if settings.cors_allow_methods == "*":
        return ["*"]
    return [
        method.strip()
        for method in settings.cors_allow_methods.split(",")
        if method.strip()
    ]


def get_cors_headers():
    """Parse CORS headers from comma-separated string."""
    if settings.cors_allow_headers == "*":
        return ["*"]
    return [
        header.strip()
        for header in settings.cors_allow_headers.split(",")
        if header.strip()
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=get_cors_methods(),
    allow_headers=get_cors_headers(),
)


@app.exception_handler(TTSAPIException)
async def tts_api_exception_handler(request, exc: TTSAPIException):
    """Handle TTS API exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.message, detail=exc.detail).model_dump(),
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error", detail=str(exc)
        ).model_dump(),
    )


# Include routers
app.include_router(health.router)
app.include_router(tts.router)
