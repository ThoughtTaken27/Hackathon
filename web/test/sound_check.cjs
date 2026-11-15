// Sound check on the real kitchen page: each WAV in <dir> plays into Chromium's fake microphone (getUserMedia -> worklet -> ONNX -> head),
// and every window the kitchen sent to the sync server is read back. Run with node web/dev.mjs up:
//   NODE_PATH=$(npm root -g) node web/test/sound_check.cjs <dir of .wav> <out.json> [windows=3] [parallel=4]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const BASE = 'http://localhost:8787';
const [dir, out, NW = '3', PAR = '4'] = process.argv.slice(2);
const files = fs.readdirSync(dir).filter((f) => f.endsWith('.wav')).sort();
const api = async (p, opt = {}) => { const r = await fetch(BASE + p, { method: opt.method || 'GET', headers: { 'content-type': 'application/json', ...(opt.key ? { authorization: 'Bearer ' + opt.key } : {}) }, body: opt.body ? JSON.stringify(opt.body) : undefined }); return r.json(); };
async function one(f) {
  const h = await api('/api/households', { method: 'POST', body: { parent: 'Mom', caregiver: 'Asha', tz: 'America/Chicago', as: 'family' } });
  await api(`/api/h/${h.id}/action`, { method: 'POST', key: h.kitchenKey, body: { type: 'consent' } });
  const br = await chromium.launch({ args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', `--use-file-for-fake-audio-capture=${path.resolve(dir, f)}`, '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await br.newContext({ permissions: ['microphone'] });
  await ctx.addInitScript((id) => localStorage.setItem(`kettle.setup.${id}`, '1'), h.id);
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', (e) => errs.push(e.message)); p.on('dialog', (d) => d.dismiss());
  await p.goto(`${BASE}/kitchen#k=${h.id}.${h.kitchenKey}`);
  const t0 = Date.now(); let ev = [], st = null;
  while (Date.now() - t0 < 90000) {
    await p.waitForTimeout(2000);
    const r = await api(`/api/h/${h.id}/state?since=0`, { key: h.familyKey }); ev = r.events || []; st = r.state;
    if (ev.length >= +NW || (st && st.mic === 'blocked' && Date.now() - t0 > 45000)) break;
  }
  const chip = await p.locator('.chip .txt').first().innerText().catch(() => '');
  const head = await p.locator('#head').innerText().catch(() => '');
  await br.close();
  await fetch(`${BASE}/api/h/${h.id}`, { method: 'DELETE', headers: { authorization: 'Bearer ' + h.familyKey } });
  return { file: f, windows: ev.map((e) => ({ label: e.label, conf: e.conf, novel: e.novel, kinds: e.kinds, sounds: (e.sounds || []).map((s) => s.name) })), chip, head, mic: st && st.mic, errors: errs };
}
(async () => {
  const res = []; let i = 0;
  await Promise.all(Array.from({ length: +PAR }, async () => { while (i < files.length) { const f = files[i++]; const r = await one(f).catch((e) => ({ file: f, fail: String(e) })); res.push(r); console.log(f, '->', r.fail || r.windows.map((w) => `${w.label}${w.novel ? '*' : ''}:${w.conf}${w.kinds && w.kinds.length ? '[' + w.kinds + ']' : ''}`).join(' '), '| chip:', r.chip, r.mic === 'blocked' ? '| MIC BLOCKED' : '', r.errors && r.errors.length ? r.errors : ''); } }));
  fs.writeFileSync(out, JSON.stringify(res.sort((a, b) => a.file.localeCompare(b.file)), null, 1));
})();
