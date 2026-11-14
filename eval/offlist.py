"""Off-list sounds: what does Kettle do with a sound that is none of its 9 activities?

~200 ESC-50 clips from 20 categories that are not household activities (dog, siren, rain, alarm clock...),
plus 20 white-noise, 20 pink-noise and 20 silent clips we generate. A good "Not sure" should catch most of
them; every confident label on these is a confident mistake. Used for the risk-coverage curve.
ESC-50: K. J. Piczak, ESC: Dataset for Environmental Sound Classification, ACM MM 2015.
https://github.com/karolpiczak/ESC-50 · CC BY-NC 3.0 · fetched to data/clips/offlist/ (git-ignored), never committed.
5-s clips are resampled to 16 kHz and repeated to 10 s (repeating avoids a fake half-silence).
Usage: python -m eval.offlist   (fetch + generate, ~2 min)
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "clips" / "offlist"
BASE = "https://raw.githubusercontent.com/karolpiczak/ESC-50/master"
CATEGORIES = ["dog", "rooster", "rain", "sea_waves", "crying_baby", "clapping", "clock_alarm", "clock_tick",
              "glass_breaking", "helicopter", "chainsaw", "siren", "car_horn", "church_bells", "airplane",
              "fireworks", "cat", "chirping_birds", "thunderstorm", "washing_machine"]
PER_CATEGORY = 10


def to_10s_16k(x: np.ndarray, sr: int) -> np.ndarray:
    from scipy.signal import resample_poly
    if x.ndim > 1:
        x = x.mean(1)
    g = np.gcd(sr, 16000)
    y = resample_poly(x, 16000 // g, sr // g).astype(np.float32)
    return np.tile(y, int(np.ceil(160000 / len(y))))[:160000]


def pink(n: int, rng) -> np.ndarray:
    """Pink (1/f) noise by shaping white noise in the frequency domain."""
    f = np.fft.rfft(rng.standard_normal(n))
    f /= np.sqrt(np.maximum(np.arange(len(f)), 1))
    y = np.fft.irfft(f, n)
    return (y / np.abs(y).max() * 0.3).astype(np.float32)


def build() -> dict:
    import requests
    OUT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(io.StringIO(requests.get(f"{BASE}/meta/esc50.csv", timeout=60).text)))
    labels = []
    for c in CATEGORIES:
        for r in [r for r in rows if r["category"] == c][:PER_CATEGORY]:
            name = f"esc50_{c}_{Path(r['filename']).stem}"
            if not (OUT / f"{name}.flac").exists():
                x, sr = sf.read(io.BytesIO(requests.get(f"{BASE}/audio/{r['filename']}", timeout=60).content), dtype="float32")
                sf.write(OUT / f"{name}.flac", to_10s_16k(x, sr), 16000, format="FLAC", subtype="PCM_16")
            labels.append({"file": name, "source": "esc50", "category": c})
    rng = np.random.default_rng(7)
    for i in range(20):
        for kind, x in (("white", (rng.standard_normal(160000) * rng.uniform(0.01, 0.3)).astype(np.float32)),
                        ("pink", pink(160000, rng)), ("silence", np.zeros(160000, np.float32))):
            name = f"gen_{kind}_{i:02d}"
            sf.write(OUT / f"{name}.flac", np.clip(x, -1, 1), 16000, format="FLAC", subtype="PCM_16")
            labels.append({"file": name, "source": "generated", "category": f"{kind} noise" if kind != "silence" else "silence"})
    import json
    (OUT / "labels.json").write_text(json.dumps(labels, indent=0))
    return {"n": len(labels), "esc50": sum(l["source"] == "esc50" for l in labels)}


if __name__ == "__main__":
    print(build())
