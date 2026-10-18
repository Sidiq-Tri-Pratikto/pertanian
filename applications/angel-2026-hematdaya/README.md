# HematDaya: prototipe

Prototipe web **berjalan** (satu berkas HTML, tanpa server): menerima data historis konsumsi energi (CSV), lalu menghitung di peramban:

- energi dan estimasi biaya per mesin (tarif opsional),
- konsumsi di luar jam operasional dan perbandingan dengan median minggu-minggu sebelumnya,
- IKE (kWh per unit) dari produksi rata-rata yang diisi pengguna,
- saran dengan bukti, cakupan data, dan hal yang belum diketahui; umpan balik opsional.

Data bawaan **sintetis** (4 mesin, 4 minggu). Belum diuji dengan meter dan data pabrik nyata (TKT 3).

| Berkas | Isi |
|---|---|
| [hematdaya.html](hematdaya.html) | Prototipe; buka langsung di browser |
| [data-contoh-ikm.csv](data-contoh-ikm.csv) | Data contoh yang sama dalam format impor (`timestamp,perangkat,energi_wh`, 2.592 baris) |

Format CSV: judul kolom `timestamp`, `perangkat`, dan `energi_wh` (Wh per interval) atau `daya_w` (rata-rata watt per interval); pemisah `,` atau `;`; waktu `2026-10-12 08:00` dianggap waktu setempat. Dokumen: [docs/angel-2026-hematdaya](../../docs/angel-2026-hematdaya/).

Tautan online: https://claude.ai/artifact/M7yATNgrVRv3EJksg1NnqP (privat sampai dibagikan).
