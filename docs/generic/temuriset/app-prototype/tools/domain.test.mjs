// Service-level oracles for the prototype. Run: node docs/generic/temuriset/app-prototype/tools/domain.test.mjs
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const D = createRequire(import.meta.url)('../project/domain.js');
const { RANI, MITRA_A, BIMA, INVESTOR_B } = D.actors;
const results = [];
function check(id, fn) {
  try { fn(); results.push(['PASS', id]); } catch (e) { results.push(['FAIL', id, e.message.split('\n')[0]]); }
}
const SR = (id) => ({ type: 'SUPPORT_REQUEST', id });
const FR = { type: 'FUNDING_REQUEST', id: 'FRaise01' };
const row = (r, id) => r.rows.find((x) => x.id === id);

check('Fixture F01 baseline READY_TO_SUBMIT, company/patent absence no blocker', () => {
  const r = D.create().evaluate(SR('sr-f01'), 'A1');
  assert.equal(r.readiness, 'READY_TO_SUBMIT');
  assert.equal(r.eligibility, 'ELIGIBLE');
  assert.equal(row(r, 'A1-file').result, 'PASS');
  assert.equal(row(r, 'A1-cert').result, 'UNKNOWN');
});
check('F01-GAP UNKNOWN budget then completing restores readiness (J01)', () => {
  const s = D.create(); s.setVariant('gap', true);
  let r = s.evaluate(SR('sr-f01'), 'A1');
  assert.equal(r.readiness, 'NEEDS_INFORMATION'); assert.equal(r.label, 'Perlu konfirmasi');
  assert.equal(r.gap.id, 'A1-budget');
  const saved = s.saveSupportRequest({ actor: RANI }, { id: 'sr-f01', fields: {}, budget: { min: '20.000', max: '30000' } });
  assert.ok(saved.ok);
  r = s.evaluate(SR('sr-f01'), 'A1');
  assert.equal(r.readiness, 'READY_TO_SUBMIT');
  assert.equal(s.state.requests['sr-f01'].budget.min, '20000');
});
check('AC16 min -1 and max below min rejected, no save', () => {
  const s = D.create();
  assert.equal(s.saveSupportRequest({ actor: RANI }, { id: 'sr-f01', fields: {}, budget: { min: '-1', max: '30000' } }).code, 'VALIDATION');
  const r = s.saveSupportRequest({ actor: RANI }, { id: 'sr-f01', fields: {}, budget: { min: '30000', max: '20000' } });
  assert.ok(r.fields.max);
  assert.equal(s.state.requests['sr-f01'].version, 1);
});
check('F01-SCAN file passes, extraction NEEDS_MANUAL_INPUT, reviewed stays UNKNOWN', () => {
  const s = D.create(); s.setVariant('scan', true);
  const r = s.evaluate(SR('sr-f01'), 'A1');
  assert.equal(row(r, 'A1-file').result, 'PASS');
  assert.equal(s.state.documents['doc-f01'].versions[0].extraction, 'NEEDS_MANUAL_INPUT');
  assert.equal(row(r, 'A1-cert').result, 'UNKNOWN');
});
check('F02 authority UNKNOWN gives NEEDS_INFORMATION, no invented money', () => {
  const s = D.create(), r = s.evaluate(SR('sr-f02'), 'A2');
  assert.equal(row(r, 'A2-auth').result, 'UNKNOWN'); assert.equal(r.readiness, 'NEEDS_INFORMATION');
  assert.equal(s.state.requests['sr-f02'].budget.min, null);
});
check('F03 PLANNED SSO FAIL, blocked despite topic overlap (AC31)', () => {
  const r = D.create().evaluate(SR('sr-f03'), 'D1');
  assert.equal(row(r, 'D1-sso').result, 'FAIL');
  assert.equal(r.readiness, 'BLOCKED_FOR_THIS_TARGET'); assert.equal(r.eligibility, 'INCOMPATIBLE');
  assert.equal(r.label, 'Tidak cocok untuk target ini');
});
check('F04 contribution PASS against desired range, not whole round (AC20)', () => {
  const s = D.create(), r = s.evaluate(FR, 'B1');
  assert.equal(row(r, 'B1-check').result, 'PASS'); assert.equal(r.readiness, 'READY_TO_SUBMIT');
  assert.equal(s.state.fundings.FRaise01.target, '500000');
});
check('F05 one active pitch through second link, duplicate points to existing (AC39)', () => {
  const s = D.create(), id = D.seeds.funding(s);
  const pre = s.preflight({ actor: BIMA }, { source: FR, opportunityId: 'B1' });
  assert.equal(pre.duplicate, id);
  const dup = s.submitPitch({ actor: BIMA, key: 'second' }, { source: FR, opportunityId: 'B1', token: pre.token, brief: 'x', files: [] });
  assert.equal(dup.code, 'DUPLICATE'); assert.equal(dup.pitchId, id);
  assert.equal(Object.keys(s.state.pitches).length, 1);
  assert.equal(s.state.pitches[id].inventions.length, 2);
  assert.equal(Object.keys(s.state.fundings).length, 1);
});
check('J02 target edit makes a new version, sent snapshot unchanged', () => {
  const s = D.create(), id = D.seeds.funding(s), f = s.state.fundings.FRaise01;
  const r = s.saveFundingRequest({ actor: BIMA }, { id: f.id, expected: 1, fields: { target: '600000', desiredMin: '50000', desiredMax: '100000' } });
  assert.equal(r.version, 2); assert.equal(s.state.fundings.FRaise01.target, '600000');
  assert.equal(s.state.pitches[id].submissions[0].funding.target, '500000');
});
check('Proposed entity: B1 FAIL, B2 allows discussion, equity confirmation blocked (AC21)', () => {
  const s = D.create(); s.setProposedEntity(true);
  assert.equal(row(s.evaluate(FR, 'B1'), 'B1-entity').result, 'FAIL');
  assert.equal(s.evaluate(FR, 'B2').readiness, 'READY_TO_SUBMIT');
});
check('F06 mentoring passes, entity UNKNOWN for equity target', () => {
  const s = D.create();
  assert.equal(s.evaluate(SR('sr-f06'), 'A3').readiness, 'READY_TO_SUBMIT');
  assert.equal(row(s.evaluate(SR('sr-f06'), 'B1'), 'B1-entity').result, 'UNKNOWN');
});
check('Project funding vs equity-only mandate is a relationship-form FAIL', () => {
  assert.equal(row(D.create().evaluate(SR('sr-f01'), 'B1'), 'B1-form').result, 'FAIL');
});
check('EUR and unlike periods stay UNKNOWN', () => {
  const s = D.create(); s.state.requests['sr-f01'].budget.currency = 'EUR';
  assert.equal(row(s.evaluate(SR('sr-f01'), 'A1'), 'A1-budget').result, 'UNKNOWN');
  const t = D.create(); t.state.requests['sr-f01'].budget.period = '1 bulan';
  assert.equal(row(t.evaluate(SR('sr-f01'), 'A1'), 'A1-budget').result, 'UNKNOWN');
});
check('AC33 score oracle 71.72-80.00', () => {
  const b = D.fitBounds({ low: 0.8, high: 0.8, known: 1 }, { low: 0.65, high: 0.8, known: 0.85 });
  assert.equal(b.lower, 71.72); assert.equal(b.upper, 80);
});
check('F01-STALE target change rejected, recheck required (AC34)', () => {
  const s = D.create(), src = SR('sr-f01'), pre = s.preflight({ actor: RANI }, { source: src, opportunityId: 'A1' });
  s.changeTargetVersion();
  const r = s.submitPitch({ actor: RANI, key: 'k1' }, { source: src, opportunityId: 'A1', token: pre.token, brief: 'draf', files: [] });
  assert.equal(r.code, 'STALE_VERSION'); assert.equal(Object.keys(s.state.pitches).length, 0);
});
check('AC26 closed opportunity rejects fresh submit', () => {
  const s = D.create(), src = SR('sr-f01'), pre = s.preflight({ actor: RANI }, { source: src, opportunityId: 'A1' });
  s.setOpportunityStatus({ actor: MITRA_A }, { id: 'A1', status: 'CLOSED' });
  assert.equal(s.submitPitch({ actor: RANI, key: 'k1' }, { source: src, opportunityId: 'A1', token: pre.token, brief: 'x', files: [] }).code, 'TARGET_CLOSED');
});
check('F01-TIMEOUT same key returns one pitch; changed body conflicts (AC37, AC38)', () => {
  const s = D.create(), src = SR('sr-f01'), pre = s.preflight({ actor: RANI }, { source: src, opportunityId: 'A1' });
  const args = { source: src, opportunityId: 'A1', token: pre.token, brief: 'draf', files: [{ docId: 'doc-f01', version: 1 }] };
  s.setFault('lostAfterCommit', 'submitPitch');
  const lost = s.submitPitch({ actor: RANI, key: 'k1' }, args);
  assert.equal(lost.code, 'LOST_RESPONSE');
  const retry = s.submitPitch({ actor: RANI, key: 'k1' }, args);
  assert.ok(retry.ok && retry.replayed);
  assert.equal(Object.keys(s.state.pitches).length, 1);
  assert.equal(s.submitPitch({ actor: RANI, key: 'k1' }, { ...args, brief: 'lain' }).code, 'IDEMPOTENCY_CONFLICT');
});
check('F01-DENIED unrelated actor gets no metadata (AC48)', () => {
  const s = D.create(), id = D.seeds.submitted(s);
  assert.equal(s.pitchFor({ account: 'lain', party: 'p-x' }, id), null);
  const r = s.fetchDocument({ actor: { account: 'lain', party: 'p-x' } }, { docId: 'doc-f01', version: 1 });
  assert.equal(r.code, 'NOT_FOUND'); assert.equal(r.title, undefined);
});
check('AC04 member without decide capability rejected', () => {
  const s = D.create(), id = D.seeds.submitted(s);
  const r = s.decide({ actor: { account: 'stafA', party: 'p-a' } }, { pitchId: id, decision: 'APPROVE', expected: s.state.pitches[id].version });
  assert.equal(r.code, 'FORBIDDEN');
});
check('AC40 approval opens discussion only, no relationship', () => {
  const s = D.create(), id = D.seeds.approved(s);
  assert.equal(s.state.pitches[id].status, 'APPROVED_FOR_DISCUSSION');
  assert.equal(Object.keys(s.state.partnerships).length, 0);
});
check('AC41 stale decision loses', () => {
  const s = D.create(), id = D.seeds.submitted(s), v = s.state.pitches[id].version;
  assert.ok(s.decide({ actor: MITRA_A }, { pitchId: id, decision: 'APPROVE', expected: v }).ok);
  assert.equal(s.decide({ actor: MITRA_A }, { pitchId: id, decision: 'REJECT', reason: 'x', expected: v }).code, 'STALE_VERSION');
});
check('AC42 withdrawn pitch cannot be decided; approved cannot go to revision', () => {
  const s = D.create(), id = D.seeds.submitted(s);
  s.withdraw({ actor: RANI }, { pitchId: id });
  assert.equal(s.decide({ actor: MITRA_A }, { pitchId: id, decision: 'APPROVE', expected: s.state.pitches[id].version }).code, 'INVALID_STATE');
  const t = D.create(), a = D.seeds.approved(t);
  assert.equal(t.requestRevision({ actor: MITRA_A }, { pitchId: a, expected: t.state.pitches[a].version, items: D.revisionItems }).code, 'INVALID_STATE');
});
check('J03 required answer enforced; inability valid; prior round and snapshot kept (AC43, AC45)', () => {
  const s = D.create(), id = D.seeds.revision(s), p = s.state.pitches[id];
  assert.equal(s.resubmit({ actor: RANI }, { pitchId: id, expected: p.version }).code, 'VALIDATION');
  s.saveAnswer({ actor: RANI }, { pitchId: id, itemId: 'r1i1', value: { response: 'CANNOT', text: 'Baru satu lokasi' } });
  const r = s.resubmit({ actor: RANI }, { pitchId: id, expected: p.version, files: [{ docId: 'doc-f01', version: 1 }] });
  assert.ok(r.ok); assert.equal(p.status, 'SUBMITTED'); assert.equal(p.submissions.length, 2);
  assert.equal(p.rounds[0].items[0].answer.response, 'CANNOT');
  assert.equal(p.decisions.length, 0);
  assert.ok(s.reviewItem({ actor: MITRA_A }, { pitchId: id, itemId: 'r1i1', result: 'ACCEPTED' }).ok);
  assert.ok(s.decide({ actor: MITRA_A }, { pitchId: id, decision: 'APPROVE', expected: p.version }).ok);
});
check('AC44 revision does not turn planned into current', () => {
  const s = D.create(), id = D.seeds.revision(s);
  s.saveAnswer({ actor: RANI }, { pitchId: id, itemId: 'r1i2', value: { response: 'CAN', text: 'Tahun depan' } });
  const f = s.pubV(s.state.inventions['inv-f01']).facts.find((x) => x.id === 'fct-plan');
  assert.equal(f.timing, 'PLANNED');
});
check('J04 conflict, half-open acceptance, one active meeting (AC50)', () => {
  const s = D.create(), id = D.seeds.proposal(s), pr = s.openProposal(id);
  assert.equal(s.acceptSlot({ actor: RANI, key: 'a' }, { proposalId: pr.id, slotId: 'slot1' }).code, 'BOOKING_CONFLICT');
  assert.equal(s.openProposal(id).agenda, 'Membahas rencana validasi enam bulan');
  s.proposeSlots({ actor: RANI }, { pitchId: id, slots: ['2026-11-04T09:30:00Z', '2026-11-04T10:00:00Z'], minutes: 60, zone: 'Asia/Jakarta', agenda: 'Membahas rencana validasi enam bulan' });
  assert.equal(pr.state, 'SUPERSEDED');
  const cp = s.openProposal(id);
  assert.equal(s.acceptSlot({ actor: MITRA_A, key: 'b' }, { proposalId: cp.id, slotId: 'slot1' }).code, 'BOOKING_CONFLICT');
  const ok = s.acceptSlot({ actor: MITRA_A, key: 'c' }, { proposalId: cp.id, slotId: 'slot2' });
  assert.ok(ok.ok);
  assert.equal(Object.values(s.state.meetings).filter((m) => m.state === 'CONFIRMED').length, 1);
  const ics = s.ics(s.state.meetings[ok.meetingId]);
  assert.ok(ics.includes('DTSTART:20261104T100000Z') && ics.includes('DTEND:20261104T110000Z'));
});
check('Selection alone is no booking; proposer cannot accept own proposal', () => {
  const s = D.create(), id = D.seeds.proposal(s), pr = s.openProposal(id);
  assert.equal(Object.keys(s.state.meetings).length, 0);
  assert.equal(s.acceptSlot({ actor: MITRA_A }, { proposalId: pr.id, slotId: 'slot2' }).code, 'FORBIDDEN');
});
check('All-slots-past expiry before 72h leaves pitch approved', () => {
  const s = D.create(), id = D.seeds.proposal(s), pr = s.openProposal(id);
  s.setClock('2026-11-04T13:00:00Z');
  assert.equal(pr.state, 'EXPIRED'); assert.equal(pr.expiredBy, 'ALL_PAST');
  assert.equal(s.state.pitches[id].status, 'APPROVED_FOR_DISCUSSION');
});
check('SCHED-72H age expiry at exactly 72 hours with future slots', () => {
  const s = D.create(), id = D.seeds.approved(s);
  s.proposeSlots({ actor: MITRA_A }, { pitchId: id, slots: ['2026-11-06T09:00:00Z', '2026-11-06T11:00:00Z', '2026-11-06T13:00:00Z'], minutes: 60, zone: 'Asia/Jakarta', agenda: 'Agenda' });
  const pr = s.openProposal(id);
  s.setClock('2026-11-05T07:59:00Z'); assert.equal(pr.state, 'OPEN');
  s.setClock('2026-11-05T08:00:00Z'); assert.equal(pr.state, 'EXPIRED'); assert.equal(pr.expiredBy, 'AGE');
});
check('AC51 reschedule keeps old meeting until replacement', () => {
  const s = D.create(), id = D.seeds.approved(s);
  s.proposeSlots({ actor: MITRA_A }, { pitchId: id, slots: ['2026-11-04T10:00:00Z', '2026-11-04T11:00:00Z'], minutes: 60, zone: 'Asia/Jakarta', agenda: 'A' });
  const old = s.acceptSlot({ actor: RANI }, { proposalId: s.openProposal(id).id, slotId: 'slot1' }).meetingId;
  s.proposeSlots({ actor: RANI }, { pitchId: id, slots: ['2026-11-05T10:30:00Z', '2026-11-05T11:30:00Z'], minutes: 60, zone: 'Asia/Jakarta', agenda: 'A', replaces: old });
  assert.equal(s.state.meetings[old].state, 'CONFIRMED');
  const nw = s.acceptSlot({ actor: MITRA_A }, { proposalId: s.openProposal(id).id, slotId: 'slot1' }).meetingId;
  assert.equal(s.state.meetings[old].state, 'CANCELLED');
  assert.equal(s.activeMeeting(id).id, nw);
  assert.equal(s.state.bookings.filter((b) => b.meetingId === old).length, 0);
});
check('AC47 elapsed meeting is not completed without outcomes', () => {
  const s = D.create(), id = D.seeds.approved(s);
  s.proposeSlots({ actor: MITRA_A }, { pitchId: id, slots: ['2026-11-04T10:00:00Z', '2026-11-04T11:00:00Z'], minutes: 60, zone: 'Asia/Jakarta', agenda: 'A' });
  const m = s.acceptSlot({ actor: RANI }, { proposalId: s.openProposal(id).id, slotId: 'slot1' }).meetingId;
  s.setClock('2026-11-20T00:00:00Z');
  assert.equal(s.state.meetings[m].state, 'CONFIRMED');
});
check('J05 correction resets confirmations; intersection hides amount; narrowing immediate (AC52-55)', () => {
  const s = D.create(), id = D.seeds.partnership(s), r = s.state.partnerships[id];
  assert.equal(s.effectiveFields(r).version, null);
  assert.equal(s.publicRelationships('p-rani').length, 0);
  s.requestCorrection({ actor: MITRA_A }, { id, version: 1, note: 'Durasi enam bulan', values: { scope: 'Validasi prototipe enam bulan' } });
  assert.equal(r.versions[0].status, 'CHANGES_REQUESTED');
  assert.deepEqual(Object.keys(r.versions[1].confirmations), []);
  s.confirmPartnership({ actor: RANI }, { id, version: 2, subset: ['name', 'type', 'scope', 'date', 'amount'] });
  assert.equal(s.effectiveFields(r).version, null);
  assert.equal(s.confirmPartnership({ actor: MITRA_A }, { id, version: 1, subset: [] }).code, 'STALE_VERSION');
  s.confirmPartnership({ actor: MITRA_A }, { id, version: 2, subset: ['name', 'type', 'scope', 'date'] });
  assert.deepEqual(s.effectiveFields(r).fields, ['name', 'type', 'scope', 'date']);
  s.restrictField({ actor: RANI }, { id, field: 'date' });
  assert.deepEqual(s.effectiveFields(r).fields, ['name', 'type', 'scope']);
  assert.equal(s.publicRelationships('p-a')[0].fields.amount, undefined);
  assert.equal(s.publicRelationships('p-a')[0].fields.date, undefined);
  assert.equal(r.versions[1].status, 'CONFIRMED');
});
check('AC21 equity on proposed entity blocked; PROJECT creates no percent', () => {
  const s = D.create(); s.setProposedEntity(true);
  const source = FR, pre = s.preflight({ actor: BIMA }, { source, opportunityId: 'B2' });
  const id = s.submitPitch({ actor: BIMA, key: 'p' }, { source, opportunityId: 'B2', token: pre.token, brief: 'x', files: [] }).pitchId;
  s.decide({ actor: INVESTOR_B }, { pitchId: id, decision: 'APPROVE', expected: s.state.pitches[id].version });
  s.proposeSlots({ actor: INVESTOR_B }, { pitchId: id, slots: ['2026-11-04T10:00:00Z', '2026-11-04T11:00:00Z'], minutes: 30, zone: 'Asia/Jakarta', agenda: 'A' });
  const m = s.acceptSlot({ actor: BIMA }, { proposalId: s.openProposal(id).id, slotId: 'slot1' }).meetingId;
  s.setClock('2026-11-04T12:00:00Z');
  s.recordOutcome({ actor: BIMA }, { id: m, result: 'COMPLETED' }); s.recordOutcome({ actor: INVESTOR_B }, { id: m, result: 'COMPLETED' });
  const r = s.proposePartnership({ actor: BIMA }, { pitchId: id, type: 'EQUITY', values: { scope: 'Ekuitas', date: '1 Januari 2027' }, ceiling: ['name'], subset: ['name'] });
  assert.ok(r.fields.type);
});
check('AC60 disabling review blocked while queue pending; AC58 off by default', () => {
  const s = D.create();
  assert.equal(s.state.flags.orgReview, false);
  s.setFlag('orgReview', true);
  const id = D.seeds.funding(s);
  assert.equal(s.state.pitches[id].status, 'PENDING_WORKSPACE_REVIEW');
  assert.equal(s.setFlag('orgReview', false).code, 'PENDING_REVIEW_ITEMS');
  const rid = Object.keys(s.state.reviews)[0];
  s.decideReview({ actor: BIMA }, { id: rid, approve: true });
  assert.equal(s.state.pitches[id].status, 'SUBMITTED');
  assert.ok(s.setFlag('orgReview', false).ok);
});
check('AC67 company funding off rejects mutation, project support works', () => {
  const s = D.create(); s.setFlag('companyFunding', false);
  assert.equal(s.saveFundingRequest({ actor: BIMA }, { id: 'FRaise01', fields: { target: '1', desiredMin: '', desiredMax: '' } }).code, 'CAPABILITY_UNAVAILABLE');
  assert.ok(s.saveSupportRequest({ actor: RANI }, { id: 'sr-f01', fields: {}, budget: { min: '20000', max: '30000' } }).ok);
});
check('AC65 revocation blocks new fetch, prior download remains counted', () => {
  const s = D.create(), id = D.seeds.submitted(s), gid = Object.keys(s.state.grants)[0];
  assert.ok(s.fetchDocument({ actor: MITRA_A }, { docId: 'doc-f01', version: 1 }).ok);
  s.revokeGrant({ actor: RANI }, { id: gid });
  assert.equal(s.fetchDocument({ actor: MITRA_A }, { docId: 'doc-f01', version: 1 }).code, 'NOT_FOUND');
  assert.equal(s.state.grants[gid].downloads, 1);
  assert.ok(id);
});
check('Pre-commit failure leaves state untouched; retry succeeds', () => {
  const s = D.create(); s.startDraft({ actor: RANI }, { id: 'inv-f01' });
  s.setFault('preCommit', 'saveDraft');
  const r = s.saveDraft({ actor: RANI, key: 'd1' }, { id: 'inv-f01', rev: 1, fields: { title: 'ClearSpring 2' } });
  assert.equal(r.code, 'NETWORK'); assert.equal(s.state.inventions['inv-f01'].draft.title, 'ClearSpring');
  assert.ok(s.saveDraft({ actor: RANI, key: 'd1' }, { id: 'inv-f01', rev: 1, fields: { title: 'ClearSpring 2' } }).ok);
});
check('AC08 edit after submission leaves snapshot intact', () => {
  const s = D.create(), id = D.seeds.submitted(s);
  s.startDraft({ actor: RANI }, { id: 'inv-f01' });
  s.saveDraft({ actor: RANI }, { id: 'inv-f01', rev: 1, fields: { title: 'ClearSpring Baru' } });
  s.publishInvention({ actor: RANI }, { id: 'inv-f01' });
  assert.equal(s.state.pitches[id].submissions[0].inventions[0].title, 'ClearSpring');
  assert.equal(s.pubV(s.state.inventions['inv-f01']).n, 2);
});

check('No relevance signal abstains from a positive match even when rules pass', () => {
  const s = D.create(), off = s.evaluate(SR('sr-f01'), 'A3');
  assert.equal(off.readiness, 'READY_TO_SUBMIT'); assert.equal(off.relevant, false);
  assert.equal(off.label, 'Belum ada sinyal relevansi');
  assert.equal(s.evaluate(SR('sr-f06'), 'A3').relevant, true);
});
check('Reset replaces the one state authority for every reader', () => {
  const s = D.create(), id = D.seeds.submitted(s);
  assert.ok(s.state.pitches[id]);
  s.replace(D.baseline());
  assert.equal(Object.keys(s.state.pitches).length, 0);
  s.setVariant('gap', true);
  assert.equal(s.state.variants.gap, true);
});

const failed = results.filter((r) => r[0] === 'FAIL');
results.forEach((r) => console.log(r.join(' · ')));
console.log(`${results.length - failed.length}/${results.length} passed`);
process.exit(failed.length ? 1 : 0);
