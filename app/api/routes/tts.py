"""TTS conversion endpoints."""

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.dependencies import get_task_service, get_tts_engine_manager
from app.core.exceptions import (
    TaskNotFoundException,
    TTSServiceException,
    ValidationException,
)
from app.models.schemas import (
    ErrorResponse,
    TTSConvertRequest,
    TTSConvertResponse,
    TTSMultiConvertRequest,
    TTSMultiConvertResponse,
    TTSTaskResponse,
)
from app.models.enums import TaskStatus
from app.services.task_service import TaskService
from app.tts_engine.tts_engine_manager import TTSEngineManager

router = APIRouter(prefix="/api/v1/tts", tags=["TTS"])


@router.post(
    "/convert",
    response_model=TTSConvertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit text for TTS conversion",
    description="Submit text for text-to-speech conversion. Returns conversion ID and status.",
    responses={
        201: {"description": "Conversion task created successfully"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        503: {"model": ErrorResponse, "description": "TTS service unavailable"},
    },
)
async def convert_text(
    request: TTSConvertRequest,
    tts_engine_mgr: TTSEngineManager = Depends(get_tts_engine_manager),
    task_service: TaskService = Depends(get_task_service),
):
    """Submit text for TTS conversion."""
    try:
        # Submit task to TTS manager
        task_id = tts_engine_mgr.submit_task(
            text=request.text,
            custom_filename=request.custom_filename,
            language=request.language,
        )

        if not task_id:
            raise TTSServiceException("Failed to submit TTS task")

        # Get the created task from database
        task = task_service.get_task_by_id(task_id)

        return TTSConvertResponse(
            conversion_id=task.task_id,
            text=task.original_text,
            status=task.status,
            submitted_at=task.submitted_at or task.created_at,
        )

    except TaskNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except TTSServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process TTS request: {str(e)}",
        )


@router.post(
    "/convert-multiple",
    response_model=TTSMultiConvertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit multiple texts for TTS conversion",
    description="Submit multiple texts for text-to-speech conversion. Returns conversion IDs and status.",
    responses={
        201: {"description": "Multiple conversion tasks created successfully"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        503: {"model": ErrorResponse, "description": "TTS service unavailable"},
    },
)
async def convert_multiple_texts(
    request: TTSMultiConvertRequest,
    tts_engine_mgr: TTSEngineManager = Depends(get_tts_engine_manager),
    task_service: TaskService = Depends(get_task_service),
):
    """Submit multiple texts for TTS conversion."""
    try:
        # Submit multiple tasks to TTS manager
        task_ids = tts_engine_mgr.submit_multiple_tasks(
            texts=request.texts, language=request.language
        )

        if not task_ids:
            raise TTSServiceException("Failed to submit TTS tasks")

        # Get the created tasks from database
        tasks = []
        for task_id in task_ids:
            task = task_service.get_task_by_id(task_id)
            tasks.append(task)

        return TTSMultiConvertResponse(
            conversion_ids=task_ids,
            texts=request.texts,
            status="queued",
            submitted_at=(
                tasks[0].submitted_at or tasks[0].created_at
                if tasks
                else datetime.now()
            ),
        )

    except TaskNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except TTSServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process multiple TTS requests: {str(e)}",
        )


