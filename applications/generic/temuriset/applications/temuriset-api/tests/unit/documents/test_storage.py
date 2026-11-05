"""Storage adapter contracts for a private object store."""

from collections.abc import AsyncIterator
from io import BytesIO

import pytest
from botocore.exceptions import EndpointConnectionError

from app.documents.service.s3_storage_service import S3Storage
from app.documents.service.storage_service import StorageUnavailableError, TooLargeError


class FakeS3:
    """An in-memory test endpoint that observes S3 requests."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.ranges: list[str] = []

    def put_object(self, *, Bucket: str, Key: str, Body: BytesIO, ContentLength: int) -> None:  # noqa: N803 - mirror the SDK keyword names
        """Record a private upload."""
        assert Bucket == "private"
        self.objects[Key] = Body.read(ContentLength)

    def get_object(self, *, Bucket: str, Key: str, Range: str | None = None) -> dict:  # noqa: N803 - mirror the SDK keyword names
        """Read only the requested byte range."""
        assert Bucket == "private"
        content = self.objects[Key]
        if Range:
            self.ranges.append(Range)
            first, last = Range.removeprefix("bytes=").split("-")
            content = content[int(first) : int(last) + 1 if last else None]

        class Body(BytesIO):
            def read(self, amt: int = -1) -> bytes:
                return super().read(amt)

        return {"Body": Body(content)}

    def delete_object(self, *, Bucket: str, Key: str) -> None:  # noqa: N803 - mirror the SDK keyword names
        """Simulate idempotent S3 deletion."""
        assert Bucket == "private"
        self.objects.pop(Key, None)


async def _chunks(data: bytes) -> AsyncIterator[bytes]:
    yield data


async def test_storage_bounds_uploads_and_ranges() -> None:
    """
    Condition:
    - One object fits the byte limit and another exceeds it.

    Expected:
    - Only the bounded object is stored and reads pass an exact range to the provider.
    """
    endpoint = FakeS3()
    storage = S3Storage(endpoint, "private")
    key = "a" * 32
    with pytest.raises(TooLargeError):
        await storage.write(key, _chunks(b"too long"), 2)
    assert not endpoint.objects
    assert (await storage.write(key, _chunks(b"abcdef"), 6)).size_bytes == 6
    assert b"".join([chunk async for chunk in storage.read(key, 1, 3)]) == b"bcd"
    assert endpoint.ranges == ["bytes=1-3"]
    async with storage.materialize(key, 6) as path:
        assert path.read_bytes() == b"abcdef"
    assert not path.exists()
    await storage.delete(key)
    await storage.delete(key)
    assert not endpoint.objects


async def test_provider_failure_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Condition:
    - The provider includes its endpoint in a connection error.

    Expected:
    - The adapter returns the registered failure without provider details.
    """
    endpoint = FakeS3()

    def fail(**_kwargs: object) -> None:
        raise EndpointConnectionError(endpoint_url="https://private-value.invalid")

    monkeypatch.setattr(endpoint, "get_object", fail)
    storage = S3Storage(endpoint, "private")
    with pytest.raises(StorageUnavailableError) as captured:
        _ = [chunk async for chunk in storage.read("a" * 32)]
    assert "private-value" not in str(captured.value)
    assert captured.value.__cause__ is None
