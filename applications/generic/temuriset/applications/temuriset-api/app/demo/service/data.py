"""Fixtures F01–F06, FRaise01 and Recipients A–E as plain data, shared by demo seeding (021) and tests (016, 019).

Every value is fictional. This module imports nothing, so engine tests can read it without a database. Where it
differs from the prototype's ``domain.js``, the reasons are in ``specs/016-partner-intake-api/tasks.md`` and
``specs/019-matching-engine/tasks.md``.
"""

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


# One account per inventor; an organization when the fixture names one.
ACCOUNTS: dict[str, dict[str, Any]] = {
    "rani": {"name": "Rani", "organization": None},
    "dewi": {"name": "Dewi", "organization": "Komunitas FieldDry Demo"},
    "galih": {"name": "Galih", "organization": "Tim QueueNest Demo"},
    "bima": {"name": "Bima", "organization": "Demo Circular Materials Ltd"},
    "sinta": {"name": "Sinta", "organization": "Tim GridShare Demo"},
}


def _fact(label: str, value: str, timing: str = "CURRENT", key: str | None = None, **extra: Any) -> dict[str, Any]:
    return {"label": label, "value": value, "timing": timing, "provenance": "SELF_DECLARED", "key": key, **extra}


INVENTIONS: dict[str, dict[str, Any]] = {
    "F01": {
        "account": "rani",
        "content": {
            "title": "ClearSpring",
            "summary": "Filter air sederhana yang mudah dirawat untuk keluarga tanpa akses air bersih.",
            "problem": "Keluarga tanpa akses air bersih perlu cara menyaring air yang mudah dirawat.",
            "solution": "Prototipe filter air yang sudah berfungsi.",
            "intended_users": "Keluarga dan komunitas kecil tanpa jaringan air bersih",
            "sector": "Air dan sanitasi",
            "stage": "PROTOTYPE",
            "keywords": ["air", "filter", "prototipe", "validasi"],
            "facts": [
                _fact("Kapasitas saring", "10", key="capacity", unit="L/jam", provenance="PROVIDED"),
                _fact("Kapasitas saring", "20", "PLANNED", key="capacity", unit="L/jam"),
                # Linked to the uploaded test report, which ``document:function`` requirements read.
                _fact("Laporan uji fungsi", "Laporan uji fungsi ClearSpring", key="function", provenance="PROVIDED"),
            ],
            "claims": [
                {"kind": "creator", "subject_name": "Rani"},
                {"kind": "rights_holder", "subject_name": "Rani", "scope": "belum didaftarkan"},
            ],
            "private_notes": "Catatan pribadi Rani: harga bahan rahasia 7731.",
        },
        "documents": {"function": "Laporan uji fungsi ClearSpring"},
    },
    "F02": {
        "account": "dewi",
        "content": {
            "title": "FieldDry",
            "summary": "Proses pengeringan hasil panen yang tidak bergantung pada cuaca.",
            "problem": "Hasil panen perlu dikeringkan tanpa bergantung pada cuaca.",
            "solution": "Proses pengeringan pada tahap pilot.",
            "intended_users": "Kelompok tani",
            "sector": "Pertanian",
            "stage": "PILOT",
            "keywords": ["pertanian", "pengeringan", "uji", "fasilitas"],
            "facts": [_fact("Proses pengeringan", "Berjalan pada pilot")],
            "claims": [{"kind": "authority", "subject_name": "Komunitas FieldDry Demo", "status": "asserted"}],
        },
    },
    "F03": {
        "account": "galih",
        "content": {
            "title": "QueueNest",
            "summary": "Aplikasi penjadwalan untuk tim layanan dengan koneksi tidak stabil.",
            "problem": "Tim layanan perlu mengatur antrean walau koneksi tidak stabil.",
            "solution": "Aplikasi penjadwalan dengan ekspor luring.",
            "intended_users": "Tim layanan",
            "sector": "Perangkat lunak",
            "stage": "WORKING",
            "keywords": ["perangkat", "lunak", "lisensi", "penjadwalan", "aplikasi"],
            "facts": [
                _fact("Ekspor luring", "Ekspor luring", key="offline_export"),
                _fact("SSO", "SSO", "PLANNED", key="sso"),
            ],
        },
    },
    "F04": {
        "account": "bima",
        "content": {
            "title": "LoopMaterial",
            "summary": "Material kemasan sirkular pada tahap prototipe.",
            "problem": "Kemasan sekali pakai sulit didaur ulang.",
            "solution": "Prototipe material kemasan.",
            "intended_users": "Produsen kemasan",
            "sector": "Material",
            "stage": "PROTOTYPE",
            "keywords": ["material", "kemasan", "sirkular"],
            "facts": [_fact("Prototipe material", "Lembar uji kemasan")],
        },
    },
    "F05": {
        "account": "bima",
        "content": {
            "title": "ReFormPress",
            "summary": "Proses manufaktur untuk membentuk ulang material daur ulang.",
            "problem": "Material daur ulang sulit dibentuk ulang secara konsisten.",
            "solution": "Prototipe mesin pembentuk.",
            "intended_users": "Produsen kemasan",
            "sector": "Manufaktur",
            "stage": "PROTOTYPE",
            "keywords": ["manufaktur", "material", "sirkular"],
            "facts": [_fact("Mesin pembentuk", "Prototipe berjalan")],
        },
    },
    "F06": {
        "account": "sinta",
        "curated": True,
        "content": {
            "title": "GridShare",
            "summary": "Konsep pemantauan energi bersama untuk komunitas.",
            "problem": "Komunitas perlu memantau pemakaian energi bersama.",
            "solution": "Konsep pemantauan energi komunitas.",
            "intended_users": "Komunitas energi",
            "sector": "Energi",
            "stage": "IDEA",
            "keywords": ["energi", "komunitas", "pendampingan"],
            "facts": [_fact("Konsep pemantauan", "Rancangan konsep")],
        },
    },
}

