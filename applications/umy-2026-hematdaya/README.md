# HematDaya Faskes: prototipe

Prototipe web **berjalan** (satu berkas HTML, tanpa server; tampilan seluler): menerima data historis konsumsi energi (CSV), lalu menghitung di peramban:

- energi dan estimasi biaya per perangkat (tarif opsional),
- konsumsi di luar jam layanan untuk perangkat poli, dan kenaikan konsumsi dibanding median minggu-minggu sebelumnya untuk perangkat 24 jam dan beban kritis,
- IKE: kWh per m² dan kWh per tempat tidur per hari, dari luas bangunan dan jumlah tempat tidur yang diisi pengguna (hanya beban yang terpantau),
- saran dengan bukti, cakupan data, dan hal yang belum diketahui; umpan balik opsional.

Perangkat dikelompokkan di Pengaturan: **poli** (jam layanan) atau **24 jam**, dan tanda **beban kritis**. Beban kritis hanya dipantau; sarannya tidak pernah menyebut menghentikan perangkat. Tidak ada kontrol perangkat dan tidak ada data pasien.

Data bawaan **sintetis** (5 perangkat, 4 minggu, 21 September–17 Oktober 2026). Belum diuji dengan meter dan data fasilitas nyata (TKT 3).

| Berkas | Isi |
|---|---|
| [hematdaya-faskes.html](hematdaya-faskes.html) | Prototipe; buka langsung di browser |
| [data-contoh-faskes.csv](data-contoh-faskes.csv) | Data contoh yang sama dalam format impor (`timestamp,perangkat,energi_wh`, 3.240 baris) |

Format CSV: judul kolom `timestamp`, `perangkat`, dan `energi_wh` (Wh per interval) atau `daya_w` (rata-rata watt per interval); pemisah `,` atau `;`; waktu `2026-10-12 08:00` dianggap waktu setempat. Dokumen: [docs/umy-2026-hematdaya](../../docs/umy-2026-hematdaya/). Varian IKM: [applications/angel-2026-hematdaya](../angel-2026-hematdaya/).

Tautan online: https://claude.ai/artifact/BEZeZxr64pfvfVqfDy1equ (privat sampai dibagikan).
