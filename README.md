# Last Whisper - TTS Service

A production-grade FastAPI service for Text-to-Speech conversion with multiple TTS providers (Local, Azure, Google
Cloud). Features clean architecture, robust task management, and high-quality audio generation.

## Features

- **Multiple TTS Providers**: Support for Local (Facebook MMS-TTS-Fin), Azure Speech, and Google Cloud Text-to-Speech
- **Clean Architecture**: Organized with proper separation of concerns and modular design
- **FastAPI Framework**: Modern, fast web framework with automatic OpenAPI documentation
- **SQLAlchemy 2.x**: Modern ORM with type hints and async support
- **Comprehensive Testing**: Full test suite with pytest and mocking
- **Service Layer**: Clean abstraction over TTS infrastructure with task management
- **Configuration Management**: Centralized settings with environment variable support
- **Error Handling**: Custom exceptions and proper HTTP status codes
- **Task Queue Management**: Robust task processing with status tracking
- **Multi-device Support**: Automatic GPU/CPU detection with manual override options (Local TTS)
- **Provider Flexibility**: Easy switching between TTS providers via configuration

## Project Structure

```
last-whisper-tts/
├── app/
│   ├── api/
│   │   ├── routes/          # API route definitions
│   │   │   ├── health.py    # Health check endpoints
│   │   │   └── tts.py       # TTS conversion endpoints
│   │   └── dependencies.py  # FastAPI dependencies
│   ├── core/
│   │   ├── config.py        # Application configuration
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── logging.py       # Logging configuration
│   │   └── uvicorn_logging.py # Uvicorn logging setup
│   ├── models/
│   │   ├── schemas.py       # Pydantic models and schemas
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── database_manager.py # Database management
│   │   └── enums.py         # Enumeration definitions
│   ├── services/
│   │   └── task_service.py      # Task management service
│   ├── tts_engine/
│   │   ├── tts_engine_local.py     # Local TTS engine (Facebook MMS-TTS-Fin)
│   │   ├── tts_engine_azure.py     # Azure Speech TTS engine
│   │   ├── tts_engine_gcp.py       # Google Cloud TTS engine
│   │   ├── tts_engine_manager.py   # Task orchestration and monitoring
│   │   └── tts_engine_wrapper.py   # TTS service wrapper and provider selection
│   └── main.py              # FastAPI application entry point
├── Dockerfile               # Container configuration
├── keys/                    # API keys and credentials
│   └── google-credentials.json # Google Cloud service account keys
├── audio/                   # Generated audio files
├── data/                    # Database storage
├── requirements.txt         # Python dependencies
├── run_api.py              # Server startup script
└── README.md               # This file
```

## TTS Capabilities

This API provides high-quality text-to-speech conversion with multiple provider options:

### Local TTS Engine

- **Model**: Facebook's MMS-TTS-Fin (Multilingual TTS model)
- **Output Format**: WAV audio files (24kHz, 16-bit)
- **Language Support**: Finnish and multilingual capabilities
- **Device Optimization**: Automatic GPU/CPU detection with manual override
- **Performance**: Fast local inference with no external dependencies

### Azure Speech TTS

- **Provider**: Microsoft Azure Cognitive Services Speech
- **Voice Options**: Multiple Finnish neural voices
- **Output Format**: WAV audio files (24kHz, 16-bit mono)
- **Features**: SSML support, prosody controls, high-quality neural voices
- **Scalability**: Cloud-based processing with high availability

### Google Cloud Text-to-Speech

- **Provider**: Google Cloud Platform Text-to-Speech API
- **Voice Options**: WaveNet voices (fi-FI-Wavenet-B)
- **Output Format**: WAV audio files (24kHz, 16-bit mono)
- **Features**: Advanced neural voice synthesis, SSML support
- **Quality**: Premium WaveNet voices for natural speech

### Common Features

- **Batch Processing**: Queue-based request handling for scalability
- **Task Management**: Comprehensive task lifecycle tracking and deduplication
- **Provider Switching**: Easy configuration-based provider selection
- **Error Handling**: Robust error handling and retry mechanisms

## TTS Features

The service provides a complete text-to-speech workflow:

- **Text Processing**: Submit text for high-quality speech synthesis
- **Task Management**: Track conversion status and download generated audio files
- **Multiple TTS Providers**: Support for Local, Azure, and Google Cloud TTS
- **Session-less**: No authentication or user sessions required

## API Endpoints

### TTS Endpoints

