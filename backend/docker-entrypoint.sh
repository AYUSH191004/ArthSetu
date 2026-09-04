#!/bin/sh
# Applies pending migrations, then starts the API. Separated from the
# Dockerfile CMD so it's easy to override (e.g. run only `alembic upgrade
# head` as a one-off job ahead of a multi-replica rollout).
set -e

alembic upgrade head
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers "${WEB_CONCURRENCY:-2}"
