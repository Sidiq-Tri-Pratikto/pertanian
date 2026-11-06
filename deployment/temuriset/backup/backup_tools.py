"""Capture, verify and restore one encrypted PostgreSQL/S3 recovery point."""

import argparse
import contextlib
import hashlib
import hmac
import json
import os
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote, urlsplit

BUNDLE = re.compile(r"temuriset-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}\.tar\.gpg")
DIGEST = re.compile(r"[0-9a-f]{64}")
RELEASE = re.compile(r"[0-9a-f]{40}")
SCHEMA = re.compile(r"[a-zA-Z0-9_]{1,32}")
OBJECT_PATH = re.compile(r"objects/[0-9]{8}")
RESTORE_DATABASE = re.compile(r"temuriset_restore_([a-z0-9]{1,24})")
S3_BUCKET = re.compile(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]")
CHUNK_SIZE = 1024 * 1024
READ_TIMEOUT = 120
TOOL_TIMEOUT = 3600
EMPTY_DB = """
SELECT NOT EXISTS (
  SELECT FROM pg_namespace
  WHERE nspname NOT IN ('public', 'information_schema') AND nspname !~ '^pg_'
) AND NOT EXISTS (
  SELECT FROM pg_class WHERE relnamespace = 'public'::regnamespace
) AND NOT EXISTS (
  SELECT FROM pg_proc WHERE pronamespace = 'public'::regnamespace
) AND NOT EXISTS (
  SELECT FROM pg_type WHERE typnamespace = 'public'::regnamespace
) AND NOT EXISTS (
  SELECT FROM pg_extension WHERE extname <> 'plpgsql'
) AND NOT EXISTS (
  SELECT FROM pg_largeobject_metadata
);
"""


class BackupError(RuntimeError):
    """The operation cannot proceed safely."""


def setting(name: str) -> str:
    """Read a required operator input without echoing its value."""
    value = os.environ.get(name)
    if not value:
        raise BackupError(f"Set {name} in the operator environment.")
    return value


def tool(
    args: list[str], *, env: dict[str, str] | None = None, timeout: int = TOOL_TIMEOUT
) -> str:
    """Run a local tool with bounded time and keep provider messages out of output."""
    try:
        result = subprocess.run(
            args,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=timeout,
            text=True,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise BackupError(
            f"{Path(args[0]).name} failed. Check tool availability and scoped access."
        ) from error
    return result.stdout


def passphrase_file(path: Path) -> Path:
    """Accept a protected regular file owned by the current operator."""
    try:
        info = path.lstat()
    except OSError as error:
        raise BackupError("Provide a private passphrase file.") from error
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_mode & 0o077
        or info.st_uid != os.getuid()
        or info.st_size < 16
    ):
        raise BackupError(
            "Passphrase file must be operator-owned, private, and contain at least 16 bytes."
        )
    return path.absolute()


def private_directory(path: Path) -> Path:
    """Require a dedicated output directory with no shared permissions."""
    info = path.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise BackupError("Use an operator-owned private backup directory.")
    return path.absolute()


def file_digest(path: Path) -> str:
    """Compute a streaming SHA-256 checksum."""
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def verify_archive_digest(path: Path, expected: str) -> None:
    """Refuse bytes that do not match the separately trusted digest."""
    if (
        not isinstance(expected, str)
        or not DIGEST.fullmatch(expected)
        or not hmac.compare_digest(file_digest(path), expected)
    ):
        raise BackupError("Archive checksum does not match the trusted inventory.")


def extract_archive(path: Path, directory: Path) -> None:
    """Extract only regular, uniquely named bundle members into private scratch space."""
    seen: set[str] = set()
    try:
        (directory / "objects").mkdir(mode=0o700, exist_ok=False)
        with tarfile.open(path, mode="r:") as archive:
            for member in archive:
                if (
                    member.name in seen
                    or member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE)
                    or member.sparse is not None
                    or (
                        member.name not in ("snapshot.json", "postgres.dump")
                        and not OBJECT_PATH.fullmatch(member.name)
                    )
                ):
                    raise BackupError("Unsafe or duplicate archive member.")
                seen.add(member.name)
                source = archive.extractfile(member)
                if source is None:
                    raise BackupError("Archive member is unreadable.")
                with source, (directory / member.name).open("xb") as target:
                    shutil.copyfileobj(source, target, length=CHUNK_SIZE)
    except (tarfile.TarError, EOFError, OSError) as error:
        raise BackupError("Archive could not be unpacked safely.") from error
    if not {"snapshot.json", "postgres.dump"}.issubset(seen):
        raise BackupError("Archive is missing its manifest or database dump.")


