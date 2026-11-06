"""Encoding, delimiter and records. Port of ``detectDelimiter`` (L605) and ``tokenize`` (L586)."""

import csv
import io

import pytest

from app.imports.model.models import StructuralError, StructuralReason
from app.imports.service.dialect import Record, detect_delimiter, has_bom, read_records, source_size


def _records(data: bytes, delimiter: str = ",") -> list[Record | StructuralError]:
    return list(read_records(io.BytesIO(data), delimiter))


def _lines_and_fields(data: bytes, delimiter: str = ",") -> list[tuple[int, list[str]]]:
    return [(record.file_line, record.fields) for record in _records(data, delimiter) if isinstance(record, Record)]


@pytest.mark.parametrize(
    ("data", "delimiter"),
    [
        (b"a,b\n1,2\n", ","),
        (b"a;b\n1;2\n", ";"),
        (b'"a,b";c\n', ";"),
        (b'"a;b",c\n', ","),
        (b"\n  \n\na,b\n", ","),
        (b"a;b\r1;2\r", ";"),
        (b"\xef\xbb\xbfa;b\n", ";"),
    ],
)
def test_delimiter_is_read_from_the_first_nonblank_line_outside_quotes(data: bytes, delimiter: str) -> None:
    """
    Condition:
    - A header with one delimiter outside quotes, after blank lines, a BOM or under a CR-only file.

    Expected:
    - That delimiter.
    """
    assert detect_delimiter(io.BytesIO(data)) == delimiter


@pytest.mark.parametrize(
    ("data", "reason", "message"),
    [
        (
            b"a,b;c\n",
            StructuralReason.DELIMITER_AMBIGUOUS,
            (
                "Pemisah kolom ambigu: header memakai koma dan titik koma. "
                'Gunakan salah satu, misalnya "timestamp;perangkat;energi_wh".'
            ),
        ),
        (
            b"abc\n1\n",
            StructuralReason.SINGLE_COLUMN,
            "Header hanya memiliki satu kolom. Pisahkan kolom dengan koma atau titik koma.",
        ),
        (
            b"",
            StructuralReason.EMPTY_INPUT,
            "Berkas atau tempelan kosong. Pilih berkas CSV atau tempel isi CSV.",
        ),
        (
            b" \n\t\r\n",
            StructuralReason.EMPTY_INPUT,
            "Berkas atau tempelan kosong. Pilih berkas CSV atau tempel isi CSV.",
        ),
        (
            b"\xef\xbb\xbf",
            StructuralReason.EMPTY_INPUT,
            "Berkas atau tempelan kosong. Pilih berkas CSV atau tempel isi CSV.",
        ),
        (
            b"a\x00,b\n",
            StructuralReason.NOT_UTF8,
            "Berkas bukan teks UTF-8. Simpan ulang sebagai CSV UTF-8 lalu coba lagi.",
        ),
        (
            b"caf\xe9,b\n",
            StructuralReason.NOT_UTF8,
            "Berkas bukan teks UTF-8. Simpan ulang sebagai CSV UTF-8 lalu coba lagi.",
        ),
    ],
)
def test_delimiter_failures_are_returned_with_their_message(
    data: bytes, reason: StructuralReason, message: str
) -> None:
    """
    Condition:
    - A first line that names no single delimiter, or a file with no readable text.

    Expected:
    - A structural error with the exact message, not an exception.
    """
    assert detect_delimiter(io.BytesIO(data)) == StructuralError(reason=reason, message=message)


def test_bom_before_a_quoted_header_is_removed() -> None:
    """
    Condition:
    - A BOM directly before a quoted first header.

    Expected:
    - The header reads ``waktu``, with neither the BOM nor literal quotes.
    """
    assert _lines_and_fields(b'\xef\xbb\xbf"waktu";alat\n', ";") == [(1, ["waktu", "alat"])]


@pytest.mark.parametrize(("data", "expected"), [(b"\xef\xbb\xbfa,b\n", True), (b"a,b\n", False), (b"", False)])
def test_has_bom_reports_the_marker(data: bytes, expected: bool) -> None:
    """
    Condition:
    - A file with or without a UTF-8 BOM.

    Expected:
    - The marker is reported.
    """
    assert has_bom(io.BytesIO(data)) is expected


@pytest.mark.parametrize(("data", "size"), [(b"", 0), (b"abc", 3)])
def test_source_size_is_read_without_decoding(data: bytes, size: int) -> None:
    """
    Condition:
    - A seekable source.

    Expected:
    - Its size in bytes.
    """
    assert source_size(io.BytesIO(data)) == size


def test_mixed_line_endings_count_one_line_each() -> None:
    """
    Condition:
    - ``\\r\\n``, ``\\r`` and ``\\n`` in one file.

    Expected:
    - File lines 1, 2 and 3.
    """
    assert _lines_and_fields(b"a,b\r\nc,d\re,f\n") == [(1, ["a", "b"]), (2, ["c", "d"]), (3, ["e", "f"])]


def test_record_line_is_where_the_record_starts() -> None:
    """
    Condition:
    - A quoted field spanning a ``\\n`` and a bare ``\\r``, followed by another record.

    Expected:
    - Each record reports its first physical line, and the bare ``\\r`` counts as a line (D9).
    """
    assert _lines_and_fields(b'a,b\n"x\ny\rz",1\nc,d\n') == [
        (1, ["a", "b"]),
        (2, ["x\ny\rz", "1"]),
        (5, ["c", "d"]),
    ]


