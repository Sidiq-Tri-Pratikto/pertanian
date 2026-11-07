"""The preview service's pure helpers: display names and error cursors."""

import base64

import pytest

from app.core.errors.base import RequestInvalidError
from app.imports.service.preview import clean_file_name, decode_error_cursor, encode_error_cursor


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("data.csv", "data.csv"),
        ("../../rahasia/data.csv", "data.csv"),
        ("C:\\berkas\\data.csv", "data.csv"),
        ("da\x00ta\x1f\x7f.csv", "data.csv"),
        ("  data.csv  ", "data.csv"),
        ("x" * 300, "x" * 255),
        ("", "tempelan.csv"),
        ("folder/", "tempelan.csv"),
        ("\x01\x02", "tempelan.csv"),
        (None, "tempelan.csv"),
    ],
    ids=[
        "plain",
        "posix_path",
        "windows_path",
        "control",
        "spaces",
        "too_long",
        "empty",
        "only_path",
        "only_control",
        "none",
    ],
)
def test_file_name_becomes_safe_display_text(name: str | None, expected: str) -> None:
    """
    Condition:
    - D23: an upload's name, which a client controls.

    Expected:
    - Its last path segment with no control character, at most 255 long, or the paste name when nothing remains.
    """
    assert clean_file_name(name) == expected


def test_error_cursor_round_trips() -> None:
    """
    Condition:
    - A page's last data row.

    Expected:
    - Its cursor decodes back to that row.
    """
    assert decode_error_cursor(encode_error_cursor(150_000)) == 150_000


@pytest.mark.parametrize("value", [b"0", b"-1", b"150001", b"99999999999", b"x"], ids=str)
def test_error_cursor_outside_the_row_range_is_refused(value: bytes) -> None:
    """
    Condition:
    - A well-formed cursor no page could have issued, including one too big for the database's integer.

    Expected:
    - The request error, instead of a database failure.
    """
    with pytest.raises(RequestInvalidError):
        decode_error_cursor(base64.urlsafe_b64encode(value).decode())
