"""Database service layer."""

from typing import List, Optional

from app.core.config import settings
from app.core.exceptions import DatabaseException, TaskNotFoundException
from app.models.database_manager import DatabaseManager
from app.models.models import Task


class TaskService:
    """Service for database operations."""

    def __init__(self):
        # Reuse a shared DatabaseManager if one exists
        self.db_manager = getattr(
            DatabaseManager, "default_instance", None
        ) or DatabaseManager(settings.database_url)

    def get_task_by_id(self, task_id: str) -> Task:
        """Get a task by ID, raising exception if not found."""
        try:
            task = self.db_manager.get_task_by_id(task_id)
        except Exception as e:
            # Surface database errors as DatabaseException, as tests expect
            raise DatabaseException(str(e))

        if not task:
            raise TaskNotFoundException(task_id)
        return task

    def get_all_tasks(
        self, status: Optional[str] = None, limit: int = 100
    ) -> List[Task]:
        """Get all tasks with optional filtering."""
        # Input validation as per tests
        if limit is None or limit <= 0:
            raise ValueError("limit must be a positive integer")

        try:
            return self.db_manager.get_all_tasks(status=status, limit=limit)
        except Exception as e:
            raise DatabaseException(f"Failed to retrieve tasks: {str(e)}")
