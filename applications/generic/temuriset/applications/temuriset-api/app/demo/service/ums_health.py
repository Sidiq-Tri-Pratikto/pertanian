"""UMS-01 demo set: five health products from the public UMS Innovation Hub catalog and one fictional health partner.

The UMS Health Innovation Hackathon 2026 brief (UMS-01) asks to test TemuRiset with real products from
https://ihub.ums.ac.id/katalog. Titles, summaries, TKT levels and lead inventors are copied from that public catalog;
the support needs, budgets and the partner "RS Mitra Sehat F" are fictional. Kept apart from ``data.py`` so the
matching and contract tests that read F01–F06 and Recipients A–E stay unchanged. This module imports nothing.
"""

from typing import Any

CATALOG = "Katalog publik UMS Innovation Hub (ihub.ums.ac.id/katalog)"
SECTOR = "Kesehatan"
TRIAL_SCOPE = "biaya uji coba di fasilitas kesehatan"


def _fact(label: str, value: str, key: str | None = None) -> dict[str, Any]:
    return {"label": label, "value": value, "timing": "CURRENT", "provenance": "SELF_DECLARED", "key": key}


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


def _product(
    title: str, summary: str, problem: str, users: str, stage: str, tkt: int, lead: str, keywords: list[str]
) -> dict[str, Any]:
    return {
        "account": "ums",
        "content": {
            "title": title,
            "summary": summary,
            "problem": problem,
            "solution": summary,
            "intended_users": users,
            "sector": SECTOR,
            "stage": stage,
            "keywords": [*keywords, "kesehatan", "ums"],
            "facts": [
                _fact("Tingkat Kesiapterapan Teknologi (TKT)", f"TKT {tkt}", key="tkt"),
                _fact("Ketua inovator", lead),
                _fact("Sumber data", CATALOG),
            ],
            "claims": [{"kind": "creator", "subject_name": lead}],
        },
    }


# No organization, like Rani: a demo session starts on the personal party, so the products show at once.
ACCOUNT = {"key": "ums", "name": "Tim Inovator UMS", "organization": None}

INVENTIONS: dict[str, dict[str, Any]] = {
    "UMS1": _product(
        "Smart Calibrator of Fetal Doppler terintegrasi IoT",
        "Kalibrator fetal doppler portabel berbasis IoT yang presisi dan terjangkau, dengan pemantauan data kalibrasi "
        "secara real-time.",
        "Fasilitas kesehatan dasar sulit mengkalibrasi fetal doppler karena alat kalibrasi impor mahal dan jauh.",
        "Puskesmas, klinik bersalin dan rumah sakit",
        "PROTOTYPE",
        5,
        "Noor Alis Setiyadi",
        ["fetal doppler", "kalibrasi", "alat kesehatan", "iot", "ibu dan janin"],
    ),
    "UMS2": _product(
        "ENSIKOL (Enteral Substitusi Ikan Tongkol)",
        "Formula enteral polimerik tinggi protein berbasis ikan tongkol untuk pasien kurang gizi dan inflamasi, "
        "lancar mengalir pada pipa NGT 12 Fr tanpa penyaringan.",
        "Rumah sakit bergantung pada formula enteral komersial impor yang mahal untuk pasien malnutrisi.",
        "Instalasi gizi rumah sakit dan keluarga pasien",
        "PROTOTYPE",
        6,
        "Setyaningrum Rahmawaty",
        ["gizi", "enteral", "malnutrisi", "rumah sakit", "pangan medis"],
    ),
    "UMS3": _product(
        "Personal Feedback Balance",
        "Alat deteksi dan latihan keseimbangan portabel pasca-stroke yang mengukur beban tumpuan kaki dan goyangan "
        "badan dalam 15 detik, lalu memandu latihan secara real-time.",
        "Pasien pasca-stroke perlu deteksi gangguan keseimbangan dan latihan rehabilitasi yang terukur.",
        "Fisioterapis, klinik rehabilitasi dan pasien pasca-stroke",
        "PROTOTYPE",
        6,
        "Umi Budi Rahayu",
        ["rehabilitasi", "stroke", "keseimbangan", "fisioterapi", "alat kesehatan"],
    ),
    "UMS4": _product(
        "Channa Peria",
        "Ekstrak ikan gabus dan pare berstandar GMP; kombinasi albumin dan charantin untuk membantu menurunkan glukosa "
        "darah penderita diabetes.",
        "Penderita diabetes membutuhkan pendamping terapi alami yang aman dan teruji.",
        "Penderita diabetes dan apotek",
        "PROTOTYPE",
        6,
        "Muhtadi",
        ["diabetes", "herbal", "ikan gabus", "farmasi"],
    ),
    "UMS5": _product(
        "Clovena: Aromaterapi Minyak Atsiri dan VCO",
        "Aromaterapi multiguna dari minyak atsiri daun cengkeh, adas dan kayu putih berbasis VCO, berfungsi sebagai "
        "analgesik, antiseptik, antioksidan dan repelan alami.",
        "Masyarakat membutuhkan produk kesehatan topikal alami yang aman dari bahan kimia sintetis.",
        "Konsumen umum, apotek dan petani minyak cengkeh",
        "PILOT",
        7,
        "Kun Harismah",
        ["aromaterapi", "herbal", "minyak atsiri", "farmasi"],
    ),
}

