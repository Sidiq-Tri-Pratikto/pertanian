import { useCopy } from '@/features/localization/messages';
import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { HDDataQuality } from '@/components/hd/HDDataQuality';
import { HDDisclosure } from '@/components/hd/HDDisclosure';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

type HDEvidencePanelProps = {
  observed: string;
  comparison: string;
  qualityScope: string;
  unknown: string;
  guidance: string;
  metadata: { term: string; value: string }[];
  /** Harmless feedback controls (023). They change no data and no device. */
  feedback?: ReactNode;
};

/** Ordered evidence: observed, comparison, quality and scope, unknown, then general guidance; metadata collapsed. */
export function HDEvidencePanel({ observed, comparison, qualityScope, unknown, guidance, metadata, feedback }: HDEvidencePanelProps) {
  const say = useCopy();
  const steps = [
    { heading: say("Yang tercatat", "What we recorded"), body: observed },
    { heading: say("Pembanding", "Comparison"), body: comparison },
    { heading: say("Kualitas dan cakupan data", "Data quality and scope"), body: qualityScope },
    { heading: say("Yang belum diketahui", "What we don’t know"), body: unknown },
  ];
  return (
    <View style={styles.block}>
      <View role="list" aria-label={say("Dasar saran", "Insight evidence")} style={styles.block}>
        {steps.map((step, index) => (
          <View key={step.heading} role="listitem" style={styles.step}>
            <HDText variant="labelStrong" role="heading">
              {`${index + 1}. ${step.heading}`}
            </HDText>
            <HDText>{step.body}</HDText>
          </View>
        ))}
        <View role="listitem" style={styles.step}>
          <HDText variant="labelStrong" role="heading">
            {say(`${steps.length + 1}. Saran umum`, `${steps.length + 1}. General tips`)}
          </HDText>
          <HDText>{guidance}</HDText>
          <HDText variant="label" tone="secondary">{say("Langkah pemeriksaan umum, bukan hasil analisis khusus lokasi ini.", "General checks you can try at any site.")}</HDText>
        </View>
      </View>
      {feedback}
      <HDDisclosure summary={say("Detail perhitungan", "Calculation details")}>
        <HDDataQuality rows={metadata} />
      </HDDisclosure>
    </View>
  );
}

const styles = StyleSheet.create({ block: { gap: tokens.space.stack }, step: { gap: tokens.space['4'] } });