def restore_target_id(database: str, bucket: str) -> str:
    """Require two explicitly isolated target names with a common drill ID."""
    match = RESTORE_DATABASE.fullmatch(database)
    if not match or bucket != f"temuriset-restore-{match.group(1)}":
        raise BackupError("Use a matching isolated restore database and bucket.")
    return match.group(1)


@dataclass(frozen=True)
class Postgres:
    """An explicitly named PostgreSQL database with secret DSN kept out of argv."""

    dsn: str
    name: str

    @classmethod
    def configured(cls, prefix: str) -> "Postgres":
        """Load a PostgreSQL URI that cannot redirect through query parameters."""
        dsn = setting(f"{prefix}_DATABASE_URL")
        value = urlsplit(dsn)
        name = unquote(value.path.removeprefix("/"))
        allowed = {
            "sslmode",
            "sslrootcert",
            "sslcert",
            "sslkey",
            "connect_timeout",
            "application_name",
        }
        if (
            value.scheme not in ("postgresql", "postgres")
            or not value.hostname
            or not value.username
            or value.fragment
            or not re.fullmatch(r"[a-zA-Z0-9_-]{1,63}", name)
            or any(
                key not in allowed
                for key, _ in parse_qsl(value.query, keep_blank_values=True)
            )
        ):
            raise BackupError(
                "Provide an explicit PostgreSQL host, user, and database URI."
            )
        return cls(dsn, name)

    def env(self) -> dict[str, str]:
        """Pass the database URI through the child environment."""
        parsed = urlsplit(self.dsn)
        environment = {
            name: value
            for name, value in os.environ.items()
            if not name.startswith("PG")
        }
        for name in (
            "PGPASSFILE",
            "PGSSLMODE",
            "PGSSLROOTCERT",
            "PGSSLCERT",
            "PGSSLKEY",
        ):
            if name in os.environ:
                environment[name] = os.environ[name]
        environment.update(
            PGDATABASE=self.name,
            PGCONNECT_TIMEOUT="10",
            PGHOST=parsed.hostname or "",
            PGPORT=str(parsed.port or 5432),
            PGUSER=unquote(parsed.username or ""),
        )
        if parsed.password is not None:
            environment["PGPASSWORD"] = unquote(parsed.password)
        for name, value in parse_qsl(parsed.query, keep_blank_values=True):
            environment[
                "PGAPPNAME" if name == "application_name" else f"PG{name.upper()}"
            ] = value
        return environment

    def scalar(self, sql: str) -> str:
        """Run a constant SQL read with no user interpolation."""
        return tool(
            ["psql", "-X", "-w", "-At", "-v", "ON_ERROR_STOP=1", "-c", sql],
            env=self.env(),
            timeout=60,
        ).strip()

    def verify_database(self) -> None:
        """Confirm the connected server selected the intended database."""
        if self.scalar("SELECT current_database()") != self.name:
            raise BackupError(
                "Connected database does not match the requested database."
            )

    def schema(self) -> str:
        """Read the exact single Alembic head in the connected database."""
        version = self.scalar("SELECT version_num FROM alembic_version")
        if not SCHEMA.fullmatch(version):
            raise BackupError("Expected one recorded Alembic head.")
        return version

    def available_documents(self) -> list[dict[str, Any]]:
        """Read database references that require a corresponding stored file."""
        return json.loads(
            self.scalar("""
            SELECT COALESCE(json_agg(json_build_object(
                'key', storage_key, 'size', size_bytes, 'sha256', sha256
            ) ORDER BY storage_key), '[]')
            FROM document_versions WHERE file_state IN ('AVAILABLE', 'QUARANTINED')
        """)
        )


def verify_document_pair(
    references: list[dict[str, Any]], objects: list[dict[str, Any]]
) -> None:
    """Refuse a snapshot whose live database references do not match object bytes."""
    inventory = {entry["key"]: (entry["size"], entry["sha256"]) for entry in objects}
    if any(
        inventory.get(entry["key"]) != (entry["size"], entry["sha256"])
        for entry in references
    ):
        raise BackupError("A live document reference does not match its object.")


