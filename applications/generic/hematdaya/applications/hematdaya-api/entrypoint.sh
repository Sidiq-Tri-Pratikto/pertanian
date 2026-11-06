#!/bin/sh
set -eu

if [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
    alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
