"""Nonspeech7k test split through frozen CED-tiny, cached for sound-type calibration and safety-alert evaluation.

Uses only the test split (725 human-sound clips: breath, cough, crying, laugh, screaming, sneeze, yawm).
Each clip becomes a 10-s 16 kHz window (first 10 s if longer, repeat-padded if shorter, like eval/offlist.py),
is embedded once with the frozen CED-tiny encoder, and only embeddings and AudioSet scores are cached in
results/cache/ced-tiny_nonspeech7k.npz (no audio is committed). Held out from the frozen head.

Nonspeech7k: Rashid et al., "Nonspeech7k dataset: Classification and analysis of human non-speech sound",
IET Signal Processing 2023. https://zenodo.org/records/6967442 · licence per Zenodo metadata: CC-BY-4.0
(cc-by-4.0, Creative Commons Attribution 4.0 International) · audio kept in data/clips/nonspeech7k/ (git-ignored).

Run: python -m eval.nonspeech7k
"""
from __future__ import annotations

import csv
import time
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf

from eval.offlist import to_10s_16k

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "clips" / "nonspeech7k"
CACHE = ROOT / "results" / "cache" / "ced-tiny_nonspeech7k.npz"
ZENODO = "https://zenodo.org/api/records/6967442/files"


def fetch() -> None:
    """Download test.zip and the test metadata csv once, then unzip (idempotent)."""
    import requests
    OUT.mkdir(parents=True, exist_ok=True)
    for remote, local in (("test.zip", "test.zip"), ("metadata%20of%20test%20set.csv", "meta.csv")):
        if not (OUT / local).exists():
            r = requests.get(f"{ZENODO}/{remote}/content", timeout=600)
            r.raise_for_status()
            (OUT / local).write_bytes(r.content)
    if not (OUT / "raw" / "test").exists():
        zipfile.ZipFile(OUT / "test.zip").extractall(OUT / "raw")


def main() -> None:
    from kettle import encoders
    t0 = time.time()
    fetch()
    rows = list(csv.DictReader(open(OUT / "meta.csv", encoding="utf-8-sig")))
    waves = []
    for r in rows:
        x, sr = sf.read(OUT / "raw" / "test" / r["Filename"], dtype="float32")
        waves.append(to_10s_16k(x, sr))
    waves = np.stack(waves)
    enc = encoders.load()
    embs, scores = [], []
    for i in range(0, len(waves), 32):
        e, s = encoders.embed(enc, waves[i:i + 32])
        embs.append(e), scores.append(s)
    np.savez_compressed(CACHE, files=np.array([r["Filename"] for r in rows]), category=np.array([r["Classname"] for r in rows]),
                        emb=np.concatenate(embs).astype(np.float16), scores=np.concatenate(scores).astype(np.float16),
                        rms_db=np.array([20 * np.log10(np.sqrt(np.mean(w ** 2)) + 1e-12) for w in waves], np.float32))
    print({"clips": len(rows), "cache": str(CACHE.relative_to(ROOT)), "seconds": round(time.time() - t0)})


if __name__ == "__main__":
    main()
