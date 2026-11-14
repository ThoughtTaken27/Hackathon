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
