# KuKu Promo Finder — full FastAPI app (Render / Railway / HF Spaces / Fly)
# Seed demo = full 50-ep hybrid OUTPUTS (no scripts). Visitors can create projects,
# upload their own episode .txt files, and run Generate.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEMO_PUBLIC=1 \
    DEMO_MAX_EPISODES=50 \
    DEMO_DEFAULT_MODE=hybrid \
    DEMO_LOCK_SEED=1 \
    PORT=7860

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Writable dirs for visitor uploads / generate jobs (scripts never baked into image)
RUN mkdir -p data/projects data/uploads data/processed output \
    && find data/projects -type d -name scripts -exec mkdir -p {} \; \
    && chmod -R a+rwX data output || true

RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

# HF Spaces default 7860; Render/Railway inject $PORT
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT:-7860}/api/health" || exit 1

CMD ["sh", "-c", "python -m uvicorn web.app:app --host 0.0.0.0 --port ${PORT:-7860}"]
