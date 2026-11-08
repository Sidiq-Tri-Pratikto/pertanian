import { currentCopy, useCopy } from '@/features/localization/messages';
import { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import type { ImportPreview } from '@/api/client';
import { HDButton } from '@/components/hd/HDButton';
import { HDChoiceGroup } from '@/components/hd/HDChoiceGroup';
import { HDErrorSummary } from '@/components/hd/HDErrorSummary';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDText } from '@/components/hd/HDText';
import { HDTextField } from '@/components/hd/HDTextField';
import { tokens } from '@/design/tokens.generated';
import {
  answerOf,
  answersChanged,
  askedAgain,
  mappingLine,
  mappingOf,
  minutesError,
  NEW_ASSET,
  powerOptions,
  questionControls,
  readMinutes,
  scopeOptions,
  streamRow,
  streamTarget,
  unanswered,
  valueKindOptions,
  type Control,
  type SummaryItem,
} from '@/features/imports/import-model';
import { reselectText, ReselectNotice, useFilePick } from '@/features/imports/FileSource';
import { useImportDraft } from '@/features/imports/ImportDraftProvider';
import { ImportFrame, useImportFrame } from '@/features/imports/ImportFrame';
import { CheckStatus, ImportLocalStatus, UnfinishedImportNotice } from '@/features/imports/ImportStatus';
import { useTabNavigation } from '@/features/navigation';

function copyScopeHelp(): string {
  return currentCopy("Jawaban ini hanya berlaku antar perangkat dalam berkas ini.", "This answer applies only to the devices in this file.");
}

/** Pemetaan: what the service read, one control per open question, and Lihat pratinjau (027 D13 to D15). */
export function MappingStep() {
  const say = useCopy();
  const draft = useImportDraft();
  const { goImportStep, back } = useTabNavigation();
  const frame = useImportFrame();
  const [items, setItems] = useState<SummaryItem[]>([]);
  const [submits, setSubmits] = useState(0);
  const { preview, reloadPreview, intent } = draft;
  const pickFile = useFilePick(({ text }) => {
    setItems([{ key: 'reselect', text, unanswerable: false }]);
    setSubmits((count) => count + 1);
  });

  useEffect(() => {
    if (!preview && !intent) {
      void reloadPreview();
    }
  }, [intent, preview, reloadPreview]);

  if (intent) {
    return (
      <ImportFrame step="pemetaan" frame={frame}>
        <UnfinishedImportNotice />
      </ImportFrame>
    );
  }

  if (!preview) {
    return (
      <ImportFrame step="pemetaan" frame={frame}>
        {draft.check.kind === 'failed' ? <CheckStatus check={draft.check} onRetry={() => void reloadPreview()} /> : <HDProgressStatus state="loading" />}
      </ImportFrame>
    );
  }

  // Questions answered earlier stay as controls, so an answer can be seen and changed (027 US2 scenario 4).
  const controls = questionControls({ ...preview, questions: draft.asked.length ? draft.asked : preview.questions });
  const blockedByFile = controls.filter((control) => control.kind === 'unanswerable');
  const checking = draft.check.kind === 'pending';

  const submit = async () => {
    if (checking) {
      return;
    }
    setSubmits((count) => count + 1);
    const missing = unanswered(preview, draft.answers);
    if (missing.length) {
      setItems(missing);
      return;
    }
    if (!answersChanged(draft.sentAnswers, draft.answers) && preview.questions.length === 0) {
      setItems([]);
      goImportStep('pratinjau');
      return;
    }
    if (draft.needsReselect) {
      // The answers changed, so the file's bytes are needed again, and a reload cannot give them back.
      setItems([{ key: 'reselect', text: reselectText(draft.sourceName ?? ''), unanswerable: false }]);
      return;
    }
    setItems([]);
    const answers = draft.answers;
    const next = await draft.runPreview();
    if (!next) {
      return;
    }
    if (next.questions.length === 0) {
      goImportStep('pratinjau');
    } else {
      setItems([...unanswered(next, answers), ...askedAgain(next, answers)]);
    }
  };

  // The service's refusal of the answers, each item linked to the field it names (027 Error table).
  const refused =
    draft.check.kind === 'failed' && draft.check.outcome.kind === 'refused'
      ? draft.check.outcome.items.map((item) => ({ key: item.target === 'source' ? item.key : item.target, text: item.text, unanswerable: false }))
      : [];
  const summary = [...items, ...refused];
  const errorFor = (control: Control) => summary.find((item) => item.key === control.key)?.text ?? null;
  const register = (key: string) => (node: unknown) => {
    frame.refFor(key).current = node;
  };

  return (
    <ImportFrame
      step="pemetaan"
      frame={frame}
      footer={
        blockedByFile.length ? (
          <HDButton variant="primary" fullWidth onPress={back}>{say("Ubah berkas", "Change file")}</HDButton>
        ) : (
          <HDButton variant="primary" fullWidth loading={checking} loadingLabel={say("Menyiapkan pratinjau…", "Preparing preview…")} onPress={() => void submit()}>{say("Lihat pratinjau", "View preview")}</HDButton>
        )
      }>
      <HDErrorSummary
        errors={summary.map((item) => ({ key: item.key, text: item.text, target: () => frame.revealTarget(item.key) }))}
        submitCount={submits}
      />
      <ImportLocalStatus unsent={draft.unsent} failed={draft.persistenceFailed} />
      <CheckStatus check={draft.check} onRetry={() => void submit()} />
      {draft.needsReselect && draft.sourceName ? (
        <ReselectNotice
          name={draft.sourceName}
          noticeRef={register('reselect')}
          onPick={() =>
            void pickFile('reselect').then((picked) => {
              if (picked) {
                setItems([]);
              }
            })
          }
        />
      ) : null}
      <MappingFacts preview={preview} />
      {blockedByFile.map((control) => (
        <HDNotice key={control.key} tone="attention" title={control.message} />
      ))}
      {controls.map((control) => (
        <QuestionControl
          key={control.key}
          control={control}
          preview={preview}
          error={errorFor(control)}
          register={register(control.key)}
          disabled={checking}
        />
      ))}
      {blockedByFile.length ? null : (
        <HDButton variant="text" onPress={back}>{say("Ubah berkas", "Change file")}</HDButton>
      )}
    </ImportFrame>
  );
}

