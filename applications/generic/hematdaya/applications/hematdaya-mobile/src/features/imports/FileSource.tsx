import { useCopy, currentCopy } from '@/features/localization/messages';
import * as DocumentPicker from 'expo-document-picker';
import type { ComponentRef, Ref } from 'react';
import { View } from 'react-native';

import type { ImportSource } from '@/api/client';
import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { MAX_IMPORT_BYTES, useImportDraft } from '@/features/imports/ImportDraftProvider';

// `*/*`: some Android providers label a CSV as octet-stream, which a narrower filter would grey out (027 D1).
const PICKER_OPTIONS = { type: '*/*', multiple: false, copyToCacheDirectory: true, base64: false };

export type PickRefusal = { key: string; text: string };

/**
 * Opens the system picker and turns its asset into a source, never reading the bytes in JavaScript: the web
 * uploads its File and native uploads the cached URI (027 D1). A file over the limit is refused before upload.
 */
export function useFilePick(onRefused: (refusal: PickRefusal) => void) {
  const draft = useImportDraft();
  return async (mode: 'replace' | 'reselect') => {
    let result: DocumentPicker.DocumentPickerResult;
    try {
      result = await DocumentPicker.getDocumentAsync(PICKER_OPTIONS);
    } catch {
      onRefused({ key: 'picker', text: currentCopy("Pemilih berkas tidak dapat dibuka. Coba lagi atau tempel isi CSV.", "Could not open the file picker. Try again or paste your CSV.") });
      return false;
    }
    const asset = result.canceled ? null : result.assets?.[0];
    if (!asset) {
      return false;
    }
    if (asset.size !== undefined && asset.size > MAX_IMPORT_BYTES) {
      onRefused({ key: 'size', text: currentCopy(`Ukuran ${asset.name} melebihi batas 10 MiB.`, `${asset.name} exceeds the 10 MiB limit.`) });
      return false;
    }
    if (mode === 'reselect' && asset.name !== draft.sourceName) {
      onRefused({ key: 'file', text: currentCopy(`Pilih kembali ${draft.sourceName}, atau kembali ke Berkas untuk memilih berkas lain.`, `Choose ${draft.sourceName} again, or go back to File to choose another file.`) });
      return false;
    }
    const source: ImportSource = asset.file
      ? { kind: 'file', file: asset.file }
      : { kind: 'file', uri: asset.uri, name: asset.name, mimeType: asset.mimeType };
    if (mode === 'reselect') {
      draft.reselect(source);
    } else {
      draft.replaceSource(source);
    }
    return true;
  };
}

export function reselectText(name: string): string {
  return currentCopy(`Berkas ${name} perlu dipilih ulang karena halaman dimuat ulang. Isi berkas tidak dapat dipulihkan dari peramban.`, `The page reloaded. Choose ${name} again to continue.`);
}

/** After a web reload: the file is named, and must be picked again. Nothing claims it was recovered (027 D12). */
export function ReselectNotice({ name, onPick, noticeRef }: { name: string; onPick: () => void; noticeRef?: Ref<ComponentRef<typeof View>> }) {
  const say = useCopy();
  return (
    <View ref={noticeRef} {...FOCUSABLE_BY_SCRIPT}>
      <HDNotice
        tone="attention"
        title={reselectText(name)}
        action={
          <HDButton icon="chevronRight" onPress={onPick}>{say("Pilih berkas lagi", "Choose file again")}</HDButton>
        }
      />
    </View>
  );
}

// Web only: an error summary's link can focus the notice without adding it to the tab order.
const FOCUSABLE_BY_SCRIPT = { tabIndex: -1 } as object;