SUPPORT_REQUESTS: dict[str, dict[str, Any]] = {
    key: {
        "outcome": outcome,
        "support_forms": ["project_funding"],
        "relationship_form": "PROJECT",
        "scope": TRIAL_SCOPE,
        "months": 12,
        "region": "Indonesia",
        "accepts_partial": True,
        "budget": {
            "min": minimum,
            "max": maximum,
            "currency": "IDR",
            "basis": "total_period",
            "period": "12 bulan",
            "scope": TRIAL_SCOPE,
            "estimated_on": "2026-11-27",
            "assumptions": "Uji coba di dua fasilitas kesehatan",
        },
    }
    for key, outcome, minimum, maximum in (
        ("UMS1", "Uji coba kalibrator di fasilitas kesehatan", "150000000", "250000000"),
        ("UMS2", "Uji coba formula enteral di instalasi gizi rumah sakit", "120000000", "200000000"),
    )
}

PROFILE = {
    "party": {"kind": "organization", "name": "RS Mitra Sehat F", "organization_kind": "company"},
    "content": {
        "subtype": "Rumah sakit mitra uji coba",
        "thesis": "Membuka fasilitas kesehatan untuk uji coba inovasi kesehatan lokal yang siap dipakai pasien.",
        "sectors": [SECTOR],
        "stages": ["PROTOTYPE", "PILOT"],
        "regions": ["Indonesia"],
        "support_forms": ["Pendanaan proyek", "Fasilitas uji", "Pendampingan"],
    },
}

RECIPIENT_ACCOUNT = {"key": "faskes-f", "name": "Perwakilan RS Mitra Sehat F", "zone": "Asia/Jakarta"}

OPPORTUNITY = {
    "title": "Uji coba inovasi kesehatan di rumah sakit",
    "outcome": "Inovasi kesehatan teruji pada pasien dan tenaga kesehatan dalam dua belas bulan.",
    "included": "Uji coba di instalasi rumah sakit dan pendampingan tenaga kesehatan",
    "excluded": "Pengurusan izin edar dan produksi massal",
    "support": "Pendanaan uji coba dan akses fasilitas",
    "accepted_stages": ["PROTOTYPE", "PILOT"],
    "relationship_forms": ["PROJECT"],
    "sectors": [SECTOR],
    "keywords": ["kesehatan", "uji coba", "rumah sakit", "alat kesehatan", "gizi"],
    "timing": "Dibuka sampai 30 Juni 2027",
    "financial": {
        "subject": "partner",
        "basis": "total_period",
        "min": "100000000",
        "max": "300000000",
        "currency": "IDR",
        "period": "12 bulan",
        "months": 12,
        "scope": TRIAL_SCOPE,
    },
    "requirements": [
        _requirement(
            "Tahap inovasi",
            "stage",
            "in_set",
            ["PROTOTYPE", "PILOT"],
            "SUBMISSION",
            "DECLARATION",
            "Rumah sakit hanya menguji inovasi yang sudah memiliki purwarupa.",
        ),
        _requirement(
            "Kisaran biaya uji coba",
            "budget",
            "range_overlap",
            None,
            "SUBMISSION",
            "DECLARATION",
            "Biaya dibandingkan dengan dukungan rumah sakit pada cakupan dan periode yang sama.",
        ),
        _requirement(
            "Izin edar atau sertifikasi alat kesehatan",
            "document:certificate",
            "exists",
            True,
            "COMMERCIALIZATION",
            "REVIEWER_CONFIRMED",
            "Diperlukan sebelum dipakai rutin atau dijual, bukan untuk uji coba.",
        ),
    ],
}

ACCOUNT_SUMMARIES = {
    "ums": "Lima produk kesehatan dari katalog publik UMS Innovation Hub (TKT 5–7), dua punya kebutuhan uji coba.",
    "faskes-f": "Rumah sakit mitra fiktif yang membuka uji coba inovasi kesehatan, Rp100–300 juta per 12 bulan.",
}
