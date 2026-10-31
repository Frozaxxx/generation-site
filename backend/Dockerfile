# syntax=docker/dockerfile:1

# ────────────────────────────────────────────────
# Стадия 1 — сборка зависимостей (builder)
# ────────────────────────────────────────────────
FROM python:3.14-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Сначала только lock-файлы: слой с зависимостями кешируется между сборками
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    pip install --no-cache-dir uv && \
    uv sync --frozen --no-install-project --no-dev

# ────────────────────────────────────────────────
# Стадия 2 — финальный образ (runtime)
# ────────────────────────────────────────────────
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    APP_HOST=0.0.0.0 \
    STORAGE_DATA_DIR=/app/data

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY . .

# База, фото команды и собранные сайты живут в volume
VOLUME ["/app/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["python", "main.py"]
