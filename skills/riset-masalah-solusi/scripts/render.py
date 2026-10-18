#!/usr/bin/env python3
"""Render laporan riset (laporan.json) menjadi Markdown, LaTeX, dan PDF.

Pemakaian:
    render.py laporan.json [--out DIR] [--name NAMA] [--no-pdf] [--check] [--ringkas | --lengkap]

Hanya memakai pustaka standar Python. PDF dibuat dengan `tectonic`
(brew install tectonic); bila tidak ada, .md dan .tex tetap ditulis.
Kode keluar: 0 sukses, 1 laporan.json tidak valid, 2 kompilasi PDF gagal.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

VERDICT_OK = ("BELUM_ADA", "ADA_DI_WILAYAH_LAIN", "PERNAH_ADA_TIDAK_AKTIF")
VERDICT_LABEL = {
    "BELUM_ADA": "Belum ada di wilayah",
    "ADA_DI_WILAYAH_LAIN": "Ada di wilayah lain",
    "PERNAH_ADA_TIDAK_AKTIF": "Pernah ada, tidak aktif",
    "SUDAH_ADA_DI_WILAYAH": "Sudah ada di wilayah",
}
VERDICT_COLOR = {
    "BELUM_ADA": "okgreen",
    "ADA_DI_WILAYAH_LAIN": "amber",
    "PERNAH_ADA_TIDAK_AKTIF": "burnt",
    "SUDAH_ADA_DI_WILAYAH": "bad",
}
STATUS = ("prioritas", "terlayani", "tidak_prioritas")
STATUS_LABEL = {
    "prioritas": "Prioritas",
    "terlayani": "Sudah terlayani",
    "tidak_prioritas": "Tidak diprioritaskan",
}
JENIS = ("data", "resmi", "berita", "jurnal", "lainnya")
SKOR_KEYS = ("dampak", "urgensi", "bukti", "kelayakan_digital")
MODE = ("lengkap", "ringkas")
JENIS_SOLUSI = ("software", "software_hardware")
JENIS_SOLUSI_LABEL = {
    "software": "Software",
    "software_hardware": "Software + perangkat keras",
}
PEMROSESAN = ("edge", "cloud", "hibrida")
PEMROSESAN_LABEL = {
    "edge": "Di perangkat (edge)",
    "cloud": "Di cloud",
    "hibrida": "Hibrida (edge dan cloud)",
}
CITE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\](?!\()")


# --------------------------------------------------------------------------
# Validasi
# --------------------------------------------------------------------------

def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def safe_url(u):
    """Percent-encode karakter yang memutus sintaks link/\\url (spasi, [ ] ( ) < > dsb.).

    '%' dibiarkan agar URL yang sudah di-encode tidak di-encode dua kali.
    Contoh nyata: URL sales kit PLN Icon Plus berisi spasi dan '[Customer]', dan URL
    Wikipedia yang berakhir ')' sebelumnya terpotong di PDF dan Markdown.
    """
    if not isinstance(u, str):
        return u
    return quote(u.strip(), safe=":/?#@!$&'*+,;=%~")


def normalize_urls(d):
    """Rapikan semua field url di laporan sebelum validasi dan render."""
    if not isinstance(d, dict):
        return d

    def fix(o):
        if isinstance(o, dict) and isinstance(o.get("url"), str):
            o["url"] = safe_url(o["url"])

    for s in d.get("sumber") or []:
        fix(s)
    for m in d.get("masalah") or []:
        for e in (m.get("solusi_existing") or []) if isinstance(m, dict) else []:
            fix(e)
    for s in d.get("solusi") or []:
        kb = s.get("kebaruan") if isinstance(s, dict) else None
        for r in (kb.get("referensi_serupa") or []) if isinstance(kb, dict) else []:
            fix(r)
        hw = s.get("perangkat_keras") if isinstance(s, dict) else None
        for p in (hw.get("perangkat") or []) if isinstance(hw, dict) else []:
            fix(p)
    for g in d.get("ide_gugur") or []:
        if isinstance(g, dict):
            fix(g.get("ditemukan"))
    fix(d.get("prototipe"))
    return d


def walk_strings(o, p=""):
    if isinstance(o, str):
        yield p, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from walk_strings(v, f"{p}.{k}" if p else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_strings(v, f"{p}[{i}]")


def validate(d):
    """Kembalikan (errors, warnings); keduanya daftar string berbahasa Indonesia."""
    E, W = [], []

    def err(p, m):
        E.append(f"{p}: {m}")

    def warn(p, m):
        W.append(f"{p}: {m}")

    def text(o, k, p, required=True):
        v = o.get(k) if isinstance(o, dict) else None
        if isinstance(v, str) and v.strip():
            return v
        if required:
            err(f"{p}.{k}", "wajib diisi (teks tidak boleh kosong)")
        return ""

    def items(o, k, p, n=1):
        v = o.get(k) if isinstance(o, dict) else None
        if not isinstance(v, list) or len(v) < n:
            err(f"{p}.{k}", f"wajib berupa daftar dengan minimal {n} isi")
            return []
        return v

    def strs(o, k, p, n=1):
        out = []
        for i, it in enumerate(items(o, k, p, n)):
            if isinstance(it, str) and it.strip():
                out.append(it)
            else:
                err(f"{p}.{k}[{i}]", "harus berupa teks yang tidak kosong")
        return out

    def opt_url(o, p, required=False):
        """url opsional (atau wajib) harus diawali http(s); tanpa itu link rusak di PDF."""
        if not isinstance(o, dict):
            return
        u = o.get("url")
        if u is None or (isinstance(u, str) and not u.strip()):
            if required:
                err(f"{p}.url", "wajib diisi")
            return
        if not isinstance(u, str) or not u.startswith(("http://", "https://")):
            err(f"{p}.url", "harus diawali http:// atau https://")

    def dicts(o, k, p, n, keys):
        out = []
        for i, it in enumerate(items(o, k, p, n)):
            q = f"{p}.{k}[{i}]"
            if not isinstance(it, dict):
                err(q, "harus berupa objek")
                continue
            for kk in keys:
                text(it, kk, q)
            out.append(it)
        return out

    if not isinstance(d, dict):
        return ["(root): laporan.json harus berupa objek JSON"], W

    meta = d.get("meta") if isinstance(d.get("meta"), dict) else {}
    if not meta:
        err("meta", "wajib berupa objek")
    for k in ("judul", "topik", "wilayah", "tanggal"):
        text(meta, k, "meta")
    if meta.get("mode") is not None and meta["mode"] not in MODE:
        err("meta.mode", f"harus salah satu dari {', '.join(MODE)}")
    ringkas = meta.get("mode") == "ringkas"
    text(d, "ringkasan_eksekutif", "(root)")

    met = d.get("metodologi") if isinstance(d.get("metodologi"), dict) else {}
    if not met:
        err("metodologi", "wajib berupa objek")
    text(met, "pendekatan", "metodologi")

    prof = d.get("profil_wilayah") if isinstance(d.get("profil_wilayah"), dict) else {}
    if not prof:
        err("profil_wilayah", "wajib berupa objek")
    text(prof, "ringkasan", "profil_wilayah")
    text(prof, "kondisi_digital", "profil_wilayah")

    # --- sumber ---
    ids = set()
    jenis_of = {}
    for i, s in enumerate(items(d, "sumber", "(root)", 2)):
        q = f"sumber[{i}]"
        if not isinstance(s, dict):
            err(q, "harus berupa objek")
            continue
        if not is_int(s.get("id")):
            err(f"{q}.id", "wajib berupa angka bulat")
        elif s["id"] in ids:
            err(f"{q}.id", f"id {s['id']} dipakai dua kali")
        else:
            ids.add(s["id"])
            jenis_of[s["id"]] = s.get("jenis")
        for k in ("judul", "penerbit", "tanggal"):
            text(s, k, q)
        u = text(s, "url", q)
        if u and not u.startswith(("http://", "https://")):
            err(f"{q}.url", "harus diawali http:// atau https://")
        if s.get("jenis") not in JENIS:
            err(f"{q}.jenis", f"harus salah satu dari {', '.join(JENIS)}")
        if isinstance(s.get("tanggal"), str) and not re.search(r"\d{4}", s["tanggal"]):
            warn(f"{q}.tanggal", "tidak memuat tahun (mis. '2025' atau '12 Mar 2025')")

    def check_cites(lst, p):
        if not isinstance(lst, list) or not lst:
            err(p, "wajib berupa daftar id sumber (minimal 1)")
            return []
        good = []
        for c in lst:
            if not is_int(c) or c not in ids:
                err(p, f"id sumber {c!r} tidak ada di daftar 'sumber'")
            else:
                good.append(c)
        return good

    # --- profil: indikator ---
    for i, it in enumerate(prof.get("indikator", []) or []):
        q = f"profil_wilayah.indikator[{i}]"
        if not isinstance(it, dict):
            err(q, "harus berupa objek")
            continue
        for k in ("nama", "nilai", "tahun"):
            text(it, k, q)
        check_cites(it.get("sumber"), f"{q}.sumber")
    if not prof.get("indikator"):
        warn("profil_wilayah.indikator", "kosong; sebaiknya ada indikator kuantitatif wilayah")

    # --- masalah ---
    mids = {}
    used = set()
    n_prioritas = 0
    for i, m in enumerate(items(d, "masalah", "(root)", 1)):
        q = f"masalah[{i}]"
        if not isinstance(m, dict):
            err(q, "harus berupa objek")
            continue
        mid = text(m, "id", q)
        if mid in mids:
            err(f"{q}.id", f"id '{mid}' dipakai dua kali")
        mids[mid] = m
        text(m, "judul", q)
        text(m, "deskripsi", q)
        st = m.get("status")
        if st not in STATUS:
            err(f"{q}.status", f"harus salah satu dari {', '.join(STATUS)}")
        sk = m.get("skor")
        if not isinstance(sk, dict) or any(
            not is_int(sk.get(k)) or not 1 <= sk[k] <= 5 for k in SKOR_KEYS
        ):
            err(f"{q}.skor", f"wajib objek dengan {', '.join(SKOR_KEYS)} berupa angka 1-5")
        cited = set()
        for j, b in enumerate(items(m, "bukti", q, 1)):
            qq = f"{q}.bukti[{j}]"
            if not isinstance(b, dict):
                err(qq, "harus berupa objek")
                continue
            text(b, "fakta", qq)
            cited.update(check_cites(b.get("sumber"), f"{qq}.sumber"))
        used |= cited
        if st == "prioritas":
            n_prioritas += 1
            if len(cited) < 2:
                err(f"{q}.bukti", "masalah prioritas butuh minimal 2 sumber berbeda")
            if not any(jenis_of.get(c) in ("data", "resmi") for c in cited):
                err(f"{q}.bukti", "masalah prioritas butuh minimal 1 sumber berjenis data/resmi")
            text(m, "pihak_terdampak", q)
            strs(m, "akar_masalah", q, 1)
        if st == "terlayani":
            dicts(m, "solusi_existing", q, 1, ("nama", "celah"))
        elif m.get("solusi_existing"):
            dicts(m, "solusi_existing", q, 1, ("nama", "celah"))
        for j, e in enumerate(m.get("solusi_existing") or []):
            opt_url(e, f"{q}.solusi_existing[{j}]")
    if n_prioritas == 0:
        err("masalah", "minimal 1 masalah berstatus 'prioritas'")
    elif n_prioritas < 2:
        warn("masalah", "hanya 1 masalah prioritas; target 3-5")

    # --- solusi ---
    sol_ids = set()
    for i, s in enumerate(items(d, "solusi", "(root)", 1)):
        q = f"solusi[{i}]"
        if not isinstance(s, dict):
            err(q, "harus berupa objek")
            continue
        sid = text(s, "id", q)
        if sid in sol_ids:
            err(f"{q}.id", f"id '{sid}' dipakai dua kali")
        sol_ids.add(sid)
        mid = text(s, "masalah_id", q)
        if mid and mid not in mids:
            err(f"{q}.masalah_id", f"masalah '{mid}' tidak ada")
        elif mid and mids[mid].get("status") != "prioritas":
            warn(f"{q}.masalah_id", f"masalah '{mid}' tidak berstatus prioritas")
        for k in ("nama", "tagline", "ringkasan", "value_proposition", "platform", "model_bisnis"):
            text(s, k, q)
        if not ringkas:
            text(s, "arsitektur", q)
        elif s.get("arsitektur") is not None:
            text(s, "arsitektur", q)
        # di mode ringkas, bagian berikut tidak ditampilkan sehingga boleh dikosongkan
        if not ringkas or s.get("target_pengguna"):
            dicts(s, "target_pengguna", q, 1, ("persona", "kebutuhan"))
        strs(s, "fitur_mvp", q, 3)
        if not ringkas or s.get("fitur_lanjutan"):
            strs(s, "fitur_lanjutan", q, 1)
        dicts(s, "tech_stack", q, 3, ("lapisan", "teknologi"))
        if not ringkas or s.get("integrasi_data"):
            strs(s, "integrasi_data", q, 1)
        if not ringkas or s.get("mitra"):
            strs(s, "mitra", q, 1)
        strs(s, "regulasi", q, 1)
        dicts(s, "risiko", q, 2, ("risiko", "mitigasi"))
        dicts(s, "roadmap", q, 3, ("fase", "durasi", "target"))
        strs(s, "metrik", q, 2)
        if s.get("kompetitor"):
            dicts(s, "kompetitor", q, 1, ("nama", "kekuatan", "kelemahan"))
        elif not ringkas:
            warn(f"{q}.kompetitor", "kosong; cantumkan alternatif/kompetitor bila ada")
        # jenis solusi: software saja (default) atau software + perangkat keras
        js = s.get("jenis_solusi", "software")
        if js not in JENIS_SOLUSI:
            err(f"{q}.jenis_solusi", f"harus salah satu dari {', '.join(JENIS_SOLUSI)}")
        elif js == "software_hardware":
            hw = s.get("perangkat_keras")
            hq = f"{q}.perangkat_keras"
            if not isinstance(hw, dict):
                err(hq, "wajib berupa objek bila jenis_solusi = software_hardware")
            else:
                text(hw, "ringkasan", hq)
                text(hw, "data_sensor", hq)
                dicts(hw, "perangkat", hq, 1, ("nama", "fungsi", "spesifikasi", "perkiraan_biaya"))
                for j, pr in enumerate(hw.get("perangkat") or []):
                    if not isinstance(pr, dict):
                        continue
                    opt_url(pr, f"{hq}.perangkat[{j}]")
                    if pr.get("jumlah") is not None and not (isinstance(pr["jumlah"], str) and pr["jumlah"].strip()):
                        err(f"{hq}.perangkat[{j}].jumlah", "bila diisi harus berupa teks yang tidak kosong")
                    if pr.get("sumber"):
                        for c in check_cites(pr["sumber"], f"{hq}.perangkat[{j}].sumber"):
                            used.add(c)
                    else:
                        warn(f"{hq}.perangkat[{j}].sumber",
                             "harga/spesifikasi tanpa sumber; cantumkan halaman produk atau datasheet bertanggal, "
                             "atau tulis jelas bahwa angkanya estimasi")
                if hw.get("pemrosesan") not in PEMROSESAN:
                    err(f"{hq}.pemrosesan", f"harus salah satu dari {', '.join(PEMROSESAN)}")
                for k in ("pemrosesan_keterangan", "konektivitas_daya", "instalasi_pemeliharaan",
                          "biaya", "pengadaan"):
                    text(hw, k, hq)
                strs(hw, "privasi_keselamatan", hq, 1)
        elif s.get("perangkat_keras") is not None:
            err(f"{q}.perangkat_keras", "hanya boleh ada bila jenis_solusi = software_hardware")
        pn = s.get("penilaian")
        if (not isinstance(pn, dict)
                or any(not is_int(pn.get(k)) or not 1 <= pn[k] <= 5 for k in ("dampak", "kompleksitas"))
                or not isinstance(pn.get("waktu_mvp"), str) or not pn["waktu_mvp"].strip()):
            err(f"{q}.penilaian", "wajib objek: dampak (1-5), kompleksitas (1-5), waktu_mvp (teks)")
        for c in check_cites(s.get("sumber"), f"{q}.sumber"):
            used.add(c)
        kb = s.get("kebaruan")
        if not isinstance(kb, dict):
            err(f"{q}.kebaruan", "wajib berupa objek")
            continue
        v = kb.get("verdict")
        if v == "SUDAH_ADA_DI_WILAYAH":
            err(f"{q}.kebaruan.verdict",
                "solusi yang sudah ada di wilayah harus dipindahkan ke 'ide_gugur', bukan 'solusi'")
        elif v not in VERDICT_OK:
            err(f"{q}.kebaruan.verdict", f"harus salah satu dari {', '.join(VERDICT_OK)}")
        text(kb, "ringkasan", f"{q}.kebaruan")
        text(kb, "pembeda", f"{q}.kebaruan")
        dicts(kb, "log_pencarian", f"{q}.kebaruan", 3, ("kanal", "query", "hasil"))
        if js == "software_hardware":
            kanal_hw = re.compile(r"marketplace|toko|e-?katalog|katalog|vendor|cctv|iot|pengadaan|lpse|kampus|pilot|distributor",
                                  re.I)
            if not any(isinstance(l, dict) and kanal_hw.search(str(l.get("kanal", "")))
                       for l in kb.get("log_pencarian") or []):
                warn(f"{q}.kebaruan.log_pencarian",
                     "solusi berperangkat keras sebaiknya punya minimal 1 kanal khusus perangkat keras "
                     "(marketplace, e-katalog, vendor CCTV/IoT, atau proyek kampus)")
        if v in ("ADA_DI_WILAYAH_LAIN", "PERNAH_ADA_TIDAK_AKTIF"):
            dicts(kb, "referensi_serupa", f"{q}.kebaruan", 1, ("nama", "lokasi", "catatan"))
        for j, r in enumerate(kb.get("referensi_serupa") or []):
            opt_url(r, f"{q}.kebaruan.referensi_serupa[{j}]")

    # --- prototipe (opsional) ---
    pt = d.get("prototipe")
    if pt is not None:
        if not isinstance(pt, dict):
            err("prototipe", "harus berupa objek")
        else:
            sid = text(pt, "solusi_id", "prototipe")
            if sid and sid not in sol_ids:
                err("prototipe.solusi_id", f"solusi '{sid}' tidak ada")
            u = text(pt, "url", "prototipe")
            if u and not u.startswith(("http://", "https://")):
                err("prototipe.url", "harus diawali http:// atau https://")
            text(pt, "ringkasan", "prototipe")
            strs(pt, "skenario", "prototipe", 1)
            strs(pt, "cara_mencoba", "prototipe", 1)
            if pt.get("batasan"):
                strs(pt, "batasan", "prototipe", 1)

    # --- ide gugur ---
    for i, g in enumerate(d.get("ide_gugur") or []):
        q = f"ide_gugur[{i}]"
        if not isinstance(g, dict):
            err(q, "harus berupa objek")
            continue
        text(g, "nama", q)
        text(g, "alasan", q)
        f = g.get("ditemukan")
        if not isinstance(f, dict) or not isinstance(f.get("nama"), str) or not isinstance(f.get("url"), str):
            err(f"{q}.ditemukan", "wajib objek berisi nama dan url aplikasi/sistem yang sudah ada")
        else:
            opt_url(f, f"{q}.ditemukan", required=True)
        if g.get("masalah_id") and g["masalah_id"] not in mids:
            err(f"{q}.masalah_id", f"masalah '{g['masalah_id']}' tidak ada")

    # --- sitasi inline [n] ---
    for k, v in d.items():
        if k == "sumber":
            continue
        for p, t in walk_strings(v, k):
            for m_ in CITE.finditer(t):
                for c in m_.group(1).split(","):
                    c = int(c)
                    used.add(c)
                    if c not in ids:
                        err(p, f"sitasi [{c}] tidak ada di daftar 'sumber'")
    for sid in sorted(ids - used):
        warn("sumber", f"sumber {sid} tidak pernah dikutip")
    return E, W


# --------------------------------------------------------------------------
# Blok dokumen (dipakai bersama oleh emitter MD dan TeX)
# --------------------------------------------------------------------------

def paras(t):
    return [p.strip() for p in re.split(r"\n\s*\n", t.strip()) if p.strip()]


def cites(ids):
    return f" [{', '.join(str(i) for i in ids)}]" if ids else ""


def skor_total(m):
    return sum(m["skor"][k] for k in SKOR_KEYS)


def build_blocks(d):
    B = []
    A = B.append
    meta = d["meta"]
    masalah = d["masalah"]
    solusi = d["solusi"]
    M = {m["id"]: m for m in masalah}
    src = sorted(d["sumber"], key=lambda s: s["id"])
    anyhw = any(s.get("jenis_solusi") == "software_hardware" for s in solusi)
    ringkas = meta.get("mode") == "ringkas"

    def jenis_pendek(s):
        return "Software + hardware" if s.get("jenis_solusi") == "software_hardware" else "Software"

    # 1. Ringkasan eksekutif
    A(("h", 1, "Ringkasan Eksekutif"))
    for p in paras(d["ringkasan_eksekutif"]):
        A(("p", p))
    rows = []
    for s in solusi:
        m = M.get(s["masalah_id"], {})
        rows.append([
            f"**{s['id']}** {s['nama']}",
            f"{m.get('id', '')} {m.get('judul', '')}",
            VERDICT_LABEL[s["kebaruan"]["verdict"]],
        ])
    if anyhw:
        rows = [r[:2] + [jenis_pendek(s)] + r[2:] for r, s in zip(rows, solusi)]
        A(("table", ["Solusi", "Masalah yang diselesaikan", "Jenis", "Kebaruan di wilayah"], rows,
           [0.28, 0.36, 0.16, 0.2]))
    else:
        A(("table", ["Solusi", "Masalah yang diselesaikan", "Kebaruan di wilayah"], rows, [0.34, 0.44, 0.22]))

    # 2. Metodologi
    A(("h", 1, "Metodologi"))
    for p in paras(d["metodologi"]["pendekatan"]):
        A(("p", p))
    if d["metodologi"].get("langkah") and not ringkas:
        A(("ol", d["metodologi"]["langkah"]))
    if ringkas:
        digital_r = ("software, termasuk software yang terintegrasi perangkat keras" if anyhw else "software")
        A(("h", 3, "Penilaian dan cek kebaruan"))
        A(("p", "Setiap masalah dinilai 1-5 pada **dampak**, **urgensi**, **bukti**, dan **kelayakan digital** "
                f"(porsi masalah yang bisa dibantu {digital_r}); skor total maksimum 20. Setiap ide solusi "
                "dicek terhadap sistem yang sudah berjalan di wilayah ini dan diberi label **Belum ada di "
                "wilayah**, **Ada di wilayah lain**, atau **Pernah ada, tidak aktif**. Ide yang sudah ada "
                "di wilayah dibuang (Lampiran A)."))
    else:
        A(("h", 3, "Penilaian masalah"))
        digital = "software"
        if anyhw:
            digital = ("software, termasuk software yang terintegrasi perangkat keras seperti kamera, "
                       "sensor, atau edge device")
        A(("p", "Setiap masalah dinilai 1-5 pada empat dimensi: **dampak** (skala pihak terdampak dan "
                "tingkat keparahan), **urgensi** (tren dan tenggat), **bukti** (kekuatan dan kebaruan "
                "data), dan **kelayakan digital** (seberapa besar porsi masalah yang bisa dibantu "
                f"{digital}). Skor total maksimum 20."))
        A(("h", 3, "Cek kebaruan solusi"))
        A(("p", "Setiap ide solusi dicek terhadap aplikasi, sistem, dan program yang sudah berjalan di "
                "wilayah ini. Ide yang sudah ada di wilayah dibuang dari rekomendasi (lihat Lampiran A). "
                "Hasil cek yang lolos diberi salah satu label berikut:"))
        A(("ul", [
            "**Belum ada di wilayah**: tidak ditemukan solusi serupa yang aktif di mana pun relevan.",
            "**Ada di wilayah lain**: ada di daerah/negara lain; dicatat sebagai referensi dan diadaptasi.",
            "**Pernah ada, tidak aktif**: pernah dicoba di wilayah ini namun berhenti; pelajarannya dicatat.",
        ]))
    if anyhw:
        A(("h", 3, "Solusi dengan perangkat keras"))
        A(("p", "Solusi yang memakai perangkat keras (kamera, CCTV, Raspberry Pi atau mikrokontroler, "
                "sensor) dinilai juga pada biaya perangkat, ketersediaan dan pengadaan lokal, "
                "pemasangan dan perawatan, serta privasi dan keselamatan. Cek kebaruan mencakup "
                "produk perangkat keras yang dijual dan dipasang di wilayah ini, bukan hanya aplikasi. "
                "Harga dan spesifikasi adalah perkiraan bertanggal dari sumber yang dicantumkan; "
                "angka tanpa sumber ditandai sebagai estimasi."))
    A(("h", 3, "Keterbatasan"))
    lim = list(d["metodologi"].get("keterbatasan") or [])
    lim.append("Cek kebaruan berbasis pencarian publik pada tanggal riset; tidak menjamin tidak ada "
               "sistem serupa yang belum terpublikasi atau tidak terindeks. Validasi lapangan dengan "
               "calon pengguna dan pemerintah daerah tetap diperlukan.")
    A(("ul", lim))

    # 3. Profil wilayah
    A(("h", 1, "Profil Wilayah"))
    for p in paras(d["profil_wilayah"]["ringkasan"]):
        A(("p", p))
    ind = d["profil_wilayah"].get("indikator") or []
    if ind:
        A(("table", ["Indikator", "Nilai", "Tahun", "Sumber"],
           [[i["nama"], i["nilai"], i["tahun"], cites(i["sumber"]).strip()] for i in ind],
           [0.42, 0.26, 0.12, 0.2]))
    A(("h", 3, "Kondisi digital"))
    for p in paras(d["profil_wilayah"]["kondisi_digital"]):
        A(("p", p))

    # 4. Peta dan prioritas masalah
    A(("h", 1, "Peta dan Prioritas Masalah"))
    A(("p", "Skor 1-5 per dimensi; total maksimum 20. Diurutkan dari skor total tertinggi."))
    rows = []
    for m in sorted(masalah, key=lambda m: -skor_total(m) if "skor" in m else 0):
        sk = m["skor"]
        rows.append([m["id"], m["judul"], STATUS_LABEL[m["status"]], str(sk["dampak"]), str(sk["urgensi"]),
                     str(sk["bukti"]), str(sk["kelayakan_digital"]), f"**{skor_total(m)}**"])
    A(("table", ["ID", "Masalah", "Status", "Dampak", "Urgensi", "Bukti", "Digital", "Total"], rows,
       [0.06, 0.30, 0.15, (0.1, "c"), (0.1, "c"), (0.1, "c"), (0.1, "c"), (0.09, "c")]))

    # 5. Detail masalah
    A(("h", 1, "Detail Masalah"))
    order = [m for m in masalah if m["status"] == "prioritas"] + \
            [m for m in masalah if m["status"] != "prioritas"]
    if ringkas:
        skipped = [m for m in order if m["status"] == "tidak_prioritas"]
        order = [m for m in order if m["status"] != "tidak_prioritas"]
        if skipped:
            A(("p", "Masalah yang tidak diprioritaskan (" + ", ".join(m["id"] for m in skipped)
                    + ") hanya tercantum pada tabel di bagian sebelumnya."))
    for m in order:
        A(("h", 2, f"{m['id']}: {m['judul']}"))
        if m["status"] != "prioritas":
            A(("callout", STATUS_LABEL[m["status"]],
               "Masalah ini tidak menjadi dasar rekomendasi solusi baru."))
        for p in paras(m["deskripsi"]):
            A(("p", p))
        A(("h", 3, "Bukti"))
        A(("ul", [b["fakta"] + cites(b["sumber"]) for b in m["bukti"]]))
        if m.get("pihak_terdampak"):
            if ringkas:
                A(("p", "**Pihak terdampak:** " + m["pihak_terdampak"]))
            else:
                A(("h", 3, "Pihak terdampak"))
                A(("p", m["pihak_terdampak"]))
        if m.get("akar_masalah"):
            A(("h", 3, "Akar masalah"))
            A(("ul", m["akar_masalah"]))
        if m.get("solusi_existing"):
            A(("h", 3, "Solusi yang sudah ada dan celahnya"))
            A(("table", ["Solusi/program", "Celah"],
               [[(f"[{e['nama']}]({e['url']})" if e.get("url") else e["nama"]), e["celah"]]
                for e in m["solusi_existing"]], [0.35, 0.65]))
        if m.get("catatan_non_software"):
            A(("callout", "Di luar jangkauan software", m["catatan_non_software"]))

    # 6. Solusi software
    A(("h", 1, "Solusi Software dan Perangkat Keras" if anyhw else "Solusi Software"))
    A(("p", "Semua solusi di bawah lolos cek kebaruan: tidak ditemukan sistem dengan fungsi inti yang "
            "sama dan aktif melayani wilayah ini"
            + (" (termasuk produk perangkat keras yang dijual dan dipasang di wilayah ini)" if anyhw else "")
            + ". Kemiripan sebagian dicatat pada bagian Kebaruan dan "
            "Kompetitor tiap solusi. Detail pencarian ada di Lampiran B."))
    for s in solusi:
        m = M.get(s["masalah_id"], {})
        pn = s["penilaian"]
        kb = s["kebaruan"]
        A(("h", 2, f"{s['id']}: {s['nama']}"))
        hw = s.get("perangkat_keras") if s.get("jenis_solusi") == "software_hardware" else None
        card_rows = [
            ("Masalah", f"{m.get('id', '')} {m.get('judul', '')}"),
            ("Platform", s["platform"]),
        ]
        if hw:
            card_rows += [("Jenis solusi", JENIS_SOLUSI_LABEL["software_hardware"]),
                          ("Pemrosesan", PEMROSESAN_LABEL[hw["pemrosesan"]])]
        card_rows += [
            ("Dampak / kompleksitas", f"{pn['dampak']}/5 dan {pn['kompleksitas']}/5"),
            ("Waktu MVP", pn["waktu_mvp"]),
        ]
        A(("card", f"{s['id']} / {s['nama']}", s["tagline"], kb["verdict"], card_rows))
        A(("h", 3, "Ringkasan"))
        for p in paras(s["ringkasan"]):
            A(("p", p))
        if not ringkas:
            A(("h", 3, "Target pengguna"))
            A(("table", ["Persona", "Kebutuhan"],
               [[t["persona"], t["kebutuhan"]] for t in s["target_pengguna"]], [0.3, 0.7]))
        elif s.get("target_pengguna"):
            A(("p", "**Pengguna:** " + "; ".join(f"{t['persona']} ({t['kebutuhan']})" for t in s["target_pengguna"])))
        A(("h", 3, "Value proposition"))
        A(("p", s["value_proposition"]))
        A(("h", 3, "Fitur MVP"))
        A(("ul", s["fitur_mvp"]))
        if not ringkas:
            A(("h", 3, "Fitur lanjutan"))
            A(("ul", s["fitur_lanjutan"]))
        A(("h", 3, "Platform dan tech stack"))
        A(("p", s["platform"]))
        A(("table", ["Lapisan", "Teknologi"],
           [[t["lapisan"], t["teknologi"]] for t in s["tech_stack"]], [0.25, 0.75]))
        if not ringkas:
            A(("h", 3, "Arsitektur"))
            for p in paras(s["arsitektur"]):
                A(("p", p))
        if hw:
            A(("h", 3, "Perangkat keras dan integrasi"))
            for p in paras(hw["ringkasan"]):
                A(("p", p))
            bom = []
            for pr in hw["perangkat"]:
                nama = f"[{pr['nama']}]({pr['url']})" if pr.get("url") else pr["nama"]
                bom.append([nama, pr["fungsi"], pr["spesifikasi"], pr.get("jumlah") or "-",
                            pr["perkiraan_biaya"] + cites(pr.get("sumber"))])
            A(("table", ["Komponen", "Fungsi", "Spesifikasi", "Jumlah", "Perkiraan biaya"], bom,
               [0.19, 0.2, 0.27, 0.1, 0.24]))
            A(("table", ["Aspek", "Keterangan"], [
                ["Data yang ditangkap", hw["data_sensor"]],
                ["Pemrosesan", f"{PEMROSESAN_LABEL[hw['pemrosesan']]}: {hw['pemrosesan_keterangan']}"],
                ["Konektivitas dan daya", hw["konektivitas_daya"]],
                ["Pemasangan dan perawatan", hw["instalasi_pemeliharaan"]],
                ["Biaya", hw["biaya"]],
                ["Pengadaan", hw["pengadaan"]],
            ], [0.26, 0.74]))
            A(("h", 3, "Privasi dan keselamatan perangkat"))
            A(("ul", hw["privasi_keselamatan"]))
        if not ringkas:
            A(("h", 3, "Integrasi dan sumber data"))
            A(("ul", s["integrasi_data"]))
        A(("h", 3, "Kebaruan di wilayah ini"))
        A(("p", kb["ringkasan"]))
        A(("table", None, [["**Pembeda**", kb["pembeda"]]], [0.2, 0.8]))
        if kb.get("referensi_serupa"):
            A(("table", ["Referensi serupa", "Lokasi", "Catatan dan adaptasi"],
               [[(f"[{r['nama']}]({r['url']})" if r.get("url") else r["nama"]), r["lokasi"], r["catatan"]]
                for r in kb["referensi_serupa"]], [0.28, 0.2, 0.52]))
        if s.get("kompetitor") and not ringkas:
            A(("h", 3, "Kompetitor dan alternatif"))
            A(("table", ["Nama", "Kekuatan", "Kelemahan"],
               [[c["nama"], c["kekuatan"], c["kelemahan"]] for c in s["kompetitor"]], [0.24, 0.38, 0.38]))
        A(("h", 3, "Model bisnis dan pendanaan"))
        A(("p", s["model_bisnis"]))
        if not ringkas:
            A(("h", 3, "Mitra dan stakeholder"))
            A(("ul", s["mitra"]))
        A(("h", 3, "Regulasi dan kepatuhan"))
        A(("ul", s["regulasi"]))
        A(("h", 3, "Risiko dan mitigasi"))
        A(("table", ["Risiko", "Mitigasi"],
           [[r["risiko"], r["mitigasi"]] for r in s["risiko"]], [0.4, 0.6]))
        A(("h", 3, "Roadmap"))
        A(("table", ["Fase", "Durasi", "Target"],
           [[r["fase"], r["durasi"], r["target"]] for r in s["roadmap"]], [0.24, 0.16, 0.6]))
        A(("h", 3, "Metrik keberhasilan"))
        A(("ul", s["metrik"]))
        A(("p", "Rujukan:" + cites(s["sumber"])))

    # 7. Prototipe (opsional)
    pt = d.get("prototipe")
    if pt:
        ps = next((x for x in solusi if x["id"] == pt["solusi_id"]), None)
        A(("h", 1, "Prototipe"))
        for p in paras(pt["ringkasan"]):
            A(("p", p))
        A(("table", None, [
            ["**Solusi**", f"{ps['id']} {ps['nama']}" if ps else pt["solusi_id"]],
            ["**Tautan**", f"[{pt['url']}]({pt['url']})"],
        ], [0.2, 0.8]))
        A(("h", 3, "Skenario yang didemokan"))
        A(("ol", pt["skenario"]))
        A(("h", 3, "Cara mencoba"))
        A(("ul", pt["cara_mencoba"]))
        if pt.get("batasan"):
            A(("h", 3, "Batasan prototipe"))
            A(("ul", pt["batasan"]))

    # 8. Matriks rekomendasi
    A(("h", 1, "Matriks Rekomendasi"))
    A(("p", "Urutan: dampak tertinggi lebih dulu; kompleksitas terendah sebagai pemisah."))
    rows = []
    for n, s in enumerate(sorted(solusi, key=lambda s: (-s["penilaian"]["dampak"],
                                                       s["penilaian"]["kompleksitas"])), 1):
        pn = s["penilaian"]
        row = [str(n), f"**{s['id']}** {s['nama']}", s["masalah_id"]]
        if anyhw:
            row.append(jenis_pendek(s))
        row += [str(pn["dampak"]), str(pn["kompleksitas"]), pn["waktu_mvp"],
                VERDICT_LABEL[s["kebaruan"]["verdict"]]]
        rows.append(row)
    if anyhw:
        A(("table", ["#", "Solusi", "Masalah", "Jenis", "Dampak", "Kompleksitas", "Waktu MVP", "Kebaruan"], rows,
           [(0.05, "c"), 0.18, (0.08, "c"), 0.12, (0.1, "c"), (0.15, "c"), 0.14, 0.18]))
    else:
        A(("table", ["#", "Solusi", "Masalah", "Dampak", "Kompleksitas", "Waktu MVP", "Kebaruan"], rows,
           [(0.05, "c"), 0.25, (0.09, "c"), (0.1, "c"), (0.16, "c"), 0.14, 0.21]))

    # Lampiran
    A(("appendix",))
    A(("h", 1, "Ide yang Gugur"))
    gugur = d.get("ide_gugur") or []
    if gugur:
        A(("p", "Ide berikut dibuang karena sudah ada sistem serupa yang berjalan di wilayah ini."))
        A(("table", ["Ide", "Masalah", "Alasan", "Sudah ada"],
           [[g["nama"], g.get("masalah_id", "-"), g["alasan"],
             f"[{g['ditemukan']['nama']}]({g['ditemukan']['url']})"] for g in gugur],
           [0.24, 0.1, 0.38, 0.28]))
    else:
        A(("p", "Tidak ada ide yang gugur pada riset ini."))
    A(("h", 1, "Log Pencarian Kebaruan"))
    if ringkas:
        A(("table", ["Solusi", "Kanal", "Query", "Hasil"],
           [[f"**{s['id']}**", l["kanal"], f"`{l['query']}`", l["hasil"]]
            for s in solusi for l in s["kebaruan"]["log_pencarian"]],
           [0.08, 0.17, 0.33, 0.42]))
    else:
        for s in solusi:
            A(("h", 2, f"{s['id']}: {s['nama']}"))
            A(("table", ["Kanal", "Query", "Hasil"],
               [[l["kanal"], f"`{l['query']}`", l["hasil"]] for l in s["kebaruan"]["log_pencarian"]],
               [0.2, 0.34, 0.46]))
    A(("h", 1, "Daftar Pustaka"))
    ent = []
    for s in src:
        ent.append((s["id"], f"**{s['judul']}**. {s['penerbit']}, {s['tanggal']}. "
                             f"({s['jenis']}) {s['url']}"))
    A(("bib", ent))
    return B


# --------------------------------------------------------------------------
# Emitter Markdown
# --------------------------------------------------------------------------

def md_cell(c):
    return str(c).replace("|", "\\|").replace("\n", "<br>")


def emit_md(d, blocks):
    meta = d["meta"]
    out = [f"# {meta['judul']}", "",
           f"**Topik:** {meta['topik']}  ",
           f"**Wilayah:** {meta['wilayah']}  ",
           f"**Tanggal riset:** {meta['tanggal']}  ",
           f"**Disusun oleh:** {meta.get('penyusun') or 'Claude Code (skill riset-masalah-solusi)'}", ""]
    sec = sub = 0
    appendix = False
    prefix = ""
    for b in blocks:
        t = b[0]
        if t == "appendix":
            appendix, sec = True, 0
        elif t == "h":
            lvl, text = b[1], b[2]
            if lvl == 1:
                sec += 1
                sub = 0
                prefix = chr(64 + sec) if appendix else str(sec)
                head = f"{'Lampiran ' if appendix else ''}{prefix}. {text}"
                out += [f"## {head}", ""]
            elif lvl == 2:
                sub += 1
                out += [f"### {prefix}.{sub} {text}", ""]
            else:
                out += [f"#### {text}", ""]
        elif t == "p":
            out += [b[1], ""]
        elif t == "ul":
            out += [f"- {x}" for x in b[1]] + [""]
        elif t == "ol":
            out += [f"{i}. {x}" for i, x in enumerate(b[1], 1)] + [""]
        elif t == "table":
            head, rows = b[1], b[2]
            if not rows:
                continue
            n = len(rows[0])
            out.append("| " + " | ".join(md_cell(h) for h in head) + " |" if head else "|" + " |" * n)
            out.append("|" + "---|" * n)
            for r in rows:
                out.append("| " + " | ".join(md_cell(c) for c in r) + " |")
            out.append("")
        elif t == "callout":
            out += [f"> **{b[1]}**: {b[2]}", ""]
        elif t == "card":
            _, title, tagline, verdict, rows = b
            out += [f"> **{title}**  ", f"> *{tagline}*  ",
                    f"> **Kebaruan:** {VERDICT_LABEL[verdict]}  "]
            out += [f"> **{k}:** {v}  " for k, v in rows] + [""]
        elif t == "bib":
            out += [f"- **[{i}]** {x}" for i, x in b[1]] + [""]
    return "\n".join(out).rstrip() + "\n"


# --------------------------------------------------------------------------
# Emitter LaTeX
# --------------------------------------------------------------------------

TEX_MAP = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
TEX_SYMS = {"✅": "[v]", "✔": "[v]", "✓": "[v]", "❌": "[x]", "✗": "[x]", "✘": "[x]", "⚠": "(!)",
            "\u2011": "-", "\u00a0": " ", "\u200b": ""}
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200d]")
INL = re.compile(
    r"\*\*(?P<b>.+?)\*\*"
    r"|`(?P<c>[^`]+)`"
    r"|\[(?P<lt>[^\]]+)\]\((?P<lu>https?://[^)\s]+)\)"
    r"|\[(?P<n>\d+(?:\s*,\s*\d+)*)\]"
    r"|(?P<u>https?://[^\s<>\]\)]*[^\s<>\]\).,;:!?])"
)


def tex_escape(t):
    for k, v in TEX_SYMS.items():
        t = t.replace(k, v)
    t = EMOJI.sub("", t)
    t = re.sub(r'"([^"\n]*)"', "\u201c\\1\u201d", t)
    return "".join(TEX_MAP.get(c, c) for c in t)


def tex_url(u):
    return u.replace("%", r"\%").replace("#", r"\#").replace("&", r"\&")


def tex_inline(t, plain=False):
    out, pos = [], 0
    for m in INL.finditer(t):
        out.append(tex_escape(t[pos:m.start()]))
        pos = m.end()
        if m.group("b") is not None:
            inner = tex_inline(m.group("b"), plain)
            out.append(inner if plain else r"\textbf{" + inner + "}")
        elif m.group("c") is not None:
            c = tex_escape(m.group("c"))
            out.append(c if plain else r"\texttt{" + c + "}")
        elif m.group("lt") is not None:
            txt = tex_escape(m.group("lt"))
            out.append(txt if plain else r"\href{" + tex_url(m.group("lu")) + "}{" + txt + "}")
        elif m.group("n") is not None:
            ids = [x.strip() for x in m.group("n").split(",")]
            out.append("[" + ", ".join(ids if plain else [r"\hyperlink{src%s}{%s}" % (i, i) for i in ids]) + "]")
        else:
            u = m.group("u")
            out.append(tex_escape(u) if plain else r"\url{" + tex_url(u) + "}")
    out.append(tex_escape(t[pos:]))
    return "".join(out)


PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}
\setmainfont{texgyrepagella}[Ligatures=TeX,Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
\setsansfont{texgyreheros}[Ligatures=TeX,Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
\usepackage[indonesian]{babel}
\usepackage[a4paper,margin=2.3cm]{geometry}
\usepackage[table]{xcolor}
\definecolor{primary}{HTML}{0F4C5C}
\definecolor{accent}{HTML}{E36414}
\definecolor{linkblue}{HTML}{1F5FA8}
\definecolor{okgreen}{HTML}{2E7D32}
\definecolor{amber}{HTML}{9A6700}
\definecolor{burnt}{HTML}{C2410C}
\definecolor{bad}{HTML}{B91C1C}
\usepackage{booktabs,longtable,array,tabularx,enumitem,fancyhdr,titlesec,needspace}
\usepackage[most]{tcolorbox}
\usepackage{xurl}
\usepackage[colorlinks=true,linkcolor=primary,urlcolor=linkblue,citecolor=primary,pdftitle={%%PDFTITLE%%},pdfauthor={Claude Code}]{hyperref}

\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}
\clubpenalty=10000
\widowpenalty=10000
\emergencystretch=3em
\setcounter{secnumdepth}{2}
\setcounter{tocdepth}{2}
\setlist{leftmargin=1.4em,itemsep=2pt,topsep=3pt,parsep=0pt}
\titleformat{\section}{\sffamily\bfseries\Large\color{primary}}{\thesection}{0.6em}{}[{\color{primary}\titlerule[0.8pt]}]
\titleformat{\subsection}{\sffamily\bfseries\large\color{primary}}{\thesubsection}{0.6em}{}
\titleformat{\subsubsection}{\sffamily\bfseries\normalsize\color{black!75}}{}{0em}{}
\titlespacing*{\section}{0pt}{18pt}{8pt}
\titlespacing*{\subsection}{0pt}{14pt}{5pt}
\titlespacing*{\subsubsection}{0pt}{9pt}{3pt}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\sffamily\small\color{black!60}%%SHORT%%}
\fancyhead[R]{\sffamily\small\color{black!60}%%WILAYAH%%}
\fancyfoot[C]{\sffamily\small\thepage}
\renewcommand{\headrulewidth}{0.3pt}
\setlength{\headheight}{14pt}
\newlength{\tw}
\newcommand{\badge}[2]{\colorbox{#1}{\strut\textcolor{white}{\sffamily\bfseries\small\,#2\,}}}

\begin{document}
"""


