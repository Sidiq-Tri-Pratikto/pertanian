"""Scanner, sniffing, extraction and storage adapters, without a database."""

import asyncio
import struct
import zipfile
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from app.core.settings import Settings
from app.documents.service.extraction import extract_text
from app.documents.service.scanner_service import (
    ClamAvScanner,
    DevelopmentAcceptScanner,
    ScannerUnavailableError,
    scanner_for,
)
from app.documents.service.sniff import DOCX, JPEG, PDF, PNG, WEBP, sniff
from app.documents.service.storage_service import LocalStorage, TooLargeError


async def fake_clamd(answer: bytes, received: list[bytes]) -> tuple[asyncio.Server, int]:
    """A clamd that reads one INSTREAM and answers."""

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        assert await reader.readexactly(10) == b"zINSTREAM\0"
        while size := struct.unpack(">I", await reader.readexactly(4))[0]:
            received.append(await reader.readexactly(size))
        writer.write(answer)
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


@pytest.mark.parametrize(("answer", "clean"), [(b"stream: OK\0", True), (b"stream: Eicar-Signature FOUND\0", False)])
async def test_clamav_streams_the_file_and_reads_the_verdict(tmp_path: Path, answer: bytes, clean: bool) -> None:
    """
    Condition:
    - clamd answers OK or FOUND.

    Expected:
    - The file is streamed with INSTREAM and the verdict is read.
    """
    path = tmp_path / "file"
    path.write_bytes(b"%PDF-1.4 content")
    received: list[bytes] = []
    server, port = await fake_clamd(answer, received)
    async with server:
        assert await ClamAvScanner("127.0.0.1", port).is_clean(path) is clean
    assert b"".join(received) == b"%PDF-1.4 content"


async def test_clamav_unreachable_or_unclear_keeps_the_file_in_quarantine(tmp_path: Path) -> None:
    """
    Condition:
    - clamd is down, or answers something unknown.

    Expected:
    - ``ScannerUnavailableError``, so the job retries and the file stays quarantined.
    """
    path = tmp_path / "file"
    path.write_bytes(b"x")
    with pytest.raises(ScannerUnavailableError):
        await ClamAvScanner("127.0.0.1", 1).is_clean(path)
    server, port = await fake_clamd(b"something else\0", [])
    async with server:
        with pytest.raises(ScannerUnavailableError):
            await ClamAvScanner("127.0.0.1", port).is_clean(path)


def test_configuration_picks_the_scanner() -> None:
    """
    Condition:
    - ``FILE_SCANNER`` is ``clamav`` or ``development-accept``.

    Expected:
    - The matching adapter.
    """
    base = {"database_url": "postgresql+asyncpg://a:b@localhost/c"}
    assert isinstance(scanner_for(Settings(**base, file_scanner="clamav")), ClamAvScanner)
    assert isinstance(scanner_for(Settings(**base)), DevelopmentAcceptScanner)


@pytest.mark.parametrize(
    ("head", "expected"),
    [
        (b"%PDF-1.7\n", PDF),
        (b"\x89PNG\r\n\x1a\n0000", PNG),
        (b"\xff\xd8\xff\xe0", JPEG),
        (b"RIFF\x00\x00\x00\x00WEBPVP8 ", WEBP),
        (b"MZ\x90\x00", None),
        (b"PK\x03\x04broken zip", None),
    ],
)
def test_types_come_from_bytes(tmp_path: Path, head: bytes, expected: str | None) -> None:
    """
    Condition:
    - Files with known and unknown signatures.

    Expected:
    - The media type from the bytes, or None.
    """
    path = tmp_path / "file"
    path.write_bytes(head)

    assert sniff(path) == expected


def test_a_zip_is_a_docx_only_with_a_word_document(tmp_path: Path) -> None:
    """
    Condition:
    - A zip without ``word/document.xml``, and a real DOCX.

    Expected:
    - Only the second is a DOCX; an unreadable DOCX fails extraction instead of inventing text.
    """
    plain, word = tmp_path / "plain.zip", tmp_path / "word.docx"
    with zipfile.ZipFile(plain, "w") as archive:
        archive.writestr("a.txt", "x")
    with zipfile.ZipFile(word, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<not xml")

    assert sniff(plain) is None
    assert sniff(word) == DOCX
    with pytest.raises(ValueError, match="unreadable DOCX"):
        extract_text(word, DOCX)


def test_images_and_broken_pdfs_never_yield_text(tmp_path: Path) -> None:
    """
    Condition:
    - An image, and a file that claims to be a PDF but is not.

    Expected:
    - No text for the image; a parse failure for the broken PDF.
    """
    image, broken = tmp_path / "a.png", tmp_path / "b.pdf"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    broken.write_bytes(b"%PDF-1.4 truncated")

    assert extract_text(image, PNG) is None
    with pytest.raises(ValueError, match="unreadable PDF"):
        extract_text(broken, PDF)


async def test_storage_stops_past_the_limit_and_reads_ranges(tmp_path: Path) -> None:
    """
    Condition:
    - A stream larger than allowed, then a normal one read back in ranges.

    Expected:
    - The oversized write leaves no file; ranges return the exact bytes.
    """
    storage = LocalStorage(str(tmp_path))

    async def chunks(data: bytes) -> AsyncIterator[bytes]:
        for start in range(0, len(data), 4):
            yield data[start : start + 4]

    with pytest.raises(TooLargeError):
        await storage.write("big", chunks(b"0123456789"), max_bytes=5)
    stored = await storage.write("ok", chunks(b"0123456789"), max_bytes=10)

    assert not (tmp_path / "big").exists()
    assert stored.size_bytes == 10
    assert b"".join([chunk async for chunk in storage.read("ok", 2, 5)]) == b"2345"
