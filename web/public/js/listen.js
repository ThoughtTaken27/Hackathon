// On-device listening for the kitchen screen: microphone -> 10-second windows -> the frozen CED-tiny encoder + head
// (the same numbers as the Python app; tools/export_onnx.py proves the ONNX graph matches on 90 clips) -> a label.
// Audio stays in this tab's memory: one 10-second array, overwritten as sound comes in, dropped on pause.
// Only the label, its scores, a few sound names and the time are handed to the caller.
import { prepare, decide } from "./head.js";
import { prepareSense, refine, levelDb } from "./sense.js";

export const SR = 16000, WIN_S = 10, HOP_S = 10;
let ortReady = null, model = null;
/** The frozen head (head.json) once loaded: setup standardises embeddings with its mean and std. */
export function modelHead() { return model ? model.head.head : null; }

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
  const [head, ev, wit, kinds, enrolCfg] = await Promise.all(["head", "evidence", "witness", "kinds", "enrol"]
    .map((n) => fetch(`/model/${n}.json`).then((r) => { if (!r.ok) throw new Error("model download failed"); return r.json(); })));
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
  const sense = prepareSense(kinds, enrolCfg);
  // AudioSet classes 0 Speech, 4 Conversation, 5 Narration/monologue, 70 Hubbub: used on this device only, never sent,
  // so the voices rule keeps working if voice names leave the shown-sounds allow-list (handover v3.2, 3.5).
  sense.speech = [0, 4, 5, 70];
  model = { ort, front, session, head: prepare(head, ev, wit), sense };
  return model;
}

/** float32 [160000] at 16 kHz -> { label, conf, probs, novel, w, sounds, ms } */
export async function classify(wave, ctx = null) {
  const m = model, t0 = performance.now();
  const f = await m.front.run({ wave: new m.ort.Tensor("float32", wave, [1, wave.length]) });
  const out = await m.session.run({ feats: f.feats });
  const r = decide(m.head, out.emb.data, out.audioset.data);
  if (!ctx) return { ...r, ms: Math.round(performance.now() - t0) };          // the raw frozen head (parity tests)
  // on the kitchen device: this kitchen's setup windows and the named sound types (sense.js). emb and db never leave it.
  const db = levelDb(wave);
  return { ...refine(m.sense, { head: m.head.head, ...ctx }, out.emb.data, out.audioset.data, r, db), emb: out.emb.data, db,
    ms: Math.round(performance.now() - t0) };
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
// Local testing only: on localhost, ?qamic=cooking plays web/public/_qa/cooking.flac (git-ignored) in place of the microphone,
// so every screen can be checked without a real mic. Never active on any other host.
function qaClip() {
  if (!/^(localhost|127\.0\.0\.1)$/.test(location.hostname)) return null;
  const q = new URLSearchParams(location.search).get("qamic");
  if (q && /^[a-z]+$/.test(q)) sessionStorage.setItem("kettle.qamic", q);
  return sessionStorage.getItem("kettle.qamic");
}
qaClip();   // read ?qamic now: kitchen.js strips the query from the address when it reads the pairing key
async function micStream() {
  const qa = qaClip();
  if (!qa) return navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 } });
  const ctx = new AudioContext({ sampleRate: SR });
  const src = ctx.createBufferSource();
  src.buffer = await ctx.decodeAudioData(await (await fetch(`/_qa/${qa}.flac`)).arrayBuffer());
  src.loop = true;
  const dest = ctx.createMediaStreamDestination();
  src.connect(dest); src.start(); await ctx.resume();
  dest.stream.getTracks().forEach((tr) => tr.addEventListener("ended", () => ctx.close()));
  const stop = MediaStreamTrack.prototype.stop;
  dest.stream.getTracks().forEach((tr) => { tr.stop = function () { stop.call(this); ctx.close().catch(() => {}); }; });
  return dest.stream;
}

export async function startMic({ onWindow, onLevel = () => {}, clockNow, context = () => ({}) }) {
  const stream = await micStream();
  let ctx;
  try { ctx = new AudioContext({ sampleRate: SR }); } catch { ctx = new AudioContext(); }
  await ctx.audioWorklet.addModule("/js/worklet.js");
  const src = ctx.createMediaStreamSource(stream);
  const tap = new AudioWorkletNode(ctx, "kettle-tap");
  const mute = ctx.createGain(); mute.gain.value = 0;
  src.connect(tap); tap.connect(mute); mute.connect(ctx.destination);
  // Some browsers suspend audio in a background tab or after the laptop wakes; ask for it back so listening carries on.
  ctx.onstatechange = () => { if (!stopped && ctx.state !== "running" && ctx.state !== "closed") ctx.resume().catch(() => {}); };
  if (ctx.state !== "running") ctx.resume().catch(() => {});
  const ratio = ctx.sampleRate / SR;
  const ring = new Float32Array(SR * WIN_S);
  let filled = 0, sinceHop = 0, prevEnd = null, busy = false, stopped = false, frac = 0, hop = HOP_S;
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
      const snap = ring.slice();
      let winPeak = 0; for (let i = 0; i < snap.length; i += 4) { const a = Math.abs(snap[i]); if (a > winPeak) winPeak = a; }
      const r = { ...(await classify(snap, context())), peak: winPeak };
      const end = clockNow();
      const start = prevEnd && end - prevEnd < 3 * HOP_S ? Math.max(prevEnd, end - WIN_S) : end - WIN_S;
      prevEnd = end;
      if (!stopped) onWindow({ start, end, ...r });
    } finally { busy = false; }
  };
  return {
    sampleRate: ctx.sampleRate,
    /** seconds between windows: 10 normally, 2 while teaching Kettle this kitchen */
    setHop(sec) { hop = sec; sinceHop = Math.min(sinceHop, sec * SR); },
    stop() { stopped = true; ring.fill(0); tap.port.onmessage = null; stream.getTracks().forEach((t) => t.stop()); ctx.close(); },
  };
}
