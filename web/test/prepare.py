"""Inputs for the two heavier web checks, written to one folder (default web/.data/test):

  fake-kitchen.wav   30 s of sample-day kitchen sound, played into Chromium's fake microphone by e2e.py
  clips.f32          the 90 sample clips as raw float32 (10 s each), for parity-web.mjs
  expect.json        the Python app's label, novelty flag, confidence and top sound for each clip

    python web/test/prepare.py [out_dir]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from export_onnx import clip  # noqa: E402
from kettle import encoders, live, model  # noqa: E402


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "web" / ".data" / "test")
    out.mkdir(parents=True, exist_ok=True)
    sc = json.loads((ROOT / "demo_cache" / "scenarios.json").read_text())["usual"]
    x = np.concatenate([sf.read(ROOT / "demo_cache" / "clips" / c, dtype="float32")[0][:160000] for c in sc["segments"][1]["clips"]])
    sf.write(out / "fake-kitchen.wav", x, 16000, subtype="PCM_16")

    enc = encoders.load()
    head = model.load(ROOT / "models" / "head.json")
    clips = sorted((ROOT / "demo_cache" / "clips").glob("*.flac"))
    W = np.stack([clip(p) for p in clips]).astype("float32")
    W.tofile(out / "clips.f32")
    exp = [live.classify(enc, head, w[None])[0] for w in W]
    (out / "expect.json").write_text(json.dumps([{"label": e["label"], "novel": e["novel"], "conf": e["conf"], "top": e["sounds"][0]["name"]} for e in exp]))
    print(f"wrote {out}/fake-kitchen.wav, clips.f32 ({len(W)} clips), expect.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
