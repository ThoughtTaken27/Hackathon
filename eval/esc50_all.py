"""All 2000 ESC-50 clips through frozen CED-tiny, cached for sound-type calibration and safety-alert evaluation.

Fetches every ESC-50 clip (50 categories, 5 folds), turns each into a 10-s 16 kHz window the same way
eval/offlist.py does (repeat the 5-s clip), runs the frozen CED-tiny encoder once, and caches only embeddings
and AudioSet scores in results/cache/ced-tiny_esc50all.npz (no audio is committed). Held out from the frozen head.
Clips already fetched by eval/esc50_kinds.py are reused from data/clips/esc50_kinds/.

ESC-50: K. J. Piczak, ESC: Dataset for Environmental Sound Classification, ACM MM 2015.
https://github.com/karolpiczak/ESC-50 · CC BY-NC 3.0 · audio kept in data/clips/esc50_all/ (git-ignored).

Run: python -m eval.esc50_all
"""
from __future__ import annotations

import csv
import io
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf

from eval.offlist import BASE, to_10s_16k

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "clips" / "esc50_all"
REUSE = ROOT / "data" / "clips" / "esc50_kinds"
CACHE = ROOT / "results" / "cache" / "ced-tiny_esc50all.npz"


def fetch_one(row: dict) -> str:
    """Make data/clips/esc50_all/<name>.flac for one csv row (copy if already local, else download with retries)."""
    import requests
    name = f"esc50_{row['category']}_{Path(row['filename']).stem}"
    dst = OUT / f"{name}.flac"
    if dst.exists():
        return name
    if (REUSE / f"{name}.flac").exists():
        shutil.copy(REUSE / f"{name}.flac", dst)
        return name
    for attempt in range(4):
        try:
            r = requests.get(f"{BASE}/audio/{row['filename']}", timeout=60)
            r.raise_for_status()
            x, sr = sf.read(io.BytesIO(r.content), dtype="float32")
            sf.write(dst, to_10s_16k(x, sr), 16000, format="FLAC", subtype="PCM_16")
            return name
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    return name


def main() -> None:
    import requests
    from kettle import encoders
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(io.StringIO(requests.get(f"{BASE}/meta/esc50.csv", timeout=60).text)))
    with ThreadPoolExecutor(16) as ex:
        names = list(ex.map(fetch_one, rows))
    enc = encoders.load()
    waves = np.stack([sf.read(OUT / f"{n}.flac", dtype="float32")[0] for n in names])
    embs, scores = [], []
    for i in range(0, len(waves), 32):
        e, s = encoders.embed(enc, waves[i:i + 32])
        embs.append(e), scores.append(s)
    np.savez_compressed(CACHE, files=np.array(names), category=np.array([r["category"] for r in rows]),
                        fold=np.array([int(r["fold"]) for r in rows]), emb=np.concatenate(embs).astype(np.float16),
                        scores=np.concatenate(scores).astype(np.float16),
                        rms_db=np.array([20 * np.log10(np.sqrt(np.mean(w ** 2)) + 1e-12) for w in waves], np.float32))
    print({"clips": len(names), "cache": str(CACHE.relative_to(ROOT)), "seconds": round(time.time() - t0)})


if __name__ == "__main__":
    main()
