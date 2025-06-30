# MLX LLM Server Dockerfile
# Note: This is experimental - MLX requires Apple Silicon hardware
# This Dockerfile is primarily for development/testing purposes

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# Install dependencies
RUN uv sync --frozen

# Default runtime environment – overridable at `docker run -e ...`
ENV SERVER_PORT=9123 \
    ENABLE_AUTH=false \
    ENABLE_METRICS=true

# Create necessary directories
RUN mkdir -p logs models

# Copy configuration
COPY .env.example .env

# Expose ports
EXPOSE 9123 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9123/api/v1/health || exit 1

# Run the server
CMD ["uv", "run", "-m", "src.main"]