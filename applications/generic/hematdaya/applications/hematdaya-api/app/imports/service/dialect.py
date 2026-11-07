"""Reads the file: size, encoding, delimiter and records. The only place that sees csv and decode errors."""

import codecs
import csv
import io
import re
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from typing import BinaryIO, NamedTuple

from app.imports.model.models import StructuralError, StructuralReason

_QUOTED_TEXT = re.compile(r'"[^"]*"')
_UNCLOSED_QUOTE_ERRORS = ("unexpected end of data", "field larger than field limit")
_NOT_UTF8 = StructuralError(
    reason=StructuralReason.NOT_UTF8,
    message="Berkas bukan teks UTF-8. Simpan ulang sebagai CSV UTF-8 lalu coba lagi.",
)


class Record(NamedTuple):
    """One CSV record.

    Attributes:
        file_line (int): File line the record starts on, from 1.
        fields (list[str]): Its cells as written. Empty for an empty line.
        blank (bool): Whether the record holds at most one cell and that cell is whitespace.
    """

    file_line: int
    fields: list[str]

    @property
    def blank(self) -> bool:
        """Whether the record holds at most one cell and that cell is whitespace."""
        return not self.fields or (len(self.fields) == 1 and not self.fields[0].strip())


def source_size(source: BinaryIO) -> int:
    """Measure a source without decoding it.

    Args:
        source (BinaryIO): A seekable binary file.

    Returns:
        int: Its size in bytes.
    """
    return source.seek(0, io.SEEK_END)


def has_bom(source: BinaryIO) -> bool:
    """Tell whether a source starts with a UTF-8 BOM.

    Args:
        source (BinaryIO): A seekable binary file.

    Returns:
        bool: Whether the marker is there.
    """
    source.seek(0)
    return source.read(len(codecs.BOM_UTF8)) == codecs.BOM_UTF8


@contextmanager
def _decoded_lines(source: BinaryIO) -> Iterator[Iterable[str]]:
    # ``newline=""`` splits on \n, \r and \r\n only, where str.splitlines also splits on \x0b, \x85 and U+2028.
    source.seek(0)
    text = io.TextIOWrapper(source, encoding="utf-8-sig", newline="")
    try:
        yield _without_nul(text)
    finally:
        # Without this, garbage collection of the wrapper closes the caller's file.
        text.detach()


def _without_nul(lines: Iterable[str]) -> Iterator[str]:
    # Postgres text and JSONB reject NUL, so a file holding one must stop here. It is not text we can keep.
    for line in lines:
        if "\x00" in line:
            raise UnicodeDecodeError("utf-8", b"\x00", 0, 1, "NUL character")
        yield line


def detect_delimiter(source: BinaryIO) -> str | StructuralError:
    """Read the column separator from the first nonblank line, outside quotes.

    Args:
        source (BinaryIO): A seekable binary file.

    Returns:
        str | StructuralError: ``,`` or ``;``, or why neither can be chosen.
    """
    try:
        with _decoded_lines(source) as lines:
            first = next((line for line in lines if line.strip()), None)
    except UnicodeDecodeError:
        return _NOT_UTF8
    if first is None:
        return StructuralError(
            reason=StructuralReason.EMPTY_INPUT,
            message="Berkas atau tempelan kosong. Pilih berkas CSV atau tempel isi CSV.",
        )
    outside_quotes = _QUOTED_TEXT.sub("", first)
    has_comma, has_semicolon = "," in outside_quotes, ";" in outside_quotes
    if has_comma and has_semicolon:
        return StructuralError(
            reason=StructuralReason.DELIMITER_AMBIGUOUS,
            message=(
                "Pemisah kolom ambigu: header memakai koma dan titik koma. "
                'Gunakan salah satu, misalnya "timestamp;perangkat;energi_wh".'
            ),
        )
    if not has_comma and not has_semicolon:
        return StructuralError(
            reason=StructuralReason.SINGLE_COLUMN,
            message="Header hanya memiliki satu kolom. Pisahkan kolom dengan koma atau titik koma.",
        )
    return ";" if has_semicolon else ","


def _quote_failure(error: csv.Error, file_line: int) -> StructuralError:
    if str(error).startswith(_UNCLOSED_QUOTE_ERRORS):
        return StructuralError(
            reason=StructuralReason.QUOTE_UNCLOSED,
            message=f"Tanda kutip tidak ditutup mulai baris file {file_line}.",
            file_line=file_line,
        )
    return StructuralError(
        reason=StructuralReason.QUOTE_MALFORMED,
        message=f"Tanda kutip tidak valid pada baris file {file_line}. Tutup tanda kutip tepat sebelum pemisah kolom.",
        file_line=file_line,
    )


def read_records(source: BinaryIO, delimiter: str) -> Iterator[Record | StructuralError]:
    """Yield one record at a time from the start of the source, keeping none of them.

    Args:
        source (BinaryIO): A seekable binary file. It stays open.
        delimiter (str): The column separator.

    Yields:
        Record | StructuralError: Each record, then a failure as the last item if the file stops being readable.
    """
    next_line = 1
    try:
        with _decoded_lines(source) as lines:
            reader = csv.reader(lines, delimiter=delimiter, strict=True)
            for fields in reader:
                yield Record(next_line, fields)
                next_line = reader.line_num + 1
    except csv.Error as error:
        yield _quote_failure(error, next_line)
    except UnicodeDecodeError:
        yield _NOT_UTF8
