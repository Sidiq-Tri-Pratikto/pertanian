#!/usr/bin/env bash
# Compose readiness alone cannot prove external S3 writes are fenced.
set -euo pipefail
: "${BACKUP_COMPOSE_FILE:?Set BACKUP_COMPOSE_FILE}"
: "${BACKUP_COMPOSE_PROJECT:?Set BACKUP_COMPOSE_PROJECT}"
: "${BACKUP_COMPOSE_ENV_FILE:?Set BACKUP_COMPOSE_ENV_FILE}"
[[ "${BACKUP_S3_WRITERS_FENCED:-}" == yes ]] || exit 1
[[ "$BACKUP_COMPOSE_PROJECT" =~ ^[a-z0-9][a-z0-9_-]*$ ]] || exit 1
compose=(docker compose --project-name "$BACKUP_COMPOSE_PROJECT" --file "$BACKUP_COMPOSE_FILE" --env-file "$BACKUP_COMPOSE_ENV_FILE")
# Ensure the selected project has a live source before treating empty writer results as quiescence.
running="$("${compose[@]}" ps --services --status running)"
grep -Fxq postgres <<< "$running"
grep -Fxq object-store <<< "$running"
if grep -Exq 'api|worker|migrate' <<< "$running"; then
  exit 1
fi
