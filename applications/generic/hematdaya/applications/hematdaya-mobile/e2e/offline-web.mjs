import assert from 'node:assert/strict';
import { randomBytes } from 'node:crypto';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.HEMATDAYA_PLAYWRIGHT_MODULE ?? 'playwright');
const web = new URL(process.env.HEMATDAYA_WEB_URL ?? 'http://localhost:8081').origin;
const api = new URL(process.env.HEMATDAYA_API_URL ?? 'http://localhost:8000').origin;
const workspaceKey = 'hematdaya.workspace.v1';
const week = '?start_date=2026-10-19&end_date=2026-10-25';
const button = (page, name) => page.getByRole('button', { name, exact: true });
const heading = (page, name) => page.getByRole('heading', { name, exact: true });
const visibleText = (page, value) => page.getByText(value, { exact: typeof value === 'string' }).filter({ visible: true }).first();
const visible = (locator) => locator.waitFor({ state: 'visible' });
const offlineSnapshot = (page) => visibleText(page, 'Offline · menampilkan data tersimpan');
const fetchStamp = (page) => visibleText(page, /^Terakhir dimuat: /);
const editDialog = (page) => page.getByRole('dialog', { name: 'Ubah detail perangkat' });
const nameField = (page) => editDialog(page).getByRole('textbox', { name: 'Nama perangkat' });

async function seed(page, scenario) {
  const response = await page.request.post(api + '/api/v1/demo/sessions', {
    data: { scenario_id: scenario },
    headers: {
      'Idempotency-Key': randomBytes(16).toString('base64url'),
      'X-Demo-Replay-Proof': randomBytes(32).toString('base64url'),
    },
  });
  assert.equal(response.status(), 201);
  const body = await response.json();
  return {
    token: body.token,
    siteId: body.site_id,
    scenarioId: body.scenario_id,
    expiresAt: body.expires_at,
    initialPeriod: body.initial_period,
  };
}

async function openFixture(browser, scenario) {
  const page = await browser.newPage({ viewport: { width: 320, height: 800 } });
  page.setDefaultTimeout(25000);
  try {
    const workspace = await seed(page, scenario);
    // Seed only the legacy credential record. The app must attest it against the real owned-site endpoint.
    await page.goto(web + '/beranda');
    await page.evaluate(({ key, value }) => sessionStorage.setItem(key, JSON.stringify(value)), {
      key: workspaceKey, value: workspace,
    });
    await page.reload();
    await visible(heading(page, 'Beranda'));
    return { page, workspace };
  } catch (error) {
    await page.close();
    throw error;
  }
}

async function fromApi(page, workspace, path) {
  const response = await page.request.get(api + '/api/v1' + path, {
    headers: { Authorization: 'Bearer ' + workspace.token },
  });
  assert.equal(response.status(), 200);
  return response.json();
}

async function offline(page, value) {
  await page.context().setOffline(value);
  await page.waitForFunction((expected) => navigator.onLine === expected, !value);
}

/** The app shell is served for this reload. Only the API and the browser's online signal are unavailable. */
async function coldWithoutApi(page) {
  const drop = (route) => route.abort('internetdisconnected');
  await page.route(api + '/**', drop);
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'onLine', { get: () => false, configurable: true });
  });
  await page.reload();
  return async () => {
    await page.unroute(api + '/**', drop);
    await page.evaluate(() => {
      delete navigator.onLine;
      window.dispatchEvent(new Event('online'));
    });
  };
}

async function checkStale(page, workspace) {
  await visible(visibleText(page, '14,640 kWh'));
  await visible(visibleText(page, /^Data belum diperbarui/));
  await visible(visibleText(page, /25 Oktober 2026 18[.:]00/));
  await visible(visibleText(page, /1 jam/));
  await offline(page, true);
  await visible(offlineSnapshot(page));
  const firstFetch = await fetchStamp(page).innerText();
  assert(!firstFetch.includes('25 Oktober 2026'));

  const summary = api + '/api/v1/sites/' + workspace.siteId + '/summary?*';
  const reject = (route) => route.fulfill({
    status: 400,
    headers: { 'Access-Control-Allow-Origin': web },
    json: {
      error: {
        code: 'BAD_REQUEST', message: 'Permintaan uji tidak diterima.', request_id: 'offline-web-read',
        recovery: { retryable: false },
      },
    },
  });
  await page.route(summary, reject);
  await offline(page, false);
  await visible(fetchStamp(page));
  const requests = [];
  page.on('request', (request) => {
    if (request.url().startsWith(api) && request.method() !== 'OPTIONS') requests.push(request);
  });
  const failed = page.waitForResponse((response) => response.url().includes('/summary?') && response.status() === 400);
  await button(page, 'Periksa sumber').click();
  await failed;
  assert(requests.length > 0);
  assert(requests.every((request) => request.method() === 'GET' && request.url().includes('/summary?')));
  await visible(visibleText(page, '14,640 kWh'));
  assert.equal(await fetchStamp(page).innerText(), firstFetch);
  await page.unroute(summary, reject);
  await coldWithoutApi(page);
  await visible(offlineSnapshot(page));
  await visible(visibleText(page, '14,640 kWh'));
  await visible(visibleText(page, /25 Oktober 2026 18[.:]00/));
  assert.equal(await fetchStamp(page).innerText(), firstFetch);
}

