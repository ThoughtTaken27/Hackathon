"""The small committed cache that lets anyone reproduce every number without downloading SINS (~76 min).

python -m eval.cache   writes results/cache/:
- ced-tiny_dev.npz     files, CED-tiny embeddings float16 [n, 4, 192], AudioSet scores float16 [n, 1, 527]
                       (channel 0; only the labels the frozen zero-shot map and the evidence list use; the rest are 0)
- logmel_dev.npz       log-mel statistics [n, 1, 129] (the no-deep-model baseline's features)
- ced-tiny-5s_dev.npz  5-s chip embeddings [n, 1, 192]
- ced-tiny_offlist.npz off-list clips (ESC-50 non-activities, noise, silence) + their labels
- probes_dev.npz       out-of-fold predictions of the AST / CED-small / CLAP linear probes and zero-shot maps
                       (their embeddings are 768/384/512-d and too big to commit)
Apple's scores are committed as per-activity scores after the frozen map (results/baselines/apple_*_activity.csv).
Eval-set embeddings are NOT committed (the eval audio is CC BY-NC-ND: no derivatives); results/eval_predictions.jsonl is.
eval/common.py reads these files whenever data/emb/ is missing, so the notebook runs the same code as python -m eval.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "cache"


def keep_labels() -> np.ndarray:
    """Indices of AudioSet labels used by the frozen zero-shot map or shown as evidence."""
    names = json.loads((ROOT / "models" / "audioset_labels.json").read_text())
    amap = json.loads((ROOT / "docs/research/kettle/probes/maps/audioset_map.json").read_text())["map"]
    ev = json.loads((ROOT / "kettle" / "evidence_labels.json").read_text())["labels"]
    keep = {n for v in amap.values() for n in v} | set(ev)
    return np.array([i for i, n in enumerate(names) if n in keep])


def export() -> dict:
    from eval import embed
    OUT.mkdir(parents=True, exist_ok=True)
    sizes = {}
    d = embed.load("ced-tiny", "dev")
    sc = np.zeros((len(d["files"]), 1, 527), np.float16)
    k = keep_labels()
    sc[:, 0, k] = d["scores"][:, 0, k]
    np.savez_compressed(OUT / "ced-tiny_dev.npz", files=d["files"], emb=d["emb"].astype(np.float16), scores=sc)
    for enc, split in (("logmel", "dev"), ("ced-tiny-5s", "dev"), ("ced-tiny", "offlist")):
        try:
            e = embed.load(enc, split)
        except FileNotFoundError:
            continue
        dtype = np.float32 if enc == "logmel" else np.float16      # log-mel statistics are precision-sensitive
        chans = slice(None) if enc == "logmel" else slice(0, 1)     # the log-mel baseline trains on all 4 channels, like ours
        np.savez_compressed(OUT / f"{enc}_{split}.npz", files=e["files"], emb=e["emb"][:, chans].astype(dtype),
                            scores=np.zeros((len(e["files"]), 1, 0), np.float16))
    lab = ROOT / "data" / "clips" / "offlist" / "labels.json"
    if lab.exists():
        (OUT / "offlist_labels.json").write_text(lab.read_text())
    for p in OUT.glob("*"):
        sizes[p.name] = round(p.stat().st_size / 1e6, 2)
    return sizes


def apple_activity_csv(split: str) -> Path | None:
    """Collapse Apple's 303 class means to the 9 activity scores the frozen map uses (max over mapped classes)."""
    src = ROOT / "results" / "baselines" / f"apple_{split}.jsonl"
    if not src.exists():
        return None
    from kettle.labels import CLASSES
    amap = json.loads((ROOT / "docs/research/kettle/probes/maps/apple_map.json").read_text())["map"]
    out = ROOT / "results" / "baselines" / f"apple_{split}_activity.csv"
    with open(out, "w") as f:
        f.write("file," + ",".join(CLASSES) + "\n")
        for line in open(src):
            r = json.loads(line)
            f.write(r["file"] + "," + ",".join(f"{max((r['mean'].get(c, 0.0) for c in amap[a]), default=0.0):.4f}" for a in CLASSES) + "\n")
    return out


if __name__ == "__main__":
    print(export())
    for s in ("dev",):
        print(apple_activity_csv(s))
