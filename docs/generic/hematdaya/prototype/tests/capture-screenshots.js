const { chromium } = require('playwright');
// Captures the proposal screenshots (390x844 viewport @2x, top 480 px without the tab bar) from standalone.html.
// Serve the prototype first (see ../README.md), then: node tests/capture-screenshots.js <out-dir>
const OUT=process.argv[2];
(async()=>{
  const b=await chromium.launch(); const p=await b.newPage({viewport:{width:390,height:844},deviceScaleFactor:2});
  const errs=[]; p.on('pageerror',e=>errs.push(e.message));
  await p.goto('http://127.0.0.1:8811/standalone.html'); await p.addScriptTag({path:require('path').join(__dirname, 'browser-helper.js')});
  await p.waitForTimeout(400);
  const W=ms=>p.waitForTimeout(ms);
  const scrollTo=async(text,offset=0)=>{await p.evaluate(([t,o])=>{const app=document.querySelector('.hd-app');
     const el=[...app.querySelectorAll('h1,h2,h3,p,span,div,button,a,legend,summary')].find(e=>e.innerText&&e.innerText.trim().startsWith(t)&&e.children.length<4);
     if(!el) throw new Error('no '+t); app.scrollTop=0; const r=el.getBoundingClientRect(); app.scrollTop=r.top-app.getBoundingClientRect().top-o;},[text,offset]); await W(250);};
  const shot=async(n)=>{await p.evaluate(()=>document.activeElement&&document.activeElement.blur()); await W(150); await p.screenshot({path:`${OUT}/${n}.png`, clip:{x:0,y:0,width:390,height:480}});};
  await p.evaluate(()=>__t.demo('industry')); await W(800);
  await p.evaluate(()=>__t.scenario('Industri · kompresor di luar jadwal')); await W(900);
  await scrollTo('Cakupan pengukuran: 4',16); await shot('01-beranda');
  await scrollTo('Kontributor terbesar',16); await shot('02-kontributor-pengamatan');
  await p.evaluate(()=>__t.btn('Lihat dasar saran')); await W(900);
  await shot('03-dasar-saran');
  // import flow
  await p.evaluate(()=>__t.btn('Perangkat')); await W(500);
  await p.evaluate(()=>__t.btn('Impor data')); await W(500);
  await p.evaluate(()=>{__t.btn('Contoh berkas yang dapat disalin');}); await W(200);
  await p.evaluate(()=>{const bs=[...document.querySelectorAll('pre')]; const i=bs.findIndex(x=>/tidak valid \(diblokir\)/.test(x.getAttribute('aria-label'))===false && /2 dari 10/.test(x.getAttribute('aria-label'))); __t.btn('Gunakan contoh ini', i);}); await W(200);
  await p.evaluate(()=>__t.btn('Periksa berkas')); await W(700);
  await p.evaluate(()=>{ try{__t.pick('Konfirmasi zona waktu','Waktu dalam berkas');}catch(e){} __t.pick('Apakah beban','Ya'); }); await W(200);
  await p.evaluate(()=>{ document.querySelectorAll('select').forEach(s=>{ if(!s.value){ Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set.call(s,'new'); s.dispatchEvent(new Event('change',{bubbles:true}));}}); }); await W(200);
  await p.evaluate(()=>__t.btn('Lihat pratinjau')); await W(700);
  await p.evaluate(()=>{document.querySelector('.hd-app').scrollTop=0}); await shot('04-impor-pratinjau');
  if(errs.length) throw new Error(errs.join('\n')); await b.close();
})();
