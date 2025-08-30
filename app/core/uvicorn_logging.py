"""Custom Uvicorn logging configuration for consistent log formatting."""

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S,%f"[:-3],
        },
        "access": {
            "format": "%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S,%f"[:-3],
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        "uvicorn.asgi": {"handlers": ["default"], "level": "INFO", "propagate": False},
    },
    "root": {
        "handlers": ["default"],
        "level": "INFO",
    },
}
