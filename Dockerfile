# Multi-stage build for Last Whisper Backend
FROM python:3.12-slim AS base

# Set default environment variables
ENV ENVIRONMENT=production \
    TTS_PROVIDER=local \
    LOG_LEVEL=info \
    CORS_ORIGINS=http://localhost:8008 \
    HF_HOME=/app/.cache/huggingface

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn for production WSGI server
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY app/ ./app/
COPY run_api.py .

# Create necessary directories and set permissions
RUN mkdir -p audio keys data /app/.cache/huggingface && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /home/appuser && \
    # Clean up any existing lock files
    find /app/.cache/huggingface -name "*.lock" -delete 2>/dev/null || true

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Default command - use Gunicorn with Uvicorn workers for production
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
