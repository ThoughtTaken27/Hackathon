"""Which eval sensor nodes are the 3 microphones the development set never had? Decided without labels.

The DCASE 2018 Task 5 page says three eval sensor nodes are not in the development set but doesn't say which.
Rule (fixed in docs/PRD.md §13.2 before any eval audio was fetched):
- For every node, compute the mean log-mel spectrum (64 bands, channel 0) over its clips. Unlabelled: no
  activity labels and no model predictions are used.
- For each dev node k, its "spread" = the largest cosine distance between its own per-fold centroids.
- An EvalNode is matched to DevNode k if k is its nearest dev centroid and the distance is below k's spread.
- EvalNodes matched one-to-one to DevNode1-4 are "known"; the rest are "unknown". If fewer than 4 nodes
  match one-to-one, the unknown-mic slice is not reported as such (per-node numbers only).
"""
from __future__ import annotations

import numpy as np
import torch
import torchaudio.transforms as T

_MEL = T.MelSpectrogram(sample_rate=16000, n_fft=512, win_length=512, hop_length=160, n_mels=64)


def log_mel_mean(wave: np.ndarray) -> np.ndarray:
    """One clip (float32, 16 kHz) -> its mean log-mel spectrum (64 numbers)."""
    m = _MEL(torch.from_numpy(np.ascontiguousarray(wave, dtype=np.float32)))
    return torch.log(m + 1e-6).mean(-1).numpy()


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(1 - a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def decide(dev: dict[str, dict[int, np.ndarray]], ev: dict[str, np.ndarray]) -> dict:
    """dev: {DevNode: {fold: mean spectrum}}; ev: {EvalNode: mean spectrum} -> the rule's decision, with every distance."""
    centroid = {k: np.mean(list(f.values()), 0) for k, f in dev.items()}
    spread = {k: max(cosine_distance(a, b) for i, a in f.items() for j, b in f.items() if i < j) for k, f in dev.items()}
    rows, matched = {}, {}
    for e, spec in sorted(ev.items()):
        d = {k: cosine_distance(spec, c) for k, c in centroid.items()}
        near = min(d, key=d.get)
        ok = d[near] < spread[near]
        rows[e] = {"distances": d, "nearest": near, "within_spread": ok}
        if ok:
            matched.setdefault(near, []).append(e)
    one_to_one = {k: v[0] for k, v in matched.items() if len(v) == 1}
    known = sorted(one_to_one.values())
    confirmed = len(known) == 4
    return {"spread": spread, "nodes": rows, "known": known if confirmed else [],
            "unknown": sorted(set(ev) - set(known)) if confirmed else [],
            "confirmed": confirmed, "dev_match": one_to_one}


def main() -> dict:
    """Compute unlabelled per-node spectra for dev (per fold) and the eval sample, apply the rule, save it."""
    import json
    from collections import defaultdict
    from pathlib import Path
    import soundfile as sf
    from kettle.data import load_meta
    root = Path(__file__).resolve().parents[1]
    dev_meta = {Path(r["file"]).stem: r for r in load_meta("dev")}
    acc = defaultdict(lambda: defaultdict(list))
    for p in sorted((root / "data" / "clips" / "dev").glob("*.flac")):
        r = dev_meta[p.stem]
        acc[r["node"]][r["fold"]].append(log_mel_mean(sf.read(p, dtype="float32", always_2d=True)[0][:, 0]))
    dev = {nd: {f: np.mean(v, 0) for f, v in folds.items()} for nd, folds in acc.items()}
    ev_meta = {Path(r["file"]).stem: r for r in load_meta("eval")}   # node names only; labels are never read here
    eacc = defaultdict(list)
    for p in sorted((root / "data" / "clips" / "eval").glob("*.flac")):
        eacc[ev_meta[p.stem]["node"]].append(log_mel_mean(sf.read(p, dtype="float32", always_2d=True)[0][:, 0]))
    ev = {nd: np.mean(v, 0) for nd, v in eacc.items()}
    out = decide(dev, ev)
    out["n_clips"] = {"dev": {k: sum(len(v) for v in f.values()) for k, f in acc.items()}, "eval": {k: len(v) for k, v in eacc.items()}}
    out["rule"] = __doc__.strip().splitlines()[2:]
    (root / "results").mkdir(exist_ok=True)
    (root / "results" / "fingerprint.json").write_text(json.dumps(out, indent=1, default=float))
    return out


if __name__ == "__main__":
    r = main()
    print({k: r[k] for k in ("known", "unknown", "confirmed", "dev_match")})
