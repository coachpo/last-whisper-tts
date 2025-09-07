# Last Whisper - TTS Service

A FastAPI service for Text-to-Speech conversion with multiple providers (Local, Azure, Google Cloud).

## Features

- **Multiple TTS Providers**: Local (Facebook MMS-TTS-Fin), Azure Speech, Google Cloud Text-to-Speech
- **FastAPI Framework**: Modern web framework with automatic OpenAPI documentation
- **Task Management**: Queue-based processing with status tracking
- **Provider Switching**: Easy configuration-based provider selection

## Project Structure

```
last-whisper-tts/
├── app/
│   ├── api/routes/          # API endpoints
│   ├── core/                # Configuration and utilities
│   ├── models/              # Database models and schemas
│   ├── services/            # Business logic
│   ├── tts_engine/          # TTS provider implementations
│   └── main.py              # FastAPI application
├── run_api.py              # Server startup script
└── pyproject.toml          # Dependencies and project config
```

## TTS Providers

- **Local**: Facebook MMS-TTS-Fin model (Finnish, GPU/CPU)
- **Azure**: Microsoft Cognitive Services Speech (Finnish neural voices)
- **Google Cloud**: Text-to-Speech API (WaveNet voices)

## API Endpoints

- `POST /api/v1/tts/convert` - Submit text for TTS conversion
- `GET /api/v1/tts/{conversion_id}` - Get conversion status
- `GET /api/v1/tts` - List conversions
- `POST /api/v1/tts/convert-multiple` - Batch TTS conversion
- `GET /api/v1/tts/{conversion_id}/download` - Download audio file
- `GET /api/v1/tts/supported-languages` - Get supported languages
- `GET /health` - Health check

## Installation

```bash
git clone https://github.com/coachpo/last-whisper-tts
cd last-whisper-tts
pip install -e .
```

## Running

```bash
python run_api.py
```

API available at `http://localhost:8000` with docs at `http://localhost:8000/docs`.

## Configuration

Key environment variables:

```bash
# TTS Provider
TTS_PROVIDER="gcp"  # "local", "azure", "gcp"

# Azure (when TTS_PROVIDER="azure")
AZURE_SPEECH_KEY="your_key"
AZURE_SPEECH_REGION="your_region"

# Google Cloud (when TTS_PROVIDER="gcp")
GOOGLE_APPLICATION_CREDENTIALS="keys/google-credentials.json"

# Local (when TTS_PROVIDER="local")
TTS_DEVICE="cpu"  # "cuda" for GPU
```

## Development

```bash
# Install with dev tools
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Lint code
ruff check .
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
