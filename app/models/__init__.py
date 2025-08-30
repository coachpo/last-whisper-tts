"""Models package for SQLAlchemy models, database manager, and Pydantic schemas."""

# Import database manager
from .database_manager import DatabaseManager, Base
# Import SQLAlchemy models
from .models import Task
# Import Pydantic schemas
from .schemas import (
    # TTS schemas
    TTSConvertRequest,
    TTSMultiConvertRequest,
    TTSConvertResponse,
    TTSMultiConvertResponse,
    TTSTaskResponse,

    # Only TTS-related schemas are needed

    # Health and error schemas
    HealthResponse,
    HealthCheckResponse,
    ErrorResponse,
)

__all__ = [
    # SQLAlchemy models
    "Task",

    # Database manager
    "DatabaseManager",
    "Base",

    # TTS schemas
    "TTSConvertRequest",
    "TTSMultiConvertRequest",
    "TTSConvertResponse",
    "TTSMultiConvertResponse",
    "TTSTaskResponse",

    # Only TTS-related schemas are exported

    # Health and error schemas
    "HealthResponse",
    "HealthCheckResponse",
    "ErrorResponse",
]
