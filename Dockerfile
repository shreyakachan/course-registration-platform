# Production-grade lightweight Dockerfile for Course Registration Platform
FROM python:3.11-slim

# Prevent bytecode caching and enable real-time unbuffered log streaming
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    PORT=5000 \
    FLASK_CONFIG=production

WORKDIR /app

# Install system dependencies (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications first to leverage Docker layer caching
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create non-root system user and prepare persistent storage directory
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Copy application source code and assets with appropriate ownership
COPY --chown=appuser:appuser app.py config.py extensions.py ./
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=appuser:appuser forms/ ./forms/
COPY --chown=appuser:appuser routes/ ./routes/
COPY --chown=appuser:appuser services/ ./services/
COPY --chown=appuser:appuser utils/ ./utils/
COPY --chown=appuser:appuser templates/ ./templates/
COPY --chown=appuser:appuser static/ ./static/

# Declare mount point for persistent SQLite database volume
VOLUME ["/app/data"]

# Switch to unprivileged non-root user
USER appuser

# Expose web application port
EXPOSE 5000

# Built-in Docker Healthcheck against the /health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=8s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Launch production WSGI server (Gunicorn) with 2 workers and 2 threads
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
