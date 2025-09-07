"""Pydantic models for API request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .enums import TaskStatus


class TTSConvertRequest(BaseModel):
    """Request model for TTS conversion."""

    text: str = Field(
        ..., min_length=1, max_length=10000, description="Text to convert to speech"
    )
    custom_filename: Optional[str] = Field(
        None, max_length=255, description="Optional custom filename (without extension)"
    )
    language: str = Field(
        default="fi",
        min_length=2,
        max_length=10,
        description="Language code for TTS (default: 'fi')",
    )


class TTSMultiConvertRequest(BaseModel):
    """Request model for multiple text TTS conversion."""

    texts: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of texts to convert to speech",
    )
    language: str = Field(
        default="fi",
        min_length=2,
        max_length=10,
        description="Language code for TTS (default: 'fi')",
    )

    @field_validator("texts")
    @classmethod
    def validate_texts_not_empty(cls, v):
        """Validate that individual text items are not empty."""
        for i, text in enumerate(v):
            if not text or not text.strip():
                raise ValueError(f"Text item at index {i} cannot be empty")
        return v


class TTSConvertResponse(BaseModel):
    """Response model for TTS conversion submission."""

    conversion_id: str = Field(..., description="Unique ID for the conversion task")
    text: str = Field(..., description="Echo of the submitted text")
    status: TaskStatus = Field(..., description="Current status of the conversion")
    submitted_at: datetime = Field(
        ..., description="Timestamp when the task was submitted"
    )


class TTSMultiConvertResponse(BaseModel):
    """Response model for multiple text TTS conversion submission."""

    conversion_ids: list[str] = Field(
        ..., description="List of unique IDs for the conversion tasks"
    )
    texts: list[str] = Field(..., description="Echo of the submitted texts")
    status: TaskStatus = Field(..., description="Current status of the conversions")
    submitted_at: datetime = Field(
        ..., description="Timestamp when the tasks were submitted"
    )


class TTSTaskResponse(BaseModel):
    """Response model for TTS task status and details."""

    conversion_id: str = Field(..., description="Unique ID for the conversion task")
    text: str = Field(..., description="Original text submitted for conversion")
    status: TaskStatus = Field(
        ..., description="Current status: queued, processing, completed, failed"
    )
    output_file_path: Optional[str] = Field(
        None, description="Path to the generated audio file (when completed)"
    )
    custom_filename: Optional[str] = Field(
        None, description="Custom filename specified in request"
    )

    # Timestamps
    submitted_at: Optional[datetime] = Field(
        None, description="When the task was submitted"
    )
    started_at: Optional[datetime] = Field(None, description="When processing started")
    completed_at: Optional[datetime] = Field(
        None, description="When processing completed"
    )
    failed_at: Optional[datetime] = Field(None, description="When the task failed")

    # Audio metadata (when completed)
    file_size: Optional[int] = Field(None, description="File size in bytes")
    sampling_rate: Optional[int] = Field(None, description="Audio sampling rate in Hz")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")

    # Processing metadata
    device: Optional[str] = Field(None, description="Device used for processing")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ErrorResponse(BaseModel):
    """Response model for API errors."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Current timestamp")


# Only TTS-related schemas are needed


class HealthCheckResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Overall health status")
    checks: dict = Field(..., description="Individual health checks")


# No tag schemas needed for TTS-only functionality
