import Link from 'next/link';

import { EmptyState } from '@/components/tr/EmptyState';
import { NextStep } from '@/components/tr/NextStep';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import type { Destination } from '@/features/destinations';
import type { Me } from '@/api/client';
import { ContextBar } from '@/features/ContextBar';
import { NotificationList, type Notice } from '@/features/discussion/NotificationList';
import { readPersona } from '@/features/persona';
import type { Capabilities } from '@/features/registry';
import { ServiceStatus } from '@/features/ServiceStatus';
import { FeatureList, PROVENANCE } from '@/views/parts';

/** One primary destination: what waits first, then the rest of the queue, notifications, and what is coming. */
export type QueueItem = { href: string; label: string; context: string; who?: 'you' | 'other'; text?: string };
type DestinationViewProps = { me: Me; destination: Destination; capabilities: Capabilities; queue?: QueueItem[]; notifications?: Notice[] };

const TURN = { you: 'Menunggu Anda', other: 'Menunggu pihak lain' } as const;

export function DestinationView({ me, destination, capabilities, queue = [], notifications = [] }: DestinationViewProps) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  return (
    <Screen
      persona={persona}
      current={destination.nav}
      title={destination.title}
      subtitle={destination.subtitle}
      provenance={PROVENANCE}
      context={<ContextBar me={me} />}>
      {destination.showServiceStatus ? <ServiceStatus /> : null}
      {queue.length ? (
        <>
          <NextStep
            who={queue[0].who ?? 'you'}
            title={queue[0].label}
            action={
              <Link className="tr-btn tr-btn--primary" href={queue[0].href}>
                {queue[0].who === 'other' ? 'Buka' : 'Kerjakan sekarang'}
                <span className="tr-sr">{`: ${queue[0].context}`}</span>
              </Link>
            }>
            {queue[0].text ? `${queue[0].context}. ${queue[0].text}` : queue[0].context}
          </NextStep>
          {queue.length > 1 ? (
            <section className="tr-stack" aria-labelledby="perlu-dikerjakan">
              <h2 id="perlu-dikerjakan" className="tr-sys-type-heading-sm">
                Perlu diperhatikan
              </h2>
              <ul className="tr-stack">
                {queue.slice(1).map((item) => (
                  <li key={item.href} className="tr-panel tr-stack">
                    {item.who ? <Status tone={item.who === 'you' ? 'action' : 'neutral'} label={TURN[item.who]} /> : null}
                    <p className="tr-muted tr-sys-type-support">{item.context}</p>
                    <p>
                      <Link className="tr-link" href={item.href}>
                        {item.label}
                      </Link>
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </>
      ) : (
        <EmptyState icon={destination.empty.icon} title={destination.empty.title}>
          {destination.empty.body}
        </EmptyState>
      )}
      {notifications.length ? <NotificationList notifications={notifications} zone={me.account.time_zone} /> : null}
      <FeatureList ids={destination.features} capabilities={capabilities} />
    </Screen>
  );
}