def tex_table(head, rows, widths):
    n = len(widths)
    cols = []
    for w in widths:
        f, al = w if isinstance(w, tuple) else (w, "l")
        fmt = r">{\centering\arraybackslash}" if al == "c" else r">{\raggedright\arraybackslash}"
        cols.append(f"{fmt}p{{{f:.3f}\\tw}}")
    o = [r"{\small\arrayrulecolor{black!35}\renewcommand{\arraystretch}{1.25}",
         r"\setlength{\tw}{\dimexpr\linewidth-%d\tabcolsep\relax}" % (2 * n),
         r"\begin{longtable}{" + "".join(cols) + "}"]
    if head:
        row = r"\rowcolor{primary!12} " + " & ".join(r"\textbf{" + tex_inline(h, True) + "}" for h in head) + r" \\"
        o += [r"\toprule", row, r"\midrule\endfirsthead", r"\toprule", row, r"\midrule\endhead"]
    o += [r"\bottomrule\endfoot", r"\bottomrule\endlastfoot"]
    if not head:
        o.append(r"\toprule")
    for i, r in enumerate(rows):
        o.append(" & ".join(tex_inline(c) for c in r) + r" \\")
        if i < len(rows) - 1:
            o.append(r"\midrule[0.3pt]")
    o += [r"\end{longtable}}", ""]
    return "\n".join(o)


