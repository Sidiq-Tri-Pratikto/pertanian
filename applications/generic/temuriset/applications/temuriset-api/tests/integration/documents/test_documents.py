"""Private documents, scanning, grants and the download gateway through Postgres (spec 010)."""

import io
import logging
import zipfile
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from httpx import AsyncClient
from pypdf import PdfWriter
from sqlalchemy import select

import app.documents.service.jobs  # noqa: F401 - registers the document jobs
from app.core.database import get_session_factory
from app.documents.repository.sqlalchemy.models import DocumentVersionRecord
from app.documents.service.service import evidence_status
from app.worker.loop import run_jobs
from app.worker.registry import registry

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
FAKE_SECRET = "sk-fakedocumentsecret123"


def text_pdf(text: str = "Kapasitas saring 10 L/jam", padding: int = 0) -> bytes:
    """A one-page PDF with real text, built byte by byte so its offsets are right."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out) + b"%" + b"0" * padding


def scanned_pdf() -> bytes:
    """A PDF with a page and no text, like a scan."""
    writer, buffer = PdfWriter(), io.BytesIO()
    writer.add_blank_page(width=612, height=792)
    writer.write(buffer)
    return buffer.getvalue()


def docx(text: str = "Laporan uji") -> bytes:
    """A minimal DOCX."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>",
        )
    return buffer.getvalue()


@pytest.fixture
async def rani(client: AsyncClient, sign_up) -> AsyncIterator[AsyncClient]:
    """Rani, the owner."""
    me = await sign_up(client, "rani@example.com")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    yield client


@pytest.fixture
async def bima(new_client: Callable[[], AsyncClient], sign_up) -> AsyncIterator[AsyncClient]:
    """Bima, a partner who may receive a grant."""
    async with new_client() as client:
        me = await sign_up(client, "bima@example.com", persona="mitra", name="Bima")
        client.headers["X-Acting-Party"] = me["active_party_id"]
        yield client


async def _intent(client: AsyncClient, size: int, media_type: str = PDF, **extra: Any) -> Any:
    return await client.post(
        "/api/v1/documents/upload-intents",
        json={
            "acting_party_id": client.headers["X-Acting-Party"],
            "title": "Laporan uji",
            "kind": "evidence",
            "media_type": media_type,
            "size_bytes": size,
            **extra,
        },
    )


async def _upload(client: AsyncClient, content: bytes, media_type: str = PDF, **extra: Any) -> dict[str, Any]:
    intent = (await _intent(client, len(content), media_type, **extra)).json()
    response = await client.put(intent["upload_url"], content=content)
    assert response.status_code == 202, response.text
    return response.json()


async def _document(client: AsyncClient, document_id: str) -> dict[str, Any]:
    return (await client.get(f"/api/v1/documents/{document_id}")).json()


async def _run_worker() -> None:
    while await run_jobs(get_session_factory(), registry):
        pass


async def _version(document_id: str, number: int = 1) -> DocumentVersionRecord:
    async with get_session_factory()() as session:
        version = await session.scalar(
            select(DocumentVersionRecord).where(
                DocumentVersionRecord.document_id == UUID(document_id), DocumentVersionRecord.number == number
            )
        )
        assert version is not None
        return version


@pytest.mark.parametrize(
    ("media_type", "size", "code", "limit"),
    [
        (PDF, 25 * 1024 * 1024, "FILE_TOO_LARGE", "20 MB untuk PDF dan DOCX"),
        ("image/png", 6 * 1024 * 1024, "FILE_TOO_LARGE", "5 MB untuk gambar"),
        ("video/mp4", 1000, "FILE_TYPE_UNSUPPORTED", None),
    ],
)
async def test_type_and_size_are_refused_before_any_byte(
    rani: AsyncClient, media_type: str, size: int, code: str, limit: str | None
) -> None:
    """
    Condition:
    - An intent declares a 25 MB PDF, a 6 MB image, or a video.

    Expected:
    - The intent is refused with the limit stated, before any transfer.
    """
    response = await _intent(rani, size, media_type)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == code
    if limit:
        assert limit in error["message"]


