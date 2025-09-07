import hashlib
import json
import queue
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func

from app.core.config import settings
from app.core.logging import get_logger
from app.models.database_manager import DatabaseManager
from app.models.models import Task
from app.models.enums import TaskStatus

# Setup logger for this module
logger = get_logger(__name__)


class TTSEngineManager:
    def __init__(self, database_url: str = settings.database_url, tts_service=None):
        self.db_manager = DatabaseManager(database_url)
        self.tts_service = tts_service
        self.is_running = False
        self.monitor_thread = None

    def _calculate_text_hash(self, text: str) -> str:
        """Calculate MD5 hash of text for deduplication"""
        return hashlib.md5(text.encode()).hexdigest()

    def _get_existing_task_by_hash(self, text_hash: str) -> Optional[Task]:
        """Get any existing task by text hash (any status except failed)"""
        with self.db_manager.get_session() as session:
            return (
                session.query(Task)
                .filter(
                    and_(Task.text_hash == text_hash, Task.status != TaskStatus.FAILED)
                )
                .first()
            )

    def submit_task(
        self, text: str, custom_filename: Optional[str] = None, language: str = "fi"
    ) -> Optional[str]:
        """Submit a new TTS task and store it in database"""
        if not text.strip():
            logger.error("Error: Empty text provided")
            return None

        if not self.tts_service:
            logger.error("Error: TTS service not available")
            return None

        # Validate language support
        if language not in settings.tts_supported_languages:
            logger.error(
                f"Error: Language '{language}' is not supported. Supported languages: {settings.tts_supported_languages}"
            )
            return None

        text_hash = self._calculate_text_hash(text)

        # Check for existing task with same text hash (any status except failed)
        existing_task = self._get_existing_task_by_hash(text_hash)
        if existing_task:
            status = existing_task.status
            task_id = existing_task.task_id

            if status in [TaskStatus.COMPLETED, TaskStatus.DONE]:
                logger.info(
                    f"TTS task with same text already completed (ID: {task_id})"
                )
                return task_id
            elif status in [TaskStatus.QUEUED, TaskStatus.PROCESSING]:
                logger.info(f"TTS task with same text already {status} (ID: {task_id})")
                return task_id

        # No existing task found, create new one
        task_id = self.tts_service.submit_request(text, custom_filename, language)
        if not task_id:
            return None

        # Insert initial task record into database
        with self.db_manager.get_session() as session:
            new_task = Task(
                task_id=task_id,
                original_text=text,
                text_hash=text_hash,
                status=TaskStatus.QUEUED,
                custom_filename=custom_filename,
                created_at=datetime.now(),
                submitted_at=datetime.now(),
            )
            session.add(new_task)
            session.commit()

        logger.info(f"New TTS task created successfully (ID: {task_id})")
        return task_id

    def _task_exists(self, task_id: str) -> bool:
        """Check if task already exists in database"""
        with self.db_manager.get_session() as session:
            return (
                session.query(Task).filter(Task.task_id == task_id).first() is not None
            )

    def _get_completed_task_by_hash(self, text_hash: str) -> Optional[Task]:
        """Get completed task by text hash for deduplication"""
        with self.db_manager.get_session() as session:
            return (
                session.query(Task)
                .filter(
                    and_(
                        Task.text_hash == text_hash, Task.status == TaskStatus.COMPLETED
                    )
                )
                .first()
            )

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get current status of a task"""
        with self.db_manager.get_session() as session:
            task = session.query(Task).filter(Task.task_id == task_id).first()
            if task:
                return {
                    "id": task.id,
                    "task_id": task.task_id,
                    "original_text": task.original_text,
                    "text_hash": task.text_hash,
                    "status": task.status,
                    "output_file_path": task.output_file_path,
                    "custom_filename": task.custom_filename,
                    "created_at": (
                        task.created_at.isoformat() if task.created_at else None
                    ),
                    "submitted_at": (
                        task.submitted_at.isoformat() if task.submitted_at else None
                    ),
                    "started_at": (
                        task.started_at.isoformat() if task.started_at else None
                    ),
                    "completed_at": (
                        task.completed_at.isoformat() if task.completed_at else None
                    ),
                    "failed_at": task.failed_at.isoformat() if task.failed_at else None,
                    "error_message": task.error_message,
                    "file_size": task.file_size,
                    "sampling_rate": task.sampling_rate,
                    "device": task.device,
                    "metadata": task.metadata_dict,
                    "duration": task.duration,
                }
            return None

    def get_all_tasks(self, status: Optional[str] = None) -> List[Dict]:
        """Get all tasks, optionally filtered by status"""
        with self.db_manager.get_session() as session:
            query = session.query(Task)
            if status:
                query = query.filter(Task.status == status)

            tasks = query.order_by(Task.created_at.desc()).all()

            return [
                {
                    "id": task.id,
                    "task_id": task.task_id,
                    "original_text": task.original_text,
                    "text_hash": task.text_hash,
                    "status": task.status,
                    "output_file_path": task.output_file_path,
                    "custom_filename": task.custom_filename,
                    "created_at": (
                        task.created_at.isoformat() if task.created_at else None
                    ),
                    "submitted_at": (
                        task.submitted_at.isoformat() if task.submitted_at else None
                    ),
                    "started_at": (
                        task.started_at.isoformat() if task.started_at else None
                    ),
                    "completed_at": (
                        task.completed_at.isoformat() if task.completed_at else None
                    ),
                    "failed_at": task.failed_at.isoformat() if task.failed_at else None,
                    "error_message": task.error_message,
                    "file_size": task.file_size,
                    "sampling_rate": task.sampling_rate,
                    "device": task.device,
                    "metadata": task.metadata_dict,
                    "duration": task.duration,
                }
                for task in tasks
            ]

    def get_tasks_by_text_hash(self, text_hash: str) -> List[Dict]:
        """Get all tasks with the same text hash"""
        with self.db_manager.get_session() as session:
            tasks = session.query(Task).filter(Task.text_hash == text_hash).all()

            return [
                {
                    "id": task.id,
                    "task_id": task.task_id,
                    "original_text": task.original_text,
                    "text_hash": task.text_hash,
                    "status": task.status,
                    "output_file_path": task.output_file_path,
                    "custom_filename": task.custom_filename,
                    "created_at": (
                        task.created_at.isoformat() if task.created_at else None
                    ),
                    "submitted_at": (
                        task.submitted_at.isoformat() if task.submitted_at else None
                    ),
                    "started_at": (
                        task.started_at.isoformat() if task.started_at else None
                    ),
                    "completed_at": (
                        task.completed_at.isoformat() if task.completed_at else None
                    ),
                    "failed_at": task.failed_at.isoformat() if task.failed_at else None,
                    "error_message": task.error_message,
                    "file_size": task.file_size,
                    "sampling_rate": task.sampling_rate,
                    "device": task.device,
                    "metadata": task.metadata_dict,
                    "duration": task.duration,
                }
                for task in tasks
            ]

    def start_monitoring(self):
        """Start monitoring TTS service task queue"""
        if not self.is_running and self.tts_service:
            self.is_running = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_task_message_queue, daemon=True
            )
            self.monitor_thread.start()
            logger.info("TTS engine manager task monitoring started!")

    def stop_monitoring(self):
        """Stop monitoring task queue"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("TTS engine manager task monitoring stopped!")

    def _monitor_task_message_queue(self):
        """Monitor TTS service task queue and update database"""
        task_message_queue = self.tts_service.get_task_message_queue()

        while self.is_running:
            try:
                # Get a task message from queue with timeout
                task_message = task_message_queue.get(timeout=1)
                self._update_task_from_message(task_message)
                task_message_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error monitoring task queue: {e}")

    def _update_task_from_message(self, message: Dict[str, Any]):
        """Update task status based on task queue message"""
        task_id = message.get("request_id")
        status = message.get("status")
        output_file_path = message.get("output_file_path")
        metadata = message.get("metadata", {})

        if not task_id:
            return

        logger.info(f"TTS engine manager updating task {task_id} status to {status}")

        with self.db_manager.get_session() as session:
            task = session.query(Task).filter(Task.task_id == task_id).first()

            if not task:
                logger.warning(f"TTS task {task_id} not found in database")
                return

            # Update basic fields
            task.status = status
            task.output_file_path = output_file_path
            task.task_metadata = json.dumps(metadata) if metadata else None

            # Update status-specific fields
            if status == TaskStatus.PROCESSING:
                if metadata.get("started_at"):
                    task.started_at = datetime.fromisoformat(metadata["started_at"])
                else:
                    task.started_at = datetime.now()
                task.device = metadata.get("device")

            elif status == TaskStatus.COMPLETED:
                if metadata.get("completed_at"):
                    task.completed_at = datetime.fromisoformat(metadata["completed_at"])
                else:
                    task.completed_at = datetime.now()
                task.file_size = metadata.get("file_size")
                task.sampling_rate = metadata.get("sampling_rate")
                task.device = metadata.get("device")

            elif status == TaskStatus.FAILED:
                if metadata.get("failed_at"):
                    task.failed_at = datetime.fromisoformat(metadata["failed_at"])
                else:
                    task.failed_at = datetime.now()
                task.error_message = metadata.get("error")
                task.device = metadata.get("device")

            session.commit()

            # Handle item updates if task is linked to an item
            self._update_item_from_task_status(
                task, status, output_file_path, metadata, session
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get task statistics"""
        with self.db_manager.get_session() as session:
            # Get status counts
            status_counts = {}
            status_results = (
                session.query(Task.status, func.count(Task.id))
                .group_by(Task.status)
                .all()
            )
            for status, count in status_results:
                status_counts[status] = count

            # Get total tasks
            total_tasks = session.query(func.count(Task.id)).scalar()

            # Get average file size for completed tasks
            avg_file_size = (
                session.query(func.avg(Task.file_size))
                .filter(
                    and_(
                        Task.status == TaskStatus.COMPLETED, Task.file_size.isnot(None)
                    )
                )
                .scalar()
            )

            # Get duplicate text hashes
            duplicate_results = (
                session.query(Task.text_hash, func.count(Task.id).label("count"))
                .group_by(Task.text_hash)
                .having(func.count(Task.id) > 1)
                .all()
            )

            return {
                "total_tasks": total_tasks or 0,
                "status_counts": status_counts,
                "average_file_size": float(avg_file_size) if avg_file_size else 0.0,
                "duplicate_texts": len(duplicate_results),
                "duplicate_details": [
                    (hash_val, count) for hash_val, count in duplicate_results
                ],
            }

    def cleanup_failed_tasks(self, days: int = 7) -> int:
        """Remove failed tasks older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)

        with self.db_manager.get_session() as session:
            deleted_count = (
                session.query(Task)
                .filter(
                    and_(Task.status == TaskStatus.FAILED, Task.failed_at < cutoff_date)
                )
                .delete()
            )
            session.commit()

        logger.info(f"TTS engine manager cleaned up {deleted_count} old failed tasks")
        return deleted_count

    # Item-related functionality removed for TTS-only service

    # All Item-related methods removed for TTS-only service

    def get_tts_worker_health(self) -> Dict[str, Any]:
        """Check TTS worker health."""
        is_running = self.is_running

        # Get queue status if available
        queue_size = 0
        try:
            if self.tts_service and hasattr(self.tts_service, "get_task_message_queue"):
                task_message_queue = self.tts_service.get_task_message_queue()
                queue_size = (
                    task_message_queue.qsize()
                    if hasattr(task_message_queue, "qsize")
                    else 0
                )
        except Exception:
            pass

        return {
            "worker_running": is_running,
            "queue_size": queue_size,
            "tts_service_available": self.tts_service is not None,
        }

    def submit_multiple_tasks(
        self, texts: list[str], language: str = "fi"
    ) -> list[str]:
        """Submit multiple tasks for processing."""
        task_ids = []
        for text in texts:
            task_id = self.submit_task(text, language=language)
            if task_id:
                task_ids.append(task_id)
        return task_ids

    @property
    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self.tts_service is not None

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages for TTS."""
        return settings.tts_supported_languages.copy()
