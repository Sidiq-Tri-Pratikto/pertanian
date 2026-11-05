"""File types from bytes, never from the client's word or the extension."""

import zipfile
from pathlib import Path

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PNG, JPEG, WEBP = "image/png", "image/jpeg", "image/webp"

MB = 1024 * 1024
# Announced before upload (FR-003): documents up to 20 MB, images up to 5 MB.
LIMITS = {PDF: 20 * MB, DOCX: 20 * MB, PNG: 5 * MB, JPEG: 5 * MB, WEBP: 5 * MB}
LIMIT_TEXT = {
    PDF: "20 MB untuk PDF dan DOCX",
    DOCX: "20 MB untuk PDF dan DOCX",
    PNG: "5 MB untuk gambar",
    JPEG: "5 MB untuk gambar",
    WEBP: "5 MB untuk gambar",
}


def sniff(path: Path) -> str | None:
    """Recognize a stored file by its signature.

    A DOCX is a zip holding ``[Content_Types].xml`` and ``word/document.xml``; any other zip is not a DOCX.

    Args:
        path (Path): The stored file.

    Returns:
        str | None: The media type, or None for anything unsupported.
    """
    with path.open("rb") as handle:
        head = handle.read(16)
    if head.startswith(b"%PDF-"):
        return PDF
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return PNG
    if head.startswith(b"\xff\xd8\xff"):
        return JPEG
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return WEBP
    if head.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
        except zipfile.BadZipFile:
            return None
        return DOCX if {"[Content_Types].xml", "word/document.xml"} <= names else None
    return None
