import { readDraft, storeDraft } from '@/features/imports/draft-store';

it('stores a filename for reselection while dropping file bytes, credentials and pending operations', () => {
  const raw = storeDraft({
    source: { kind: 'file', name: 'reading.csv', uri: 'file:///secret-location' },
    answers: { scope: 'disjoint' }, intervalText: {}, importId: 'preview-1',
  });
  expect(raw).not.toMatch(/secret-location|intent|token/);
  expect(readDraft(raw)).toMatchObject({ source: { name: 'reading.csv' }, needsReselect: true, importId: 'preview-1' });
});

it('uses a bounded paste with an honest reselection label', () => {
  const raw = storeDraft({ source: { kind: 'paste', text: 'x'.repeat(600_000) }, answers: {}, intervalText: {}, importId: null });
  expect(readDraft(raw)).toMatchObject({ source: null, textDropped: true });
});
