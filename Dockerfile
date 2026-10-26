# Multi-stage / lightweight production-ready Dockerfile for Course Registration Web App
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    PORT=5000 \
    FLASK_ENV=production

# Set working directory inside container
WORKDIR /app

# Install system dependencies (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and assets
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/

# Create data directory for SQLite persistent storage and assign proper permissions
RUN mkdir -p /app/data

# Declare mount point for persistent SQLite database volume
VOLUME ["/app/data"]

# Expose web application port
EXPOSE 5000

# Built-in Docker Healthcheck against the /health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Launch production WSGI server (Gunicorn) with 2 workers and 2 threads
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