@pytest.mark.parametrize(("line", "blank"), [(b"", True), (b"   ", True), (b'""', True), (b",,", False), (b"x", False)])
def test_blank_records_keep_numbering(line: bytes, blank: bool) -> None:
    """
    Condition:
    - A line between two records that may or may not be blank.

    Expected:
    - It yields a record with the right blank flag, and the next record's number still counts it.
    """
    records = _records(b"a,b\n" + line + b"\nc,d\n")
    assert [record.file_line for record in records] == [1, 2, 3]
    assert records[1].blank is blank
    assert records[2].blank is False


@pytest.mark.parametrize("data", [b"a,b\n", b"a,b"])
def test_no_trailing_record_after_the_final_line(data: bytes) -> None:
    """
    Condition:
    - A file with or without a final newline.

    Expected:
    - Exactly one record.
    """
    assert _lines_and_fields(data) == [(1, ["a", "b"])]


@pytest.mark.parametrize("separator", ["\x0b", "\x0c", "\x1c", "\x85", " "])
def test_only_real_line_endings_split_records(separator: str) -> None:
    """
    Condition:
    - A character inside a name that ``str.splitlines`` treats as a line end.

    Expected:
    - The name stays in one field on one line (D7).
    """
    assert _lines_and_fields(f"Mesin{separator}A,1\nB,2\n".encode()) == [
        (1, [f"Mesin{separator}A", "1"]),
        (2, ["B", "2"]),
    ]


def test_doubled_quotes_read_as_one_quote() -> None:
    """
    Condition:
    - A quoted name holding doubled quotes.

    Expected:
    - One literal quote each.
    """
    assert _lines_and_fields(b'"Mesin ""A""",1\n') == [(1, ['Mesin "A"', "1"])]


def test_unclosed_quote_fails_at_its_first_line() -> None:
    """
    Condition:
    - An unterminated quote that would otherwise swallow the rest of the file.

    Expected:
    - ``quote_unclosed`` naming the line it starts on, after the records before it.
    """
    assert _records(b'a,b\n"x,1\n2,3\n') == [
        Record(1, ["a", "b"]),
        StructuralError(
            reason=StructuralReason.QUOTE_UNCLOSED,
            message="Tanda kutip tidak ditutup mulai baris file 2.",
            file_line=2,
        ),
    ]


def test_oversize_unterminated_field_reports_the_same_failure() -> None:
    """
    Condition:
    - A 200,000-character unterminated field, which hits the csv field limit first.

    Expected:
    - The same ``quote_unclosed``, with no csv text in the message.
    """
    failure = _records(b'a,b\n"' + b"x" * 200_000)[-1]
    assert failure == StructuralError(
        reason=StructuralReason.QUOTE_UNCLOSED,
        message="Tanda kutip tidak ditutup mulai baris file 2.",
        file_line=2,
    )


def test_text_after_a_closing_quote_is_malformed() -> None:
    """
    Condition:
    - A closing quote followed by text before the delimiter.

    Expected:
    - ``quote_malformed`` with the line and the correction.
    """
    assert _records(b'a,b\n"x"y,1\n')[-1] == StructuralError(
        reason=StructuralReason.QUOTE_MALFORMED,
        message="Tanda kutip tidak valid pada baris file 2. Tutup tanda kutip tepat sebelum pemisah kolom.",
        file_line=2,
    )


@pytest.mark.parametrize(
    "data",
    [
        b"a,b\n" + b"1,2\n" * 5000 + b"caf\xe9,1\n",
        b"\xff\xfea\x00,\x00b\x00\n\x00",
        b"a,b\n" + b"1,2\n" * 5000 + b"x\x00y,1\n",
    ],
)
def test_undecodable_or_nul_text_is_not_utf8(data: bytes) -> None:
    """
    Condition:
    - Invalid UTF-8 deep in a file, a UTF-16 BOM, or a NUL character past the first chunk.

    Expected:
    - ``not_utf8`` as the last result, with no decoder text in it.
    """
    assert _records(data)[-1] == StructuralError(
        reason=StructuralReason.NOT_UTF8,
        message="Berkas bukan teks UTF-8. Simpan ulang sebagai CSV UTF-8 lalu coba lagi.",
    )


@pytest.mark.parametrize(
    "data", [b"a,b\n1,2\n", b'a,b\n"x,1\n', b"a,b\ncaf\xe9,1\n"], ids=["complete", "unclosed", "undecodable"]
)
def test_source_stays_open_and_a_second_pass_is_equal(data: bytes) -> None:
    """
    Condition:
    - Full passes over a good file and over two that fail.

    Expected:
    - The caller's source stays open, and a second pass gives equal results.
    """
    source = io.BytesIO(data)
    first = list(read_records(source, ","))
    second = list(read_records(source, ","))
    assert first == second
    assert not source.closed


def test_source_stays_open_after_closing_the_generator_early() -> None:
    """
    Condition:
    - A generator closed after one record.

    Expected:
    - The source stays open, and a later pass starts from the first line.
    """
    source = io.BytesIO(b"a,b\nc,d\n")
    records = read_records(source, ",")
    assert next(records) == Record(1, ["a", "b"])
    records.close()
    assert not source.closed
    assert next(read_records(source, ",")) == Record(1, ["a", "b"])


def test_delimiter_detection_leaves_the_source_open_and_changes_no_csv_limit() -> None:
    """
    Condition:
    - Delimiter detection and a pass that hits the field limit.

    Expected:
    - The source stays open, and the process-wide csv field limit is unchanged.
    """
    limit = csv.field_size_limit()
    source = io.BytesIO(b'a,b\n"' + b"x" * 200_000)
    detect_delimiter(source)
    list(read_records(source, ","))
    assert not source.closed
    assert csv.field_size_limit() == limit
