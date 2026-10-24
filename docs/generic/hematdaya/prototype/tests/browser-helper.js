// Test driver injected into standalone.html / the exported page during browser walkthroughs.
// Clicks real DOM controls (element.click()) and sets inputs through React-compatible setters.
window.__t = {
  sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
  ctl(text, nth) { return [...document.querySelectorAll('button, a, summary')].filter((e) => (e.innerText || e.textContent).trim().replace(/\s+/g, ' ') === text)[nth || 0]; },
  btn(text, nth) { const el = this.ctl(text, nth); if (!el) throw new Error('no control: ' + text); el.click(); return true; },
  pick(legend, label) {
    const fs = [...document.querySelectorAll('fieldset')].find((f) => f.querySelector('legend') && f.querySelector('legend').innerText.trim().startsWith(legend));
    if (!fs) throw new Error('no fieldset ' + legend);
    const lab = [...fs.querySelectorAll('label')].find((l) => l.innerText.trim().startsWith(label));
    if (!lab) throw new Error('no option ' + label + ' in ' + legend); lab.click();
  },
  select(legend, value) {
    const s = [...document.querySelectorAll('select')].find((x) => x.closest('div').innerText.trim().startsWith(legend));
    if (!s) throw new Error('no select ' + legend);
    Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(s, value); s.dispatchEvent(new Event('change', { bubbles: true }));
  },
  field(label) { const l = [...document.querySelectorAll('label')].find((x) => x.innerText.trim().startsWith(label)); if (!l) throw new Error('no field ' + label); return document.getElementById(l.htmlFor); },
  type(label, v) {
    const el = typeof label === 'string' ? this.field(label) : label;
    const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, v); el.dispatchEvent(new Event('input', { bubbles: true }));
  },
  has(text) { return document.body.innerText.includes(text); },
  h1() { const h = document.querySelector('h1'); return h && h.innerText; },
  focus() { const a = document.activeElement; return a && (a.tagName + ':' + (a.innerText || a.value || '').slice(0, 60).replace(/\s+/g, ' ')); },
  text(max) { return document.querySelector('.hd-app').innerText.slice(0, max || 4000); },
  notices() { return [...document.querySelectorAll('.hd-notice, .hd-progress')].map((e) => e.innerText.replace(/\s+/g, ' ').trim()).filter(Boolean); },
  async demo(kind) { this.btn('Coba demo'); await this.sleep(80); if (kind === 'industry') this.pick('Data simulasi', 'Industri'); await this.sleep(30); this.btn('Buka demo'); await this.sleep(700); },
  async scenario(name) { this.btn('Tentang demo'); await this.sleep(80); this.pick('Pilih skenario', name); await this.sleep(40); this.btn('Muat skenario'); await this.sleep(150); }
};
