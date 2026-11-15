// On-device listening for the kitchen screen: microphone -> 10-second windows -> the frozen CED-tiny encoder + head
// (the same numbers as the Python app; tools/export_onnx.py proves the ONNX graph matches on 90 clips) -> a label.
// Audio stays in this tab's memory: one 10-second array, overwritten as sound comes in, dropped on pause.
// Only the label, its scores, a few sound names and the time are handed to the caller.
import { prepare, decide } from "./head.js";
import { prepareSense, refine, levelDb, quietWindow } from "./sense.js";

export const SR = 16000, WIN_S = 10, HOP_S = 10;
let ortReady = null, model = null;

function loadScript(src) {
  return new Promise((ok, bad) => { const s = document.createElement("script"); s.src = src; s.onload = ok; s.onerror = () => bad(new Error("script")); document.head.append(s); });
}

/** Download and start the model once. onProgress(fraction 0..1). Cached by the browser after the first time. */
export async function loadModel(onProgress = () => {}) {
  if (model) return model;
  if (!ortReady) ortReady = loadScript("/vendor/ort/ort.wasm.min.js");
  await ortReady;
  const ort = window.ort;
  ort.env.wasm.wasmPaths = "/vendor/ort/";
  ort.env.wasm.numThreads = 1;
  const [head, ev, kinds, enrolCfg] = await Promise.all(["/model/head.json", "/model/evidence.json", "/model/kinds.json", "/model/enrol.json"]
    .map((u) => fetch(u).then((r) => { if (!r.ok) throw new Error("model download failed"); return r.json(); })));
  const front = await ort.InferenceSession.create(new Uint8Array(await (await fetch("/model/logmel.onnx")).arrayBuffer()), { executionProviders: ["wasm"] });
  const res = await fetch("/model/ced-tiny.onnx");
  if (!res.ok) throw new Error("model download failed");
  const total = +res.headers.get("content-length") || 22.1e6;
  const reader = res.body.getReader();
  const parts = []; let got = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    parts.push(value); got += value.length; onProgress(Math.min(0.97, got / total));
  }
  const buf = new Uint8Array(got); let o = 0;
  for (const p of parts) { buf.set(p, o); o += p.length; }
  const session = await ort.InferenceSession.create(buf, { executionProviders: ["wasm"], graphOptimizationLevel: "all" });
  onProgress(1);
  model = { ort, front, session, head: prepare(head, ev), sense: prepareSense(kinds, enrolCfg) };
  return model;
}

/** The raw frozen-head result for a window (what tools/export_onnx.py and parity-web.mjs compare with Python). */
export async function classifyRaw(wave) {
  const m = model;
  const f = await m.front.run({ wave: new m.ort.Tensor("float32", wave, [1, wave.length]) });
  const out = await m.session.run({ feats: f.feats });
  return { emb: out.emb.data, as: out.audioset.data, r: decide(m.head, out.emb.data, out.audioset.data) };
}

/**
 * float32 [160000] at 16 kHz -> { label, conf, probs, novel, hold, why, kinds, sounds, db, ms, emb }.
 * ctx = { enrolment (this kitchen's setup record or null), kindsOff (sound types the parent switched off) }.
 * emb and db stay on this device (setup uses them); kitchen.js sends only the listed label fields.
 */
export async function classify(wave, ctx = {}) {
  const m = model, t0 = performance.now();
  const db = levelDb(wave);
  const floor = ctx.enrolment && Number.isFinite(ctx.enrolment.floor) ? ctx.enrolment.floor : m.sense.quiet_floor_dbfs;
  if (!(db >= floor)) return { ...quietWindow(db), db, emb: null, ms: Math.round(performance.now() - t0) };
  const { emb, as, r } = await classifyRaw(wave);
  return { ...refine(m.sense, { head: m.head.head, ...ctx }, emb, as, r), db, emb, ms: Math.round(performance.now() - t0) };
}

