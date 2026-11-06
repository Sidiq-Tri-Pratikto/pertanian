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
  const steps = [
    { heading: 'Yang tercatat', body: observed },
    { heading: 'Pembanding', body: comparison },
    { heading: 'Kualitas dan cakupan data', body: qualityScope },
    { heading: 'Yang belum diketahui', body: unknown },
  ];
  return (
    <View style={styles.block}>
      <View role="list" aria-label="Dasar saran" style={styles.block}>
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
            {`${steps.length + 1}. Saran umum`}
          </HDText>
          <HDText>{guidance}</HDText>
          <HDText variant="label" tone="secondary">
            Langkah pemeriksaan umum, bukan hasil analisis khusus lokasi ini.
          </HDText>
        </View>
      </View>
      {feedback}
      <HDDisclosure summary="Detail perhitungan">
        <HDDataQuality rows={metadata} />
      </HDDisclosure>
    </View>
  );
}

const styles = StyleSheet.create({ block: { gap: tokens.space.stack }, step: { gap: tokens.space['4'] } });
