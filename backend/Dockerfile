FROM python:3.12-slim

WORKDIR /app

# System deps needed to build a couple of Python packages' native
# extensions (argon2-cffi's C bindings in particular).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Reads $PORT at container start (Render, and most PaaS hosts, inject
# this and expect the app to bind to it - defaults to 8000 so the
# existing docker-compose.yml/docker-compose.prod.yml setups, which
# don't set PORT, keep working unchanged.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8000') + '/api/v1/health')" || exit 1

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
