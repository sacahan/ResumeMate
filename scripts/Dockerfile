# ResumeMate Backend + Admin Docker Image
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (git and ssh for auto-commit feature)
RUN apt-get update && apt-get install -y \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py ./
COPY src/backend ./src/backend
COPY src/frontend ./src/frontend

# Create directories
RUN mkdir -p /app/logs /app/chroma_db /root/.ssh

# Configure Git to trust /app directory (for Git operations inside container)
RUN git config --global --add safe.directory /app

# Environment variables
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860
ENV INFOGRAPHICS_ADMIN_HOST=0.0.0.0
ENV INFOGRAPHICS_ADMIN_PORT=7870

# Expose both ports (main app and admin)
EXPOSE 7860 7870

# Start both services using shell script
CMD ["/bin/bash", "-c", "python -m src.backend.infographics.admin_app & sleep 2 && python app.py"]
