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
type DestinationViewProps = { me: Me; destination: Destination; capabilities: Capabilities };

export function DestinationView({ me, destination, capabilities }: DestinationViewProps) {
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
      <EmptyState icon={destination.empty.icon} title={destination.empty.title}>
        {destination.empty.body}
      </EmptyState>
      <FeatureList ids={destination.features} capabilities={capabilities} />
    </Screen>
  );
}