def emit_tex(d, blocks):
    meta = d["meta"]
    pdftitle = re.sub(r"[\\{}%#&_~^$]", "", meta["judul"])
    def clip(t, n):
        return t if len(t) <= n else t[:n - 3].rstrip() + "..."
    short = clip(meta["topik"], 46)
    region = clip(meta["wilayah"], 36)
    pre = (PREAMBLE.replace("%%PDFTITLE%%", pdftitle)
           .replace("%%SHORT%%", tex_inline(short, True))
           .replace("%%WILAYAH%%", tex_inline(region, True)))
    penyusun = meta.get("penyusun") or "Claude Code (skill riset-masalah-solusi)"
    o = [pre, r"""\begin{titlepage}
\thispagestyle{empty}
\raggedright
\vspace*{2.2cm}
{\color{accent}\rule{3.2cm}{4pt}}\par\vspace{0.7cm}
{\sffamily\bfseries\fontsize{27}{33}\selectfont\color{primary} """ + tex_inline(meta["judul"], True) + r"""\par}
\vspace{0.8cm}
{\sffamily\large\color{black!75}
\textbf{Topik}\quad """ + tex_inline(meta["topik"], True) + r"""\par\smallskip
\textbf{Wilayah}\quad """ + tex_inline(meta["wilayah"], True) + r"""\par}
\vfill
{\sffamily\small\color{black!60} Tanggal riset: """ + tex_inline(meta["tanggal"], True) + r"""\par
""" + tex_inline(penyusun, True) + r"""\par}
\end{titlepage}
\tableofcontents
\clearpage
"""]
    for idx, b in enumerate(blocks):
        t = b[0]
        nxt = blocks[idx + 1][0] if idx + 1 < len(blocks) else None
        if t == "appendix":
            o.append(r"\appendix")
        elif t == "h":
            cmd = {1: r"\section", 2: r"\subsection", 3: r"\subsubsection*"}[b[1]]
            need = {1: 12, 2: 9, 3: 8}[b[1]]
            o.append(r"\Needspace{%d\baselineskip}" % need + cmd + "{" + tex_inline(b[2], True) + "}")
        elif t == "p":
            # paragraf pengantar tabel dijaga satu halaman dengan baris pertama tabel
            keep = r"\Needspace{9\baselineskip}" if nxt == "table" else ""
            o += [keep + tex_inline(b[1]), ""]
        elif t in ("ul", "ol"):
            env = "itemize" if t == "ul" else "enumerate"
            o.append(r"\begin{%s}" % env)
            o += [r"\item\relax{} " + tex_inline(x) for x in b[1]]
            o += [r"\end{%s}" % env, ""]
        elif t == "table":
            o.append(tex_table(b[1], b[2], b[3]))
        elif t == "callout":
            o += [r"\begin{tcolorbox}[enhanced,breakable,colback=accent!8!white,colframe=accent!80!black,"
                  r"boxrule=0.5pt,arc=2pt,left=6pt,right=6pt,top=4pt,bottom=4pt,"
                  r"title={" + tex_inline(b[1], True) + r"},fonttitle=\sffamily\bfseries\small]",
                  tex_inline(b[2]), r"\end{tcolorbox}", ""]
        elif t == "card":
            _, title, tagline, verdict, rows = b
            o += [r"\begin{tcolorbox}[enhanced,breakable,colback=primary!5!white,colframe=primary,"
                  r"colbacktitle=primary,coltitle=white,boxrule=0.6pt,arc=2pt,"
                  r"title={" + tex_inline(title, True) + r"},fonttitle=\sffamily\bfseries\large]",
                  r"{\itshape " + tex_inline(tagline, True) + r"}\par\smallskip",
                  r"\badge{%s}{%s}\par\smallskip" % (VERDICT_COLOR[verdict], tex_escape(VERDICT_LABEL[verdict])),
                  r"\begin{tabularx}{\linewidth}{@{}>{\bfseries\sffamily\small}p{4.6cm}>{\raggedright\arraybackslash}X@{}}"]
            o += [tex_inline(k, True) + " & " + tex_inline(v) + r" \\" for k, v in rows]
            o += [r"\end{tabularx}", r"\end{tcolorbox}", ""]
        elif t == "bib":
            o += [r"\begin{list}{}{\setlength{\leftmargin}{1.1cm}\setlength{\labelwidth}{1cm}"
                  r"\setlength{\labelsep}{0.1cm}\setlength{\itemsep}{3pt}\small}"]
            o += [r"\item[\hypertarget{src%d}{[%d]}] " % (i, i) + tex_inline(x) for i, x in b[1]]
            o += [r"\end{list}", ""]
    o.append(r"\end{document}")
    return "\n".join(o) + "\n"


