# HematDaya Faskes — UMY Hackathon DeepTech 2026

Pemantauan dan analitik konsumsi energi berbasis data untuk rumah sakit dan klinik: membaca konsumsi listrik per perangkat (meter plug-in atau impor CSV), menghitung biaya, konsumsi di luar jam layanan, kenaikan konsumsi, dan IKE per m² dan per tempat tidur, lalu menjelaskan temuan dengan bukti dan keterbatasannya. Hanya memantau dan menyarankan; tidak mengendalikan perangkat, dan beban kritis (pendingin vaksin dan obat) tidak pernah disarankan dihentikan.

- **Bidang Strategis (di proposal):** Energi. Buku pedoman UMY menempatkan topik ini di bidang Kesehatan (*Smart and Sustainable Health Ecosystem for Human Well-being*); konfirmasi ke panitia bila bidang yang dipilih perlu disamakan.
- **Klaster:** 08 *Sustainable and Green Healthcare*
- **Problem statement (dari panitia):** konsumsi energi rumah sakit dan klinik tinggi dan belum terpantau secara terukur
- **Tim:** Petani Digital (sama dengan proyek ANGEL): Ahmad Widardi (Ketua; Koordinator Bisnis dan Hilirisasi) · Sidiq Tri Pratikto (Koordinator Teknis) · Akmal Rafli Fauzan (mahasiswa; Koordinator Klinis dan Validasi Pengguna) · Erwin Eko Wahyudi (dosen; konsultan analitik data)
- **Asal:** varian faskes dari [HematDaya ANGEL](../angel-2026-hematdaya/) (IKM); mesin analitik sama, konteks dan atribut perangkat berbeda.

## Status

- **TKT 3**: prototipe seluler berjalan dengan data sintetis (lima beban contoh klinik dan rawat inap kecil); belum diuji dengan meter dan data fasilitas nyata. Target TKT 4 pada akhir program.
- Dukungan mitra: belum ada; tim belum memiliki tenaga kesehatan.
- Jadwal program (buku pedoman): pendaftaran 15–20 Oktober 2026; seleksi 21–25 Oktober; pengumuman 27 Oktober; *Bootcamp* 2–5 November; Uji Terbatas 9–12 November; Klinik Regulasi 24–25 November; *Demo Day* 26 November; pascakompetisi Desember 2026–April 2027.

## Isi

| Folder | Isi |
|---|---|
| [../../applications/umy-2026-hematdaya](../../applications/umy-2026-hematdaya/) | Prototipe faskes dan data contoh |
| [submission/proposal/](submission/proposal/) | [Proposal-HematDaya-Faskes-UMY.pdf](submission/proposal/Proposal-HematDaya-Faskes-UMY.pdf) (7 halaman; format "Lampiran 2 | Format Proposal Peserta Hackathon Deeptech"), sumber HTML, dan logo sampul |
| [submission/pakta-integritas/](submission/pakta-integritas/) | [Pakta-Integritas-HematDaya-UMY.pdf](submission/pakta-integritas/Pakta-Integritas-HematDaya-UMY.pdf) (2 halaman; 6 butir sesuai dokumen format yang sama) dan sumber HTML |

Tautan online: prototipe https://claude.ai/artifact/BEZeZxr64pfvfVqfDy1equ (privat sampai dibagikan lewat menu Share).

## Yang masih perlu diselesaikan sebelum submit

- **Tenggat pendaftaran 20 Oktober 2026.**
- Tanda tangan basah Ketua di Lembar Identitas proposal, dan tanda tangan semua anggota di Pakta Integritas.
- Bagikan prototipe lewat menu Share; unggah Daftar Riwayat Hidup dan portofolio (tautan Google Drive di Lampiran harus dapat dibuka siapa saja yang memiliki tautan).
- **Syarat tim di buku pedoman:** "Dosen dan mahasiswa dalam satu tim berasal dari institusi yang sama." Dosen (Erwin Eko Wahyudi) dan mahasiswa (Akmal Rafli Fauzan, NIM 24/533033/TK/59053) sama-sama di Universitas Gadjah Mada, jadi syarat ini terpenuhi; pastikan status mahasiswa aktif di PDDIKTI (butir 2 Pakta).
- Tim belum memiliki tenaga kesehatan; konfirmasi ke panitia apakah pendamping klinis dari panitia memenuhi syarat komposisi tim.
- Pakta Integritas butir 1: pernyataan belum pernah memenangkan pendanaan atau kompetisi sejenis dalam dua tahun terakhir. HematDaya juga diajukan ke ANGEL Innovation Hackathon; periksa ketentuan pengajuan ganda sebelum menandatangani.

## Format

Proposal dan Pakta mengikuti dokumen resmi "Lampiran 2 | Format Proposal Peserta Hackathon Deeptech" (Word), bukan Lampiran buku pedoman. Nomor bagian proposal sengaja 1, 2, 5, 6, 7, 8, 9 seperti di dokumen itu. Bagian 6 (Deskripsi Inovasi) memiliki enam butir; isi keselamatan, etik, dan keamanan data digabung ke butir b karena format tidak menyediakan butir sendiri. Pakta versi dokumen tidak memuat butir "Etik dan Keselamatan" yang ada di buku pedoman; konfirmasi ke panitia bila versi buku pedoman yang diminta.

## Cetak proposal

Cetak HTML dengan Chrome headless (`--headless=new --no-pdf-header-footer --print-to-pdf`; gunakan `--user-data-dir` terpisah bila Chrome sedang terbuka), lalu cap nomor halaman (sampul tanpa nomor) dengan PyMuPDF: lihat `stamp_pages.py` di [docs/angel-2026-sopilot](../angel-2026-sopilot/README.md#cetak-proposal). Pakta dicetak tanpa nomor halaman.
