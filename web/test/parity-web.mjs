import * as ort from "../node_modules/onnxruntime-web/dist/ort.wasm.mjs";
import { readFileSync } from "node:fs";
import { prepare, decide } from "../public/js/head.js";
const S = process.argv[2], M = new URL("../public/model/", import.meta.url).pathname;
ort.env.wasm.numThreads = 1;
const front = await ort.InferenceSession.create(readFileSync(M + "logmel.onnx"));
const sess = await ort.InferenceSession.create(readFileSync(M + "ced-tiny.onnx"));
const m = prepare(JSON.parse(readFileSync(M + "head.json")), JSON.parse(readFileSync(M + "evidence.json")));
const exp = JSON.parse(readFileSync(S + "/expect.json"));
const all = new Float32Array(readFileSync(S + "/clips.f32").buffer.slice(0));
let same = 0, nov = 0, top = 0, ms = 0, maxd = 0;
for (let i = 0; i < exp.length; i++) {
  const w = all.slice(i * 160000, (i + 1) * 160000);
  const t0 = Date.now();
  const f = await front.run({ wave: new ort.Tensor("float32", w, [1, 160000]) });
  const o = await sess.run({ feats: f.feats });
  ms += Date.now() - t0;
  const r = decide(m, o.emb.data, o.audioset.data);
  same += r.label === exp[i].label; nov += r.novel === exp[i].novel; top += r.sounds[0].name === exp[i].top;
  maxd = Math.max(maxd, Math.abs(r.conf - exp[i].conf));
}
console.log(JSON.stringify({ clips: exp.length, same_label: same, same_novel: nov, same_top_sound: top, max_conf_diff: maxd, mean_ms: Math.round(ms / exp.length) }));