# --------------------------------------------------------------------------
# Kompilasi dan CLI
# --------------------------------------------------------------------------

RINGKAS_KATA_MAX = 3800  # kira-kira 15 halaman PDF (3.300 kata = 15 halaman pada contoh)


def md_words(md):
    """Hitung kata isi laporan (tanpa URL dan sintaks tabel) untuk perkiraan panjang."""
    t = re.sub(r"\]\([^)]*\)", "]", md)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"[|*>#`-]+", " ", t)
    return len(t.split())


def length_note(data, md):
    """Pesan perkiraan panjang untuk mode ringkas (kosong bila bukan mode ringkas)."""
    if data.get("meta", {}).get("mode") != "ringkas":
        return "", False
    w = md_words(md)
    pages = round(w / 240 + 1.5)
    over = w > RINGKAS_KATA_MAX
    msg = f"mode ringkas: sekitar {w} kata, perkiraan {pages} halaman PDF (target maksimal 15)"
    if over:
        msg += "; terlalu panjang, persingkat teks atau kurangi masalah dan solusi"
    return msg, over


def compile_pdf(tex_path):
    """Jalankan tectonic. Kembalikan (ok, pesan, karakter_hilang)."""
    exe = shutil.which("tectonic")
    if not exe:
        return False, "tectonic tidak ditemukan. Pasang dengan: brew install tectonic", []
    for args in ([exe, "-X", "compile", tex_path.name], [exe, tex_path.name]):
        r = subprocess.run(args, cwd=tex_path.parent, capture_output=True, text=True)
        log = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 0:
            missing = sorted(set(re.findall(r"Missing character: There is no (.+?) in font", log)))
            return True, "", missing
        if "-X" in args and "unrecognized" in log.lower():
            continue
        tail = "\n".join(log.strip().splitlines()[-25:])
        return False, f"tectonic gagal:\n{tail}", []
    return False, "tectonic gagal", []


