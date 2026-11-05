"""Recipients A–E from the fixtures, as plain data and as a loader through the API (spec 016, used by 019 and 021).

The data imports nothing from the application, so engine tests can read it without a database. Where it differs from
the prototype's ``domain.js``, the reasons are in ``specs/016-partner-intake-api/tasks.md``.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any


def _requirement(
    label: str, name: str, operator: str, value: Any, applies_at: str, mode: str, reason: str
) -> dict[str, Any]:
    return {
        "label": label,
        "field": name,
        "operator": operator,
        "value": value,
        "mandatory": True,
        "applies_at": applies_at,
        "verification_mode": mode,
        "visibility": "PUBLIC",
        "reason": reason,
    }


INVESTOR_CHECK = {
    "subject": "investorCheck",
    "basis": "per_investment",
    "min": "50000.0000",
    "max": "150000.0000",
    "currency": "USD",
    "period": "per investasi",
}

PROFILES: dict[str, dict[str, Any]] = {
    "A": {
        "party": {"kind": "organization", "name": "Mitra A", "organization_kind": "company"},
        "content": {
            "subtype": "Mitra validasi prototipe",
            "thesis": "Membantu prototipe menjadi siap uji lapangan.",
            "sectors": ["Air dan sanitasi", "Pertanian", "Energi"],
            "stages": ["IDEA", "PROTOTYPE", "PILOT"],
            "regions": ["Indonesia"],
            "support_forms": ["Pendanaan proyek", "Fasilitas uji", "Pendampingan"],
        },
    },
    "B": {
        "party": {"kind": "personal", "name": "Investor B"},
        "content": {
            "subtype": "Investor individu",
            "thesis": "Investasi ekuitas pada perusahaan tahap awal.",
            "sectors": ["Material", "Manufaktur"],
            "stages": ["PROTOTYPE"],
            "regions": ["Indonesia"],
            "support_forms": ["Ekuitas"],
            "check_range": INVESTOR_CHECK,
        },
    },
    "C": {
        "party": {"kind": "organization", "name": "Distributor C", "organization_kind": "company"},
        "content": {
            "subtype": "Distributor",
            "thesis": "Mendistribusikan produk yang sudah siap pasar.",
            "sectors": ["Air dan sanitasi", "Material"],
            "stages": ["MARKET"],
            "regions": ["Indonesia"],
            "support_forms": ["Distribusi"],
        },
    },
    "D": {
        "party": {"kind": "organization", "name": "Mitra Lisensi D", "organization_kind": "company"},
        "content": {
            "subtype": "Mitra lisensi perangkat lunak",
            "thesis": "Melisensikan perangkat lunak untuk pelanggan korporasi.",
            "sectors": ["Perangkat lunak"],
            "stages": ["WORKING"],
            "regions": ["Indonesia"],
            "support_forms": ["Lisensi"],
        },
    },
    # A source-reported directory entry: what the source did not say stays empty, and intake is unconfirmed.
    "E": {
        "party": {"kind": "organization", "name": "Dana Riset E", "organization_kind": "nonprofit"},
        "content": {
            "subtype": "Direktori pendanaan",
            "thesis": "Pendanaan riset terapan.",
            "sectors": ["Air dan sanitasi"],
            "stages": [],
            "regions": [],
            "support_forms": ["Hibah"],
            "contact_route": "EXTERNAL",
            "external_url": "https://example.org/formulir-demo",
        },
    },
}

OPPORTUNITIES: dict[str, dict[str, Any]] = {
    "A1": {
        "partner": "A",
        "content": {
            "title": "Validasi prototipe enam bulan",
            "outcome": "Prototipe teruji di lapangan dalam enam bulan.",
            "included": "Uji fungsi dan uji lapangan terbatas",
            "excluded": "Sertifikasi dan produksi massal",
            "support": "Pendanaan proyek dan pendampingan uji",
            "accepted_stages": ["PROTOTYPE", "PILOT"],
            "relationship_forms": ["PROJECT"],
            "sectors": ["Air dan sanitasi", "Pertanian", "Energi"],
            "keywords": ["prototipe", "validasi", "uji", "air"],
            "timing": "Dibuka sampai 31 Desember 2026",
            "financial": {
                "subject": "partner",
                "basis": "total_period",
                "min": "15000.0000",
                "max": "40000.0000",
                "currency": "USD",
                "period": "6 bulan",
                "months": 6,
                "scope": "biaya pilot enam bulan",
            },
            "requirements": [
                _requirement(
                    "Tahap inovasi",
                    "stage",
                    "in_set",
                    ["PROTOTYPE", "PILOT"],
                    "SUBMISSION",
                    "DECLARATION",
                    "Mitra ini hanya menguji inovasi yang sudah memiliki prototipe.",
                ),
                _requirement(
                    "Berkas uji fungsi",
                    "document:function",
                    "exists",
                    True,
                    "SUBMISSION",
                    "DOCUMENT_PRESENT",
                    "Mitra perlu melihat bukti fungsi sebelum menyiapkan uji.",
                ),
                _requirement(
                    "Kisaran biaya pilot",
                    "budget",
                    "range_overlap",
                    None,
                    "SUBMISSION",
                    "DECLARATION",
                    "Biaya dibandingkan dengan dukungan mitra pada cakupan dan periode yang sama.",
                ),
                _requirement(
                    "Sertifikat komersialisasi",
                    "document:certificate",
                    "exists",
                    True,
                    "COMMERCIALIZATION",
                    "REVIEWER_CONFIRMED",
                    "Diperlukan nanti sebelum dijual, bukan untuk uji prototipe.",
                ),
            ],
        },
    },
    "A2": {
        "partner": "A",
        "content": {
            "title": "Fasilitas uji pascapanen",
            "outcome": "Akses fasilitas uji untuk proses pascapanen.",
            "included": "Pemakaian fasilitas uji",
            "excluded": "Dana tunai",
            "support": "Fasilitas uji",
            "accepted_stages": ["PILOT"],
            "relationship_forms": ["PROJECT"],
            "sectors": ["Pertanian"],
            "keywords": ["pertanian", "pengeringan", "fasilitas", "uji"],
            "timing": "Dibuka sampai 31 Desember 2026",
            "financial": {"subject": "partner", "noncash": "Tanpa dana tunai: fasilitas uji"},
            "requirements": [
                _requirement(
                    "Tahap inovasi",
                    "stage",
                    "in_set",
                    ["PILOT"],
                    "SUBMISSION",
                    "DECLARATION",
                    "Fasilitas ini disediakan bagi inovasi yang sudah masuk tahap pilot.",
                ),
                _requirement(
                    "Wewenang atas inovasi",
                    "authority",
                    "equals",
                    "REVIEWED",
                    "SUBMISSION",
                    "REVIEWER_CONFIRMED",
                    "Fasilitas hanya dibuka bagi pihak yang wewenangnya sudah diperiksa.",
                ),
            ],
        },
    },
    "A3": {
        "partner": "A",
        "content": {
            "title": "Pendampingan ide tahap awal",
            "outcome": "Ide tahap awal mendapat pendampingan.",
            "included": "Sesi pendampingan",
            "excluded": "Dana tunai",
            "support": "Pendampingan",
            "accepted_stages": ["IDEA", "PROTOTYPE"],
            "relationship_forms": ["PROJECT"],
            "sectors": ["Energi", "Air dan sanitasi"],
            "keywords": ["pendampingan", "komunitas", "energi"],
            "timing": "Dibuka sampai 31 Desember 2026",
            "financial": {"subject": "partner", "noncash": "Pendampingan tanpa dana tunai"},
            "requirements": [
                _requirement(
                    "Tahap inovasi",
                    "stage",
                    "in_set",
                    ["IDEA", "PROTOTYPE"],
                    "SUBMISSION",
                    "DECLARATION",
                    "Pendampingan ini ditujukan bagi inovasi tahap ide atau prototipe.",
                )
            ],
        },
    },
    "B1": {
        "partner": "B",
        "content": {
            "title": "Investasi ekuitas pre-seed",
            "outcome": "Investasi pada perusahaan pre-seed dengan prototipe.",
            "included": "Ekuitas pada badan usaha yang sudah ada",
            "excluded": "Pendanaan proyek",
            "support": "Investasi ekuitas",
            "accepted_stages": ["PROTOTYPE"],
            "relationship_forms": ["EQUITY"],
            "sectors": ["Material", "Manufaktur"],
            "keywords": ["material", "sirkular", "manufaktur"],
            "timing": "Dibuka sampai 31 Maret 2027",
            "financial": INVESTOR_CHECK,
            "requirements": [
                _requirement(
                    "Bentuk pendanaan",
                    "relationship",
                    "equals",
                    "EQUITY",
                    "SUBMISSION",
                    "DECLARATION",
                    "Mandat ini hanya untuk ekuitas.",
                ),
                _requirement(
                    "Badan usaha yang sudah berdiri",
                    "entity",
                    "equals",
                    "IDENTIFIED",
                    "SUBMISSION",
                    "DECLARATION",
                    "Ekuitas memerlukan subjek hukum yang nyata.",
                ),
                _requirement(
                    "Kisaran kontribusi",
                    "contribution",
                    "range_overlap",
                    None,
                    "SUBMISSION",
                    "DECLARATION",
                    "Dibandingkan dengan kontribusi yang diinginkan, bukan seluruh target.",
                ),
            ],
        },
    },
    "B2": {
        "partner": "B",
        "content": {
            "title": "Diskusi tim pra-pendirian",
            "outcome": "Diskusi awal dengan tim yang belum mendirikan perusahaan.",
            "included": "Diskusi",
            "excluded": "Konfirmasi ekuitas sebelum badan usaha ada",
            "support": "Diskusi investasi",
            "accepted_stages": ["PROTOTYPE"],
            "relationship_forms": ["EQUITY"],
            "sectors": ["Material", "Manufaktur"],
            "keywords": ["material", "sirkular"],
            "timing": "Dibuka sampai 31 Maret 2027",
            "financial": INVESTOR_CHECK,
            "requirements": [
                _requirement(
                    "Bentuk pendanaan",
                    "relationship",
                    "equals",
                    "EQUITY",
                    "SUBMISSION",
                    "DECLARATION",
                    "Diskusi ini hanya untuk rencana pendanaan ekuitas.",
                ),
                _requirement(
                    "Kisaran kontribusi",
                    "contribution",
                    "range_overlap",
                    None,
                    "SUBMISSION",
                    "DECLARATION",
                    "Dibandingkan dengan kontribusi yang diinginkan, bukan seluruh target.",
                ),
            ],
        },
    },
    "C1": {
        "partner": "C",
        "content": {
            "title": "Distribusi produk siap pasar",
            "outcome": "Produk bersertifikat masuk jaringan distribusi.",
            "included": "Distribusi",
            "excluded": "Pengembangan prototipe",
            "support": "Distribusi",
            "accepted_stages": ["MARKET"],
            "relationship_forms": ["PROJECT"],
            "sectors": ["Air dan sanitasi", "Material"],
            "keywords": ["distribusi", "pasar", "sertifikat", "air"],
            "timing": "Dibuka sampai 31 Desember 2026",
            "financial": {"subject": "partner", "noncash": "Jaringan distribusi"},
            "requirements": [
                _requirement(
                    "Tahap inovasi",
                    "stage",
                    "in_set",
                    ["MARKET"],
                    "SUBMISSION",
                    "DECLARATION",
                    "Mitra ini hanya menerima produk siap pasar.",
                ),
                _requirement(
                    "Sertifikat yang berlaku",
                    "document:certificate",
                    "exists",
                    True,
                    "SUBMISSION",
                    "REVIEWER_CONFIRMED",
                    "Distribusi memerlukan sertifikat saat pengajuan.",
                ),
            ],
        },
    },
    "D1": {
        "partner": "D",
        "content": {
            "title": "Lisensi perangkat lunak korporasi",
            "outcome": "Lisensi perangkat lunak untuk pelanggan korporasi.",
            "included": "Diskusi lisensi",
            "excluded": "Pendanaan",
            "support": "Lisensi",
            "accepted_stages": ["WORKING"],
            "relationship_forms": ["LICENSE"],
            "sectors": ["Perangkat lunak"],
            "keywords": ["perangkat", "lunak", "lisensi", "penjadwalan"],
            "timing": "Dibuka sampai 31 Desember 2026",
            # The prototype's "Belum ditentukan" is unknown, so it travels as a reason and not as a value.
            "financial": {"subject": "license", "unknown_reason": "not_determined"},
            "requirements": [
                _requirement(
                    "SSO yang sudah berjalan",
                    "feature:sso",
                    "equals",
                    "CURRENT",
                    "SUBMISSION",
                    "DECLARATION",
                    "Pelanggan korporasi memerlukan SSO saat ini, bukan rencana.",
                ),
                _requirement(
                    "Bentuk kerja sama",
                    "relationship",
                    "equals",
                    "LICENSE",
                    "SUBMISSION",
                    "DECLARATION",
                    "Mandat ini hanya untuk kerja sama lisensi.",
                ),
            ],
        },
    },
}


@dataclass
class LoadedRecipients:
    """What ``load_recipients`` made.

    Attributes:
        parties (dict[str, str]): Party id per recipient, such as ``A``.
        opportunities (dict[str, str]): Opportunity id per target, such as ``A1``.
        clients (dict[str, Any]): A signed-in client acting for each recipient. The caller closes them.
    """

    parties: dict[str, str] = field(default_factory=dict)
    opportunities: dict[str, str] = field(default_factory=dict)
    clients: dict[str, Any] = field(default_factory=dict)

    async def close(self) -> None:
        """Close every client."""
        for client in self.clients.values():
            await client.aclose()


async def save_profile(
    client: Any,
    party_id: str,
    content: dict[str, Any],
    *,
    version: int | None = None,
    key: str = "profile",
    **extra: Any,
) -> Any:
    """Save a party's profile through the API.

    Args:
        client (Any): A client acting for the party.
        party_id (str): The party.
        content (dict[str, Any]): Profile content.
        version (int | None, optional): ``expected_version``. Defaults to None, for a first save.
        key (str, optional): Idempotency key. Defaults to "profile".
        **extra (Any): More body fields, such as ``intake_status``.

    Returns:
        Any: The response.
    """
    body = {"acting_party_id": party_id, "expected_version": version, **content, **extra}
    return await client.put(f"/api/v1/partners/{party_id}", json=body, headers={"Idempotency-Key": key})


async def create_opportunity(client: Any, party_id: str, content: dict[str, Any], *, key: str = "create") -> Any:
    """Start an opportunity through the API.

    Args:
        client (Any): A client acting for the party.
        party_id (str): The acting party.
        content (dict[str, Any]): Opportunity content, optionally with ``kind``.
        key (str, optional): Idempotency key. Defaults to "create".

    Returns:
        Any: The response.
    """
    body = {"acting_party_id": party_id, **content}
    return await client.post("/api/v1/opportunities", json=body, headers={"Idempotency-Key": key})


async def save_opportunity(
    client: Any, party_id: str, opportunity_id: str, content: dict[str, Any], version: int, *, key: str = "save"
) -> Any:
    """Save an opportunity through the API.

    Args:
        client (Any): A client acting for the party.
        party_id (str): The acting party.
        opportunity_id (str): The opportunity.
        content (dict[str, Any]): Opportunity content.
        version (int): ``expected_version``.
        key (str, optional): Idempotency key. Defaults to "save".

    Returns:
        Any: The response.
    """
    body = {"acting_party_id": party_id, "expected_version": version, **content}
    return await client.put(f"/api/v1/opportunities/{opportunity_id}", json=body, headers={"Idempotency-Key": key})


async def move_opportunity(
    client: Any, party_id: str, opportunity_id: str, action: str, version: int, *, key: str | None = None
) -> Any:
    """Activate, pause or close an opportunity through the API.

    Args:
        client (Any): A client acting for the party.
        party_id (str): The acting party.
        opportunity_id (str): The opportunity.
        action (str): ``activate``, ``pause`` or ``close``.
        version (int): ``expected_version``.
        key (str | None, optional): Idempotency key. Defaults to one per action and version.

    Returns:
        Any: The response.
    """
    return await client.post(
        f"/api/v1/opportunities/{opportunity_id}/{action}",
        json={"acting_party_id": party_id, "expected_version": version},
        headers={"Idempotency-Key": key or f"{opportunity_id}-{action}-{version}"},
    )


async def _party_for(client: Any, key: str, sign_up: Callable[..., Awaitable[dict]]) -> str:
    party = PROFILES[key]["party"]
    me = await sign_up(client, f"recipient-{key.lower()}@example.com", persona="mitra", name=party["name"])
    if party["kind"] == "personal":
        client.headers["X-Acting-Party"] = me["active_party_id"]
        return me["active_party_id"]
    organization = await client.post(
        "/api/v1/organizations",
        json={"name": party["name"], "kind": party["organization_kind"]},
        headers={"Idempotency-Key": f"organization-{key}"},
    )
    assert organization.status_code == 201, organization.text  # noqa: S101 - a test fixture stops on a broken setup
    party_id = organization.json()["party_id"]
    await client.put("/api/v1/me/context", json={"party_id": party_id})
    client.headers["X-Acting-Party"] = party_id
    return party_id


async def load_recipients(
    new_client: Callable[[], Any], sign_up: Callable[..., Awaitable[dict]], *, activate: bool = True
) -> LoadedRecipients:
    """Create Recipients A–E: A–D through the API, as a partner would, and E as a directory entry.

    E has no route of its own because nobody may claim a source through the API, so it goes through the service with
    an organization owned by a test operator account.

    Args:
        new_client (Callable[[], Any]): Makes a client with its own cookie jar.
        sign_up (Callable[..., Awaitable[dict]]): Signs a client up.
        activate (bool, optional): Whether to activate the opportunities. Defaults to True.

    Returns:
        LoadedRecipients: Parties, opportunities and a client per recipient.
    """
    # Imported here so that reading the plain data above needs no application or database.
    from app.core.database import get_session_factory  # noqa: PLC0415
    from app.intake.model.schema import PartnerProfileContent  # noqa: PLC0415
    from app.intake.service.service import IntakeService  # noqa: PLC0415

    loaded = LoadedRecipients()
    for key, profile in PROFILES.items():
        client = new_client()
        loaded.clients[key] = client
        party_id = await _party_for(client, key, sign_up)
        loaded.parties[key] = party_id
        if key == "E":
            async with get_session_factory()() as session, session.begin():
                content = PartnerProfileContent.model_validate(profile["content"])
                await IntakeService(session).record_directory_profile(party_id, content)
            continue
        saved = await save_profile(client, party_id, profile["content"])
        assert saved.status_code == 200, saved.text  # noqa: S101 - a test fixture stops on a broken setup
    for key, opportunity in OPPORTUNITIES.items():
        partner = opportunity["partner"]
        client, party_id = loaded.clients[partner], loaded.parties[partner]
        created = await create_opportunity(client, party_id, opportunity["content"], key=f"create-{key}")
        assert created.status_code == 201, created.text  # noqa: S101 - a test fixture stops on a broken setup
        loaded.opportunities[key] = created.json()["id"]
        if activate:
            moved = await move_opportunity(client, party_id, created.json()["id"], "activate", 1)
            assert moved.status_code == 200, moved.text  # noqa: S101 - a test fixture stops on a broken setup
    return loaded