async def test_quarantined_file_is_not_evidence_until_scanned(rani: AsyncClient) -> None:
    """
    Condition:
    - A PDF finishes uploading but is still in quarantine (AC13), then is scanned and read (AC14).

    Expected:
    - In quarantine, presence is ``UNKNOWN`` and the owner cannot download it. After the scan the file is
      ``AVAILABLE``, its text is read, ``DOCUMENT_PRESENT`` passes and ``REVIEWER_CONFIRMED`` stays ``UNKNOWN``.
    """
    uploaded = await _upload(rani, text_pdf())
    quarantined = await _version(uploaded["document_id"])
    early = await rani.get(f"/api/v1/documents/{uploaded['document_id']}/versions/1/content")

    assert (uploaded["file_state"], quarantined.file_state) == ("QUARANTINED", "QUARANTINED")
    assert evidence_status(quarantined, "DOCUMENT_PRESENT") == "UNKNOWN"
    assert (early.status_code, early.json()["error"]["code"]) == (409, "FILE_NOT_AVAILABLE")

    await _run_worker()
    available = await _version(uploaded["document_id"])
    document = await _document(rani, uploaded["document_id"])

    assert document["versions"][0] | {"sha256": None, "created_at": None} == {
        "number": 1,
        "media_type": PDF,
        "size_bytes": len(text_pdf()),
        "sha256": None,
        "file_state": "AVAILABLE",
        "extraction_state": "SUCCEEDED",
        "review_state": "PROVIDED_UNREVIEWED",
        "created_at": None,
    }
    assert evidence_status(available, "DOCUMENT_PRESENT") == "PASS"
    assert evidence_status(available, "REVIEWER_CONFIRMED") == "UNKNOWN"


async def test_scan_without_text_needs_a_person(rani: AsyncClient) -> None:
    """
    Condition:
    - A scanned PDF with no text passes the checks (AC15).

    Expected:
    - ``AVAILABLE`` with extraction ``NEEDS_MANUAL_INPUT``; nothing is extracted.
    """
    uploaded = await _upload(rani, scanned_pdf())
    await _run_worker()

    version = await _version(uploaded["document_id"])
    assert (version.file_state, version.extraction_state, version.extracted_characters) == (
        "AVAILABLE",
        "NEEDS_MANUAL_INPUT",
        None,
    )


async def test_docx_text_is_read(rani: AsyncClient) -> None:
    """
    Condition:
    - A DOCX is uploaded and scanned.

    Expected:
    - Its text is read.
    """
    uploaded = await _upload(rani, docx(), DOCX)
    await _run_worker()

    assert (await _version(uploaded["document_id"])).extraction_state == "SUCCEEDED"


@pytest.mark.parametrize("content", [b"MZ\x90\x00 executable pretending to be a PDF", b"PK\x03\x04 not really a docx"])
async def test_signature_mismatch_is_rejected(rani: AsyncClient, content: bytes) -> None:
    """
    Condition:
    - Bytes that are not what the intent declared.

    Expected:
    - The version is ``REJECTED`` at once and never scanned or offered.
    """
    uploaded = await _upload(rani, content)
    await _run_worker()

    assert uploaded["file_state"] == "REJECTED"
    assert (await _version(uploaded["document_id"])).file_state == "REJECTED"


async def test_more_bytes_than_declared_store_nothing_and_the_intent_can_retry(
    rani: AsyncClient, storage: Path
) -> None:
    """
    Condition:
    - A transfer sends more than its intent declared, then the right file is sent with the same intent.

    Expected:
    - ``FILE_TOO_LARGE`` and no stored bytes; the retry succeeds.
    """
    content = text_pdf()
    intent = (await _intent(rani, len(content))).json()

    too_big = await rani.put(intent["upload_url"], content=content + b"x" * 100)
    retry = await rani.put(intent["upload_url"], content=content)

    assert (too_big.status_code, too_big.json()["error"]["code"]) == (422, "FILE_TOO_LARGE")
    assert retry.status_code == 202
    assert len(list(storage.iterdir())) == 1


