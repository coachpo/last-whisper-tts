"""FastAPI dependencies."""

from app.core.config import settings
from app.models.database_manager import DatabaseManager

# Only TTS-related services are needed
from app.services.task_service import TaskService
from app.tts_engine.tts_engine_manager import TTSEngineManager
from app.tts_engine.tts_engine_wrapper import TTSEngineWrapper

# Global instances
_database_manager = None
_task_manager = None
_tts_engine = None
_task_service = None


def get_database_manager() -> DatabaseManager:
    """Dependency to get database manager."""
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager()
    return _database_manager


# Only TTS-related service dependencies are needed


def get_tts_engine_manager() -> TTSEngineManager:
    """Dependency to get unified task manager."""
    global _task_manager
    if _task_manager is None:
        tts_service = get_tts_engine()
        _task_manager = TTSEngineManager(
            settings.database_url,
            tts_service._service if tts_service.is_initialized else None,
        )
    return _task_manager


def get_tts_engine() -> TTSEngineWrapper:
    """Dependency to get TTS engine."""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TTSEngineWrapper()
    return _tts_engine


# No tags service needed for TTS-only functionality


# Legacy dependencies for backward compatibility
def get_task_service() -> TaskService:
    """Dependency to get database service."""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service
