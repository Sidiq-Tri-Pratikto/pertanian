"""Text reading. Nothing is executed and nothing is invented: a scan without text needs a person."""

import zipfile
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.documents.service.sniff import DOCX, PDF

_WORD_TEXT = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
_MAX_PAGES = 200


def extract_text(path: Path, media_type: str) -> str | None:
    """Read the text of a PDF or DOCX.

    Args:
        path (Path): The stored file.
        media_type (str): Its sniffed media type.

    Returns:
        str | None: The text, or None when the file has no machine-readable text (images, scans).

    Raises:
        ValueError: When the file cannot be parsed.
    """
    if media_type == PDF:
        try:
            reader = PdfReader(str(path))
            text = "\n".join((page.extract_text() or "") for page in reader.pages[:_MAX_PAGES])
        except (PdfReadError, OSError) as error:
            raise ValueError("unreadable PDF") from error
    elif media_type == DOCX:
        try:
            with zipfile.ZipFile(path) as archive:
                # ElementTree does not resolve external entities, so the document cannot reach outside itself.
                root = ElementTree.fromstring(archive.read("word/document.xml"))
        except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as error:
            raise ValueError("unreadable DOCX") from error
        text = " ".join(node.text or "" for node in root.iter(_WORD_TEXT))
    else:
        return None
    return text.strip() or None