#### POST /api/v1/tts/convert

Submit text for TTS conversion.

**Request:**

```json
{
  "text": "Hello world",
  "custom_filename": "optional_filename"
}
```

**Response:**

```json
{
  "conversion_id": "20231201_120000_abc123",
  "text": "Hello world",
  "status": "queued",
  "submitted_at": "2023-12-01T12:00:00"
}
```

#### GET /api/v1/tts/{id}

Get conversion status and metadata.

#### GET /api/v1/tts

List conversions with optional status filtering.

#### POST /api/v1/tts/convert-multiple

Submit multiple texts for batch TTS conversion.

### Additional TTS Endpoints

#### GET /api/v1/tts/supported-languages

Get list of supported languages for TTS conversion.

### Health Endpoints

#### GET /health

Comprehensive health check with detailed service status.

## Installation

1. Clone the repository and navigate to the project directory:

```bash
git clone <repository-url>
cd last-whisper-tts
```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Initialize database (optional):

```bash
# The database will be created automatically on first run
```

## Running the Application

### Development Server

```bash
python run_api.py
```

### Production Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## Configuration

Configuration is managed through environment variables or `.env` file:

```bash
# API Settings
APP_NAME="Last Whisper"
APP_VERSION="1.0.0"
HOST="0.0.0.0"
PORT=8000
RELOAD=true
LOG_LEVEL="info"

# Database
DATABASE_URL="sqlite:///dictation.db"

# TTS Provider Selection
TTS_PROVIDER="local"  # Options: "local", "azure", "gcp"

# Local TTS Settings (when TTS_PROVIDER="local")
TTS_DEVICE="cpu"  # or "cuda" for GPU, None for auto-detection
TTS_THREAD_COUNT=1
TTS_SUPPORTED_LANGUAGES=["fi"]

# Azure TTS Settings (when TTS_PROVIDER="azure")
AZURE_SPEECH_KEY="your_azure_key"
AZURE_SERVICE_REGION="your_azure_region"
AZURE_LANGUAGE_CODE="fi-FI"
AZURE_SAMPLE_RATE_HZ=24000

# Google Cloud TTS Settings (when TTS_PROVIDER="gcp")
# Set GOOGLE_APPLICATION_CREDENTIALS environment variable
GCP_VOICE_NAME="fi-FI-Wavenet-B"
GCP_LANGUAGE_CODE="fi-FI"
GCP_SAMPLE_RATE_HZ=24000

# Audio Storage
AUDIO_DIR="audio"
BASE_URL="http://localhost:8000"

# API Documentation
DOCS_URL="/docs"
REDOC_URL="/redoc"
OPENAPI_URL="/openapi.json"
```

## Testing

Run the full test suite:

```bash
pytest
```

Run specific test modules:

```bash
pytest tests/test_api/ -v
pytest tests/test_services/ -v
```

## Code Quality

Format code:

```bash
black .
```

Lint code:

```bash
ruff check .
```

## Architecture

The application follows clean architecture principles:

- **API Layer**: FastAPI routes with request/response models
- **Service Layer**: Business logic and external service integration
- **Data Layer**: Database operations and models
- **Core**: Configuration, exceptions, and utilities

### Key Components

- **TTSEngine**: Core TTS engine with Hugging Face model integration
- **TTSEngineManager**: Task orchestration and monitoring
- **TTSEngineWrapper**: Service lifecycle management
- **TaskService**: TTS task database operations

This design provides:

- **Testability**: Easy to mock and test individual components
- **Maintainability**: Clear separation of concerns
- **Scalability**: Modular design allows easy extension
- **Reliability**: Comprehensive error handling and logging
- **Performance**: GPU acceleration support and efficient queue processing

## Dependencies

### Core Framework

- **FastAPI**: Modern web framework for building APIs
- **SQLAlchemy**: Database ORM and management
- **Pydantic**: Data validation and settings management
- **Uvicorn**: ASGI server for production deployment

### TTS Engines

- **Transformers**: Hugging Face transformers for local TTS models
- **PyTorch**: Deep learning framework for local model inference
- **Azure Cognitive Services Speech**: Azure TTS integration
- **Google Cloud Text-to-Speech**: GCP TTS integration

### TTS Features

- **transformers**: Hugging Face transformers for local TTS models
- **torch**: Deep learning framework for local model inference

### Development Tools

- **pytest**: Testing framework
- **black**: Code formatting
- **ruff**: Code linting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions, please open an issue in the repository.
