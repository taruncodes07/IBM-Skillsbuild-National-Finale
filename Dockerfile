# syntax=docker/dockerfile:1
FROM node:24-bookworm-slim AS frontend
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY tsconfig.json vite.config.ts index.html ./
COPY frontend/ ./frontend/
COPY public/ ./public/
RUN npm run build

FROM python:3.11-slim-bookworm AS dependencies
WORKDIR /build
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.lock.txt

FROM python:3.11-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GRIDTRACE_DATA=/var/lib/gridtrace \
    LANGSMITH_TRACING=false
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 gridtrace \
    && useradd --uid 10001 --gid gridtrace --create-home --shell /usr/sbin/nologin gridtrace \
    && mkdir -p /var/lib/gridtrace \
    && chown gridtrace:gridtrace /var/lib/gridtrace
WORKDIR /app
COPY --from=dependencies /install/ /usr/local/
COPY backend/ ./backend/
# These three scorer sources are required for the saved evaluation fingerprint.
COPY tests/benchmark_independent.py tests/planner_pilot.py tests/adaptive_evaluation.py ./tests/
COPY docs/ ./docs/
COPY --from=frontend /build/dist/ ./dist/
USER gridtrace
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["sh", "-c", "python -c \"import os, urllib.request; p = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{p}/api/health', timeout=4).read()\""]
# One process owns the SQLite connection, clock and in-process investigation jobs.
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-graceful-shutdown 10"]

