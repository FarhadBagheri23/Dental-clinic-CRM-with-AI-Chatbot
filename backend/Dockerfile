# ---------------------------------------------------------------- builder
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY pyproject.toml ./
# Dependencies only — the source is copied into the runtime stage, so editing
# a .py file does not invalidate this layer.
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir .

# ---------------------------------------------------------------- runtime
FROM python:3.12-slim AS runtime

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN useradd --create-home --uid 10001 api

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=api:api app ./app

USER api
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
