# PAEOS-FX backend image (development-oriented; production hardening is Phase 12).
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for psycopg (libpq) and build tooling.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY paeos_fx ./paeos_fx
COPY migrations ./migrations
COPY alembic.ini ./

RUN pip install --upgrade pip && pip install ".[jobs]"

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "paeos_fx.main:app", "--host", "0.0.0.0", "--port", "8000"]
