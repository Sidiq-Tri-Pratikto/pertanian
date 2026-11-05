import type { MouseEventHandler, ReactNode } from 'react';

import { Icon } from '@/components/tr/Icon';

type LinkProps = {
  children: ReactNode;
  href: string;
  /** Opens another site in a new tab, and says so to everyone. */
  external?: boolean;
  /** Hidden words that make the link's name unique on the page. */
  context?: string;
  /** Runs beside the navigation, never instead of it: routes are real links (deviation D3). */
  onClick?: MouseEventHandler<HTMLAnchorElement>;
  id?: string;
};

/** Port of TR.Link for addresses outside the app's router. */
export function Link({ children, href, external, context, onClick, id }: LinkProps) {
  return (
    <a id={id} href={href} className="tr-link" target={external ? '_blank' : undefined} rel={external ? 'noopener noreferrer' : undefined} onClick={onClick}>
      {children}
      {context ? <span className="tr-sr">{` ${context}`}</span> : null}
      {external ? (
        <>
          <Icon name="external" size="small" />
          <span className="tr-sr"> (membuka situs lain)</span>
        </>
      ) : null}
    </a>
  );
}
