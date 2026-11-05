/**
 * Every planned feature, in one place. The "Segera hadir" screen and the feature lists render from it, and each
 * feature's pull request flips `status`. `screens` map to S01–S18 of the application handoff; `specs` name folders
 * under `specs/`. Spec numbers are for engineers and stay out of product copy.
 */
export type FeatureStatus = 'coming_soon' | 'available';

export type Feature = {
  id: string;
  title: string;
  summary: string;
  points: string[];
  screens: string[];
  specs: string[];
  status: FeatureStatus;
  /** Optional capability the feature needs; absent from deployments that do not run it. */
  capability?: string;
  /** Where a shipped feature lives. */
  home?: string;
};

export const FEATURES: Feature[] = [
  {
    id: 'akun',
    title: 'Akun dan konteks kerja',
    summary: 'Masuk dengan email terverifikasi, lalu bertindak sebagai diri sendiri atau atas nama organisasi.',
    points: [
      'Inovator independen dan investor individu tidak perlu membuat organisasi',
      'Konteks yang dipakai selalu terlihat sebelum mengirim, memutuskan, atau mengonfirmasi',
      'Undangan anggota dapat kedaluwarsa dan dicabut',
    ],
    screens: ['S01', 'S18'],
    specs: ['006', '007', '008'],
    status: 'available',
    home: '/settings',
  },
  {
    id: 'inovasi',
    title: 'Portofolio inovasi',
    summary: 'Susun profil inovasi yang aman untuk publik dalam empat langkah, lalu terbitkan versi yang Anda pilih.',
    points: [
      'Draf tersimpan walau belum lengkap',
      'Yang sudah ada dipisahkan dari yang direncanakan',
      'Pratinjau tampilan publik sebelum terbit',
    ],
    screens: ['S04', 'S05'],
    specs: ['009', '011'],
    status: 'available',
    home: '/inventions',
  },
  {
    id: 'dokumen',
    title: 'Dokumen dan bukti',
    summary: 'Simpan berkas secara privat dan bagikan satu versi kepada satu penerima saat pitching.',
    points: [
      'Berkas privat secara bawaan',
      'Pemeriksaan keamanan, pembacaan teks, dan pemeriksaan bukti ditampilkan terpisah',
      'Mencabut akses memblokir unduhan baru, tetapi salinan yang sudah diunduh tidak dapat ditarik',
    ],
    screens: ['S05', 'S13'],
    specs: ['010', '012'],
    status: 'available',
    home: '/inventions',
  },
  {
    id: 'dukungan-proyek',
    title: 'Dukungan Proyek',
    summary: 'Nyatakan hasil yang ingin dicapai, bentuk dukungan, dan kisaran biaya untuk satu inovasi.',
    points: [
      'Setiap jumlah memakai mata uang, cakupan, dan periode',
      'Belum ditentukan tidak pernah dianggap nol',
      'Dukungan nonfinansial juga dapat dicatat',
    ],
    screens: ['S06'],
    specs: ['013', '015'],
    status: 'available',
    home: '/support-requests',
  },
  {
    id: 'pendanaan-perusahaan',
    capability: 'company_funding',
    title: 'Pendanaan Perusahaan',
    summary: 'Catat satu putaran pendanaan perusahaan yang dapat didukung beberapa inovasi.',
    points: [
      'Target Pendanaan terpisah dari Kisaran kontribusi per investor',
      'Perusahaan yang belum didirikan diberi label jelas',
      'Tidak ada valuasi atau persentase kepemilikan yang dihitung otomatis',
    ],
    screens: ['S07'],
    specs: ['014', '015'],
    status: 'available',
    home: '/support-requests#pendanaan',
  },
  {
    id: 'profil-mitra',
    title: 'Profil Investor/Mitra',
    summary: 'Tampilkan minat, tahap yang diterima, bentuk dukungan, dan jalur kontak Anda.',
    points: [
      'Investor individu tidak perlu organisasi',
      'Ketersediaan yang belum dikonfirmasi diberi label',
      'Formulir di luar TemuRiset bukan pitching yang terkirim',
    ],
    screens: ['S08'],
    specs: ['016', '017'],
    status: 'coming_soon',
  },
  {
    id: 'mandat',
    title: 'Kebutuhan dan mandat',
    summary: 'Terbitkan mandat dengan cakupan, syarat yang terlihat, dan tahap pemeriksaannya.',
    points: [
      'Setiap syarat memiliki alasan yang terlihat oleh pengirim',
      'Tidak ada syarat tersembunyi yang menolak otomatis',
      'Mandat berversi dan dapat dijeda atau ditutup',
    ],
    screens: ['S09'],
    specs: ['016', '017'],
    status: 'coming_soon',
  },
  {
    id: 'jelajahi',
    title: 'Jelajahi dan temukan',
    summary: 'Cari inovasi, pendanaan perusahaan, atau investor dan mitra dengan filter yang jelas.',
    points: [
      'Pencarian dalam bahasa Indonesia dan Inggris',
      'Hasil kosong menjelaskan filter tanpa melonggarkan syarat diam-diam',
      'Tidak ada label tren dari aktivitas demo',
    ],
    screens: ['S03'],
    specs: ['018', '020'],
    status: 'coming_soon',
  },
  {
    id: 'kecocokan',
    title: 'Kecocokan dengan alasan',
    summary: 'Lihat mengapa satu kebutuhan cocok dengan satu mandat, dan apa yang masih kurang.',
    points: [
      'Tiga alasan singkat dan kekurangan yang menghalangi',
      'Belum diketahui berbeda dari tidak terpenuhi',
      'Skor bukan peluang pendanaan',
    ],
    screens: ['S10'],
    specs: ['019', '020'],
    status: 'coming_soon',
  },
  {
    id: 'data-demo',
    title: 'Data demo berlabel',
    summary: 'Coba alur lengkap dengan akun dan data fiktif yang diberi label jelas.',
    points: ['Data demo tidak masuk statistik nyata', 'Dapat diatur ulang kapan saja', 'Contoh dari beberapa sektor'],
    screens: [],
    specs: ['021'],
    status: 'coming_soon',
  },
  {
    id: 'pemeriksaan-pitching',
    title: 'Pemeriksaan sebelum kirim',
    summary: 'Periksa penerima, versi, syarat, berkas, dan brief sebelum apa pun terkirim.',
    points: [
      'Brief dibuat dari fakta yang ada dan dapat diubah',
      'Perubahan versi terdeteksi sebelum kirim',
      'Draf brief Anda tetap aman saat perlu diperiksa ulang',
    ],
    screens: ['S11'],
    specs: ['022', '024'],
    status: 'coming_soon',
  },
  {
    id: 'pitching',
    title: 'Kirim pitching',
    summary: 'Kirim pitching dengan sengaja ke satu mandat, dengan berkas yang Anda pilih sendiri.',
    points: [
      'Versi yang dikirim dibekukan',
      'Kirim ulang aman tanpa kiriman ganda',
      'Satu pitching aktif untuk setiap kebutuhan dan mandat',
    ],
    screens: ['S11', 'S12'],
    specs: ['023', '024'],
    status: 'coming_soon',
  },
  {
    id: 'keputusan-revisi',
    title: 'Keputusan dan revisi',
    summary: 'Setujui untuk diskusi, minta revisi per butir, atau tolak dengan alasan privat.',
    points: [
      'Persetujuan membuka diskusi, belum merupakan pendanaan atau kerja sama',
      'Jawaban jujur bahwa sesuatu belum dapat dipenuhi tetap sah',
      'Putaran dan kiriman sebelumnya tetap tersimpan',
    ],
    screens: ['S12', 'S13'],
    specs: ['025', '026'],
    status: 'coming_soon',
  },
  {
    id: 'diskusi',
    title: 'Diskusi, tugas, dan pemberitahuan',
    summary: 'Bahas pitching dalam satu ruang dengan giliran yang selalu jelas.',
    points: [
      'Menunggu Anda dan Menunggu pihak lain selalu terlihat',
      'Klarifikasi setelah persetujuan dicatat sebagai tugas',
      'Pemberitahuan tersedia di dalam aplikasi',
    ],
    screens: ['S02', 'S13'],
    specs: ['027', '029'],
    status: 'coming_soon',
  },
  {
    id: 'jadwal',
    title: 'Jadwal pertemuan',
    summary: 'Usulkan dua sampai lima waktu, pilih, lalu konfirmasi pertemuan dengan zona waktu yang jelas.',
    points: [
      'Memilih waktu belum memesan pertemuan',
      'Bentrok jadwal dapat dipulihkan tanpa kehilangan agenda',
      'Berkas kalender ICS untuk pertemuan yang dikonfirmasi',
    ],
    screens: ['S14'],
    specs: ['028', '029'],
    status: 'coming_soon',
  },
  {
    id: 'kerja-sama',
    title: 'Kerja Sama',
    summary: 'Catat ringkasan Kerja Sama yang dikonfirmasi kedua pihak pada versi yang sama.',
    points: [
      'Koreksi membuat versi baru tanpa konfirmasi lama',
      'Setiap pihak memilih data yang boleh tampil di publik',
      'Dana proyek tidak menciptakan kepemilikan saham',
    ],
    screens: ['S15'],
    specs: ['030', '032'],
    status: 'coming_soon',
  },
  {
    id: 'profil-publik',
    title: 'Profil publik',
    summary: 'Tampilkan inovasi yang terbit dan data Kerja Sama yang diizinkan kedua pihak.',
    points: [
      'Jumlah dana privat secara bawaan',
      'Penyempitan izin langsung berlaku',
      'Klaim yang dipersoalkan dapat disembunyikan selama ditinjau',
    ],
    screens: ['S16'],
    specs: ['031', '032'],
    status: 'coming_soon',
  },
  {
    id: 'tinjauan-organisasi',
    capability: 'organization_review',
    title: 'Tinjauan organisasi',
    summary: 'Organisasi dapat meninjau versi yang tepat sebelum diterbitkan atau dikirim.',
    points: [
      'Mati secara bawaan',
      'Peninjau tidak memutuskan atas nama mitra',
      'Tidak berlaku untuk inovator pribadi',
    ],
    screens: ['S17'],
    specs: ['033'],
    status: 'coming_soon',
  },
  {
    id: 'privasi-laporan',
    title: 'Privasi dan laporan',
    summary: 'Laporkan masalah secara privat, lalu ajukan ekspor atau penghapusan data.',
    points: [
      'Laporan tidak menurunkan reputasi publik siapa pun',
      'Penghapusan menjelaskan data yang masih disimpan beserta alasannya',
      'Unduhan yang sudah terjadi tidak dapat ditarik kembali',
    ],
    screens: ['S18'],
    specs: ['034', '035'],
    status: 'coming_soon',
  },
  {
    id: 'impor-ekspor',
    title: 'Impor dan ekspor data',
    summary: 'Pindahkan data portofolio dengan pratinjau sebelum diterapkan.',
    points: [
      'Impor dua kali tidak membuat data ganda',
      'Fakta yang sudah diperiksa tidak ditimpa diam-diam',
      'Ekspor mengikuti izin terbaru',
    ],
    screens: [],
    specs: ['036'],
    status: 'coming_soon',
  },
  {
    id: 'pemberitahuan-email',
    title: 'Pemberitahuan email',
    summary: 'Terima pemberitahuan penting lewat email sesuai preferensi Anda.',
    points: ['Mati sampai Anda menyalakannya', 'Gagal kirim tidak mengulang keputusan'],
    screens: ['S18'],
    specs: ['042'],
    status: 'coming_soon',
  },
  {
    id: 'kalender',
    title: 'Sinkron kalender',
    summary: 'Periksa ketersediaan dari kalender yang Anda hubungkan.',
    points: [
      'Tanpa kalender, jadwal internal dan berkas ICS tetap berjalan',
      'Ketersediaan di luar TemuRiset tidak diklaim tanpa koneksi',
    ],
    screens: ['S14'],
    specs: ['043'],
    status: 'coming_soon',
  },
  {
    id: 'ringkasan-otomatis',
    title: 'Ringkasan otomatis',
    summary: 'Ringkas brief dari fakta yang Anda berikan, tanpa menambah klaim.',
    points: ['Brief templat tetap tersedia', 'Tidak pernah mengirim atau menerbitkan sendiri'],
    screens: ['S11'],
    specs: ['044'],
    status: 'coming_soon',
  },
];

/** Capability ids this deployment runs, or `null` when the manifest could not be read. */
export type Capabilities = string[] | null;

/** A feature tied to an optional capability is offered only when the deployment runs it. */
export function isOffered(feature: Feature, capabilities: Capabilities): boolean {
  return feature.capability === undefined || (capabilities?.includes(feature.capability) ?? false);
}

export function findFeature(id: string | undefined): Feature | undefined {
  return FEATURES.find((feature) => feature.id === id);
}
