# Multi-stage Dockerfile for KDM SDK testing
# Supports Python 3.10, 3.11, 3.12

ARG PYTHON_VERSION=3.10

# Base stage - common dependencies
FROM python:${PYTHON_VERSION}-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for layer caching)
COPY requirements.txt requirements-dev.txt ./
COPY setup.py pyproject.toml MANIFEST.in ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY pytest.ini ./

# Install package in editable mode
RUN pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default command: run unit tests (fast)
CMD ["pytest", "-v", "-m", "not integration and not slow"]

# Development stage with additional tools
FROM base as dev

# Install additional development tools
RUN pip install --no-cache-dir \
    ipython \
    jupyter

# Copy examples and docs
COPY examples/ ./examples/
COPY docs/ ./docs/

WORKDIR /app

# Start bash for interactive development
CMD ["/bin/bash"]
