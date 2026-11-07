import { Redirect } from 'expo-router';

import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { ImportFrame, useImportFrame } from '@/features/imports/ImportFrame';
import { useImportDraft } from '@/features/imports/ImportDraftProvider';
import { InputStep } from '@/features/imports/InputStep';
import { MappingStep } from '@/features/imports/MappingStep';
import { PreviewStep } from '@/features/imports/PreviewStep';
import { ResultStep } from '@/features/imports/ResultStep';
import { useTabNavigation, type ImportStep } from '@/features/navigation';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

function isStep(value: string | undefined): value is ImportStep {
  return value === 'berkas' || value === 'pemetaan' || value === 'pratinjau' || value === 'hasil';
}

/** S10: four routes, one per step (027 D10). A step whose draft data is missing goes back to Berkas. */
export function ImportScreen({ step }: { step: string | undefined }) {
  const { status, workspace } = useWorkspace();
  const draft = useImportDraft();
  const { importHref } = useTabNavigation();
  const current: ImportStep = isStep(step) ? step : 'berkas';
  const frame = useImportFrame();

  if (status === 'loading' || !draft.ready) {
    return (
      <ImportFrame step={current} frame={frame}>
        <HDProgressStatus state="loading" label="Memuat ruang kerja…" />
      </ImportFrame>
    );
  }
  const hasPreview = draft.preview !== null || draft.importId !== null;
  const missing =
    !isStep(step) ||
    (current !== 'berkas' && !workspace) ||
    ((current === 'pemetaan' || current === 'pratinjau') && !hasPreview) ||
    (current === 'hasil' && draft.commit.kind !== 'committed');
  if (missing && current !== 'berkas') {
    return <Redirect href={importHref('berkas')} />;
  }
  if (!isStep(step)) {
    return <Redirect href={importHref('berkas')} />;
  }
  switch (current) {
    case 'pemetaan':
      return <MappingStep />;
    case 'pratinjau':
      return <PreviewStep />;
    case 'hasil':
      return <ResultStep />;
    default:
      return <InputStep />;
  }
}
