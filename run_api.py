#!/usr/bin/env python3
"""Script to run the Last Whisper backend API server."""
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.uvicorn_logging import LOGGING_CONFIG


def main():
    """Run the API server."""
    # Setup logging before starting the server
    setup_logging()

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level,
        access_log=True,  # Enable access logs with custom formatting
        log_config=LOGGING_CONFIG,  # Use our custom logging config
    )


if __name__ == "__main__":
    main()