async function checkDraft(page, workspace) {
  await visible(visibleText(page, '14,700 kWh'));
  const assets = await fromApi(page, workspace, '/sites/' + workspace.siteId + '/assets');
  const asset = assets.items.find((item) => item.name === 'Kulkas');
  assert(asset);
  const patches = [];
  page.on('request', (request) => {
    if (request.method() === 'PATCH' && request.url().endsWith('/assets/' + asset.id)) patches.push(request.postDataJSON());
  });
  await button(page, 'Lihat perangkat terbesar').click();
  await button(page, 'Ubah detail').click();
  await offline(page, true);
  const draftName = 'Kulkas Draf Offline';
  await nameField(page).fill(draftName);
  await button(page, 'Simpan').click();
  await visible(visibleText(page, 'Perubahan belum dikirim'));
  assert.deepEqual(patches, []);
  await page.waitForFunction((name) => Object.values(localStorage).some((value) => value.includes(name)), draftName);
  await offline(page, false);
  const reconnect = await coldWithoutApi(page);
  await button(page, 'Buka draf detail').click();
  assert.equal(await nameField(page).inputValue(), draftName);
  await reconnect();
  await button(page, 'Simpan').click();
  await visible(visibleText(page, 'Detail terkini sudah diperiksa'));
  assert.deepEqual(patches, []);
  await button(page, 'Simpan').click();
  await visible(heading(page, draftName));
  assert.deepEqual(patches, [{ name: draftName }]);
}

async function checkOwner(page) {
  await visible(visibleText(page, '14,700 kWh'));
  await button(page, 'Lihat perangkat terbesar').click();
  await button(page, 'Ubah detail').click();
  const oldDraft = 'Draf pemilik rumah';
  await nameField(page).fill(oldDraft);
  await page.waitForFunction((name) => Object.values(localStorage).some((value) => value.includes(name)), oldDraft);
  const { page: other } = await openFixture(page.context().browser(), 'i-base');
  try {
    await visible(visibleText(other, '144,000 kWh'));
    // Copy only the newly attested test identity. Keep the first owner's local storage to test isolation.
    const control = await other.evaluate((key) => sessionStorage.getItem(key), workspaceKey);
    assert(control && JSON.parse(control).attestation);
    await page.evaluate(({ key, value }) => {
      sessionStorage.setItem(key, value);
      history.replaceState(null, '', '/beranda');
    }, { key: workspaceKey, value: control });
  } finally {
    await other.close();
  }
  const reconnect = await coldWithoutApi(page);
  await visible(visibleText(page, 'Offline · belum ada data tersimpan'));
  assert(await page.evaluate((name) => Object.values(localStorage).some((value) => value.includes(name)), oldDraft));
  assert(!(await page.locator('body').innerText()).includes('14,700 kWh'));
  await reconnect();
  await visible(visibleText(page, '144,000 kWh'));
  await offline(page, true);
  await visible(offlineSnapshot(page));
  const body = await page.locator('body').innerText();
  assert(!body.includes('Kulkas') && !body.includes(oldDraft));
}

