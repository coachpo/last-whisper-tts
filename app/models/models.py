"""SQLAlchemy database models."""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text

# Import Base from database_manager to avoid circular imports
from .database_manager import Base
from .enums import TaskStatus


class Task(Base):
    """SQLAlchemy model for TTS tasks, matching existing database schema."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, unique=True, nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    text_hash = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default=TaskStatus.PENDING, index=True)
    output_file_path = Column(Text)
    custom_filename = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    submitted_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    failed_at = Column(DateTime)
    error_message = Column(Text)
    file_size = Column(Integer)
    sampling_rate = Column(Integer)
    device = Column(String)
    task_metadata = Column("metadata", Text)  # JSON string

    # No relationships needed for TTS-only functionality

    @property
    def metadata_dict(self) -> dict:
        """Parse metadata JSON string to dict."""
        if self.task_metadata:
            try:
                return json.loads(self.task_metadata)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @property
    def duration(self) -> Optional[float]:
        """Calculate audio duration from metadata."""
        metadata = self.metadata_dict
        return metadata.get("duration")


# Only Task model is needed for TTS-only functionality
