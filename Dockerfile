# syntax=docker/dockerfile:1.7
# ---------------------------------------------------------------------------
# FlightDeck Alpha — single-container build for Fly.io.
#
# Stage 1 builds the Vite SPA into /web/dist.
# Stage 2 installs Python deps and the Alpaca CLI binary.
# Stage 3 copies both into a slim runtime image. Uvicorn serves the FastAPI
# app and the SPA from the same origin so the deployed app is a single URL.
# ---------------------------------------------------------------------------

# ---- Stage 1: build the Vite SPA ------------------------------------------
FROM node:20-alpine AS web-build
WORKDIR /web

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

# ---- Stage 2: install Alpaca CLI binary -----------------------------------
FROM golang:1.23-alpine AS alpaca-cli-build
RUN apk add --no-cache git
RUN go install github.com/alpacahq/cli/cmd/alpaca@latest

# ---- Stage 3: Python runtime ----------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    STATIC_DIR=/app/static \
    DATABASE_URL=sqlite:////data/flightdeck_alpha.db

WORKDIR /app

# System deps for building Python wheels and for the Alpaca CLI runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies — copy only the requirements file first so this layer
# caches when the rest of the source has not changed.
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install -r backend/requirements.txt

# Application source.
COPY backend/ ./backend/

# Static SPA bundle from stage 1.
COPY --from=web-build /web/dist ./backend/static

# Alpaca CLI binary from stage 2.
COPY --from=alpaca-cli-build /go/bin/alpaca /usr/local/bin/alpaca
RUN chmod +x /usr/local/bin/alpaca && alpaca --version || true

# Persistent storage for the SQLite audit log. Fly will mount a volume here.
RUN mkdir -p /data && chown -R nobody:nogroup /data

USER nobody
WORKDIR /app/backend

EXPOSE 8000

# Healthcheck so Fly's proxy can verify the service before sending traffic.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
