#!/usr/bin/env bash
# Sourced by drill.sh. This override exists only in the private synthetic workspace.
compose_file="$root/deployment/temuriset/compose.staging.yml"
project="temuriset-backup-drill-$id"
compose_fixture() {
  docker compose --env-file /dev/null --project-name "$project" --file "$compose_file" --file "$scratch/compose.yml" "$@"
}

start_compose_fixture() {
  export TEMURISET_API_IMAGE="${TEMURISET_API_IMAGE:-temuriset-m11-api:local}"
  export TEMURISET_WEB_IMAGE="${TEMURISET_WEB_IMAGE:-temuriset-m11-web:local}"
  api_image_id="$(docker image inspect --format '{{.Id}}' "$TEMURISET_API_IMAGE")"
  web_image_id="$(docker image inspect --format '{{.Id}}' "$TEMURISET_WEB_IMAGE")"
  export RELEASE_SHA="$(git -C "$root" rev-parse HEAD)"
  export EDGE_BIND_ADDRESS=127.0.0.1
  export EDGE_PORT="$("$python" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')"
  export WEB_ORIGIN="https://localhost:$EDGE_PORT"
  export API_URL=http://api:8000
  export POSTGRES_PASSWORD="$(openssl rand -hex 24)"
  export DATABASE_URL="postgresql+asyncpg://temuriset:$POSTGRES_PASSWORD@postgres:5432/temuriset"
  export ENVIRONMENT=development MAILBOX_ADAPTER=development COMPOSITION=generic-base CLAMAV_NO_FRESHCLAMD=true
  export TLS_CERT_FILE="$scratch/tls.crt" TLS_KEY_FILE="$scratch/tls.key" S3_CONFIG_FILE="$scratch/identity.json"
  export S3_BUCKET="$BACKUP_SOURCE_S3_BUCKET" S3_ACCESS_KEY="runtime-$id" S3_SECRET_KEY="$(openssl rand -hex 24)"
  openssl req -x509 -newkey rsa:2048 -nodes -keyout "$TLS_KEY_FILE" -out "$TLS_CERT_FILE" \
    -days 1 -subj /CN=localhost -addext subjectAltName=DNS:localhost >/dev/null 2>&1
  "$python" - <<'PY'
import json
import os
from pathlib import Path

buckets = [os.environ["BACKUP_SOURCE_S3_BUCKET"], os.environ["BACKUP_RESTORE_S3_BUCKET"]]
Path(os.environ["S3_CONFIG_FILE"]).write_text(json.dumps({"identities": [
    {"name": "synthetic-drill", "credentials": [{
        "accessKey": os.environ["AWS_ACCESS_KEY_ID"], "secretKey": os.environ["AWS_SECRET_ACCESS_KEY"],
    }], "actions": ["Admin"]},
    {"name": "synthetic-runtime", "credentials": [{
        "accessKey": os.environ["S3_ACCESS_KEY"], "secretKey": os.environ["S3_SECRET_KEY"],
    }], "actions": [f"{action}:{bucket}" for bucket in buckets for action in ("Read", "Write", "List")]},
]}))
PY
  # The store reads as UID/GID 1000 inside Docker. The host scratch directory stays private.
  chmod 0444 "$S3_CONFIG_FILE"
  cat > "$scratch/compose.yml" <<'YAML'
services:
  postgres:
    networks: [backend, drill-access]
    ports:
      - {host_ip: 127.0.0.1, target: 5432}
  object-store:
    networks: [backend, drill-access]
    ports:
      - {host_ip: 127.0.0.1, target: 8333}
networks:
  drill-access:
YAML
  compose_started=1
  compose_fixture up --detach --wait --wait-timeout 240 >&2
  verify_compose_images
  printf 'Compose API image %s, web image %s.\n' "$api_image_id" "$web_image_id"
  local pg_address
  pg_address="$(compose_fixture port postgres 5432)"
  s3_address="$(compose_fixture port object-store 8333)"
  [[ "$pg_address" == 127.0.0.1:* ]]
  pg_port="${pg_address##*:}"
  pg_role=temuriset
  source_db=temuriset
  export PGPASSWORD="$POSTGRES_PASSWORD"
  export BACKUP_SOURCE_DATABASE_URL="postgresql://$pg_role:$POSTGRES_PASSWORD@127.0.0.1:$pg_port/$source_db"
  export BACKUP_RESTORE_DATABASE_URL="postgresql://$pg_role:$POSTGRES_PASSWORD@127.0.0.1:$pg_port/$target_db"
  export BACKUP_COMPOSE_FILE="$compose_file" BACKUP_COMPOSE_PROJECT="$project" BACKUP_COMPOSE_ENV_FILE=/dev/null
}

verify_compose_images() {
  [[ "$(docker inspect --format '{{.Image}}' "$(compose_fixture ps --quiet api)")" == "$api_image_id" ]]
  [[ "$(docker inspect --format '{{.Image}}' "$(compose_fixture ps --quiet web)")" == "$web_image_id" ]]
}

open_restored_gateway() {
  local target_env="$scratch/restore-gateway.yml"
  export DRILL_RESTORED_DATABASE_URL="postgresql+asyncpg://temuriset:$POSTGRES_PASSWORD@postgres:5432/$target_db"
  export DRILL_RESTORED_BUCKET="$BACKUP_RESTORE_S3_BUCKET"
  cat > "$target_env" <<'YAML'
services:
  api:
    environment:
      DATABASE_URL: ${DRILL_RESTORED_DATABASE_URL}
      S3_BUCKET: ${DRILL_RESTORED_BUCKET}
YAML
  docker compose --env-file /dev/null --project-name "$project" --file "$compose_file" \
    --file "$scratch/compose.yml" --file "$target_env" up --detach --no-deps --wait --wait-timeout 120 api >&2
  compose_fixture up --detach --no-deps --force-recreate --wait --wait-timeout 120 web edge >&2
  verify_compose_images
}