@dataclass(frozen=True)
class ObjectStore:
    """Private S3 endpoint and bucket chosen through explicit operator inputs."""

    bucket: str
    client: Any

    @classmethod
    def configured(cls, prefix: str) -> "ObjectStore":
        """Use the AWS credential chain and bounded requests to a chosen endpoint."""
        import boto3
        from botocore.config import Config

        endpoint = setting(f"{prefix}_S3_ENDPOINT")
        value = urlsplit(endpoint)
        bucket = setting(f"{prefix}_S3_BUCKET")
        if (
            value.scheme not in ("https", "http")
            or not value.hostname
            or any((value.username, value.password, value.query, value.fragment))
            or value.path not in ("", "/")
            or not S3_BUCKET.fullmatch(bucket)
        ):
            raise BackupError("Use an explicit HTTP(S) S3 origin and bucket.")
        config = Config(
            connect_timeout=10,
            read_timeout=READ_TIMEOUT,
            retries={"mode": "standard", "total_max_attempts": 3},
            s3={"addressing_style": "path"},
        )
        return cls(bucket, boto3.client("s3", endpoint_url=endpoint, config=config))

    def inventory(self) -> dict[str, tuple[int, str]]:
        """Read the complete visible object inventory for consistency checks."""
        pages = self.client.get_paginator("list_objects_v2").paginate(
            Bucket=self.bucket
        )
        return {
            row["Key"]: (row["Size"], row["ETag"])
            for page in pages
            for row in page.get("Contents", [])
        }

    def read(self, key: str, etag: str, size: int, target: Path | None = None) -> str:
        """Hash one object with a conditional read, optionally capturing it."""
        response = self.client.get_object(Bucket=self.bucket, Key=key, IfMatch=etag)
        digest = hashlib.sha256()
        copied = 0
        stream = response["Body"]
        try:
            if response.get("ETag") != etag or response.get("ContentLength") != size:
                raise BackupError("Object changed during its conditional read.")
            with (
                target.open("xb")
                if target is not None
                else open(os.devnull, "wb") as handle
            ):
                for block in stream.iter_chunks(CHUNK_SIZE):
                    copied += len(block)
                    if copied > size:
                        raise BackupError("Object exceeded its inventory size.")
                    digest.update(block)
                    handle.write(block)
        finally:
            stream.close()
        if copied != size:
            raise BackupError("Object read did not match its inventory size.")
        return digest.hexdigest()


def gpg(args: list[str], key: Path) -> str:
    """Run authenticated encryption with an isolated keyring and no passphrase cache."""
    # Keep the agent socket below the Unix path limit, even when the bundle path is long.
    with tempfile.TemporaryDirectory(prefix="temuriset-gpg-", dir="/tmp") as home:
        try:
            return tool(
                [
                    "gpg",
                    "--homedir",
                    home,
                    "--batch",
                    "--no-tty",
                    "--pinentry-mode",
                    "loopback",
                    "--no-symkey-cache",
                    "--passphrase-file",
                    str(key),
                    *args,
                ]
            )
        finally:
            if shutil.which("gpgconf"):
                with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                    subprocess.run(
                        ["gpgconf", "--homedir", home, "--kill", "gpg-agent"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                        timeout=10,
                    )


def check_fence(executable: Path) -> None:
    """Ask the operator's environment-specific checker to prove writer quiescence."""
    if (
        not executable.is_absolute()
        or not executable.is_file()
        or not os.access(executable, os.X_OK)
    ):
        raise BackupError("Provide an absolute executable quiescence checker.")
    tool([str(executable)], timeout=60)


def capture(directory: Path, key: Path) -> None:
    """Capture the fenced database and bucket, then publish one encrypted artifact."""
    database = Postgres.configured("BACKUP_SOURCE")
    store = ObjectStore.configured("BACKUP_SOURCE")
    fence = Path(setting("BACKUP_QUIESCENCE_CHECK"))
    environment = setting("BACKUP_SOURCE_ENVIRONMENT")
    release = setting("BACKUP_RELEASE_SHA")
    schema = setting("BACKUP_SCHEMA_VERSION")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", environment) or not RELEASE.fullmatch(
        release
    ):
        raise BackupError(
            "Provide a named source environment and its exact release commit."
        )
    check_fence(fence)
    database.verify_database()
    if database.schema() != schema:
        raise BackupError(
            "The database head differs from the supplied release inventory."
        )
    with tempfile.TemporaryDirectory(prefix=".backup-", dir=directory) as scratch:
        work = Path(scratch)
        objects = work / "objects"
        objects.mkdir()
        dump = work / "postgres.dump"
        snapshot = datetime.now(UTC)
        before = store.inventory()
        references = database.available_documents()
        tool(
            [
                "pg_dump",
                "-w",
                "--format=custom",
                "--no-owner",
                "--no-privileges",
                "--file",
                str(dump),
            ],
            env=database.env(),
        )
        check_fence(fence)
        entries = []
        for position, (object_key, (size, etag)) in enumerate(sorted(before.items())):
            member = f"objects/{position:08d}"
            digest = store.read(object_key, etag, size, work / member)
            entries.append(
                {"key": object_key, "path": member, "size": size, "sha256": digest}
            )
        verify_document_pair(references, entries)
        if (
            store.inventory() != before
            or database.schema() != schema
            or database.available_documents() != references
        ):
            raise BackupError(
                "The source changed during capture. Keep writers fenced and retry."
            )
        check_fence(fence)
        manifest = {
            "format": 1,
            "snapshot_utc": snapshot.isoformat(),
            "source_environment": environment,
            "source_database": database.name,
            "source_bucket": store.bucket,
            "release_sha": release,
            "schema_version": schema,
            "postgres_sha256": file_digest(dump),
            "objects": entries,
        }
        (work / "snapshot.json").write_text(
            json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
        )
        tar = work / "bundle.tar"
        with tarfile.open(tar, "w") as archive:
            for member in [
                "snapshot.json",
                "postgres.dump",
                *(entry["path"] for entry in entries),
            ]:
                archive.add(work / member, arcname=member, recursive=False)
        encrypted = work / "encrypted.tar.gpg"
        gpg(
            [
                "--symmetric",
                "--cipher-algo",
                "AES256",
                "--force-mdc",
                "--compress-algo",
                "none",
                "--output",
                str(encrypted),
                str(tar),
            ],
            key,
        )
        artifact = (
            directory
            / f"temuriset-{snapshot:%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}.tar.gpg"
        )
        digest = file_digest(encrypted)
        os.link(encrypted, artifact)
        print(
            json.dumps(
                {
                    "archive": str(artifact),
                    "sha256": digest,
                    "snapshot_utc": manifest["snapshot_utc"],
                    "source_environment": environment,
                    "release_sha": release,
                    "schema_version": schema,
                    "object_count": len(entries),
                },
                sort_keys=True,
            )
        )


