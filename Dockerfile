# Multi-stage build for Last Whisper TTS Service
FROM python:3.12-slim AS base

# Set default environment variables
ENV ENVIRONMENT=production \
    TTS_PROVIDER=gcp \
    LOG_LEVEL=info \
    CORS_ORIGINS=http://localhost:3000 \
    HF_HOME=/app/.cache/huggingface \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY run_api.py .

# Create necessary directories and set permissions
RUN mkdir -p audio keys data /app/.cache/huggingface && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /home/appuser && \
    find /app/.cache/huggingface -name "*.lock" -delete 2>/dev/null || true

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - use Gunicorn with Uvicorn workers for production
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
