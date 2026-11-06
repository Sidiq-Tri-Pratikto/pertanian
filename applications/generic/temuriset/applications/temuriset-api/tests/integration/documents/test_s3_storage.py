"""Real provider integration for the disposable private S3 Compose network."""

from collections.abc import AsyncIterator
from uuid import uuid4

import anyio

from app.core.settings import get_settings
from app.documents.service.s3_storage_service import s3_storage
from app.documents.service.storage_service import CHUNK_BYTES, StorageUnavailableError, TooLargeError


async def _chunks(data: bytes) -> AsyncIterator[bytes]:
    for start in range(0, len(data), CHUNK_BYTES):
        yield data[start : start + CHUNK_BYTES]


async def _check_private_storage() -> None:
    settings = get_settings()
    assert settings.environment == "development"
    assert settings.storage_adapter == "s3"
    storage = s3_storage(settings)
    key = uuid4().hex
    content = b"s" * CHUNK_BYTES + b"fixture-end"

    async def absent() -> None:
        try:
            async for _chunk in storage.read(key):
                raise AssertionError("Disposable S3 test object is still readable.")
        except StorageUnavailableError:
            return
        raise AssertionError("A missing object unexpectedly returned a successful response.")

    try:
        try:
            await storage.write(key, _chunks(content), len(content) - 1)
        except TooLargeError:
            await absent()
        else:
            raise AssertionError("Oversized data was accepted.")
        stored = await storage.write(key, _chunks(content), len(content))
        assert stored.size_bytes == len(content)
        chunks = [chunk async for chunk in storage.read(key)]
        assert max(map(len, chunks)) <= CHUNK_BYTES and b"".join(chunks) == content
        assert b"".join([chunk async for chunk in storage.read(key, CHUNK_BYTES, CHUNK_BYTES + 6)]) == b"fixture"
        async with storage.materialize(key, len(content)) as path:
            assert path.read_bytes() == content
        assert not path.exists()
    finally:
        await storage.delete(key)
        await storage.delete(key)
    await absent()


if __name__ == "__main__":
    anyio.run(_check_private_storage)
