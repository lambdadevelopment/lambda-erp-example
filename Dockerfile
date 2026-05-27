# syntax=docker/dockerfile:1.6
#
# Example customer deployment — a single container that:
#   Stage 1: builds the customer frontend (the @lambda-development/erp-core npm
#            package + this repo's overrides) into static files.
#   Stage 2: installs the backend (the lambda-erp PyPI package + the acme
#            plugin) and serves both the API and the built frontend at one origin
#            via ../app.py.
#
# Both halves consume the PUBLISHED packages — nothing is vendored from the core
# repo. Bump the versions in pyproject.toml / frontend/package.json to upgrade.

# ---------------------------------------------------------------------------
# Stage 1 — frontend build (pulls @lambda-development/erp-core from npm)
# ---------------------------------------------------------------------------
FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build
# -> /build/frontend/dist

# ---------------------------------------------------------------------------
# Stage 2 — Python runtime (pulls lambda-erp from PyPI)
# ---------------------------------------------------------------------------
FROM python:3.12-slim
WORKDIR /app

# weasyprint (a lambda-erp dep) needs the Pango/Cairo stack; curl powers the
# healthcheck. Mirrors the core image's system deps.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz0b \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install the backend: this repo's `acme` package + its lambda-erp==X.Y.Z dep.
COPY pyproject.toml ./
COPY acme ./acme
RUN pip install --no-cache-dir .

# ASGI entry + the built frontend it serves.
COPY app.py ./
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

RUN mkdir -p /data \
    && groupadd -r app && useradd -r -g app -d /app app \
    && chown -R app:app /data /app
USER app

ENV LAMBDA_ERP_PLUGINS=acme \
    LAMBDA_ERP_DB=/data/acme.db \
    LAMBDA_ERP_AUTO_DEMO=1 \
    PORT=8000 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/api/health" || exit 1

# --workers 1 is a hard constraint inherited from the core: SQLite + in-memory
# chat session state can't be shared across worker processes.
CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT} --workers 1"]
