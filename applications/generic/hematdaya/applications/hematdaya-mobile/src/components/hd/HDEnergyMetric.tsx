import { useCopy } from '@/features/localization/messages';
import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { HDProvenanceTag } from '@/components/hd/HDProvenanceTag';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import type { MetricState } from '@/features/energy/beranda-model';

type HDEnergyMetricProps = {
  state: MetricState;
  kwh: string | null;
  qualifier: string | null;
  gaps: string[];
  periodLabel: string;
  scopeLabel: string;
  origins: string[];
  emptyDetail: string | null;
  issues: string[];
  action?: ReactNode;
};

/** Recorded kWh for a period and scope, with provenance and the quality qualifier beside the number. */
export function HDEnergyMetric({ state, kwh, qualifier, gaps, periodLabel, scopeLabel, origins, emptyDetail, issues, action }: HDEnergyMetricProps) {
  const say = useCopy();
  return (
    <View role="region" aria-label={say("Energi yang dipantau", "Monitored energy")} style={styles.block}>
      <View style={styles.head}>
        <HDText variant="labelStrong">{say("Energi yang dipantau", "Monitored energy")}</HDText>
        <HDProvenanceTag origins={origins} />
      </View>
      <HDText variant="label">
        {periodLabel} · {scopeLabel}
      </HDText>
      {state === 'conflict' ? (
        <>
          <HDText variant="section">{say("Total gabungan belum dapat dihitung", "Combined total unavailable")}</HDText>
          <HDText>{say("Cakupan tumpang tindih atau sumber acuan belum dipilih, sehingga nilai tidak dijumlahkan. Nilai masing-masing perangkat tetap tersedia.", "The selected sources overlap or need a reference source. You can still see each device’s readings.")}</HDText>
          {issues.map((issue) => (
            <HDText key={issue} tone="attention">
              {issue}
            </HDText>
          ))}
        </>
      ) : state === 'none' ? (
        <>
          <HDText variant="section">{say("Belum ada energi pada periode ini", "No energy data for this period")}</HDText>
          {emptyDetail ? <HDText>{emptyDetail}</HDText> : null}
        </>
      ) : (
        <>
          <HDText variant="metric">{kwh}</HDText>
          {qualifier ? <HDText tone={state === 'partial' ? 'attention' : 'primary'}>{qualifier}</HDText> : null}
          {gaps.map((gap) => (
            <HDText key={gap} variant="label" tone="attention">{say("Data", "Data")} {gap} {say("belum tersedia.", "is unavailable.")}</HDText>
          ))}
        </>
      )}
      {action}
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: tokens.space.stackTight },
  head: { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: tokens.space.inlineGap },
});
