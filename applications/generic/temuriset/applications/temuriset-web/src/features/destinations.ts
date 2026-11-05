import type { IconName } from '@/components/tr/Icon';
import type { Persona } from '@/features/persona';

/** What one primary destination says while its features are still coming. Copy is Indonesian. */
export type Destination = {
  /** Navigation item marked as current. */
  nav: string;
  title: string;
  subtitle: string;
  showServiceStatus?: boolean;
  empty: { icon: IconName; title: string; body: string };
  /** Feature ids from the registry, in reading order. */
  features: string[];
};

export type DestinationId = 'home' | 'inventions' | 'discover' | 'opportunities' | 'pitches';

type PitchBox = 'masuk' | 'diskusi';

const HOME: Record<Persona, Destination> = {
  inovator: {
    nav: 'beranda',
    title: 'Beranda',
    subtitle: 'Pekerjaan yang menunggu Anda akan tampil di sini.',
    showServiceStatus: true,
    empty: {
      icon: 'bulb',
      title: 'Belum ada yang perlu dikerjakan',
      body: 'Draf, pitching, dan jadwal Anda akan muncul di sini setelah fiturnya tersedia.',
    },
    features: ['akun', 'inovasi', 'dukungan-proyek', 'kecocokan', 'diskusi'],
  },
  mitra: {
    nav: '',
    title: 'Beranda',
    subtitle: 'Pitching yang menunggu keputusan Anda akan tampil di sini.',
    showServiceStatus: true,
    empty: {
      icon: 'inbox',
      title: 'Belum ada yang perlu dikerjakan',
      body: 'Pitching masuk dan jadwal akan muncul di sini setelah fiturnya tersedia.',
    },
    features: ['akun', 'profil-mitra', 'keputusan-revisi', 'jadwal'],
  },
};

const DISCOVER: Record<Persona, Destination> = {
  inovator: {
    nav: 'temukan',
    title: 'Temukan Investor/Mitra',
    subtitle: 'Investor dan mitra dengan mandat yang mereka nyatakan.',
    empty: {
      icon: 'search',
      title: 'Belum ada investor atau mitra untuk ditampilkan',
      body: 'Daftar dan kecocokan muncul setelah profil mitra dan kebutuhan Anda tersedia.',
    },
    features: ['profil-mitra', 'jelajahi', 'kecocokan', 'pemeriksaan-pitching'],
  },
  mitra: {
    nav: 'jelajahi',
    title: 'Jelajahi',
    subtitle: 'Inovasi dan pendanaan perusahaan yang sedang mencari dukungan.',
    showServiceStatus: true,
    empty: {
      icon: 'search',
      title: 'Belum ada inovasi untuk dijelajahi',
      body: 'Inovasi yang diterbitkan pemiliknya akan tampil di sini.',
    },
    features: ['jelajahi', 'pendanaan-perusahaan', 'data-demo'],
  },
};

const INVENTIONS: Destination = {
  nav: 'inovasi',
  title: 'Inovasi Saya',
  subtitle: 'Inovasi yang Anda kelola, termasuk drafnya.',
  empty: {
    icon: 'bulb',
    title: 'Belum ada inovasi yang terbit',
    body: 'Inovasi Anda baru terlihat oleh investor dan mitra setelah Anda menerbitkannya.',
  },
  features: ['inovasi', 'dokumen', 'dukungan-proyek', 'pendanaan-perusahaan', 'impor-ekspor'],
};

const OPPORTUNITIES: Destination = {
  nav: 'mandat',
  title: 'Kebutuhan/Mandat',
  subtitle: 'Mandat yang Anda terbitkan beserta syaratnya.',
  empty: {
    icon: 'file',
    title: 'Belum ada mandat',
    body: 'Mandat menjelaskan dukungan yang Anda tawarkan dan syarat yang terlihat oleh pengirim.',
  },
  features: ['profil-mitra', 'mandat', 'tinjauan-organisasi'],
};

const PITCHES: Destination = {
  nav: 'pitching',
  title: 'Pitching dan Diskusi',
  subtitle: 'Pitching yang Anda kirim dan diskusinya.',
  empty: {
    icon: 'inbox',
    title: 'Belum ada pitching',
    body: 'Pitching muncul setelah Anda mengirimnya dengan sengaja dari pemeriksaan sebelum kirim.',
  },
  features: ['pitching', 'keputusan-revisi', 'diskusi', 'jadwal', 'kerja-sama'],
};

const PARTNER_PITCHES: Record<PitchBox, Destination> = {
  masuk: {
    nav: 'masuk',
    title: 'Pitching Masuk',
    subtitle: 'Pitching yang menunggu tinjauan atau keputusan Anda.',
    empty: {
      icon: 'inbox',
      title: 'Belum ada pitching masuk',
      body: 'Pitching masuk setelah inovator mengirimnya ke mandat Anda.',
    },
    features: ['keputusan-revisi', 'diskusi', 'tinjauan-organisasi'],
  },
  diskusi: {
    nav: 'diskusi',
    title: 'Diskusi dan Jadwal',
    subtitle: 'Pitching yang sudah disetujui untuk diskusi.',
    empty: {
      icon: 'calendar',
      title: 'Belum ada diskusi',
      body: 'Diskusi dimulai setelah Anda menyetujui sebuah pitching untuk diskusi.',
    },
    features: ['diskusi', 'jadwal', 'kerja-sama', 'kalender'],
  },
};

/** Resolves the destination copy for a persona. Partners read pitches through two boxes. */
export function destinationFor(id: DestinationId, persona: Persona, box?: string): Destination {
  switch (id) {
    case 'home':
      return HOME[persona];
    case 'discover':
      return DISCOVER[persona];
    case 'inventions':
      return INVENTIONS;
    case 'opportunities':
      return OPPORTUNITIES;
    case 'pitches':
      return persona === 'mitra' ? PARTNER_PITCHES[box === 'diskusi' ? 'diskusi' : 'masuk'] : PITCHES;
  }
}
