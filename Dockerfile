FROM public.ecr.aws/docker/library/python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies using uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application directories
COPY agent/ agent/

# Setup workspace directory
RUN mkdir -p workspace

# Set environment variables
ENV PYTHONPATH=/app
ENV WORKSPACE_DIR=/app/workspace

# Default command for worker
CMD ["python", "-m", "agent.worker"]
