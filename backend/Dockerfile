FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app
COPY scripts ./scripts
COPY artifacts ./artifacts

RUN pip install .

RUN mkdir -p /app/var

ENV DB_PATH=/app/var/buildingpulse.db

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=10 --start-period=20s \
  CMD curl -fsS http://127.0.0.1:8000/openapi.json >/dev/null || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