@router.get(
    "/supported-languages",
    response_model=list[str],
    summary="Get supported languages",
    description="Get list of supported languages for TTS conversion.",
    responses={
        200: {"description": "Supported languages retrieved successfully"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_supported_languages(
    tts_engine_mgr: TTSEngineManager = Depends(get_tts_engine_manager),
):
    """Get list of supported languages for TTS conversion."""
    try:
        return tts_engine_mgr.get_supported_languages()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supported languages: {str(e)}",
        )


@router.get(
    "/{conversion_id}",
    response_model=TTSTaskResponse,
    summary="Get TTS conversion status",
    description="Get the status and details of a TTS conversion task by ID.",
    responses={
        200: {"description": "Task status retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_conversion_status(
    conversion_id: str, task_service: TaskService = Depends(get_task_service)
):
    """Get TTS conversion status and details."""
    try:
        # Get task from database
        task = task_service.get_task_by_id(conversion_id)

        # Calculate duration if file exists and has metadata
        duration = None
        if (
            task.status in [TaskStatus.COMPLETED, TaskStatus.DONE]
            and task.output_file_path
            and os.path.exists(task.output_file_path)
        ):
            # Try to get duration from metadata first
            duration = task.duration

            # If not in metadata, calculate from file size and sampling rate
            if duration is None and task.file_size and task.sampling_rate:
                # Rough estimate: file_size / (sampling_rate * 2 bytes per sample)
                # This is approximate since it doesn't account for WAV header
                duration = task.file_size / (task.sampling_rate * 2)

        return TTSTaskResponse(
            conversion_id=task.task_id,
            text=task.original_text,
            status=task.status,
            output_file_path=task.output_file_path,
            custom_filename=task.custom_filename,
            submitted_at=task.submitted_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            failed_at=task.failed_at,
            file_size=task.file_size,
            sampling_rate=task.sampling_rate,
            duration=duration,
            device=task.device,
            error_message=task.error_message,
        )

    except TaskNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task status: {str(e)}",
        )


@router.get(
    "",
    response_model=list[TTSTaskResponse],
    summary="List TTS conversions",
    description="List TTS conversion tasks, optionally filtered by status.",
    responses={
        200: {"description": "Tasks retrieved successfully"},
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_conversions(
    status: Optional[str] = None,
    limit: int = 50,
    task_service: TaskService = Depends(get_task_service),
):
    """List TTS conversion tasks."""
    try:
        # Validate status parameter
        if status and status not in [
            TaskStatus.QUEUED,
            TaskStatus.PROCESSING,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.DONE,
        ]:
            raise ValidationException(
                "Invalid status. Must be one of: queued, processing, completed, failed, done"
            )

        # Validate limit
        if limit < 1 or limit > 1000:
            raise ValidationException("Limit must be between 1 and 1000")

        tasks = task_service.get_all_tasks(status=status, limit=limit)

        results = []
        for task in tasks:
            # Calculate duration if available
            duration = None
            if (
                task.status in [TaskStatus.COMPLETED, TaskStatus.DONE]
                and task.output_file_path
                and os.path.exists(task.output_file_path)
            ):
                duration = task.duration
                if duration is None and task.file_size and task.sampling_rate:
                    duration = task.file_size / (task.sampling_rate * 2)

            results.append(
                TTSTaskResponse(
                    conversion_id=task.task_id,
                    text=task.original_text,
                    status=task.status,
                    output_file_path=task.output_file_path,
                    custom_filename=task.custom_filename,
                    submitted_at=task.submitted_at,
                    started_at=task.started_at,
                    completed_at=task.completed_at,
                    failed_at=task.failed_at,
                    file_size=task.file_size,
                    sampling_rate=task.sampling_rate,
                    duration=duration,
                    device=task.device,
                    error_message=task.error_message,
                )
            )

        return results

    except ValidationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}",
        )


@router.get(
    "/{conversion_id}/download",
    summary="Download TTS audio file",
    description="Download the generated audio file for a completed TTS conversion.",
    responses={
        200: {"description": "Audio file download", "content": {"audio/wav": {}}},
        404: {"model": ErrorResponse, "description": "Task or file not found"},
        400: {"model": ErrorResponse, "description": "Task not completed"},
    },
)
async def download_audio_file(
    conversion_id: str, task_service: TaskService = Depends(get_task_service)
):
    """Download the audio file for a completed TTS conversion."""
    try:
        # Get task from database
        task = task_service.get_task_by_id(conversion_id)

        # Check if task is completed
        if task.status not in [TaskStatus.COMPLETED, TaskStatus.DONE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task is not completed. Current status: {task.status}",
            )

        # Check if file exists
        if not task.output_file_path or not os.path.exists(task.output_file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found"
            )

        # Determine filename for download
        filename = task.custom_filename or f"tts_{conversion_id}"
        if not filename.endswith(".wav"):
            filename += ".wav"

        return FileResponse(
            path=task.output_file_path,
            media_type="audio/wav",
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(
                    task.file_size or os.path.getsize(task.output_file_path)
                ),
            },
        )

    except TaskNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download audio file: {str(e)}",
        )
