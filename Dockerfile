# ========================================================
# IP-SAKTI Sahayak: Production Multi-Stage Containerfile
# Hardened, non-root execution for FastAPI Backend
# ========================================================

FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Final runtime image
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH" \
    PYTHONPATH="/app"

# Install curl for container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user creation (Principle of Least Privilege)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy installed python dependencies from builder stage
COPY --from=builder /root/.local /home/appuser/.local
RUN chown -R appuser:appgroup /home/appuser/.local

# Copy application source and manifests
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup ingestion/ ./ingestion/
COPY --chown=appuser:appgroup corpus/ ./corpus/
COPY --chown=appuser:appgroup scripts/ ./scripts/

# Create persistent storage directories with proper permissions
RUN mkdir -p /app/chroma_db /app/scratch && \
    chown -R appuser:appgroup /app/chroma_db /app/scratch

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8000", "src.main:app"]
