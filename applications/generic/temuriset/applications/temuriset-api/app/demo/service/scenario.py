"""The demo scenario as plain data: what a reset seeds, and what the presenter types live.

The reset starts with Inovator A and Produk A (ClearSpring), Investor A with one opportunity, and Investor B as an
empty account. Scenario 1 fills in Investor B (``INVESTOR_B``), scenario 2 creates Produk B (``PRODUCT_B``). The
values are chosen so matching reads: Produk A is a weak match for both investors, Produk B a strong one for
Investor B. ``tests/integration/demo/test_scenario.py`` runs the whole script and checks those labels. Every value is
fictional. The step-by-step script is ``docs/demo/scenario.md``.
"""

from typing import Any

# Key, display name, persona, and what the picker says about each account.
ACCOUNTS: list[dict[str, str]] = [
    {
        "key": "inovator-a",
        "name": "Inovator A",
        "persona": "inovator",
        "fixture": "Produk A",
        "summary": "Inovator perorangan. Produk A (ClearSpring, saringan air) sudah terbit dengan halaman publik.",
    },
    {
        "key": "investor-a",
        "name": "Investor A",
        "persona": "mitra",
        "fixture": "Pendanaan pilot pertanian",
        "summary": "Investor pertanian tahap pilot. Satu peluang pendanaan sudah dibuka.",
    },
    {
        "key": "investor-b",
        "name": "Investor B",
        "persona": "mitra",
        "fixture": "Belum diisi",
        "summary": "Akun investor baru tanpa profil. Skenario 1: isi kebutuhan Investor B di sini.",
    },
]

PRODUCT_A: dict[str, Any] = {
    "content": {
        "title": "ClearSpring",
        "summary": "Saringan air sederhana yang mudah dirawat untuk keluarga di desa tanpa akses air bersih.",
        "problem": "Keluarga di desa tanpa jaringan air bersih perlu cara menyaring air yang mudah dirawat.",
        "solution": "Prototipe saringan bertingkat yang dapat dibersihkan tanpa alat khusus.",
        "intended_users": "Keluarga dan komunitas kecil di desa",
        "sector": "Air dan sanitasi",
        "stage": "PROTOTYPE",
        "keywords": ["air", "filter", "prototipe", "desa"],
        "facts": [
            {
                "label": "Kapasitas saring",
                "value": "10",
                "unit": "L/jam",
                "timing": "CURRENT",
                "provenance": "SELF_DECLARED",
                "key": "capacity",
            },
        ],
        "claims": [{"kind": "creator", "subject_name": "Inovator A"}],
    },
    "readiness": {
        "tkt_level": 4,
        "note": "Komponen saringan telah diuji di laboratorium pada dua sampel air keruh.",
        "evidence_photo": {
            "title": "Dokumentasi uji laboratorium ClearSpring",
            "colors": ((13, 148, 136), (240, 253, 250)),
        },
    },
    "need": {
        "outcome": "Uji lapangan saringan di dua desa",
        "support_forms": ["project_funding"],
        "relationship_form": "PROJECT",
        "scope": "biaya uji lapangan enam bulan",
        "months": 6,
        "region": "Indonesia",
        "accepts_partial": False,
        "budget": {
            "min": "10000",
            "max": "15000",
            "currency": "USD",
            "basis": "total_period",
            "period": "6 bulan",
            "scope": "biaya uji lapangan enam bulan",
            "estimated_on": "2026-11-01",
            "assumptions": "Uji di dua desa",
        },
    },
    "public_page": {
        "field_test": "Diuji 10 L/jam di satu rumah tangga selama dua minggu. Hasil dilaporkan oleh inovator.",
        "photo": {"title": "Ilustrasi ClearSpring", "colors": ((15, 118, 110), (204, 251, 241))},
        "photo_alt": "Ilustrasi demo ClearSpring: wadah saringan di atas latar hijau toska",
        "updates": [
            ("Uji rumah tangga selesai", "Saringan dipakai satu keluarga selama dua minggu. Air jernih setiap hari."),
        ],
    },
}

