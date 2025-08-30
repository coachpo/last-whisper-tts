"""Application configuration settings."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    app_name: str = "Last Whisper"
    app_version: str = "1.0.0"
    app_description: str = (
        "Last Whisper's backend service - Dictation training with local TTS, scoring, and session-less workflow"
    )

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    log_level: str = "info"

    # Database Settings
    database_url: str = "sqlite:///data/dictation.db"
    db_path: str = "data/dictation.db"

    # Audio Storage Settings
    audio_dir: str = "audio"
    base_url: str = "http://localhost:8000"  # For building audio URLs

    # TTS Service Settings
    tts_device: Optional[str] = None  # None for auto-detection
    tts_thread_count: int = 1
    tts_supported_languages: list[str] = ["fi"]  # Supported languages for TTS
    tts_provider: str = "gcp"  # or "azure" or "gcp" TTS provider: 'local', 'azure', or 'gcp'/'google'

    # Google Cloud Settings
    google_application_credentials: Optional[str] = "keys/google-credentials.json"  # Dev: file path, Prod: set via GOOGLE_APPLICATION_CREDENTIALS env var

    # Azure Settings (optional)
    azure_speech_key: Optional[str] = None
    azure_speech_region: Optional[str] = None

    # API Settings
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    # Production Settings
    environment: str = "development"  # "development" or "production"
    disable_docs: bool = False  # Set to True to disable docs in production

    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"  # Comma-separated list of allowed origins
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"  # Comma-separated list or "*" for all methods
    cors_allow_headers: str = "*"  # Comma-separated list or "*" for all headers
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


# Global settings instance
settings = Settings()