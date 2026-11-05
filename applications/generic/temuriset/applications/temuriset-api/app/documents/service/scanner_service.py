"""Malware scanning port. Configuration refuses the development scanner outside development (spec 004)."""

import asyncio
import struct
from pathlib import Path
from typing import Protocol

from app.core.settings import Settings

CHUNK_BYTES = 64 * 1024
_TIMEOUT_SECONDS = 60


class ScannerUnavailableError(Exception):
    """The scanner could not be reached; the job retries later and the file stays in quarantine."""


class ScannerAdapter(Protocol):
    """Decides whether stored bytes are safe to offer."""

    async def is_clean(self, path: Path) -> bool:
        """Return True when nothing malicious was found."""
        ...


class DevelopmentAcceptScanner:
    """Accepts every file that passed the format checks. Development only."""

    async def is_clean(self, path: Path) -> bool:
        """Accept.

        Args:
            path (Path): The file.

        Returns:
            bool: True.
        """
        return True


class ClamAvScanner:
    """Streams the file to clamd with INSTREAM; the file is never opened by anything that executes it."""

    def __init__(self, host: str, port: int) -> None:
        """Point at a clamd daemon.

        Args:
            host (str): Host.
            port (int): Port.
        """
        self.host = host
        self.port = port

    async def is_clean(self, path: Path) -> bool:
        """Scan a file.

        Args:
            path (Path): The file.

        Returns:
            bool: True for ``stream: OK``.

        Raises:
            ScannerUnavailableError: When clamd cannot be reached or answers nothing usable.
        """
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(self.host, self.port), _TIMEOUT_SECONDS)
        except (OSError, TimeoutError) as error:
            raise ScannerUnavailableError() from error
        try:
            writer.write(b"zINSTREAM\0")
            with path.open("rb") as handle:
                while chunk := handle.read(CHUNK_BYTES):
                    writer.write(struct.pack(">I", len(chunk)) + chunk)
                    await writer.drain()
            writer.write(struct.pack(">I", 0))
            await writer.drain()
            answer = await asyncio.wait_for(reader.read(1024), _TIMEOUT_SECONDS)
        except (OSError, TimeoutError) as error:
            raise ScannerUnavailableError() from error
        finally:
            writer.close()
        text = answer.rstrip(b"\0").decode(errors="replace")
        if text.endswith("OK"):
            return True
        if text.endswith("FOUND"):
            return False
        raise ScannerUnavailableError()


def scanner_for(settings: Settings) -> ScannerAdapter:
    """Return the configured scanner.

    Args:
        settings (Settings): Settings.

    Returns:
        ScannerAdapter: The scanner.
    """
    if settings.file_scanner == "clamav":
        return ClamAvScanner(settings.clamav_host, settings.clamav_port)
    return DevelopmentAcceptScanner()