INVESTOR_A: dict[str, Any] = {
    "profile": {
        "subtype": "Investor pertanian",
        "thesis": "Mendanai pilot pertanian yang sudah diuji di lahan petani.",
        "sectors": ["Pertanian"],
        "stages": ["PILOT", "WORKING"],
        "regions": ["Indonesia"],
        "support_forms": ["Pendanaan proyek"],
        "relationship_forms": ["PROJECT"],
    },
    "opportunity": {
        "title": "Pendanaan pilot pertanian",
        "outcome": "Pilot pertanian berjalan di lahan petani selama satu musim tanam.",
        "included": "Biaya pilot dan pendampingan lapangan",
        "excluded": "Produksi massal",
        "support": "Pendanaan proyek",
        "accepted_stages": ["PILOT", "WORKING"],
        "relationship_forms": ["PROJECT"],
        "sectors": ["Pertanian"],
        "keywords": ["pertanian", "panen", "irigasi", "desa"],
        "timing": "Dibuka sampai 31 Maret 2027",
        "min_tkt": 6,
        "financial": {
            "subject": "partner",
            "basis": "total_period",
            "min": "30000.0000",
            "max": "80000.0000",
            "currency": "USD",
            "period": "12 bulan",
            "months": 12,
            "scope": "biaya pilot satu musim tanam",
        },
        "requirements": [],
    },
}

# Scenario 1: what the presenter types as Investor B.
INVESTOR_B: dict[str, Any] = {
    "profile": {
        "subtype": "Investor energi desa",
        "thesis": "Mendanai energi surya skala kecil untuk desa tanpa listrik stabil.",
        "sectors": ["Energi"],
        "stages": ["PROTOTYPE", "PILOT"],
        "regions": ["Indonesia"],
        "support_forms": ["Pendanaan proyek"],
        "relationship_forms": ["PROJECT"],
    },
    "opportunity": {
        "title": "Pendanaan energi surya desa",
        "outcome": "Prototipe energi surya teruji di desa dalam enam bulan.",
        "included": "Biaya uji lapangan dan pemasangan",
        "excluded": "Jaringan listrik skala besar",
        "support": "Pendanaan proyek",
        "accepted_stages": ["PROTOTYPE", "PILOT"],
        "relationship_forms": ["PROJECT"],
        "sectors": ["Energi"],
        "keywords": ["surya", "listrik", "desa", "baterai"],
        "timing": "Dibuka sampai 31 Maret 2027",
        "min_tkt": 3,
        "financial": {
            "subject": "partner",
            "basis": "total_period",
            "min": "25000.0000",
            "max": "60000.0000",
            "currency": "USD",
            "period": "6 bulan",
            "months": 6,
            "scope": "biaya uji lapangan enam bulan",
        },
        "requirements": [],
    },
}

# Scenario 2: what the presenter types as Inovator A for Produk B.
PRODUCT_B: dict[str, Any] = {
    "content": {
        "title": "SolarBox Desa",
        "summary": "Kotak listrik surya dengan baterai untuk rumah di desa tanpa listrik stabil.",
        "problem": "Rumah di desa sering tanpa listrik pada malam hari.",
        "solution": "Prototipe panel surya dan baterai dalam satu kotak yang dipasang tanpa teknisi.",
        "intended_users": "Rumah tangga di desa",
        "sector": "Energi",
        "stage": "PROTOTYPE",
        "keywords": ["surya", "listrik", "desa", "baterai"],
        "facts": [
            {
                "label": "Daya baterai",
                "value": "1",
                "unit": "kWh",
                "timing": "CURRENT",
                "provenance": "SELF_DECLARED",
                "key": "battery",
            },
        ],
        "claims": [{"kind": "creator", "subject_name": "Inovator A"}],
        "readiness": {
            "tkt_level": 5,
            "note": "Panel dan baterai diuji di lingkungan menyerupai rumah desa.",
        },
    },
    "need": {
        "outcome": "Uji lapangan SolarBox di satu desa",
        "support_forms": ["project_funding"],
        "relationship_form": "PROJECT",
        "scope": "biaya uji lapangan enam bulan",
        "months": 6,
        "region": "Indonesia",
        "accepts_partial": True,
        "budget": {
            "min": "30000",
            "max": "45000",
            "currency": "USD",
            "basis": "total_period",
            "period": "6 bulan",
            "scope": "biaya uji lapangan enam bulan",
            "estimated_on": "2026-11-01",
            "assumptions": "Sepuluh rumah di satu desa",
        },
    },
}
