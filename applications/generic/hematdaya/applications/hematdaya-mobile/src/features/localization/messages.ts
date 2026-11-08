import type { Locale } from '@/features/localization/locale';

const id = {
  home: 'Beranda',
  devices: 'Perangkat',
  insights: 'Saran',
  settings: 'Pengaturan',
  language: 'Bahasa',
  back: 'Kembali',
  tryDemo: 'Coba demo',
  continueWithoutData: 'Lanjut tanpa data',
  addData: 'Tambah data',
  checkStatus: 'Periksa status',
  importUnknown: 'Status impor belum diketahui',
};

type MessageKey = keyof typeof id;

const en: Record<MessageKey, string> = {
  home: 'Home',
  devices: 'Devices',
  insights: 'Insights',
  settings: 'Settings',
  language: 'Language',
  back: 'Back',
  tryDemo: 'Try demo',
  continueWithoutData: 'Continue without data',
  addData: 'Add data',
  checkStatus: 'Check status',
  importUnknown: 'Import status unknown',
};

export function message(locale: Locale, key: MessageKey): string {
  return (locale === 'en' ? en : id)[key];
}
