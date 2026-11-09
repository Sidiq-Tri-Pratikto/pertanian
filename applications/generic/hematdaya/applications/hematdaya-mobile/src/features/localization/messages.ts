import { getLocale, useLocale, type Locale } from '@/features/localization/locale';

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
  connectMeter: 'Hubungkan alat ukur',
  importHistory: 'Impor riwayat CSV',
  checkStatus: 'Periksa status',
  importUnknown: 'Status impor belum diketahui',
  navigation: 'Navigasi utama',
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
  connectMeter: 'Connect a meter',
  importHistory: 'Import CSV history',
  checkStatus: 'Check status',
  importUnknown: 'Import status unknown',
  navigation: 'Main navigation',
};

export function message(locale: Locale, key: MessageKey): string {
  return (locale === 'en' ? en : id)[key];
}

export function useLabels() {
  return useLocale() === 'en' ? en : id;
}

export function useCopy() {
  return useLocale() === 'en' ? englishCopy : indonesianCopy;
}

function englishCopy(_id: string, english: string): string {
  return english;
}

function indonesianCopy(indonesian: string, _en: string): string {
  return indonesian;
}

/** For building display models from structured data inside a localized render. */
export function currentCopy(indonesian: string, english: string): string {
  return getLocale() === 'en' ? english : indonesian;
}
