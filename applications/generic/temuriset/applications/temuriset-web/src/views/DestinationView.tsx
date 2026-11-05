import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import type { Destination } from '@/features/destinations';
import type { Persona } from '@/features/persona';
import { ServiceStatus } from '@/features/ServiceStatus';
import { FeatureList, PersonaContext, PROVENANCE } from '@/views/parts';

/** One primary destination in the base release: honest empty state, then what is coming. */
export function DestinationView({ persona, destination }: { persona: Persona; destination: Destination }) {
  return (
    <Screen
      persona={persona}
      current={destination.nav}
      title={destination.title}
      subtitle={destination.subtitle}
      provenance={PROVENANCE}
      context={<PersonaContext persona={persona} />}>
      {destination.showServiceStatus ? <ServiceStatus /> : null}
      <EmptyState icon={destination.empty.icon} title={destination.empty.title}>
        {destination.empty.body}
      </EmptyState>
      <FeatureList ids={destination.features} />
    </Screen>
  );
}
