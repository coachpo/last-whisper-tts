"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_database_manager,
    get_tts_engine,
    get_tts_engine_manager,
)
from app.core.config import settings
from app.models.database_manager import DatabaseManager
from app.models.schemas import HealthCheckResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check with details",
    description="Get the health status with detailed checks for all services",
)
async def health_check(
    db_manager: DatabaseManager = Depends(get_database_manager),
):
    """Health check endpoint with detailed checks."""
    checks = {}
    overall_status = "healthy"

    # Check database connectivity
    try:
        db_healthy = db_manager.health_check()
        checks["database"] = "healthy" if db_healthy else "unhealthy"
        if not db_healthy:
            overall_status = "unhealthy"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        overall_status = "unhealthy"

    # Check audio directory
    try:
        audio_writable = db_manager.check_audio_directory()
        checks["audio_directory"] = "healthy" if audio_writable else "unhealthy"
        if not audio_writable:
            overall_status = "unhealthy"
    except Exception as e:
        checks["audio_directory"] = f"error: {str(e)}"
        overall_status = "unhealthy"

    # Check TTS service
    try:
        tts_service = get_tts_engine()
        checks["tts_service"] = (
            "healthy" if tts_service.is_initialized else "not_initialized"
        )
    except Exception as e:
        checks["tts_service"] = f"error: {str(e)}"
        overall_status = "unhealthy"

    # Check task manager
    try:
        task_mgr = get_tts_engine_manager()
        checks["task_manager"] = (
            "healthy" if task_mgr.is_initialized else "not_initialized"
        )
    except Exception as e:
        checks["task_manager"] = f"error: {str(e)}"
        overall_status = "unhealthy"

    # Add basic service info
    checks["service"] = settings.app_name
    checks["version"] = settings.app_version
    checks["timestamp"] = datetime.now().isoformat()

    return HealthCheckResponse(
        status=overall_status,
        checks=checks,
    )
