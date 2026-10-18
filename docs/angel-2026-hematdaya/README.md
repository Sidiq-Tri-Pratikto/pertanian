# HematDaya — ANGEL Innovation Hackathon 2026

Aplikasi pemantau energi dan penasihat efisiensi berbasis data untuk IKM: membaca konsumsi listrik per mesin (meter plug-in atau impor CSV), menghitung biaya, konsumsi di luar jam operasional, dan IKE, lalu menjelaskan temuan dengan bukti dan keterbatasannya. Hanya memantau dan menyarankan; tidak mengontrol mesin.

- **Track:** Sustainable Energy, Topik 6: *Industrial Energy Efficiency Copilot*
- **Problem Owner:** PT Indmira Global Energi
- **Tim:** sama dengan SOPilot (Ahmad Widardi sebagai Ketua)
- **Asal:** PRD HematRumah (rumah tangga) v3, dibingkai ulang ke IKM; konsep awal IdleWatch.

## Status

- **TKT 3**: prototipe web berjalan menganalisis data historis, tetapi data sintetis; belum diuji dengan meter dan data pabrik nyata. Target TKT 4 pada akhir hackathon.
- **Platform:** proposal menyebut aplikasi seluler dan web (satu basis kode React Native/Expo); prototipe hanya menampilkan versi seluler, dan versi web penuh belum dibuat. PRD v3 sumber masih menyatakan web bukan target dan perlu diperbarui jika web dipertahankan.
- Dukungan mitra: belum ada.
- Jendela pendaftaran di booklet (18 September–2 Oktober 2026) sudah lewat; konfirmasi ke panitia.
- PRD sumber adalah untuk rumah tangga dan menyatakan industri di luar lingkup; proposal membingkai ulang ke IKM. Prototipe sudah memakai konteks IKM.

## Isi

| Folder | Isi |
|---|---|
| [prd/](prd/) | PRD HematRumah v3 dan handoff Claude Design (sumber) |
| [../../applications/angel-2026-hematdaya](../../applications/angel-2026-hematdaya/) | Prototipe dan data contoh |
| [submission/proposal/](submission/proposal/) | [Proposal-HematDaya.pdf](submission/proposal/Proposal-HematDaya.pdf) (7 halaman) dan sumber HTML |
| [submission/pitch-deck/](submission/pitch-deck/) | Sumber 12 slide; deck online: https://claude.ai/artifact/X1Mu5h6qMy6mJ8vtiSD8Xb |
| [submission/surat-komitmen/](submission/surat-komitmen/) | [Surat-Komitmen-Tim-HematDaya.pdf](submission/surat-komitmen/Surat-Komitmen-Tim-HematDaya.pdf) |
| [submission/video-demo/](submission/video-demo/) | [Naskah-Video-Demo-HematDaya.md](submission/video-demo/Naskah-Video-Demo-HematDaya.md) (±2:50) |

## Yang masih perlu diselesaikan

- Tanda tangan basah Ketua di proposal dan surat komitmen.
- Video demo sudah ada (YouTube Shorts: https://youtube.com/shorts/FrZBGJC-DU0); pastikan durasinya 2–3 menit dan aksesnya tidak Private. CV dan portofolio ditautkan di Lampiran (folder Google Drive; pastikan aksesnya "Siapa saja yang memiliki link").
- Bagikan prototipe dan deck lewat menu Share (masih privat); unduh deck sebagai PDF/PPT.
- Harga di slide 10 deck sengaja dikosongkan; foto anggota di slide 11 opsional.

## Cetak proposal

Cetak HTML dengan Chrome headless (`--headless=new --no-pdf-header-footer --print-to-pdf`), lalu cap nomor halaman (sampul tanpa nomor) dengan PyMuPDF: lihat `stamp_pages.py` di bawah.

```python
import sys, os, pymupdf
src = sys.argv[1]; doc = pymupdf.open(src)
for i, page in enumerate(doc):
    if i == 0: continue
    r = page.rect; txt = str(i + 1)
    w = pymupdf.get_text_length(txt, fontname="tiro", fontsize=11)
    page.insert_text(pymupdf.Point((r.width - w) / 2, r.height - 35.4), txt, fontname="tiro", fontsize=11)
doc.save(src + ".tmp", garbage=3, deflate=True); doc.close(); os.replace(src + ".tmp", src)
```
