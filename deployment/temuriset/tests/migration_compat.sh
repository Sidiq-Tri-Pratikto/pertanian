#!/usr/bin/env bash
# Compare a previous API and worker to a candidate schema in a disposable database.
set -euo pipefail
umask 077
exec "${PYTHON_BIN:-python3}" -B - "$@" <<'PY'
import argparse
import contextlib
import json
import os
import re
import socket
import subprocess
import tempfile
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import httpx

ORIGIN = "http://localhost:3020"
SCHEMA = """
SELECT COALESCE(json_agg(identity), '[]')
FROM (
  SELECT json_build_array('column', c.relname, a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull) AS identity
  FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid
  WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r', 'p', 'v', 'm')
    AND a.attnum > 0 AND NOT a.attisdropped
  UNION ALL
  SELECT json_build_array('constraint', c.relname, x.conname, pg_get_constraintdef(x.oid)) AS identity
  FROM pg_constraint x JOIN pg_class c ON c.oid = x.conrelid
  WHERE c.relnamespace = 'public'::regnamespace
) supported;
"""


def run(args: list[str], env: dict[str, str], cwd: Path | None = None) -> str:
    result = subprocess.run(args, env=env, cwd=cwd, capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise RuntimeError(f"{Path(args[0]).name} failed during compatibility check.")
    return result.stdout.strip()


def poll(check: Callable[[], bool], process: subprocess.Popen | None = None) -> None:
    for _ in range(120):
        if process is not None and process.poll() is not None:
            raise RuntimeError("Compatibility service exited during its check.")
        try:
            if check():
                return
        except (httpx.RequestError, subprocess.SubprocessError):
            pass
        time.sleep(0.25)
    raise RuntimeError("Compatibility service did not become ready.")


def stop(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def open_port() -> int:
    with socket.socket() as handle:
        handle.bind(("127.0.0.1", 0))
        return handle.getsockname()[1]


def run_api(stack: contextlib.ExitStack, api: Path, python: Path, env: dict[str, str]) -> str:
    port = open_port()
    process = subprocess.Popen(
        [str(python), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=api, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    stack.callback(stop, process)
    url = f"http://127.0.0.1:{port}"
    poll(lambda: httpx.get(f"{url}/health/ready", timeout=1).status_code == 200, process)
    return url


def require(response: httpx.Response, expected: int) -> Any:
    if response.status_code != expected:
        raise RuntimeError(f"Expected HTTP {expected}, received {response.status_code}.")
    return response.json()


def create(client: httpx.Client, url: str, party: str) -> str:
    return require(client.post(
        f"{url}/api/v1/inventions", json={"acting_party_id": party},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    ), 201)["id"]


def verify_worker(
    stack: contextlib.ExitStack, api: Path, python: Path, env: dict[str, str], sql: Callable[[str], str]
) -> None:
    # The already-supported scanner job is a safe no-op for a missing synthetic document.
    job_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())
    sql(
        "INSERT INTO jobs (id, kind, status, input, created_at, updated_at, run_after) VALUES "
        f"('{job_id}', 'documents.scan', 'PENDING', "
        f"jsonb_build_object('version_id', '{version_id}'), now(), now(), now())"
    )
    worker = subprocess.Popen(
        [str(python), "-m", "app.worker"], cwd=api, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    stack.callback(stop, worker)
    poll(lambda: sql(f"SELECT status FROM jobs WHERE id = '{job_id}'") == "SUCCEEDED", worker)
    stop(worker)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run isolated migration compatibility evidence.")
    parser.add_argument("previous", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--previous-sha", required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--comparison", required=True, choices=("pr-base", "previous-release"))
    parser.add_argument("--candidate-worktree", action="store_true")
    args = parser.parse_args()
    if args.candidate_worktree and args.comparison == "previous-release":
        raise RuntimeError("Previous-release evidence requires immutable candidate code.")
    if any(not re.fullmatch(r"[0-9a-f]{40}", value) for value in (args.previous_sha, args.candidate_sha)):
        raise RuntimeError("Provide immutable previous and candidate commit IDs.")

    dsn = os.environ["COMPAT_DATABASE_URL"]
    value = urlsplit(dsn)
    database = value.path.removeprefix("/")
    if (
        value.scheme != "postgresql+asyncpg" or value.hostname != "127.0.0.1" or not value.port
        or not value.username or value.query or value.fragment
        or not re.fullmatch(r"temuriset_compat_[a-z0-9]{1,24}", database)
    ):
        raise RuntimeError("Provide an isolated loopback compatibility database.")
    psql_env = {name: value for name, value in os.environ.items() if not name.startswith("PG")}
    psql_env.update(
        PGHOST="127.0.0.1", PGPORT=str(value.port), PGUSER=unquote(value.username), PGDATABASE=database,
        PGPASSWORD=unquote(value.password or ""), PGCONNECT_TIMEOUT="10",
    )

    def sql(query: str) -> str:
        return run(["psql", "-X", "-w", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", query], psql_env)

    if sql("SELECT current_database()") != database or sql(
        "SELECT EXISTS (SELECT FROM pg_class WHERE relnamespace = 'public'::regnamespace)"
    ) != "f":
        raise RuntimeError("Refusing to mutate a nonempty or unexpected compatibility database.")

    previous = args.previous.resolve()
    candidate = args.candidate.resolve()
    old_python = Path(os.environ.get("PREVIOUS_PYTHON", previous / ".venv/bin/python")).absolute()
    new_python = Path(os.environ.get("CANDIDATE_PYTHON", candidate / ".venv/bin/python")).absolute()
    with tempfile.TemporaryDirectory(prefix="temuriset-compat-") as scratch, contextlib.ExitStack() as stack:
        env = {
            **os.environ, "DATABASE_URL": dsn, "ENVIRONMENT": "development", "MAILBOX_ADAPTER": "development",
            "FILE_SCANNER": "development-accept", "STORAGE_ADAPTER": "local", "WEB_ORIGIN": ORIGIN,
            "SESSION_COOKIE_SECURE": "false", "STORAGE_PATH": scratch, "COMPOSITION": "generic-base",
            "COMPOSITION_OVERRIDES": "{}",
        }
        for variable in ("PYTHONPATH", "PYTHONHOME"):
            env.pop(variable, None)
        run([str(old_python), "-m", "alembic", "upgrade", "head"], env, previous)
        old_head = sql("SELECT version_num FROM alembic_version")
        before = {tuple(item) for item in json.loads(sql(SCHEMA))}
        old_url = run_api(stack, previous, old_python, env)
        email = "migration-compat@example.test"
        with httpx.Client(timeout=5, headers={"Origin": ORIGIN}) as client:
            require(client.post(f"{old_url}/api/v1/auth/code", json={
                "email": email, "purpose": "sign_up", "display_name": "Synthetic compatibility check",
                "time_zone": "Asia/Jakarta", "persona": "inovator",
            }), 202)
            mailbox = require(client.get(f"{old_url}/api/v1/dev/mailbox", params={"email": email}), 200)
            code = re.search(r"\b[0-9]{6}\b", mailbox[0]["body"])
            if code is None:
                raise RuntimeError("Synthetic mailbox did not return the compatibility code.")
            who = require(client.post(f"{old_url}/api/v1/auth/verify", json={
                "email": email, "code": code.group(),
            }), 200)
            party = who["active_party_id"]
            original = create(client, old_url, party)
            require(client.get(f"{old_url}/api/v1/inventions/{original}"), 200)

            run([str(new_python), "-m", "alembic", "upgrade", "head"], env, candidate)
            new_head = sql("SELECT version_num FROM alembic_version")
            after = {tuple(item) for item in json.loads(sql(SCHEMA))}
            removed = before - after
            if removed:
                names = ", ".join(sorted({f"{kind} {table}.{name}" for kind, table, name, *_ in removed}))
                raise RuntimeError(
                    f"Existing schema signatures changed. Alembic {old_head} to {new_head}: {names}. "
                    "Review contract changes after old-code retirement."
                )
            existing_tables = {item[1] for item in before if item[0] == "column"}
            if any(item[0] == "constraint" and item[1] in existing_tables for item in after - before):
                raise RuntimeError("An existing table gained a constraint. Review compatibility before promotion.")
            require(client.get(f"{old_url}/api/v1/inventions/{original}"), 200)
            old_write = create(client, old_url, party)
            verify_worker(stack, previous, old_python, env, sql)

            new_url = run_api(stack, candidate, new_python, env)
            for record in (original, old_write):
                require(client.get(f"{new_url}/api/v1/inventions/{record}"), 200)
            new_write = create(client, new_url, party)
            require(client.get(f"{old_url}/api/v1/inventions/{new_write}"), 200)
            verify_worker(stack, candidate, new_python, env, sql)

        print(json.dumps({
            "comparison": args.comparison, "previous_sha": args.previous_sha, "candidate_sha": args.candidate_sha,
            "previous_head": old_head, "candidate_head": new_head, "schema_changed": old_head != new_head,
            "candidate_source": "worktree" if args.candidate_worktree else "commit",
            "old_read_write": True, "new_read_write": True, "old_worker": True, "new_worker": True,
            "release_expand_evidence": args.comparison == "previous-release" and old_head != new_head,
        }, sort_keys=True))


try:
    main()
except (KeyError, ValueError, OSError, RuntimeError, httpx.HTTPError, subprocess.SubprocessError) as error:
    if isinstance(error, RuntimeError):
        raise SystemExit(str(error)) from None
    raise SystemExit("Compatibility check failed. Check isolated tooling and service readiness.") from None
PY