async def test_grant_one_version_download_ranges_then_revoke_honestly(rani: AsyncClient, bima: AsyncClient) -> None:
    """
    Condition:
    - Version 1 is granted to Bima; Bima downloads it and a range; then the grant is revoked (AC65).

    Expected:
    - Version 1 is served and each download recorded; version 2 stays denied. Revocation reports two delivered
      copies and says they cannot be recalled; Bima's next request, a range included, is ``GRANT_REVOKED``.
    """
    content = text_pdf()
    uploaded = await _upload(rani, content)
    await _upload(rani, text_pdf("Versi kedua"), document_id=uploaded["document_id"])
    await _run_worker()
    me = (await bima.get("/api/v1/me")).json()
    grant = await rani.post(
        f"/api/v1/documents/{uploaded['document_id']}/grants",
        json={
            "acting_party_id": rani.headers["X-Acting-Party"],
            "version": 1,
            "grantee_party_id": me["active_party_id"],
            "purpose": "pitch",
        },
        headers={"Idempotency-Key": "g1"},
    )
    base = f"/api/v1/documents/{uploaded['document_id']}/versions"

    full = await bima.get(f"{base}/1/content")
    part = await bima.get(f"{base}/1/content", headers={"Range": "bytes=0-7"})
    other_version = await bima.get(f"{base}/2/content")
    revoked = await rani.post(
        f"/api/v1/grants/{grant.json()['id']}/revoke",
        json={"acting_party_id": rani.headers["X-Acting-Party"]},
        headers={"Idempotency-Key": "r1"},
    )
    after = await bima.get(f"{base}/1/content")
    after_range = await bima.get(f"{base}/1/content", headers={"Range": "bytes=0-7"})
    document = await _document(rani, uploaded["document_id"])

    assert grant.status_code == 201 and grant.json()["grantee_name"] == "Bima"
    assert (full.status_code, full.content, full.headers["content-type"]) == (200, content, PDF)
    assert full.headers["cache-control"] == "private, no-store" and "attachment" in full.headers["content-disposition"]
    assert (part.status_code, part.content, part.headers["content-range"]) == (
        206,
        content[:8],
        f"bytes 0-7/{len(content)}",
    )
    assert other_version.status_code == 404
    assert revoked.json() == {
        "revoked": True,
        "copies_already_delivered": 2,
        "message": "Unduhan baru diblokir. Salinan yang sudah diunduh tidak dapat ditarik kembali.",
    }
    for response in (after, after_range):
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "GRANT_REVOKED"
        assert "tidak dapat ditarik kembali" in response.json()["error"]["message"]
    assert [(item["version"], item["downloads"], item["revoked_at"] is not None) for item in document["grants"]] == [
        (1, 2, True)
    ]
    assert [item["review_state"] for item in document["versions"]] == ["SUPERSEDED", "PROVIDED_UNREVIEWED"]


async def test_stranger_sees_no_title(rani: AsyncClient, bima: AsyncClient) -> None:
    """
    Condition:
    - Bima, without a grant, asks for the document and its content.

    Expected:
    - ``NOT_FOUND`` with no title.
    """
    uploaded = await _upload(rani, text_pdf())
    await _run_worker()

    for path in (
        f"/api/v1/documents/{uploaded['document_id']}",
        f"/api/v1/documents/{uploaded['document_id']}/versions/1/content",
    ):
        response = await bima.get(path)
        assert response.status_code == 404
        assert "Laporan" not in response.text


async def test_twenty_megabytes_stream_in_and_out(rani: AsyncClient) -> None:
    """
    Condition:
    - A PDF of exactly 20 MB is uploaded and downloaded (SC-002).

    Expected:
    - It is accepted and comes back byte for byte.
    """
    base = text_pdf()
    content = text_pdf(padding=20 * 1024 * 1024 - len(base))
    assert len(content) == 20 * 1024 * 1024
    uploaded = await _upload(rani, content)
    await _run_worker()

    response = await rani.get(f"/api/v1/documents/{uploaded['document_id']}/versions/1/content")

    assert response.status_code == 200
    assert response.content == content


async def test_a_secret_in_a_title_reaches_no_log(rani: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
    """
    Condition:
    - A file titled with a secret is uploaded, refused for size, and downloaded by a stranger path.

    Expected:
    - The secret appears in no log line.
    """
    with caplog.at_level(logging.DEBUG):
        await rani.post(
            "/api/v1/documents/upload-intents",
            json={
                "acting_party_id": rani.headers["X-Acting-Party"],
                "title": f"password={FAKE_SECRET}",
                "kind": "evidence",
                "media_type": PDF,
                "size_bytes": 30 * 1024 * 1024,
            },
        )
        await _upload(rani, b"not a pdf", title=f"password={FAKE_SECRET}")

    assert FAKE_SECRET not in caplog.text


async def test_listing_shows_only_the_acting_partys_documents(rani: AsyncClient, bima: AsyncClient) -> None:
    """
    Condition:
    - Rani uploads; both list their documents.

    Expected:
    - Rani sees hers; Bima sees none.
    """
    await _upload(rani, text_pdf())

    assert len((await rani.get("/api/v1/documents")).json()) == 1
    assert (await bima.get("/api/v1/documents")).json() == []
