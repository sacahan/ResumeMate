# ResumeMate Main Application (Gradio AI Q&A)
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests
COPY requirements.txt requirements.txt
COPY scripts/requirements-docker.txt scripts/requirements-docker.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r scripts/requirements-docker.txt

# Copy application code
COPY app.py ./
COPY src/backend ./src/backend
COPY src/frontend ./src/frontend

# Create directories
RUN mkdir -p /app/logs

# Runtime defaults (sensitive values like DIFY_API_KEY must be passed via --env-file or -e at runtime)
ENV DIFY_API_BASE=https://dify.brianhan.cc/v1 \
    DIFY_API_KEY=app-Sx2N9bTx67vNXmYvibmVoVHf \
    DIFY_USER=resumemate-interviewer \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860 \
    GRADIO_SHARE=false \
    LOG_CONSOLE_LEVEL=INFO \
    LOG_FILE_LEVEL=DEBUG \
    LOG_FILE=/app/logs/resumemate.log \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Expose port
EXPOSE 7860

# Start application
CMD ["python", "app.py"]
