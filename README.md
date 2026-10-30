# pertanian

Kumpulan proyek hackathon (private): dokumen, aplikasi atau prototipe, dan konfigurasi deployment, dikelompokkan per proyek.

## Struktur

```
/
├── docs/             # PRD, proposal, berkas submit; satu folder per proyek
│   └── <proyek>/
├── applications/     # kode aplikasi dan prototipe; satu folder per proyek
│   └── <proyek>/
├── .github/          # CI untuk aplikasi yang memiliki test
├── deployment/       # konfigurasi deployment (belum ada isi)
└── skills/           # skill Claude Code yang dipakai lintas proyek
    └── <skill>/SKILL.md
```

Nama folder proyek sama di `docs/` dan `applications/`, dengan pola `<hackathon>-<tahun>-<proyek>`.

## PRD generik

[docs/generic](docs/generic/) memuat spesifikasi lintas sektor, terpisah dari dokumen hackathon. Produk pertama: [HematDaya generik](docs/generic/hematdaya/), untuk pemantauan listrik rumah tangga, usaha, dan industri. Ini spesifikasi pengembangan baru; prototipe proyek yang sudah ada tetap memiliki cakupannya masing-masing.

Kodenya ada di [applications/generic/hematdaya](applications/generic/hematdaya/): aplikasi mobile Expo dan API FastAPI, dengan cara menjalankan dan menguji di README-nya.

## Skills

| Skill | Fungsi |
|---|---|
| [riset-masalah-solusi](skills/riset-masalah-solusi/) | Dari topik dan wilayah: riset masalah nyata berbukti, prioritas, usulan solusi software yang belum ada, laporan Markdown dan PDF. Pemakaian: `/riset-masalah-solusi <topik> di <wilayah>`. |

Untuk memakainya, salin folder skill ke `~/.claude/skills/`.

## Proyek

| Hackathon | Proyek | Tahun | Status | Docs | Aplikasi |
|---|---|---|---|---|---|
| ANGEL Innovation Hackathon 2026 (Track AI, Topik 1) | SOPilot: asisten AI untuk mengubah SOP menjadi proses bisnis BPMN yang dapat dijalankan | 2026 | Berkas submit siap; video demo belum direkam; placeholder identitas belum diisi | [docs/angel-2026-sopilot](docs/angel-2026-sopilot/) | [applications/angel-2026-sopilot](applications/angel-2026-sopilot/) |
| ANGEL Innovation Hackathon 2026 (Track Sustainable Energy, Topik 6) | HematDaya: pemantau energi dan penasihat efisiensi berbasis data untuk IKM | 2026 | Berkas submit siap; video demo belum direkam; prototipe berjalan dengan data sintetis | [docs/angel-2026-hematdaya](docs/angel-2026-hematdaya/) | [applications/angel-2026-hematdaya](applications/angel-2026-hematdaya/) |
| UMY Hackathon DeepTech 2026 (Energi, sub-tema Klaster 08 *Sustainable and Green Healthcare*) | HematDaya Faskes: pemantauan dan analitik konsumsi energi berbasis data untuk rumah sakit dan klinik | 2026 | Proposal dan Pakta Integritas siap; prototipe berjalan dengan data sintetis; tenggat pendaftaran 20 Oktober 2026 | [docs/umy-2026-hematdaya](docs/umy-2026-hematdaya/) | [applications/umy-2026-hematdaya](applications/umy-2026-hematdaya/) |
