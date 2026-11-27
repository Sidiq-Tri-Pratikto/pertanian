import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import '@/design/fonts/fonts.css';
import '@/design/tokens.css';
import '@/design/bundle.css';
import '@/design/app.css';
import { LocaleProvider } from '@/features/i18n/LocaleProvider';
import { messagesFor } from '@/features/i18n/messages';
import { serverLocale } from '@/features/i18n/server';

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: { template: '%s · TemuRiset', default: 'TemuRiset' },
    description: messagesFor(await serverLocale()).meta.description,
  };
}

/** The document language follows the address: `/en/...` pages are English, everything else Indonesian (spec 050). */
export default async function RootLayout({ children }: { children: ReactNode }) {
  const locale = await serverLocale();
  return (
    <html lang={locale} data-theme="light">
      <body>
        <LocaleProvider locale={locale}>{children}</LocaleProvider>
      </body>
    </html>
  );
}
