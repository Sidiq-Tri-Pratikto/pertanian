# HematDaya Faskes — UMY Hackathon DeepTech 2026

Pemantauan dan analitik konsumsi energi berbasis data untuk rumah sakit dan klinik: membaca konsumsi listrik per perangkat (meter plug-in atau impor CSV), menghitung biaya, konsumsi di luar jam layanan, kenaikan konsumsi, dan IKE per m² dan per tempat tidur, lalu menjelaskan temuan dengan bukti dan keterbatasannya. Hanya memantau dan menyarankan; tidak mengendalikan perangkat, dan beban kritis (pendingin vaksin dan obat) tidak pernah disarankan dihentikan.

- **Bidang Strategis:** Kesehatan, *Smart and Sustainable Health Ecosystem for Human Well-being*
- **Klaster:** 08 *Sustainable and Green Healthcare*
- **Problem statement (dari panitia):** konsumsi energi rumah sakit dan klinik tinggi dan belum terpantau secara terukur
- **Tim:** sama dengan proyek ANGEL: Ahmad Widardi (Ketua; Koordinator Bisnis dan Hilirisasi) · Sidiq Tri Pratikto (Koordinator Teknis) · Lukman Nurdinanto (Koordinator Klinis dan Validasi Pengguna) · Erwin Eko Wahyudi (dosen; konsultan analitik data)
- **Asal:** varian faskes dari [HematDaya ANGEL](../angel-2026-hematdaya/) (IKM); mesin analitik sama, konteks dan atribut perangkat berbeda.

## Status

- **TKT 3**: prototipe seluler berjalan dengan data sintetis (lima beban contoh klinik dan rawat inap kecil); belum diuji dengan meter dan data fasilitas nyata. Target TKT 4 pada akhir program.
- Dukungan mitra: belum ada; tim belum memiliki tenaga kesehatan.
- Jadwal program (buku pedoman): pendaftaran 15–20 Oktober 2026; seleksi 21–25 Oktober; pengumuman 27 Oktober; *Bootcamp* 2–5 November; Uji Terbatas 9–12 November; Klinik Regulasi 24–25 November; *Demo Day* 26 November; pascakompetisi Desember 2026–April 2027.

## Isi

| Folder | Isi |
|---|---|
| [../../applications/umy-2026-hematdaya](../../applications/umy-2026-hematdaya/) | Prototipe faskes dan data contoh |
| [submission/proposal/](submission/proposal/) | [Proposal-HematDaya-Faskes-UMY.pdf](submission/proposal/Proposal-HematDaya-Faskes-UMY.pdf) (7 halaman; format Lampiran buku pedoman) dan sumber HTML |
| [submission/pakta-integritas/](submission/pakta-integritas/) | [Pakta-Integritas-HematDaya-UMY.pdf](submission/pakta-integritas/Pakta-Integritas-HematDaya-UMY.pdf) (2 halaman; butir sesuai templat) dan sumber HTML |

Tautan online: prototipe https://claude.ai/artifact/BEZeZxr64pfvfVqfDy1equ (privat sampai dibagikan lewat menu Share).

## Yang masih perlu diselesaikan sebelum submit

- **Tenggat pendaftaran 20 Oktober 2026.**
- Tanda tangan basah Ketua di Lembar Identitas proposal, dan tanda tangan semua anggota di Pakta Integritas.
- Bagikan prototipe lewat menu Share; unggah Daftar Riwayat Hidup dan portofolio (tautan Google Drive di Lampiran harus dapat dibuka siapa saja yang memiliki tautan).
- **Syarat tim di buku pedoman:** "Dosen dan mahasiswa dalam satu tim berasal dari institusi yang sama." Saat ini dosen di Universitas Gadjah Mada dan mahasiswa di Universitas Pamulang; konfirmasi ke panitia (dih@umy.ac.id).
- Tim belum memiliki tenaga kesehatan; konfirmasi ke panitia apakah pendamping klinis dari panitia memenuhi syarat komposisi tim.
- Pakta Integritas butir 1: pernyataan belum pernah memenangkan pendanaan atau kompetisi sejenis dalam dua tahun terakhir. HematDaya juga diajukan ke ANGEL Innovation Hackathon; periksa ketentuan pengajuan ganda sebelum menandatangani.
- Batas "maksimum 3 halaman" di templat sampul ditafsirkan untuk bagian inti (Deskripsi Inovasi 2 halaman, Pembagian Tugas 1 halaman); sampul, Lembar Identitas, ringkasan, daftar pustaka, dan lampiran di luar itu.

## Cetak proposal

Cetak HTML dengan Chrome headless (`--headless=new --no-pdf-header-footer --print-to-pdf`), lalu cap nomor halaman (sampul tanpa nomor) dengan PyMuPDF, memakai skrip yang sama dengan [docs/angel-2026-sopilot](../angel-2026-sopilot/README.md#cetak-proposal). Pakta Integritas dicetak tanpa cap nomor halaman.
