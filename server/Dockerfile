# ============================================================
# COSMOS INTELLIGENCE — Docker Container Image
# For AWS Lambda (container image) or ECS Fargate deployment
#
# Build:  docker build -t cosmos-intelligence-server .
# Local:  docker run -p 8000:8000 -e ANTHROPIC_API_KEY=sk-... cosmos-intelligence-server
# ============================================================

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create data directories
RUN mkdir -p data/raw data/processed data/synthetic outputs

# Environment defaults (override via docker run -e or ECS task definition)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run FastAPI with uvicorn
# For Lambda: override CMD with the Lambda handler
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
