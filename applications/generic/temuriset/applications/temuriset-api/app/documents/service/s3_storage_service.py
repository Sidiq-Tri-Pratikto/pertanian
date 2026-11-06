"""Private S3-compatible document storage through the same gateway as local files."""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from functools import lru_cache, partial
from pathlib import Path
from typing import Any

import anyio
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.settings import Settings
from app.documents.service.storage_service import (
    CHUNK_BYTES,
    LocalStorage,
    StorageUnavailableError,
    StoredFile,
)


async def _provider[Result](call: Callable[..., Result], **kwargs: Any) -> Result:
    # The provider can include URLs, keys and credentials in exception details.
    try:
        return await anyio.to_thread.run_sync(partial(call, **kwargs))
    except (BotoCoreError, ClientError, OSError):
        raise StorageUnavailableError() from None


class S3Storage:
    """Spool each bounded upload to a private temporary file and stream reads in chunks."""

    def __init__(self, client: Any, bucket: str) -> None:
        """Use an explicitly selected private bucket."""
        self.client = client
        self.bucket = bucket

    async def check_bucket(self) -> None:
        """Check bucket access with the same scoped identity used by the gateway."""
        await _provider(self.client.head_bucket, Bucket=self.bucket)

    async def write(self, key: str, chunks: AsyncIterator[bytes], max_bytes: int) -> StoredFile:
        """Upload only after the stream has passed its size limit."""
        async with anyio.TemporaryDirectory() as directory:
            stored = await LocalStorage(directory).write(key, chunks, max_bytes)
            path = Path(directory) / key
            await _provider(self._put, key=key, path=path, size=stored.size_bytes)
            return stored

    def _put(self, key: str, path: Path, size: int) -> None:
        with path.open("rb") as handle:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=handle, ContentLength=size)

    async def read(self, key: str, start: int = 0, end: int | None = None) -> AsyncIterator[bytes]:
        """Read the selected range without returning the provider's URL or headers."""
        kwargs: dict[str, Any] = {"Bucket": self.bucket, "Key": key}
        if start or end is not None:
            kwargs["Range"] = f"bytes={start}-{end if end is not None else ''}"
        result = await _provider(self.client.get_object, **kwargs)
        body = result["Body"]
        try:
            while chunk := await _provider(body.read, amt=CHUNK_BYTES):
                yield chunk
        finally:
            with anyio.CancelScope(shield=True):
                await anyio.to_thread.run_sync(body.close)

    async def delete(self, key: str) -> None:
        """Delete the object. S3 treats deletion of an absent object as success."""
        await _provider(self.client.delete_object, Bucket=self.bucket, Key=key)

    @asynccontextmanager
    async def materialize(self, key: str, max_bytes: int) -> AsyncIterator[Path]:
        """Give scanners a bounded local copy and remove it when the caller leaves."""
        async with anyio.TemporaryDirectory() as directory:
            storage = LocalStorage(directory)
            await storage.write(key, self.read(key), max_bytes)
            yield storage.local_path(key)


@lru_cache(maxsize=4)
def _client(endpoint: str, region: str, access_key: str, secret_key: str) -> Any:
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            connect_timeout=3,
            read_timeout=10,
            retries={"total_max_attempts": 2, "mode": "standard"},
            s3={"addressing_style": "path"},
        ),
    )


def s3_storage(settings: Settings) -> S3Storage:
    """Build the adapter from the configuration validated at startup."""
    if not (settings.s3_endpoint_url and settings.s3_access_key and settings.s3_secret_key):
        raise StorageUnavailableError()
    return S3Storage(
        _client(
            settings.s3_endpoint_url.get_secret_value(),
            settings.s3_region,
            settings.s3_access_key.get_secret_value(),
            settings.s3_secret_key.get_secret_value(),
        ),
        settings.s3_bucket,
    )
