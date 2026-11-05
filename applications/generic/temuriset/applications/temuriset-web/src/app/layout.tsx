import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import '@/design/tokens.css';
import '@/design/bundle.css';
import '@/design/app.css';

export const metadata: Metadata = {
  title: { template: '%s · TemuRiset', default: 'TemuRiset' },
  description: 'Pertemukan inovasi dengan investor dan mitra yang tepat.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="id" data-theme="light">
      <body>{children}</body>
    </html>
  );
}
