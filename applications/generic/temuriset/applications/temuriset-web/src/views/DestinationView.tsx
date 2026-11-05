import Link from 'next/link';

import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import type { Destination } from '@/features/destinations';
import type { Me } from '@/api/client';
import { ContextBar } from '@/features/ContextBar';
import { readPersona } from '@/features/persona';
import type { Capabilities } from '@/features/registry';
import { ServiceStatus } from '@/features/ServiceStatus';
import { FeatureList, PROVENANCE } from '@/views/parts';

/** One primary destination in the base release: honest empty state, then what is coming. */
type QueueItem = { href: string; label: string; context: string };
type DestinationViewProps = { me: Me; destination: Destination; capabilities: Capabilities; queue?: QueueItem[] };

export function DestinationView({ me, destination, capabilities, queue = [] }: DestinationViewProps) {
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
        <section className="tr-stack" aria-labelledby="perlu-dikerjakan">
          <h2 id="perlu-dikerjakan" className="tr-sys-type-heading-sm">
            Perlu dikerjakan
          </h2>
          <ul className="tr-stack">
            {queue.map((item) => (
              <li key={item.href} className="tr-panel tr-stack">
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
      ) : (
        <EmptyState icon={destination.empty.icon} title={destination.empty.title}>
          {destination.empty.body}
        </EmptyState>
      )}
      <FeatureList ids={destination.features} capabilities={capabilities} />
    </Screen>
  );
}
