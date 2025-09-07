"""Centralized enum definitions for status fields."""

from enum import Enum


class TaskStatus(str, Enum):
    """Enum for Task model status field."""

    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DONE = "done"


# Only TaskStatus is needed for TTS-only functionality
