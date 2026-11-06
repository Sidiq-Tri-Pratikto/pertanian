#!/bin/sh
set -eu

case "${1:-}" in
    '')
        # Preserve the existing local invocation. Staging always specifies its role.
        if [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
            alembic upgrade head
        fi
        ;;
    api) ;;
    worker) exec python -m app.worker ;;
    migrate) exec alembic upgrade head ;;
    *) printf '%s\n' 'Expected api, worker or migrate.' >&2; exit 2 ;;
esac

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
