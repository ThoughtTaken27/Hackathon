"""Public test clips for the extra sound types and the privacy allow-list (improvement plan A4, A6, D1, G2).

Fetches 16 ESC-50 clips per category (household sounds Kettle may name, and sensitive sounds it must never
name), turns each into a 10-s 16 kHz window the same way eval/offlist.py does (repeat the 5-s clip), runs the
frozen CED-tiny encoder once, and caches only embeddings and AudioSet scores in
results/cache/ced-tiny_esc50kinds.npz (no audio is committed). eval/beyond.py reads that cache.

ESC-50: K. J. Piczak, ESC: Dataset for Environmental Sound Classification, ACM MM 2015.
https://github.com/karolpiczak/ESC-50 · CC BY-NC 3.0 · audio kept in data/clips/esc50_kinds/ (git-ignored).
Clips 20-35 of each category are used, so none overlaps the off-list set (clips 0-9 of its categories).

Run: python -m eval.esc50_kinds
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import numpy as np
import soundfile as sf

from eval.offlist import BASE, to_10s_16k

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "clips" / "esc50_kinds"
CACHE = ROOT / "results" / "cache" / "ced-tiny_esc50kinds.npz"
HOUSEHOLD = ["vacuum_cleaner", "washing_machine", "door_wood_knock", "keyboard_typing", "pouring_water", "water_drops",
             "clock_alarm", "glass_breaking", "footsteps", "dog", "cat", "door_wood_creaks", "can_opening", "clock_tick"]
SENSITIVE = ["toilet_flush", "crying_baby", "coughing", "snoring", "sneezing", "brushing_teeth", "laughing", "breathing"]
FIRST, PER_CATEGORY = 20, 16


def fetch() -> list[dict]:
    """Download the clips once (idempotent); returns [{file, category, group}]."""
    import requests
    OUT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(io.StringIO(requests.get(f"{BASE}/meta/esc50.csv", timeout=60).text)))
    out = []
    for group, cats in (("household", HOUSEHOLD), ("sensitive", SENSITIVE)):
        for c in cats:
            for r in [r for r in rows if r["category"] == c][FIRST:FIRST + PER_CATEGORY]:
                name = f"esc50_{c}_{Path(r['filename']).stem}"
                if not (OUT / f"{name}.flac").exists():
                    x, sr = sf.read(io.BytesIO(requests.get(f"{BASE}/audio/{r['filename']}", timeout=60).content), dtype="float32")
                    sf.write(OUT / f"{name}.flac", to_10s_16k(x, sr), 16000, format="FLAC", subtype="PCM_16")
                out.append({"file": name, "category": c, "group": group})
    return out


def main() -> None:
    from kettle import encoders
    clips = fetch()
    enc = encoders.load()
    waves = np.stack([sf.read(OUT / f"{c['file']}.flac", dtype="float32")[0] for c in clips])
    embs, scores = [], []
    for i in range(0, len(waves), 32):
        e, s = encoders.embed(enc, waves[i:i + 32])
        embs.append(e), scores.append(s)
    np.savez_compressed(CACHE, files=np.array([c["file"] for c in clips]), category=np.array([c["category"] for c in clips]),
                        group=np.array([c["group"] for c in clips]), emb=np.concatenate(embs).astype(np.float16),
                        scores=np.concatenate(scores).astype(np.float16),
                        rms_db=np.array([20 * np.log10(np.sqrt(np.mean(w ** 2)) + 1e-12) for w in waves], np.float32))
    print({"clips": len(clips), "cache": str(CACHE.relative_to(ROOT))})


if __name__ == "__main__":
    main()
