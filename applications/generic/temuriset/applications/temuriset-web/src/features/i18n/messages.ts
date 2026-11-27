import { en } from '@/features/i18n/en';
import { id, type Messages } from '@/features/i18n/id';
import type { Locale } from '@/features/i18n/locale';

export type { Messages };

export function messagesFor(locale: Locale): Messages {
  return locale === 'en' ? en : id;
}

/** A sector's name in the interface language; the stored value stays the Indonesian name. */
export function sectorLabel(messages: Messages, sector: string): string {
  return messages.sectors[sector] ?? sector;
}

/** A stage's name in the interface language. */
export function stageLabel(messages: Messages, stage: string | null | undefined): string | undefined {
  return stage ? (messages.stages[stage] ?? stage) : undefined;
}
