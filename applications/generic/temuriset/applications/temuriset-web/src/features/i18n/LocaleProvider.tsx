'use client';

import { createContext, useContext, type ReactNode } from 'react';

import type { Locale } from '@/features/i18n/locale';
import { messagesFor, type Messages } from '@/features/i18n/messages';
import { setAppLocale } from '@/features/i18n/t';

const LocaleContext = createContext<Locale>('id');

/** Gives client components the page language the layout resolved; without it, everything stays Indonesian. */
export function LocaleProvider({ locale, children }: { locale: Locale; children: ReactNode }) {
  setAppLocale(locale);
  return <LocaleContext.Provider value={locale}>{children}</LocaleContext.Provider>;
}

export function useLocale(): Locale {
  return useContext(LocaleContext);
}

export function useMessages(): Messages {
  return messagesFor(useContext(LocaleContext));
}
