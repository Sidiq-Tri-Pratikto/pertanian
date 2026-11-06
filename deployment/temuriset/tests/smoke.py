"""Exercise the HTTPS gateway and synthetic S3 document lifecycle."""

import http.cookiejar
import json
import re
import ssl
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPSHandler, HTTPCookieProcessor, Request, build_opener


def document() -> bytes:
    """Construct a minimal valid PDF with a simple extracted text line."""
    stream = b"BT /F1 12 Tf 15 80 Td (Synthetic smoke) Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    content = bytearray(b"%PDF-1.4\n")
    offsets = []
    for index, item in enumerate(objects, 1):
        offsets.append(len(content))
        content.extend(b"%d 0 obj\n%s\nendobj\n" % (index, item))
    xref = len(content)
    content.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for offset in offsets:
        content.extend(b"%010d 00000 n \n" % offset)
    content.extend(b"trailer\n<< /Root 1 0 R /Size 6 >>\nstartxref\n%d\n%%%%EOF\n" % xref)
    return bytes(content)


class Browser:
    """A cookie jar and a trusted synthetic TLS certificate."""

    def __init__(self, origin: str, certificate: str) -> None:
        self.origin = origin
        self.client = build_opener(
            HTTPSHandler(context=ssl.create_default_context(cafile=certificate)),
            HTTPCookieProcessor(http.cookiejar.CookieJar()),
        )

    def fetch(
        self, path: str, method: str = "GET", body: dict | bytes | None = None,
        headers: dict | None = None, expected: int = 200,
    ) -> tuple[bytes, dict]:
        options = {"Origin": self.origin, **(headers or {})}
        if isinstance(body, dict):
            options["Content-Type"] = "application/json"
            body = json.dumps(body).encode()
        request = Request(self.origin + path, method=method, data=body, headers=options)
        try:
            response = self.client.open(request, timeout=8)
        except HTTPError as error:
            response = error
        with response:
            payload = response.read()
            if response.status != expected:
                raise RuntimeError(f"{method} {path.split('?')[0]} returned {response.status}, expected {expected}")
            return payload, dict(response.headers)

    def sign_up(self, name: str) -> str:
        address = f"{name}@example.test"
        self.fetch(
            "/api/v1/auth/code", "POST",
            {"email": address, "purpose": "sign_up", "display_name": name, "time_zone": "Asia/Jakarta", "persona": "inovator"},
            expected=202,
        )
        mailbox, _ = self.fetch("/api/v1/dev/mailbox?" + urlencode({"email": address}))
        code = re.search(r"\b\d{6}\b", json.loads(mailbox)[0]["body"])
        if code is None:
            raise RuntimeError("Synthetic verification code was not available")
        self.fetch("/api/v1/auth/verify", "POST", {"email": address, "code": code.group()})
        return json.loads(self.fetch("/api/v1/me")[0])["active_party_id"]


def smoke(origin: str, certificate: str, composition: str, lifecycle: bool) -> None:
    """Check the real HTTP routes for this local composition."""
    owner = Browser(origin, certificate)
    for attempt in range(20):
        try:
            owner.fetch("/health/ready")
            break
        except (OSError, RuntimeError):
            if attempt == 19:
                raise
            time.sleep(1)
    owner.fetch("/start")
    manifest = json.loads(owner.fetch("/api/v1/capabilities")[0])
    assert manifest["composition"]["id"] == composition
    assert {item["id"]: item["implementation"] for item in manifest["adapters"]}["object-storage"] == "s3"
    if lifecycle:
        party = owner.sign_up("Owner")
        other = Browser(origin, certificate)
        grantee = other.sign_up("Grantee")
        content = document()
        intent, _ = owner.fetch(
            "/api/v1/documents/upload-intents", "POST",
            {"acting_party_id": party, "title": "Synthetic", "kind": "evidence",
             "media_type": "application/pdf", "size_bytes": len(content)},
            expected=201,
        )
        uploaded, _ = owner.fetch(json.loads(intent)["upload_url"], "PUT", content, expected=202)
        document_id = json.loads(uploaded)["document_id"]
        path = f"/api/v1/documents/{document_id}"
        for attempt in range(45):
            version = json.loads(owner.fetch(path)[0])["versions"][0]
            if version["file_state"] == "AVAILABLE" and version["extraction_state"] == "SUCCEEDED":
                break
            if attempt == 44:
                raise RuntimeError(f"Document scan/extraction did not succeed: {version['file_state']}")
            time.sleep(1)
        download_path = f"{path}/versions/1/content"
        other.fetch(download_path, expected=404)
        grant, _ = owner.fetch(
            path + "/grants", "POST",
            {"acting_party_id": party, "version": 1, "grantee_party_id": grantee, "purpose": "pitch"},
            {"Idempotency-Key": "smoke-grant"}, expected=201,
        )
        body, headers = other.fetch(download_path, headers={"Range": "bytes=0-7"}, expected=206)
        assert body == content[:8]
        assert any(key.lower() == "cache-control" and value == "private, no-store" for key, value in headers.items())
        assert other.fetch(download_path)[0] == content
        owner.fetch(
            f"/api/v1/grants/{json.loads(grant)['id']}/revoke", "POST",
            {"acting_party_id": party}, {"Idempotency-Key": "smoke-revoke"},
        )
        other.fetch(download_path, headers={"Range": "bytes=0-7"}, expected=403)
    else:
        owner.fetch("/api/v1/dev/mailbox?email=fixture%40example.test", expected=404)
        owner.fetch(
            "/api/v1/auth/code", "POST", {"email": "fixture@example.test", "purpose": "sign_in"}, expected=503,
        )
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    smoke(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] == "lifecycle")
