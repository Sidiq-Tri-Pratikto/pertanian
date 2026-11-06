"""Where bytes live. No adapter ever hands a client a storage URL; the gateway streams every download."""

import hashlib
import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Protocol

import anyio

CHUNK_BYTES = 64 * 1024


class StoredFile:
    """What a completed write produced."""

    def __init__(self, size_bytes: int, sha256: str) -> None:
        """Hold the result.

        Args:
            size_bytes (int): Bytes written.
            sha256 (str): Hex digest.
        """
        self.size_bytes = size_bytes
        self.sha256 = sha256


class TooLargeError(Exception):
    """The stream went past the allowed size; nothing was kept."""


class StorageAdapter(Protocol):
    """Stores and streams file bytes by generated key."""

    async def write(self, key: str, chunks: AsyncIterator[bytes], max_bytes: int) -> StoredFile:
        """Store a stream, stopping past ``max_bytes``."""
        ...

    async def read(self, key: str, start: int = 0, end: int | None = None) -> AsyncIterator[bytes]:
        """Stream bytes ``start`` to ``end`` inclusive."""
        ...

    async def delete(self, key: str) -> None:
        """Erase the bytes for a generated key, allowing an already completed erase to retry."""
        ...

    def local_path(self, key: str) -> Path:
        """A path the worker may open for scanning and extraction."""
        ...


class LocalStorage:
    """Files in a private folder, written and read in chunks so a 20 MB file never sits in memory."""

    def __init__(self, root: str) -> None:
        """Use a folder.

        Args:
            root (str): The folder; created when missing.
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def local_path(self, key: str) -> Path:
        """Return the file path for a key.

        Args:
            key (str): A generated key; never a client value.

        Returns:
            Path: The path.
        """
        return self.root / key

    async def write(self, key: str, chunks: AsyncIterator[bytes], max_bytes: int) -> StoredFile:
        """Write a stream to a new file, hashing as it goes.

        Args:
            key (str): Generated storage key.
            chunks (AsyncIterator[bytes]): The body.
            max_bytes (int): Hard limit.

        Returns:
            StoredFile: Size and checksum.

        Raises:
            TooLargeError: Past ``max_bytes``; the partial file is removed.
        """
        path = self.local_path(key)
        digest, size = hashlib.sha256(), 0
        handle = await anyio.open_file(path, "wb")
        try:
            async for chunk in chunks:
                size += len(chunk)
                if size > max_bytes:
                    raise TooLargeError()
                digest.update(chunk)
                await handle.write(chunk)
        except BaseException:
            await handle.aclose()
            path.unlink(missing_ok=True)
            raise
        await handle.aclose()
        return StoredFile(size, digest.hexdigest())

    async def delete(self, key: str) -> None:
        """Erase the bytes asynchronously. An absent file is already erased."""
        await anyio.Path(self.local_path(key)).unlink(missing_ok=True)

    async def read(self, key: str, start: int = 0, end: int | None = None) -> AsyncIterator[bytes]:
        """Stream a byte range of a stored file.

        Args:
            key (str): Storage key.
            start (int, optional): First byte. Defaults to 0.
            end (int | None, optional): Last byte, inclusive. Defaults to the end of the file.

        Yields:
            bytes: Chunks of at most 64 KiB.
        """
        path = self.local_path(key)
        remaining = (end if end is not None else os.path.getsize(path) - 1) - start + 1
        async with await anyio.open_file(path, "rb") as handle:
            await handle.seek(start)
            while remaining > 0:
                chunk = await handle.read(min(CHUNK_BYTES, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk
