import assert from 'node:assert/strict';
import { randomBytes } from 'node:crypto';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.HEMATDAYA_PLAYWRIGHT_MODULE ?? 'playwright');
const api = new URL(process.env.HEMATDAYA_API_URL ?? 'http://localhost:58029').origin;
const web = new URL(process.env.HEMATDAYA_WEB_URL ?? 'http://localhost:8129').origin;
const workspaceKey = 'hematdaya.workspace.v1';
const period = { start_date: '2026-10-25', end_date: '2026-10-25' };
const dateQuery = new URLSearchParams(period);
const button = (page, name) => page.getByRole('button', { name, exact: true });
const radio = (page, name) => page.getByRole('radio', { name, exact: typeof name === 'string' });
const text = (page, name) => page.getByText(name, { exact: typeof name === 'string' }).filter({ visible: true }).first();
const visible = (locator) => locator.waitFor({ state: 'visible' });
const scopePath = (owner) => `/api/v1/sites/${owner.siteId}/aggregation-selection`;
const summaryPath = (owner) => `/api/v1/sites/${owner.siteId}/summary?${dateQuery}`;
const pair = (result) => [result.selection_revision, result.binding_revision];

async function seed(page) {
  const response = await page.request.post(api + '/api/v1/demo/sessions', {
    data: { scenario_id: 'h-scope' },
    headers: {
      'Idempotency-Key': randomBytes(16).toString('base64url'),
      'X-Demo-Replay-Proof': randomBytes(32).toString('base64url'),
    },
  });
  assert.equal(response.status(), 201, 'fixture creation');
  const body = await response.json();
  return {
    token: body.token, siteId: body.site_id, scenarioId: body.scenario_id,
    expiresAt: body.expires_at, initialPeriod: body.initial_period,
  };
}

async function apiRead(page, owner, path, method = 'GET', data, status = 200) {
  const response = await page.request.fetch(api + path, {
    method, data, headers: { Authorization: 'Bearer ' + owner.token },
  });
  assert.equal(response.status(), status, method + ' ' + path);
  return response.json();
}

async function fixture(browser) {
  const page = await browser.newPage({ viewport: { width: 320, height: 780 } });
  page.setDefaultTimeout(25_000);
  const owner = await seed(page);
  await page.goto(web + '/beranda', { timeout: 120_000 });
  await page.evaluate(({ key, owner }) => sessionStorage.setItem(key, JSON.stringify(owner)), { key: workspaceKey, owner });
  const requests = [];
  page.on('request', (request) => {
    const url = new URL(request.url());
    if (url.origin !== api || request.method() === 'OPTIONS') return;
    const path = url.pathname.replace(owner.siteId, ':site');
    const entry = { method: request.method(), path };
    if (path.endsWith('/aggregation-selection') && entry.method === 'PUT') {
      const body = request.postDataJSON();
      Object.assign(entry, { expected: [body.expected_selection_revision, body.expected_binding_revision], period: body.resolved_period });
    }
    requests.push(entry);
  });
  await page.reload();
  await visible(button(page, 'Atur cakupan dan sumber'));
  return { page, owner, requests };
}

const writes = (requests) => requests.filter(({ method, path }) => method === 'PUT' && path.endsWith('/aggregation-selection'));

async function open(page, opener = 'Atur cakupan dan sumber', keyboard = true) {
  const control = button(page, opener);
  await visible(control);
  if (keyboard) {
    await control.focus();
    await page.keyboard.press('Enter');
  } else {
    await control.click();
  }
  const heading = page.getByRole('heading', { name: 'Cakupan dan sumber', exact: true });
  await visible(heading);
  assert(await heading.evaluate((element) => document.activeElement === element));
  return control;
}

async function preview(page) {
  await button(page, 'Pratinjau cakupan').click();
  await visible(text(page, 'Periode yang ditinjau'));
}

async function meterReview(page) {
  await radio(page, 'Meter utama · 10,000 kWh').click();
  await preview(page);
}

async function happy(browser) {
  const { page, owner, requests } = await fixture(browser);
  try {
    const before = await apiRead(page, owner, scopePath(owner));
    const opener = await open(page);
    const meter = radio(page, 'Meter utama · 10,000 kWh');
    await visible(meter);
    await meter.focus();
    await page.keyboard.press('Space');
    assert.equal(await meter.getAttribute('aria-checked'), 'true');
    await preview(page);
    assert.deepEqual(pair(await apiRead(page, owner, scopePath(owner))), pair(before));
    assert.equal(writes(requests).length, 0);
    await button(page, 'Batal').click();
    await visible(opener);
    await page.waitForFunction(() => document.activeElement?.textContent === 'Atur cakupan dan sumber');

    await open(page);
    await radio(page, /^Perangkat dalam Meter utama/).click();
    const candidate = radio(page, /^Colokan simulasi Kulkas/);
    await visible(candidate);
    await candidate.click();
    await visible(text(page, /Berlaku mulai 25 Oktober 2026 00[.:]00/));
    await visible(radio(page, 'Perangkat dalam Meter utama · 1,600 kWh'));
    await preview(page);
    assert.deepEqual(pair(await apiRead(page, owner, scopePath(owner))), pair(before));
    const enlarged = await page.evaluate(() => {
      for (const node of document.querySelectorAll('[role="main"] *, div, span')) {
        if ([...node.childNodes].some((child) => child.nodeType === Node.TEXT_NODE && child.textContent?.trim())) {
          node.style.setProperty('font-size', parseFloat(getComputedStyle(node).fontSize) * 1.3 + 'px', 'important');
        }
      }
      return { viewport: document.documentElement.clientWidth, content: document.documentElement.scrollWidth };
    });
    assert.deepEqual(enlarged, { viewport: 320, content: 320 });
    await button(page, 'Konfirmasi cakupan').click();
    await visible(text(page, 'Cakupan tersimpan di layanan'));
    const confirmed = await apiRead(page, owner, summaryPath(owner));
    assert.equal(confirmed.energy_kwh, '1.600');
    assert.deepEqual(pair(confirmed), [1, 2]);
    assert.equal(writes(requests).length, 1);
    assert.deepEqual(writes(requests)[0].expected, pair(before));
    assert.deepEqual(writes(requests)[0].period, { ...period, timezone: 'Asia/Jakarta' });

    for (const name of ['Kulkas', 'Router', 'TV', 'Meter utama', 'Pompa Air']) {
      await page.getByRole('checkbox', { name, exact: true }).click();
    }
    await preview(page);
    const disjoint = page.getByRole('checkbox', { name: /^Saya memastikan .* mengukur beban terpisah$/ });
    await visible(disjoint);
    await visible(text(page, 'Pompa Air · 0,300 kWh'));
    await disjoint.click();
    assert.equal(await disjoint.getAttribute('aria-checked'), 'true');
    await preview(page);
    await visible(text(page, '10,300 kWh'));
    await button(page, 'Konfirmasi cakupan').click();
    await visible(text(page, 'Cakupan tersimpan di layanan'));
    const separated = await apiRead(page, owner, summaryPath(owner));
    assert.equal(separated.energy_kwh, '10.300');
    assert.deepEqual(pair(separated), [2, 3]);
    assert.equal(writes(requests).length, 2);
    console.log(JSON.stringify({ case: 'keyboard, cancel, children and separate loads', children: { pair: pair(confirmed), total: confirmed.energy_kwh },
      separated: { pair: pair(separated), total: separated.energy_kwh }, requests: requests.filter((row) => row.path.includes('aggregation-selection')) }));
  } finally {
    await page.close();
  }
}

async function refusalAndStale(browser) {
  const { page, owner, requests } = await fixture(browser);
  try {
    const path = scopePath(owner);
    const before = await apiRead(page, owner, path);
    await page.getByRole('tab', { name: 'Perangkat' }).click();
    await visible(page.getByRole('heading', { name: 'Perangkat', exact: true }));
    await open(page, 'Selesaikan cakupan', false);
    await meterReview(page);
    const reject = (route) => route.request().method() !== 'PUT' ? route.continue() : route.fulfill({
      status: 409, headers: { 'Access-Control-Allow-Origin': web },
      json: { error: { code: 'SCOPE_CONFLICT', message: 'Perubahan ditolak. Periksa kembali cakupan.',
        request_id: 'scope-browser-refused', recovery: { retryable: false } } },
    });
    await page.route(api + path, reject);
    await button(page, 'Konfirmasi cakupan').click();
    await visible(text(page, 'Perubahan ditolak layanan'));
    await visible(text(page, 'ID referensi: scope-browser-refused.'));
    assert.deepEqual(pair(await apiRead(page, owner, path)), pair(before));
    await page.unroute(api + path, reject);

    await preview(page);
    const previous = await apiRead(page, owner, summaryPath(owner));
    const pump = previous.scope.included.find((row) => row.name === 'Pompa Air').asset_id;
    const proposal = { period, selected_asset_ids: [pump], authority_actions: [], disjoint_confirmations: [] };
    const base = await apiRead(page, owner, path + '/preview', 'POST', proposal);
    await apiRead(page, owner, path, 'PUT', { ...proposal, expected_selection_revision: base.selection_revision,
      expected_binding_revision: base.binding_revision, resolved_period: { ...period, timezone: 'Asia/Jakarta' } });
    await button(page, 'Konfirmasi cakupan').click();
    await visible(text(page, 'Pratinjau perlu diperbarui'));
    const current = await apiRead(page, owner, summaryPath(owner));
    assert.equal(current.energy_kwh, '0.300');
    assert.deepEqual(pair(current), [1, 1]);
    assert.equal(writes(requests).length, 2);
    await button(page, 'Batal').click();
    await visible(page.getByRole('heading', { name: 'Perangkat', exact: true }));
    console.log(JSON.stringify({ case: 'definite refusal and real stale revision', pair: pair(current), total: current.energy_kwh, requests: writes(requests) }));
  } finally {
    await page.close();
  }
}

async function lost(browser) {
  const { page, owner, requests } = await fixture(browser);
  try {
    const path = scopePath(owner);
    await open(page);
    await meterReview(page);
    const drop = async (route) => {
      if (route.request().method() !== 'PUT') return route.continue();
      const forwarded = await route.fetch();
      assert.equal(forwarded.status(), 200);
      await route.abort('failed');
    };
    await page.route(api + path, drop);
    await button(page, 'Konfirmasi cakupan').click();
    await visible(text(page, 'Hasil penyimpanan belum diketahui'));
    assert.equal(writes(requests).length, 1);
    await page.unroute(api + path, drop);
    const current = await apiRead(page, owner, summaryPath(owner));
    assert.equal(current.energy_kwh, '10.000');

    // Reload only the app shell while offline. Keep the durable marker and older snapshot.
    const offline = (route) => route.abort('internetdisconnected');
    await page.route(api + '/**', offline);
    await page.addInitScript(() => {
      if (sessionStorage.getItem('scope-browser-offline')) {
        Object.defineProperty(navigator, 'onLine', { get: () => false, configurable: true });
      }
    });
    await page.evaluate(() => sessionStorage.setItem('scope-browser-offline', '1'));
    await page.reload();
    await visible(text(page, 'Hasil penyimpanan belum diketahui'));
    await visible(text(page, 'Ringkasan masih memakai cakupan sebelumnya'));
    await page.unroute(api + '/**', offline);
    await page.evaluate(() => {
      sessionStorage.removeItem('scope-browser-offline');
      delete navigator.onLine;
      window.dispatchEvent(new Event('online'));
    });
    await visible(text(page, 'Cakupan terkonfirmasi'));
    await visible(text(page, '10,000 kWh'));
    assert.equal(writes(requests).length, 1);

    const other = await seed(page);
    await apiRead(page, other, path, 'GET', undefined, 404);
    await page.evaluate(({ key, owner }) => sessionStorage.setItem(key, JSON.stringify(owner)), { key: workspaceKey, owner: other });
    await page.reload();
    await visible(text(page, 'Total gabungan belum dapat dihitung'));
    assert.equal(await text(page, 'Hasil penyimpanan belum diketahui').count(), 0);
    assert.equal(await text(page, 'Ringkasan masih memakai cakupan sebelumnya').count(), 0);
    console.log(JSON.stringify({ case: 'lost acknowledgment, reload, reconnect, and owner isolation', pair: pair(current), total: current.energy_kwh, requests: writes(requests) }));
  } finally {
    await page.close();
  }
}

async function retrySameBase(browser) {
  const { page, owner, requests } = await fixture(browser);
  try {
    const path = scopePath(owner);
    const baseline = await apiRead(page, owner, path);
    let forwarded = 0;
    await page.route(api + path, (route) => {
      if (route.request().method() !== 'PUT') return route.continue();
      forwarded += 1;
      return forwarded === 1 ? route.abort('failed') : route.continue();
    });
    await open(page);
    await meterReview(page);
    await button(page, 'Konfirmasi cakupan').click();
    await visible(text(page, 'Hasil penyimpanan belum diketahui'));
    await button(page, 'Periksa status simpan').click();
    await visible(text(page, 'Hasil penyimpanan belum diketahui'));
    assert.deepEqual(pair(await apiRead(page, owner, path)), pair(baseline));

    await page.reload();
    await visible(text(page, 'Hasil penyimpanan belum diketahui'));
    assert.equal(writes(requests).length, 1);
    await meterReview(page);
    const confirm = button(page, 'Konfirmasi cakupan');
    await confirm.click();
    await visible(text(page, 'Cakupan tersimpan di layanan'));
    const current = await apiRead(page, owner, summaryPath(owner));
    assert.equal(current.energy_kwh, '10.000');
    assert.deepEqual(pair(current), [1, 1]);
    assert.equal(writes(requests).length, 2);
    assert.deepEqual(writes(requests).map((entry) => entry.expected), [pair(baseline), pair(baseline)]);
    console.log(JSON.stringify({ case: 'same-base recovery with a fresh explicit confirmation', pair: pair(current),
      total: current.energy_kwh, requests: writes(requests) }));
  } finally {
    await page.close();
  }
}

const browser = await chromium.launch({ headless: true });
try {
  await happy(browser);
  await refusalAndStale(browser);
  await lost(browser);
  await retrySameBase(browser);
} finally {
  await browser.close();
}
