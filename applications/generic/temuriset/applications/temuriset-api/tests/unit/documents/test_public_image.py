"""Public photos lose every metadata block and keep their size (spec 051)."""

import struct

import pytest

from app.documents.service.public_image import UnreadableImageError, clean_image

SECRET = b"GPS -7.2575,112.7521 Surabaya home"


def _exif(orientation: int) -> bytes:
    tiff = b"II*\x00" + struct.pack("<I", 8) + struct.pack("<H", 1) + struct.pack("<HHIH", 0x0112, 3, 1, orientation)
    return b"Exif\x00\x00" + tiff + b"\x00\x00" + SECRET


def _jpeg(orientation: int = 6) -> bytes:
    app1 = _exif(orientation)
    sof = b"\x08" + struct.pack(">HH", 480, 640) + b"\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01"
    comment = b"taken at " + SECRET
    return (
        b"\xff\xd8"
        + b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        + b"\xff\xe1" + struct.pack(">H", 2 + len(app1)) + app1
        + b"\xff\xfe" + struct.pack(">H", 2 + len(comment)) + comment
        + b"\xff\xc0" + struct.pack(">H", 2 + len(sof)) + sof
        + b"\xff\xda" + struct.pack(">H", 8) + b"\x01\x01\x00\x00\x3f\x00" + b"\x12\x34image-data" + b"\xff\xd9"
    )  # fmt: skip


def _png_chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + b"\x00\x00\x00\x00"


def _png() -> bytes:
    ihdr = struct.pack(">II", 300, 200) + b"\x08\x02\x00\x00\x00"
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"tEXt", b"Location\x00" + SECRET)
        + _png_chunk(b"eXIf", _exif(1)[6:])
        + _png_chunk(b"IDAT", b"pixels")
        + _png_chunk(b"IEND", b"")
    )


def _webp_chunk(kind: bytes, body: bytes) -> bytes:
    return kind + struct.pack("<I", len(body)) + body + (b"\x00" if len(body) & 1 else b"")


def _webp() -> bytes:
    vp8x = bytes([0x0C, 0, 0, 0]) + (799).to_bytes(3, "little") + (599).to_bytes(3, "little")
    vp8l = bytes([0x2F]) + ((1023) | (767 << 14)).to_bytes(4, "little") + b"data"
    chunks = (
        _webp_chunk(b"VP8X", vp8x)
        + _webp_chunk(b"VP8L", vp8l)
        + _webp_chunk(b"EXIF", SECRET)
        + _webp_chunk(b"XMP ", SECRET)
    )
    return b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WEBP" + chunks


@pytest.mark.parametrize(
    ("data", "media_type", "size", "orientation"),
    [
        (_jpeg(), "image/jpeg", (640, 480), 6),
        (_png(), "image/png", (300, 200), 1),
        (_webp(), "image/webp", (800, 600), 1),
    ],
)
def test_metadata_is_gone_and_the_size_is_read(
    data: bytes, media_type: str, size: tuple[int, int], orientation: int
) -> None:
    """
    Condition:
    - A JPEG, PNG and WebP that each carry a fake location in their metadata blocks.

    Expected:
    - The location appears nowhere in the cleaned bytes; the media type, width, height and the JPEG's recorded
      orientation are kept, and the image data survives.
    """
    clean = clean_image(data)

    assert SECRET not in clean.data
    assert (clean.media_type, (clean.width, clean.height), clean.orientation) == (media_type, size, orientation)
    assert len(clean.data) < len(data)


def test_webp_header_no_longer_announces_the_dropped_chunks() -> None:
    """
    Condition:
    - A WebP whose extended header flags EXIF and XMP.

    Expected:
    - Both flags are cleared, and the RIFF size matches the new length.
    """
    clean = clean_image(_webp())

    assert clean.data[20] & 0x0C == 0
    assert struct.unpack_from("<I", clean.data, 4)[0] == len(clean.data) - 8


@pytest.mark.parametrize("data", [b"", b"GIF89a....", b"\xff\xd8\xff\xe1\x00", b"\x89PNG\r\n\x1a\n\x00\x00"])
def test_anything_else_is_refused(data: bytes) -> None:
    """
    Condition:
    - Empty, GIF, truncated JPEG and truncated PNG bytes.

    Expected:
    - ``UnreadableImageError``, never a half-cleaned image.
    """
    with pytest.raises(UnreadableImageError):
        clean_image(data)
