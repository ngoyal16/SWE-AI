FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
# git: for cloning repos
# curl: for debugging/healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

# Setup workspace directory
RUN mkdir -p workspace

# Set environment variables
ENV PYTHONPATH=/app
ENV WORKSPACE_DIR=/app/workspace

# Expose port
EXPOSE 8000

# Default command (overridden by k8s for worker vs api)
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