def verified_manifest(directory: Path) -> dict[str, Any]:
    """Verify the complete inventory before any database or S3 mutation."""
    manifest = json.loads((directory / "snapshot.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("format") != 1:
        raise BackupError("Unsupported backup manifest.")
    required = (
        "source_environment",
        "source_database",
        "source_bucket",
        "release_sha",
        "schema_version",
        "snapshot_utc",
    )
    if any(
        not isinstance(manifest.get(field), str) or not manifest[field]
        for field in required
    ):
        raise BackupError("Backup manifest lacks its recovery point identity.")
    snapshot = datetime.fromisoformat(manifest["snapshot_utc"])
    if (
        snapshot.utcoffset() is None
        or not RELEASE.fullmatch(manifest["release_sha"])
        or not SCHEMA.fullmatch(manifest["schema_version"])
    ):
        raise BackupError("Backup manifest has invalid recovery point identity.")
    verify_archive_digest(
        directory / "postgres.dump", manifest.get("postgres_sha256", "")
    )
    if not isinstance(manifest.get("objects"), list):
        raise BackupError("Backup manifest lacks an object inventory.")
    paths = set()
    keys = set()
    for entry in manifest["objects"]:
        if not isinstance(entry, dict):
            raise BackupError("Invalid object inventory entry.")
        key, path, size = (entry.get(field) for field in ("key", "path", "size"))
        if (
            not isinstance(key, str)
            or not key
            or key in keys
            or not isinstance(path, str)
            or not OBJECT_PATH.fullmatch(path)
            or path in paths
            or type(size) is not int
            or size < 0
        ):
            raise BackupError("Invalid or duplicate object inventory entry.")
        keys.add(key)
        paths.add(path)
        stored = directory / path
        if stored.stat().st_size != size:
            raise BackupError("Object archive size differs from the manifest.")
        verify_archive_digest(stored, entry.get("sha256", ""))
    if {f"objects/{path.name}" for path in (directory / "objects").iterdir()} != paths:
        raise BackupError("Archive contains unlisted objects.")
    return manifest


def restore(artifact: Path, expected: str, key: Path) -> None:
    """Restore a trusted archive only into an explicitly isolated empty pair."""
    database = Postgres.configured("BACKUP_RESTORE")
    store = ObjectStore.configured("BACKUP_RESTORE")
    target = restore_target_id(database.name, store.bucket)
    started = time.monotonic()
    if not stat.S_ISREG(artifact.lstat().st_mode):
        raise BackupError("Restore input must be a regular encrypted archive.")
    with tempfile.TemporaryDirectory(prefix="temuriset-restore-") as scratch:
        work = Path(scratch)
        immutable_input = work / "archive.tar.gpg"
        shutil.copyfile(artifact, immutable_input)
        verify_archive_digest(immutable_input, expected)
        decrypted = work / "bundle.tar"
        status = gpg(
            [
                "--status-fd",
                "1",
                "--output",
                str(decrypted),
                "--decrypt",
                str(immutable_input),
            ],
            key,
        )
        if "[GNUPG:] GOODMDC" not in status.splitlines():
            raise BackupError("Archive did not pass authenticated decryption.")
        extract_archive(decrypted, work)
        manifest = verified_manifest(work)
        if (
            database.name == manifest["source_database"]
            or store.bucket == manifest["source_bucket"]
        ):
            raise BackupError("Source and restore targets must be separate.")
        database.verify_database()
        if database.scalar(EMPTY_DB) != "t" or store.inventory():
            raise BackupError("Refusing to restore into a nonempty target.")
        tool(
            [
                "pg_restore",
                "-w",
                "--dbname",
                database.name,
                "--single-transaction",
                "--no-owner",
                "--no-privileges",
                "--exit-on-error",
                str(work / "postgres.dump"),
            ],
            env=database.env(),
        )
        if database.schema() != manifest["schema_version"]:
            raise BackupError(
                "Restored database does not match the recorded Alembic head."
            )
        for entry in manifest["objects"]:
            with (work / entry["path"]).open("rb") as handle:
                store.client.put_object(
                    Bucket=store.bucket,
                    Key=entry["key"],
                    Body=handle,
                    ContentLength=entry["size"],
                    IfNoneMatch="*",
                )
        restored = store.inventory()
        if set(restored) != {entry["key"] for entry in manifest["objects"]}:
            raise BackupError("Restored bucket inventory does not match the archive.")
        for entry in manifest["objects"]:
            size, etag = restored[entry["key"]]
            if (
                size != entry["size"]
                or store.read(entry["key"], etag, size) != entry["sha256"]
            ):
                raise BackupError("Restored object contents do not match the archive.")
        verify_document_pair(database.available_documents(), manifest["objects"])
        print(
            json.dumps(
                {
                    "restore_id": target,
                    "snapshot_utc": manifest["snapshot_utc"],
                    "schema_version": manifest["schema_version"],
                    "release_sha": manifest["release_sha"],
                    "verified_objects": len(restored),
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                },
                sort_keys=True,
            )
        )


def prune(directory: Path, *, days: int, apply: bool) -> list[str]:
    """Return named expired bundles and remove them only when explicitly asked."""
    if not 1 <= days <= 3650:
        raise BackupError("Retention must be between 1 and 3650 days.")
    cutoff = time.time() - days * 86400
    expired = []
    retained = []
    for path in sorted(directory.iterdir()):
        if BUNDLE.fullmatch(path.name):
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                (expired if info.st_mtime < cutoff else retained).append(path)
    if apply and expired:
        if not retained:
            raise BackupError(
                "Refusing retention apply without a newer encrypted backup."
            )
        for path in expired:
            path.unlink()
    return [path.name for path in expired]


def main() -> int:
    """Run the selected operator command with a sanitized failure boundary."""
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("backup")
    create.add_argument("--prune", action="store_true")
    create.add_argument("--apply", action="store_true")
    recover = commands.add_parser("restore")
    recover.add_argument("--archive", required=True, type=Path)
    recover.add_argument("--sha256", required=True)
    args = parser.parse_args()
    try:
        if args.command == "restore":
            restore(
                args.archive,
                args.sha256,
                passphrase_file(Path(setting("BACKUP_PASSPHRASE_FILE"))),
            )
        else:
            directory = private_directory(Path(setting("BACKUP_DIRECTORY")))
            if args.apply and not args.prune:
                raise BackupError("--apply is only valid with --prune.")
            if args.prune:
                expired = prune(
                    directory,
                    days=int(os.environ.get("BACKUP_RETENTION_DAYS", "30")),
                    apply=args.apply,
                )
                print(
                    json.dumps(
                        {
                            "mode": "apply" if args.apply else "preview",
                            "expired": expired,
                        },
                        sort_keys=True,
                    )
                )
            else:
                capture(
                    directory, passphrase_file(Path(setting("BACKUP_PASSPHRASE_FILE")))
                )
    except BackupError as error:
        parser.exit(1, f"Backup operation refused. {error}\n")
    except Exception:  # noqa: BLE001 - external failures can contain credentials or protected object keys
        parser.exit(
            1,
            "Backup operation failed. Check local tooling and scoped access before retrying.\n",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
