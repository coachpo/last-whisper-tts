"""Database session manager for SQLAlchemy 2.x."""

import os
from typing import Optional, TYPE_CHECKING

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

if TYPE_CHECKING:
    from .models import Task

Base = declarative_base()


class DatabaseManager:
    """Database session manager for SQLAlchemy 2.x."""

    def __init__(self, database_url: str = settings.database_url):
        # Configure database engine
        if database_url.startswith("sqlite"):
            # Add SQLite-specific options
            self.engine = create_engine(
                database_url,
                echo=False,
                connect_args={
                    "check_same_thread": False,
                },
            )

            # Configure basic SQLite pragmas
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                # Enable foreign keys
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        else:
            self.engine = create_engine(database_url, echo=False)

        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Ensure audio directory exists
        os.makedirs(settings.audio_dir, exist_ok=True)

        # Import models to ensure they're registered with Base

        # Create tables if they don't exist
        self._create_tables_if_not_exist()

    def _create_tables_if_not_exist(self):
        """Create tables only if they don't exist."""
        try:
            # Check if tables exist by trying to query the metadata
            with self.engine.connect() as conn:
                # Try to get table names
                result = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                existing_tables = [row[0] for row in result.fetchall()]

                # Only create tables if none exist
                if not existing_tables:
                    Base.metadata.create_all(bind=self.engine)
                else:
                    # Tables exist, just ensure they're up to date
                    Base.metadata.create_all(bind=self.engine)
        except Exception:
            # If there's any error, fall back to the standard create_all
            # which should be idempotent
            Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def get_task_by_id(self, task_id: str) -> Optional["Task"]:
        """Get a task by its ID."""
        from .models import Task

        with self.get_session() as session:
            return session.query(Task).filter(Task.task_id == task_id).first()

    def get_all_tasks(
        self, status: Optional[str] = None, limit: int = 100
    ) -> list["Task"]:
        """Get all tasks, optionally filtered by status."""
        from .models import Task

        with self.get_session() as session:
            query = session.query(Task)
            if status:
                query = query.filter(Task.status == status)
            return query.order_by(Task.created_at.desc()).limit(limit).all()

    def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT 1"))
                result.fetchone()
                return True
        except Exception:
            return False

    def check_audio_directory(self) -> bool:
        """Check if audio directory is writable."""
        try:
            test_file = os.path.join(settings.audio_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            return True
        except Exception:
            return False

    def close(self):
        """Dispose of the database engine."""
        self.engine.dispose()
