#!/bin/sh
# Applies pending migrations, then starts the API. Separated from the
# Dockerfile CMD so it's easy to override (e.g. run only `alembic upgrade
# head` as a one-off job ahead of a multi-replica rollout).
set -e

alembic upgrade head
# $PORT is set by platforms like Render that assign it dynamically; falls
# back to 8000 for docker-compose / a plain `docker run`.
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers "${WEB_CONCURRENCY:-2}"