/** Decode any audio file to 16 kHz mono, first 10 s (zero-padded), for "Try your own sound". */
export async function decodeFile(file) {
  const raw = await file.arrayBuffer();
  const ctx = new OfflineAudioContext(1, SR * WIN_S, SR);
  const buf = await ctx.decodeAudioData(raw);
  const src = ctx.createBufferSource(); src.buffer = buf; src.connect(ctx.destination); src.start();
  const out = await ctx.startRendering();
  return { wave: Float32Array.from(out.getChannelData(0)), seconds: Math.min(buf.duration, WIN_S) };
}

/**
 * Start the microphone. onWindow({ start, end, ...classify() }) every HOP_S seconds once 10 s are buffered.
 * clockNow() gives the shared clock (server-corrected unix seconds). Returns { stop(), level() }.
 */
export async function startMic({ onWindow, onLevel = () => {}, onEnded = () => {}, clockNow, context = () => ({}) }) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 } });
  // the microphone can vanish while listening (unplugged, permission revoked in settings): tell the caller (plan E4)
  for (const tr of stream.getAudioTracks()) tr.addEventListener("ended", () => { if (!stopped) onEnded(); });
  let ctx;
  try { ctx = new AudioContext({ sampleRate: SR }); } catch { ctx = new AudioContext(); }
  await ctx.audioWorklet.addModule("/js/worklet.js");
  const src = ctx.createMediaStreamSource(stream);
  const tap = new AudioWorkletNode(ctx, "kettle-tap");
  const mute = ctx.createGain(); mute.gain.value = 0;
  src.connect(tap); tap.connect(mute); mute.connect(ctx.destination);
  const ratio = ctx.sampleRate / SR;
  const ring = new Float32Array(SR * WIN_S);
  let filled = 0, sinceHop = 0, prevEnd = null, busy = false, stopped = false, frac = 0, hop = HOP_S, slow = 0;
  tap.port.onmessage = async ({ data }) => {
    if (stopped) return;
    // resample to 16 kHz if the browser kept its own rate (simple linear: enough for a 10-s activity label)
    let x = data;
    if (ratio !== 1) {
      const n = Math.floor((data.length - frac) / ratio);
      const y = new Float32Array(n);
      for (let i = 0; i < n; i++) { const p = frac + i * ratio, a = Math.floor(p), t = p - a; y[i] = (data[a] || 0) * (1 - t) + (data[a + 1] || 0) * t; }
      frac = frac + n * ratio - data.length;
      x = y;
    }
    let peak = 0; for (let i = 0; i < x.length; i++) peak = Math.max(peak, Math.abs(x[i]));
    onLevel(peak);
    ring.copyWithin(0, x.length); ring.set(x, ring.length - x.length);
    filled = Math.min(ring.length, filled + x.length); sinceHop += x.length;
    if (filled < ring.length || sinceHop < hop * SR || busy) return;
    sinceHop = 0; busy = true;
    try {
      const r = await classify(ring.slice(), context());
      slow = r.ms > 0.8 * hop * 1000 ? slow + 1 : 0;           // a device too slow for this pace (plan E10)
      const end = clockNow();
      const start = prevEnd && end - prevEnd < 3 * Math.max(hop, HOP_S) ? Math.max(prevEnd, end - WIN_S) : end - WIN_S;
      prevEnd = end;
      if (!stopped) onWindow({ start, end, ...r, slow: slow >= 3 });
    } finally { busy = false; }
  };
  return {
    sampleRate: ctx.sampleRate,
    /** seconds between windows: 10 normally, 2 while teaching Kettle this kitchen */
    setHop(s) { hop = s; sinceHop = Math.min(sinceHop, s * SR); },
    stop() { stopped = true; ring.fill(0); tap.port.onmessage = null; stream.getTracks().forEach((t) => t.stop()); ctx.close(); },
  };
}