F01_BUDGET = {
    "min": "20000",
    "max": "30000",
    "currency": "USD",
    "basis": "total_period",
    "period": "6 bulan",
    "scope": "biaya pilot enam bulan",
    "estimated_on": "2026-10-30",
    "assumptions": "Uji lapangan di dua lokasi",
}
# F01-GAP: the same need before its range was filled in.
F01_GAP_BUDGET = {"unknown_reason": "not_determined", "scope": "biaya pilot enam bulan", "period": "6 bulan"}

SUPPORT_REQUESTS: dict[str, dict[str, Any]] = {
    "F01": {
        "outcome": "Validasi prototipe enam bulan",
        "support_forms": ["project_funding"],
        "relationship_form": "PROJECT",
        "scope": "biaya pilot enam bulan",
        "months": 6,
        "region": "Indonesia",
        "accepts_partial": True,
        "budget": F01_BUDGET,
    },
    "F02": {
        "outcome": "Uji proses pengeringan",
        "support_forms": ["facilities"],
        "relationship_form": "PROJECT",
        "scope": "fasilitas uji",
        "months": 6,
        "region": "Indonesia",
        "accepts_partial": True,
        "accepts_noncash": True,
        "noncash_description": "Tanpa dana tunai: fasilitas uji",
        "budget": {"unknown_reason": "not_determined", "scope": "fasilitas uji", "financial": False},
    },
    "F03": {
        "outcome": "Diskusi lisensi",
        "support_forms": ["technical_partner"],
        "relationship_form": "LICENSE",
        "scope": "lisensi",
        "months": 6,
        "region": "Indonesia",
        "accepts_partial": True,
        "budget": {"unknown_reason": "not_determined", "scope": "lisensi"},
    },
    "F06": {
        "outcome": "Pendampingan ide tahap awal",
        "support_forms": ["mentoring"],
        "relationship_form": "PROJECT",
        "scope": "pendampingan",
        "months": 6,
        "region": "Indonesia",
        "accepts_partial": True,
        "accepts_noncash": True,
        "noncash_description": "Pendampingan, kebutuhan dana belum diketahui",
        "budget": {"unknown_reason": "not_determined", "scope": "pendampingan"},
    },
}

FRAISE01 = {
    "inventions": ["F04", "F05"],
    "entity": {"name": "Demo Circular Materials Ltd", "jurisdiction": "Indonesia"},
    "content": {
        "financing_stage": "pre_seed",
        "financing_form": "equity",
        "currency": "USD",
        "target_amount": "500000",
        "desired_min": "50000",
        "desired_max": "100000",
        "accepts_partial": True,
        "intended_use": "Mengembangkan dua inovasi perusahaan",
    },
}


# Who signs in for each recipient in the demo picker; E's directory entry is kept by a demo operator.
RECIPIENT_ACCOUNTS: dict[str, dict[str, Any]] = {
    "A": {"key": "mitra-a", "name": "Peserta P", "zone": "Asia/Makassar"},
    "B": {"key": "investor-b", "name": "Investor B", "zone": "Asia/Jakarta"},
    "C": {"key": "distributor-c", "name": "Perwakilan Distributor C", "zone": "Asia/Jakarta"},
    "D": {"key": "lisensi-d", "name": "Perwakilan Mitra Lisensi D", "zone": "Asia/Jakarta"},
    "E": {"key": "direktori-e", "name": "Pengelola Direktori Demo", "zone": "Asia/Jakarta"},
}
INVENTOR_ZONES = {"sinta": "Asia/Makassar"}
INVENTOR_FIXTURES = {"rani": "F01", "dewi": "F02", "galih": "F03", "bima": "F04, F05 dan FRaise01", "sinta": "F06"}
