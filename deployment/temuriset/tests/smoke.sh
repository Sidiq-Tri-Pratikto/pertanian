#!/bin/sh
# Synthetic local environment only. The dedicated project owns every resource removed on exit.
set -eu
umask 077
here=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
repo=$(git -C "$here" rev-parse --show-toplevel)
deploy=$repo/deployment/temuriset
tmp=$(mktemp -d)
project="temuriset-m11-smoke-$(openssl rand -hex 6)"
compose() { docker compose --env-file /dev/null -p "$project" -f "$deploy/compose.staging.yml" "$@"; }
cleanup() {
    status=$?
    if [ "$status" -ne 0 ]; then compose ps -a >&2 || true; fi
    compose down --volumes --remove-orphans >&2 || true
    rm -rf "$tmp"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

export TEMURISET_API_IMAGE=${TEMURISET_API_IMAGE:-temuriset-m11-api:local}
export TEMURISET_WEB_IMAGE=${TEMURISET_WEB_IMAGE:-temuriset-m11-web:local}
export RELEASE_SHA=${RELEASE_SHA:-$(git -C "$repo" rev-parse HEAD)}
export EDGE_BIND_ADDRESS=127.0.0.1
export EDGE_PORT=${TEMURISET_SMOKE_PORT:-55443}
export WEB_ORIGIN="https://localhost:$EDGE_PORT"
export API_URL=http://api:8000
export S3_BUCKET=temuriset-documents
export S3_ACCESS_KEY="synthetic$(openssl rand -hex 8)"
export S3_SECRET_KEY=$(openssl rand -hex 24)
export POSTGRES_PASSWORD=$(openssl rand -hex 24)
export DATABASE_URL="postgresql+asyncpg://temuriset:$POSTGRES_PASSWORD@postgres:5432/temuriset"
export TLS_CERT_FILE="$tmp/tls.crt" TLS_KEY_FILE="$tmp/tls.key" S3_CONFIG_FILE="$tmp/s3.json"
export CLAMAV_NO_FRESHCLAMD=true
openssl req -x509 -newkey rsa:2048 -nodes -keyout "$TLS_KEY_FILE" -out "$TLS_CERT_FILE" \
    -days 1 -subj /CN=localhost -addext subjectAltName=DNS:localhost > /dev/null 2>&1
python3 - <<'PY'
import json
import os
from pathlib import Path
bucket = os.environ["S3_BUCKET"]
Path(os.environ["S3_CONFIG_FILE"]).write_text(json.dumps({"identities": [{
    "name": "temuriset-runtime",
    "credentials": [{"accessKey": os.environ["S3_ACCESS_KEY"], "secretKey": os.environ["S3_SECRET_KEY"]}],
    "actions": [f"Read:{bucket}", f"Write:{bucket}", f"List:{bucket}"],
}]}))
PY

inventory="$tmp/inventory.jsonl"
: > "$inventory"
for composition in generic-base generic-with-review project-support-only; do
    export COMPOSITION="$composition"
    if [ "$composition" = generic-base ]; then
        export ENVIRONMENT=development MAILBOX_ADAPTER=development
        mode=lifecycle
    else
        export ENVIRONMENT=staging MAILBOX_ADAPTER=disabled
        mode=no-mail
    fi
    compose up --detach --wait --wait-timeout 240
    compose run --rm --no-deps migrate
    python3 "$here/smoke.py" "$WEB_ORIGIN" "$TLS_CERT_FILE" "$composition" "$mode" > "$tmp/runtime.json"
    head=$(compose exec -T api alembic current | awk 'NR == 1 {print $1}')
    : > "$tmp/infrastructure"
    for service in postgres object-store clamav edge; do
        id=$(compose ps -q "$service")
        printf '%s %s\n' "$service" "$(docker inspect --format '{{.Config.Image}}' "$id")" >> "$tmp/infrastructure"
    done
    python3 - "$tmp/runtime.json" "$tmp/infrastructure" "$head" >> "$inventory" <<'PYTHON'
import json
import sys
from pathlib import Path
runtime = json.loads(Path(sys.argv[1]).read_text())
runtime["infrastructure_images"] = dict(line.split() for line in Path(sys.argv[2]).read_text().splitlines())
runtime["alembic_head"] = sys.argv[3]
print(json.dumps(runtime, sort_keys=True))
PYTHON
    if [ "$mode" = lifecycle ]; then
        integration="$repo/applications/generic/temuriset/applications/temuriset-api/tests/integration/documents/test_s3_storage.py"
        compose exec -T api python - < "$integration"
    fi
done
# Replacing web must recover through the same edge container.
edge_id=$(compose ps -q edge)
web_id=$(compose ps -q web)
compose up --detach --wait --wait-timeout 60 --no-deps --force-recreate web
test "$(compose ps -q edge)" = "$edge_id"
test "$(compose ps -q web)" != "$web_id"
python3 "$here/smoke.py" "$WEB_ORIGIN" "$TLS_CERT_FILE" "$composition" "$mode" > /dev/null

# Requests without a signature cannot inspect the bucket, even from the backend network.
compose exec -T api python - <<'PY'
from urllib.error import HTTPError
from urllib.request import urlopen
try:
    with urlopen("http://object-store:8333/temuriset-documents", timeout=5):
        raise SystemExit("Object store allowed an unsigned list")
except HTTPError as error:
    assert error.code in (401, 403), error.code
PY
if [ -n "${TEMURISET_SMOKE_INVENTORY:-}" ]; then
    cp "$inventory" "$TEMURISET_SMOKE_INVENTORY"
fi
printf '%s\n' 'Synthetic HTTPS, S3 gateway, migration and all three composition checks passed.'