async function checkHistorical(page) {
  const writes = [];
  page.on('request', (request) => {
    if (request.method() === 'POST' && request.url().includes('/imports/')) writes.push(request);
  });
  await button(page, 'Tambah data').click();
  await button(page, 'Contoh berkas yang dapat disalin').click();
  await page.getByRole('group', { name: 'Valid: dua perangkat, interval 1 jam' })
    .getByRole('button', { name: 'Gunakan contoh ini' }).click();
  await offline(page, true);
  await button(page, 'Periksa berkas').click();
  await visible(visibleText(page, 'Impor belum dikirim'));
  await offline(page, false);
  await page.waitForTimeout(450);
  assert.equal(writes.length, 0);
  await button(page, 'Periksa berkas').click();
  await visible(visibleText(page, 'Langkah 2 dari 4 · Arti kolom dan pemetaan'));
  const timezone = page.getByRole('checkbox', { name: 'Waktu dalam berkas adalah waktu lokal Asia/Jakarta' });
  if (await timezone.isVisible()) await timezone.click();
  await page.getByRole('radio', { name: 'Ya, terpisah satu sama lain dan dari perangkat lain' }).click();
  await button(page, 'Lihat pratinjau').click();
  await visible(button(page, 'Konfirmasi impor'));
  const beforeCommit = writes.length;
  await offline(page, true);
  await button(page, 'Konfirmasi impor').click();
  await visible(visibleText(page, 'Impor belum dikirim'));
  await offline(page, false);
  await page.waitForTimeout(450);
  assert.equal(writes.length, beforeCommit);

  const keys = [];
  await page.route('**/imports/*/commit', (route) => {
    if (route.request().method() !== 'POST') return route.continue();
    keys.push(route.request().headers()['idempotency-key']);
    return keys.length === 1 ? route.abort('failed') : route.continue();
  });
  await button(page, 'Konfirmasi impor').click();
  await visible(visibleText(page, 'Status impor belum diketahui'));
  await page.reload();
  await button(page, 'Periksa status').click();
  await visible(visibleText(page, 'Impor belum tercatat'));
  assert.equal(keys.length, 1);
  await button(page, 'Kirim lagi').click();
  await button(page, 'Lihat periode data').click();
  assert(keys[0] && keys[0] === keys[1]);
  assert.equal(keys.length, 2);
  await page.getByRole('textbox', { name: 'Tanggal mulai' }).fill('2026-10-20');
  await page.getByRole('textbox', { name: 'Tanggal selesai' }).fill('2026-10-20');
  await button(page, 'Terapkan').click();
  const importedPeriod = visibleText(page, /Periode aktif: 20 Oktober 2026 · Asia\/Jakarta/);
  await visible(importedPeriod);
  await visible(visibleText(page, '0,330 kWh'));
  await offline(page, true);
  await visible(offlineSnapshot(page));
  const firstFetch = await fetchStamp(page).innerText();
  await visible(visibleText(page, 'Data historis · Impor CSV'));
  await offline(page, false);
  await coldWithoutApi(page);
  await visible(offlineSnapshot(page));
  await visible(importedPeriod);
  await visible(visibleText(page, '0,330 kWh'));
  await visible(visibleText(page, 'Data historis · Impor CSV'));
  assert.equal(await fetchStamp(page).innerText(), firstFetch);
  assert(!/koneksi.*putus|sumber.*terputus/i.test(await page.locator('body').innerText()));
}

async function checkPartial(page) {
  await visible(visibleText(page, '14,000 kWh'));
  assert.match(await page.locator('body').innerText(), /belum tersedia/i);
  assert(!/Rp\s*\d/.test(await page.locator('body').innerText()));
  await page.getByRole('tab', { name: 'Saran', exact: true }).click();
  await visible(visibleText(page, /Belum cukup periode pembanding/i));
}

async function checkZero(page) {
  await visible(visibleText(page, '0,000 kWh'));
  const body = await page.locator('body').innerText();
  assert.match(body, /100%/);
  assert(!/Rp\s*\d/.test(body));
}

async function checkConflict(page, workspace) {
  const result = await fromApi(page, workspace, '/sites/' + workspace.siteId + '/summary' + week);
  assert.equal(result.energy_kwh, null);
  assert.equal(result.scope.valid, false);
  assert.equal(result.assets.find((item) => item.name === 'Meter utama').energy_kwh, '70.000');
  await button(page, '7 hari lengkap terakhir').click();
  await visible(visibleText(page, /Total gabungan belum dapat dihitung/i));
  await page.getByRole('tab', { name: 'Perangkat', exact: true }).click();
  await visible(page.getByRole('link', { name: /Meter utama.*70,000 kWh/i }).first());
}

const cases = [
  ['stale and cached time', 'h-stale-offline', checkStale],
  ['cold draft and explicit online save', 'h-base', checkDraft],
  ['owner isolation with old data still present', 'h-base', checkOwner],
  ['historical CSV, unsent actions, same-key recovery and exact cold period', 'empty', checkHistorical],
  ['learning and partial coverage', 'h-learning-partial', checkPartial],
  ['measured zero', 'h-zero', checkZero],
  ['overlapping weekly scope', 'h-scope', checkConflict],
];
const browser = await chromium.launch({ channel: 'chrome', headless: true });
try {
  console.log('Chrome ' + browser.version());
  for (const [label, scenario, check] of cases) {
    const { page, workspace } = await openFixture(browser, scenario);
    try {
      await check(page, workspace);
      console.log('PASS ' + label);
    } catch (error) {
      throw new Error('Failed ' + label, { cause: error });
    } finally {
      await page.close();
    }
  }
} finally {
  await browser.close();
}
