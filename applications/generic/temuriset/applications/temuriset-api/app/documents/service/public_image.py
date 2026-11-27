"""Public photos without their metadata: no location, camera or text tags ever reach a visitor (spec 051).

A stdlib walker over the container formats the upload check already allows (JPEG, PNG, WebP). It copies the image
data unchanged and drops the segments and chunks that carry metadata, and it reads the real width and height so the
page can reserve the space. Phones record rotation in the same EXIF block, so the orientation is returned before
the block is dropped and the page applies it.
"""

import struct
from dataclasses import dataclass


class UnreadableImageError(ValueError):
    """The bytes are not a well-formed JPEG, PNG or WebP."""


@dataclass(frozen=True)
class CleanImage:
    """A photo safe to publish.

    Attributes:
        data (bytes): The image without metadata.
        media_type (str): ``image/jpeg``, ``image/png`` or ``image/webp``.
        width (int): Pixel width as stored.
        height (int): Pixel height as stored.
        orientation (int): EXIF orientation 1 to 8; 1 when none was recorded.
    """

    data: bytes
    media_type: str
    width: int
    height: int
    orientation: int = 1


# JPEG markers that carry metadata: APP1 (EXIF, XMP), APP12 (Ducky), APP13 (IPTC/Photoshop), COM (comments).
_JPEG_DROP = {0xE1, 0xEC, 0xED, 0xFE}
_JPEG_SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_DROP = {b"eXIf", b"tEXt", b"iTXt", b"zTXt", b"tIME"}
_WEBP_DROP = {b"EXIF", b"XMP "}


def _exif_orientation(payload: bytes) -> int:
    """Read tag 0x0112 from an ``Exif\\0\\0`` APP1 payload; 1 when absent or malformed."""
    if not payload.startswith(b"Exif\x00\x00"):
        return 1
    tiff = payload[6:]
    if tiff[:2] not in (b"II", b"MM"):
        return 1
    order = "<" if tiff[:2] == b"II" else ">"
    try:
        (offset,) = struct.unpack_from(f"{order}I", tiff, 4)
        (count,) = struct.unpack_from(f"{order}H", tiff, offset)
        for index in range(count):
            tag, _kind, _count, value = struct.unpack_from(f"{order}HHIH", tiff, offset + 2 + index * 12)
            if tag == 0x0112:
                return value if 1 <= value <= 8 else 1
    except struct.error:
        return 1
    return 1


def _clean_jpeg(data: bytes) -> CleanImage:
    out = bytearray(b"\xff\xd8")
    position, width, height, orientation = 2, 0, 0, 1
    while position < len(data):
        if data[position] != 0xFF:
            raise UnreadableImageError("expected a JPEG marker")
        marker = data[position + 1]
        if marker == 0xFF:  # fill byte
            position += 1
            continue
        if marker == 0xDA:  # start of scan: the rest is image data
            out += data[position:]
            break
        if 0xD0 <= marker <= 0xD9 or marker == 0x01:
            out += data[position : position + 2]
            position += 2
            continue
        (length,) = struct.unpack_from(">H", data, position + 2)
        segment = data[position : position + 2 + length]
        if len(segment) < 2 + length:
            raise UnreadableImageError("truncated JPEG segment")
        if marker in _JPEG_SOF:
            height, width = struct.unpack_from(">HH", segment, 5)
        if marker == 0xE1:
            orientation = max(orientation, _exif_orientation(segment[4:]))
        if marker not in _JPEG_DROP:
            out += segment
        position += 2 + length
    if not width or not height:
        raise UnreadableImageError("no JPEG frame size")
    return CleanImage(bytes(out), "image/jpeg", width, height, orientation)


def _clean_png(data: bytes) -> CleanImage:
    out = bytearray(_PNG_SIGNATURE)
    position, width, height = 8, 0, 0
    while position < len(data):
        (length,) = struct.unpack_from(">I", data, position)
        kind = data[position + 4 : position + 8]
        chunk = data[position : position + 12 + length]
        if len(chunk) < 12 + length:
            raise UnreadableImageError("truncated PNG chunk")
        if kind == b"IHDR":
            width, height = struct.unpack_from(">II", chunk, 8)
        if kind not in _PNG_DROP:
            out += chunk
        position += 12 + length
        if kind == b"IEND":
            break
    if not width or not height:
        raise UnreadableImageError("no PNG header")
    return CleanImage(bytes(out), "image/png", width, height)


def _webp_size(kind: bytes, body: bytes) -> tuple[int, int] | None:
    if kind == b"VP8X" and len(body) >= 10:
        width = int.from_bytes(body[4:7], "little") + 1
        height = int.from_bytes(body[7:10], "little") + 1
        return width, height
    if kind == b"VP8L" and len(body) >= 5 and body[0] == 0x2F:
        bits = int.from_bytes(body[1:5], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if kind == b"VP8 " and len(body) >= 10 and body[3:6] == b"\x9d\x01\x2a":
        width, height = struct.unpack_from("<HH", body, 6)
        return width & 0x3FFF, height & 0x3FFF
    return None


def _clean_webp(data: bytes) -> CleanImage:
    chunks = bytearray()
    position, size = 12, None
    while position + 8 <= len(data):
        kind = data[position : position + 4]
        (length,) = struct.unpack_from("<I", data, position + 4)
        body = data[position + 8 : position + 8 + length]
        if len(body) < length:
            raise UnreadableImageError("truncated WebP chunk")
        padded = length + (length & 1)
        if size is None:
            size = _webp_size(kind, body)
        if kind == b"VP8X":
            # The extended header announces EXIF (bit 3) and XMP (bit 2); both chunks are dropped below.
            body = bytes([body[0] & ~0x0C]) + body[1:]
        if kind not in _WEBP_DROP:
            chunks += kind + struct.pack("<I", length) + body + (b"\x00" if length & 1 else b"")
        position += 8 + padded
    if size is None:
        raise UnreadableImageError("no WebP frame size")
    out = b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WEBP" + bytes(chunks)
    return CleanImage(out, "image/webp", size[0], size[1])


def clean_image(data: bytes) -> CleanImage:
    """Strip metadata from a JPEG, PNG or WebP and read its size.

    Args:
        data (bytes): The stored file.

    Returns:
        CleanImage: The image without metadata, its media type, size and orientation.

    Raises:
        UnreadableImageError: When the bytes are none of the three formats or are malformed.
    """
    try:
        if data.startswith(b"\xff\xd8"):
            return _clean_jpeg(data)
        if data.startswith(_PNG_SIGNATURE):
            return _clean_png(data)
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return _clean_webp(data)
    except (struct.error, IndexError) as error:
        raise UnreadableImageError("malformed image") from error
    raise UnreadableImageError("not a JPEG, PNG or WebP image")
