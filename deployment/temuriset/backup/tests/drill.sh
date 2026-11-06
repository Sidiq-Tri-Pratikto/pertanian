#!/usr/bin/env bash
# Spec 038. Every mutable target in this script is created here for this run.
set -euo pipefail
umask 077
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
api="$root/applications/generic/temuriset/applications/temuriset-api"
python="${PYTHON_BIN:-$api/.venv/bin/python}"
export PYTHON_BIN="$python"
mode="${1:-standalone}"
[[ $# -le 1 && ( "$mode" == standalone || "$mode" == --compose ) ]] || { printf 'Usage: %s [--compose]\n' "$0" >&2; exit 1; }
required_tools=(psql createdb pg_dump pg_restore docker gpg)
if [[ "$mode" == --compose ]]; then required_tools+=(openssl); else required_tools+=(initdb pg_ctl); fi
for tool in "${required_tools[@]}"; do
  command -v "$tool" >/dev/null || { printf 'Required tool unavailable: %s\n' "$tool" >&2; exit 1; }
done
scratch="$(mktemp -d)"
chmod 0700 "$scratch"
id="$("$python" -c 'import uuid; print(uuid.uuid4().hex[:10])')"
container="temuriset-backup-drill-$id"
postgres_started=0
storage_started=0
compose_started=0
cleanup() {
  if [[ $compose_started == 1 ]]; then compose_fixture down --volumes --remove-orphans >&2 || true; fi
  if [[ $storage_started == 1 ]]; then docker rm -f "$container" >/dev/null 2>&1 || true; fi
  if [[ $postgres_started == 1 ]]; then pg_ctl -D "$scratch/data" -m fast -w stop >/dev/null 2>&1 || true; fi
  rm -rf -- "$scratch"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Refuse inherited connection and storage credentials. Use only locally generated fixture identities.
for variable in PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE PGSERVICE PGSERVICEFILE PGOPTIONS PGSSLMODE PGHOSTADDR \
  AWS_PROFILE AWS_SESSION_TOKEN AWS_WEB_IDENTITY_TOKEN_FILE AWS_ROLE_ARN; do
  unset "$variable"
done
target_db="temuriset_restore_$id"
export AWS_ACCESS_KEY_ID="drill-$id"
export AWS_SECRET_ACCESS_KEY="$("$python" -c 'import secrets; print(secrets.token_urlsafe(32))')"
export AWS_DEFAULT_REGION=us-east-1
export BACKUP_SOURCE_S3_BUCKET="temuriset-source-$id"
export BACKUP_RESTORE_S3_BUCKET="temuriset-restore-$id"
if [[ "$mode" == --compose ]]; then
  source "$here/compose_fixture.sh"
  start_compose_fixture
else
  pg_port="$("$python" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')"
  pg_role=drill
  initdb -D "$scratch/data" -U "$pg_role" -A trust -N >/dev/null
  pg_ctl -D "$scratch/data" -l "$scratch/postgres.log" -o "-h 127.0.0.1 -p $pg_port -k $scratch" -w start >/dev/null
  postgres_started=1
  source_db="temuriset_source_$id"
  createdb -h 127.0.0.1 -p "$pg_port" -U "$pg_role" "$source_db"
  export BACKUP_SOURCE_DATABASE_URL="postgresql://$pg_role@127.0.0.1:$pg_port/$source_db"
  export BACKUP_RESTORE_DATABASE_URL="postgresql://$pg_role@127.0.0.1:$pg_port/$target_db"
"$python" - "$scratch/identity.json" <<'PY'
import json
import os
import sys
from pathlib import Path

Path(sys.argv[1]).write_text(json.dumps({"identities": [{
    "name": "synthetic-fixture",
    "credentials": [{"accessKey": os.environ["AWS_ACCESS_KEY_ID"], "secretKey": os.environ["AWS_SECRET_ACCESS_KEY"]}],
    "actions": ["Admin"],
}]}))
PY
  chmod 0444 "$scratch/identity.json"
  image=chrislusf/seaweedfs:latest@sha256:c2658820e763294a9e9de7b36c81e59b879e3459148351aee4e31a126ca64860
  docker run --rm -d --name "$container" --publish 127.0.0.1::8333 \
    --mount "type=bind,source=$scratch/identity.json,target=/run/identity.json,readonly" \
    "$image" mini -dir=/data -ip=127.0.0.1 -ip.bind=0.0.0.0 -s3.config=/run/identity.json \
    -s3.autoCreateBucket=false -bucket="$BACKUP_SOURCE_S3_BUCKET" >/dev/null
  storage_started=1
  s3_address="$(docker port "$container" 8333/tcp)"
fi
createdb -h 127.0.0.1 -p "$pg_port" -U "$pg_role" "$target_db"
postgres() {
  local db="$1"
  shift
  psql -h 127.0.0.1 -p "$pg_port" -U "$pg_role" -d "$db" "$@"
}
[[ "$s3_address" == 127.0.0.1:* ]]
export BACKUP_SOURCE_S3_ENDPOINT="http://$s3_address"
export BACKUP_RESTORE_S3_ENDPOINT="$BACKUP_SOURCE_S3_ENDPOINT"
"$python" - <<'PY'
import os
import time
import boto3
from botocore.config import Config
from botocore.exceptions import ConnectionClosedError, EndpointConnectionError

store = boto3.client("s3", endpoint_url=os.environ["BACKUP_SOURCE_S3_ENDPOINT"], config=Config(
    connect_timeout=2, read_timeout=2, retries={"total_max_attempts": 1}, s3={"addressing_style": "path"}
))
for attempt in range(30):
    try:
        store.list_buckets()
        break
    except (ConnectionClosedError, EndpointConnectionError):
        if attempt == 29:
            raise
        time.sleep(1)
store.create_bucket(Bucket=os.environ["BACKUP_RESTORE_S3_BUCKET"])
PY

export BACKUP_DIRECTORY="$scratch/bundles" BACKUP_PASSPHRASE_FILE="$scratch/passphrase"
mkdir "$BACKUP_DIRECTORY"
"$python" -c 'import secrets; print(secrets.token_urlsafe(40))' > "$BACKUP_PASSPHRASE_FILE"
export BACKUP_SOURCE_ENVIRONMENT="synthetic-$id"
export BACKUP_RELEASE_SHA="$(git -C "$root" rev-parse HEAD)"
gateway_args=()
if [[ "$mode" == --compose ]]; then
  gateway_args=(--origin "$WEB_ORIGIN" --certificate "$TLS_CERT_FILE")
else
  export ENVIRONMENT=development FILE_SCANNER=development-accept MAILBOX_ADAPTER=development STORAGE_ADAPTER=s3
  export WEB_ORIGIN=http://localhost:3020 SESSION_COOKIE_SECURE=false
  export S3_ENDPOINT_URL="$BACKUP_SOURCE_S3_ENDPOINT" S3_BUCKET="$BACKUP_SOURCE_S3_BUCKET"
  export S3_ACCESS_KEY="$AWS_ACCESS_KEY_ID" S3_SECRET_KEY="$AWS_SECRET_ACCESS_KEY" S3_REGION=us-east-1
  export STORAGE_PATH="$scratch/api-scratch"
  export DATABASE_URL="${BACKUP_SOURCE_DATABASE_URL/postgresql:/postgresql+asyncpg:}"
  (cd "$api" && "$python" -m alembic upgrade head)
fi
BACKUP_SCHEMA_VERSION="$(postgres "$source_db" -X -At -v ON_ERROR_STOP=1 -c 'SELECT version_num FROM alembic_version')"
export BACKUP_SCHEMA_VERSION
gateway_check() {
  (cd "$api" && PYTHONPATH="$api" "$python" -B "$here/gateway_fixture.py" "$1" "$scratch/fixture.json" "${gateway_args[@]}")
}
gateway_check seed
expected_row="$(postgres "$source_db" -X -At -c   'SELECT storage_key, sha256, size_bytes, file_state FROM document_versions ORDER BY storage_key')"
export BACKUP_DRILL_FENCE="$scratch/writers-stopped"
if [[ "$mode" == --compose ]]; then
  compose_fixture stop edge web api worker migrate >&2
  export BACKUP_QUIESCENCE_CHECK="$here/../compose_quiescence.sh" BACKUP_S3_WRITERS_FENCED=yes
else
  # The fixture process has exited. These two targets have only this drill's credentials.
  export BACKUP_QUIESCENCE_CHECK="$scratch/check-fence"
  cat > "$BACKUP_QUIESCENCE_CHECK" <<'CHECK'
#!/usr/bin/env bash
set -euo pipefail
test -f "$BACKUP_DRILL_FENCE"
CHECK
  chmod +x "$BACKUP_QUIESCENCE_CHECK"
  touch "$BACKUP_DRILL_FENCE"
fi
fixture_object() {
  "$python" - "$1" "$scratch/original-object" <<'PY'
import os
import sys

import boto3
from botocore.config import Config

client = boto3.client(
    "s3", endpoint_url=os.environ["BACKUP_SOURCE_S3_ENDPOINT"], config=Config(s3={"addressing_style": "path"})
)
bucket = os.environ["BACKUP_SOURCE_S3_BUCKET"]
mode, original = sys.argv[1:]
if mode == "missing":
    entries = client.list_objects_v2(Bucket=bucket)["Contents"]
    assert len(entries) == 1
    key = entries[0]["Key"]
    client.download_file(bucket, key, original)
    with open(f"{original}.key", "w", encoding="utf-8") as handle:
        handle.write(key)
    client.delete_object(Bucket=bucket, Key=key)
else:
    with open(f"{original}.key", encoding="utf-8") as handle:
        key = handle.read()
    with open(original, "rb") as handle:
        payload = handle.read()
    if mode == "wrong":
        payload = bytes([payload[0] ^ 1]) + payload[1:]
    client.put_object(Bucket=bucket, Key=key, Body=payload)
PY
}
for fixture in missing wrong; do
  fixture_object "$fixture"
  if "$here/../backup.sh" > "$scratch/failed-backup.json" 2> "$scratch/failed-backup.log"; then
    printf 'Backup unexpectedly succeeded with a %s document object.\n' "$fixture" >&2
    exit 1
  fi
  grep -q 'A live document reference does not match its object.' "$scratch/failed-backup.log"
  [[ -z "$(find "$BACKUP_DIRECTORY" -maxdepth 1 -type f -print)" ]]
done
fixture_object original
printf 'Backup rejected missing and changed objects without publishing a bundle.\n'
"$here/../backup.sh" > "$scratch/backup.json"
read_bundle() {
  "$python" -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$scratch/backup.json" "$1"
}
archive="$(read_bundle archive)"
digest="$(read_bundle sha256)"
rm -f -- "$BACKUP_DRILL_FENCE"
unset BACKUP_S3_WRITERS_FENCED
# Simulated irreversible migration and object loss only on this run's disposable source.
postgres "$source_db" -X -q -v ON_ERROR_STOP=1 \
  -c 'CREATE TABLE post_snapshot_sentinel AS SELECT clock_timestamp() AS written_at;' \
  -c 'DROP TABLE document_versions CASCADE;'
sentinel="$(postgres "$source_db" -X -At -c 'SELECT written_at FROM post_snapshot_sentinel')"
"$python" - <<'PY'
import os
import boto3
from botocore.config import Config

client = boto3.client("s3", endpoint_url=os.environ["BACKUP_SOURCE_S3_ENDPOINT"], config=Config(s3={"addressing_style":"path"}))
bucket = os.environ["BACKUP_SOURCE_S3_BUCKET"]
for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket):
    for row in page.get("Contents", []):
        client.delete_object(Bucket=bucket, Key=row["Key"])
PY
restore_start="$("$python" -c 'import time; print(time.monotonic())')"
"$here/../restore.sh" --archive "$archive" --sha256 "$digest"
[[ "$(postgres "$target_db" -X -At -c "SELECT to_regclass('post_snapshot_sentinel') IS NULL")" == t ]]
[[ "$(postgres "$target_db" -X -At -c 'SELECT count(*) FROM document_versions')" == 1 ]]
restored_row="$(postgres "$target_db" -X -At -c   'SELECT storage_key, sha256, size_bytes, file_state FROM document_versions ORDER BY storage_key')"
[[ "$restored_row" == "$expected_row" ]]
row_sha="$("$python" -c 'import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())' <<< "$restored_row")"
if [[ "$mode" == --compose ]]; then
  open_restored_gateway
else
  export S3_ENDPOINT_URL="$BACKUP_RESTORE_S3_ENDPOINT" S3_BUCKET="$BACKUP_RESTORE_S3_BUCKET"
  export DATABASE_URL="${BACKUP_RESTORE_DATABASE_URL/postgresql:/postgresql+asyncpg:}"
fi
gateway_check verify
"$python" - "$scratch/backup.json" "$sentinel" "$restore_start" "$row_sha" <<'PY'
import json
import sys
import time
from datetime import UTC, datetime

receipt = json.load(open(sys.argv[1]))
cutoff = datetime.fromisoformat(receipt["snapshot_utc"])
sentinel = datetime.fromisoformat(sys.argv[2]).astimezone(UTC)
print(json.dumps({
    "snapshot_utc": cutoff.isoformat(), "post_snapshot_write_utc": sentinel.isoformat(),
    "observed_loss_window_seconds": round((sentinel - cutoff).total_seconds(), 3),
    "source_schema": receipt["schema_version"], "object_count": receipt["object_count"],
    "verified_recovery_seconds": round(time.monotonic() - float(sys.argv[3]), 3),
    "restored_document_row_sha256": sys.argv[4], "source_code": "local worktree",
}))
PY