function MappingFacts({ preview }: { preview: ImportPreview }) {
  const say = useCopy();
  const { timezone, streams } = mappingOf(preview);
  const asksTimezone = preview.questions.some((question) => question.kind === 'timezone');
  return (
    <View style={styles.section}>
      <HDText variant="bodyStrong">{mappingLine(preview)}</HDText>
      {asksTimezone ? null : <HDText>{say(`Zona waktu ruang kerja: ${timezone}`, `Workspace time zone: ${timezone}`)}</HDText>}
      <View role="list" style={styles.section}>
        {streams.map((stream) => (
          <View key={stream.stream_key} role="listitem" style={styles.stream}>
            <HDText>{streamRow(stream)}</HDText>
            <HDText variant="label" tone="secondary">
              {streamTarget(stream)}
            </HDText>
          </View>
        ))}
      </View>
    </View>
  );
}

type QuestionControlProps = {
  control: Control;
  preview: ImportPreview;
  error: string | null;
  register: (node: unknown) => void;
  disabled: boolean;
};

function QuestionControl({ control, error, register, disabled }: QuestionControlProps) {
  const say = useCopy();
  const draft = useImportDraft();
  const answer = answerOf(control, draft.answers);
  const choose = (value: string) => draft.setAnswer(control, value);
  switch (control.kind) {
    case 'timezone':
      return (
        <HDChoiceGroup
          type="checkbox"
          legend={say(`Zona waktu ruang kerja: ${control.timezone}`, `Workspace time zone: ${control.timezone}`)}
          help={control.message}
          required
          error={error}
          disabled={disabled}
          groupRef={register}
          options={[{ value: 'confirmed', label: say(`Waktu dalam berkas adalah waktu lokal ${control.timezone}`, `The file uses local time in ${control.timezone}`) }]}
          value={answer === true ? ['confirmed'] : []}
          onChange={(value) => draft.setAnswer(control, value.includes('confirmed') ? true : undefined)}
        />
      );
    case 'scope':
      return (
        <HDChoiceGroup
          legend={say("Apakah beban perangkat dalam berkas ini terukur terpisah?", "Do the devices in this file measure separate loads?")}
          help={copyScopeHelp()}
          required
          error={error}
          disabled={disabled}
          groupRef={register}
          options={scopeOptions()}
          value={typeof answer === 'string' ? (answer as ReturnType<typeof scopeOptions>[number]['value']) : null}
          onChange={choose}
        />
      );
    case 'power_meaning':
      return (
        <HDChoiceGroup
          legend={control.message}
          required
          error={error}
          disabled={disabled}
          groupRef={register}
          options={powerOptions()}
          value={typeof answer === 'string' ? (answer as ReturnType<typeof powerOptions>[number]['value']) : null}
          onChange={choose}
        />
      );
    case 'value_kind':
      return (
        <HDChoiceGroup
          legend={control.message}
          required
          error={error}
          disabled={disabled}
          groupRef={register}
          options={valueKindOptions()}
          value={typeof answer === 'string' ? (answer as ReturnType<typeof valueKindOptions>[number]['value']) : null}
          onChange={choose}
        />
      );
    case 'interval_duration': {
      const typed = draft.intervalText[control.streamKey] ?? '';
      return (
        <HDTextField
          label={say(`Panjang interval untuk ${control.assetName} (menit)`, `Interval for ${control.assetName} (minutes)`)}
          help={control.message}
          required
          keyboardType="number-pad"
          value={typed}
          editable={!disabled}
          error={readMinutes(typed) === 'invalid' ? minutesError() : error}
          onChange={(text) => draft.setIntervalText(control, text)}
          inputRef={register}
        />
      );
    }
    case 'asset_choice':
      return (
        <HDChoiceGroup
          legend={control.message}
          required
          error={error}
          disabled={disabled}
          groupRef={register}
          options={control.options}
          value={typeof answer === 'string' ? answer : null}
          onChange={choose}
        />
      );
    case 'other_source':
      return (
        <View style={styles.section}>
          <HDChoiceGroup
            legend={control.message}
            required
            error={error}
            disabled={disabled}
            groupRef={register}
            options={[{ value: NEW_ASSET, label: say("Buat perangkat baru", "Create a new device"), description: say("Sumber yang sudah ada tidak dijumlahkan dengan berkas ini.", "Existing sources stay separate from this file.") }]}
            value={typeof answer === 'string' ? answer : null}
            onChange={choose}
          />
          <HDText variant="label">{say("Pemilihan sumber acuan belum tersedia di aplikasi ini.", "Reference source selection is unavailable here.")}</HDText>
        </View>
      );
    default:
      return null;
  }
}

const styles = StyleSheet.create({
  section: { gap: tokens.space.stackTight },
  stream: { gap: tokens.space['4'] },
});