def main():
    ap = argparse.ArgumentParser(description="laporan.json -> .md, .tex, .pdf")
    ap.add_argument("json_file")
    ap.add_argument("--out", help="folder keluaran (default: folder laporan.json)")
    ap.add_argument("--name", help="nama dasar file keluaran (default: nama file json)")
    ap.add_argument("--no-pdf", action="store_true", help="hanya tulis .md dan .tex")
    ap.add_argument("--check", action="store_true", help="hanya validasi, tidak menulis file")
    ap.add_argument("--ringkas", action="store_true", help="paksa mode ringkas (abaikan meta.mode)")
    ap.add_argument("--lengkap", action="store_true", help="paksa mode lengkap (abaikan meta.mode)")
    a = ap.parse_args()

    src = Path(a.json_file).expanduser()
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"File tidak ditemukan: {src}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"JSON tidak valid di baris {e.lineno}, kolom {e.colno}: {e.msg}", file=sys.stderr)
        return 1

    normalize_urls(data)
    if (a.ringkas or a.lengkap) and isinstance(data, dict) and isinstance(data.get("meta"), dict):
        data["meta"]["mode"] = "ringkas" if a.ringkas else "lengkap"
    errors, warnings = validate(data)
    for w in warnings:
        print(f"PERINGATAN {w}", file=sys.stderr)
    if errors:
        print(f"\n{len(errors)} kesalahan pada {src.name}:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    if a.check:
        print(f"OK: {src.name} valid ({len(warnings)} peringatan)")
        note, over = length_note(data, emit_md(data, build_blocks(data)))
        if note:
            print(("PERINGATAN " if over else "INFO ") + note, file=sys.stderr)
        return 0

    out = Path(a.out).expanduser() if a.out else src.resolve().parent
    out.mkdir(parents=True, exist_ok=True)
    name = a.name or src.stem
    blocks = build_blocks(data)
    md, tex = out / f"{name}.md", out / f"{name}.tex"
    md_text = emit_md(data, blocks)
    md.write_text(md_text, encoding="utf-8")
    note, over = length_note(data, md_text)
    if note:
        print(("PERINGATAN " if over else "INFO ") + note, file=sys.stderr)
    tex.write_text(emit_tex(data, blocks), encoding="utf-8")
    print(f"Markdown: {md}")
    print(f"LaTeX:    {tex}")
    if a.no_pdf:
        return 0
    ok, msg, missing = compile_pdf(tex)
    if not ok:
        print(msg, file=sys.stderr)
        return 2
    if missing:
        print(f"PERINGATAN glyph tidak ada di font (tidak tampil di PDF): {' '.join(missing)}", file=sys.stderr)
    print(f"PDF:      {out / (name + '.pdf')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
