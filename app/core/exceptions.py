"""Custom exceptions for the TTS API."""

from typing import Any, Dict, Optional


class TTSAPIException(Exception):
    """Base exception for TTS API."""

    def __init__(
            self,
            message: str,
            status_code: int = 500,
            detail: Optional[str] = None,
            headers: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        self.headers = headers
        super().__init__(self.message)


class TTSServiceException(TTSAPIException):
    """Exception raised when TTS service fails."""

    def __init__(self, message: str = "TTS service error", **kwargs):
        super().__init__(message, status_code=503, **kwargs)


class TaskNotFoundException(TTSAPIException):
    """Exception raised when a task is not found."""

    def __init__(self, task_id: str, **kwargs):
        message = f"Task with ID '{task_id}' not found"
        super().__init__(message, status_code=404, **kwargs)


class ValidationException(TTSAPIException):
    """Exception raised for validation errors."""

    def __init__(self, message: str = "Validation error", **kwargs):
        super().__init__(message, status_code=422, **kwargs)


class DatabaseException(TTSAPIException):
    """Exception raised for database errors."""

    def __init__(self, message: str = "Database error", **kwargs):
        super().__init__(message, status_code=500, **kwargs)
