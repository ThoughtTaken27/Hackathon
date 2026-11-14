"""Probe 4+5: live path latency and the "nothing saved" check.

Browser mic -> AudioWorklet -> 16 kHz Int16 PCM over a WebSocket -> FastAPI -> in-memory ring
buffer -> CED-tiny embedding + a throwaway logistic head (fit on the probe clips) -> label back.
Audio exists only in a numpy array in RAM; nothing is written. Run: python probe_live_server.py HOP_S WINDOW_S
"""
import json, sys, time
from pathlib import Path
import numpy as np, torch, uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[4]
HOP_S = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
WIN_S = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
SR = 16000
CLASSES = ["absence", "cooking", "dishwashing", "eating", "other", "social_activity",
           "vacuum_cleaner", "watching_tv", "working"]

from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
FE = AutoFeatureExtractor.from_pretrained("mispeech/ced-tiny", trust_remote_code=True)
M = AutoModelForAudioClassification.from_pretrained("mispeech/ced-tiny", trust_remote_code=True).eval()
z = np.load(ROOT / "data/raw/sins/probe_dev/emb_ced-tiny.npz")
lab = json.loads((ROOT / "data/raw/sins/probe_dev/labels.json").read_text())
y = np.array([CLASSES.index(x["label"]) for x in lab])
SC = StandardScaler().fit(z["emb"])
HEAD = LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced").fit(SC.transform(z["emb"]), y)

PAGE = """<!doctype html><meta charset=utf-8><title>probe</title>
<button id=go>start</button><div id=lab style="font:48px system-ui">-</div>
<script>
window.__events = [];
const W = `class P extends AudioWorkletProcessor{process(i){if(i[0][0])this.port.postMessage(i[0][0]);return true}}
registerProcessor('p',P)`;
go.onclick = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:false,noiseSuppression:false,autoGainControl:false}});
  const ctx = new AudioContext({sampleRate:16000});
  await ctx.audioWorklet.addModule(URL.createObjectURL(new Blob([W],{type:'text/javascript'})));
  const src = ctx.createMediaStreamSource(stream), node = new AudioWorkletNode(ctx,'p');
  const ws = new WebSocket(`ws://${location.host}/ws`); ws.binaryType='arraybuffer';
  let buf = [], t0 = null;
  node.port.onmessage = e => { if (t0 === null) { t0 = performance.now(); window.__t0 = t0; }
    buf.push(...e.data); if (buf.length >= 1600) { const a = new Int16Array(buf.length);
      for (let i=0;i<buf.length;i++) a[i] = Math.max(-1,Math.min(1,buf[i]))*32767;
      if (ws.readyState===1) ws.send(a.buffer); buf = []; } };
  ws.onmessage = e => { const m = JSON.parse(e.data); lab.textContent = m.label;
    window.__events.push({t:(performance.now()-t0)/1000, ...m}); };
  src.connect(node); window.__sr = ctx.sampleRate;
};
</script>"""

app = FastAPI()


@app.get("/")
def page(): return HTMLResponse(PAGE)


def classify(x):
    """10-s float32 window -> (label, confidence, seconds spent)."""
    t0 = time.time()
    with torch.no_grad():
        inp = FE([x], sampling_rate=SR, return_tensors="pt")
        e = M.encoder(inp["input_values"]).logits.mean(1).numpy()
    p = HEAD.predict_proba(SC.transform(e))[0]
    return CLASSES[int(p.argmax())], float(p.max()), time.time() - t0


@app.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()
    ring = np.zeros(0, dtype=np.float32); since = 0; got = 0
    while True:
        b = await sock.receive_bytes()
        x = np.frombuffer(b, dtype=np.int16).astype(np.float32) / 32768
        ring = np.concatenate([ring, x])[-int(WIN_S * SR):]; since += len(x); got += len(x)
        if got >= WIN_S * SR and since >= HOP_S * SR:
            since = 0
            label, conf, dt = classify(ring)
            await sock.send_text(json.dumps({"label": label, "conf": round(conf, 2),
                                             "infer_s": round(dt, 3), "audio_s": got / SR}))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
