# ArthSetu backend image. Build context is the repo root (needs backend/,
# migrations/ and alembic.ini together) — see docker-compose.yml.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    WEB_CONCURRENCY=2

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY migrations migrations
COPY alembic.ini alembic.ini
COPY backend/docker-entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && useradd --create-home --uid 1000 --shell /usr/sbin/nologin arthsetu \
    && chown -R arthsetu:arthsetu /app
USER arthsetu

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request as u,sys; sys.exit(0 if u.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3).status==200 else 1)"

ENTRYPOINT ["/entrypoint.sh"]
