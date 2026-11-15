"""Evidence: which everyday sounds CED-tiny's own AudioSet head heard in a window.

This is independent of the activity head, so a judge (or Meera) can see *why* a block says
"Washing up": the encoder heard "Dishes, pots, and pans 0.36 · Water tap, faucet 0.21".
Only a fixed list of kitchen and living-room sounds is ever shown (kettle/evidence_labels.json):
no body or bathroom sounds and no voice tags (a visit shows only as the Conversation activity).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NAMES: list[str] = json.loads((ROOT / "models" / "audioset_labels.json").read_text())
SHOWN: list[str] = json.loads((Path(__file__).with_name("evidence_labels.json")).read_text())["labels"]
_IDX = np.array([NAMES.index(n) for n in SHOWN])


def scores(audioset: np.ndarray) -> dict[str, float]:
    """527 AudioSet probabilities -> {shown label: score} for the fixed household list only."""
    return {n: float(audioset[i]) for n, i in zip(SHOWN, _IDX)}


def top_sounds(audioset: np.ndarray, k: int = 3) -> list[dict]:
    """The k highest-scoring shown labels: [{'name': 'Dishes, pots, and pans', 'score': 0.36}, ...]."""
    s = audioset[_IDX]
    order = np.argsort(-s)[:k]
    return [{"name": SHOWN[i], "score": round(float(s[i]), 3)} for i in order]


def merge(lists: list[list[dict]], k: int = 3) -> list[dict]:
    """Combine the top sounds of several windows: mean score over the windows (absent = 0), top k."""
    total: dict[str, float] = {}
    for lst in lists:
        for s in lst:
            total[s["name"]] = total.get(s["name"], 0.0) + s["score"]
    n = max(1, len(lists))
    best = sorted(total.items(), key=lambda kv: -kv[1])[:k]
    return [{"name": name, "score": round(v / n, 3)} for name, v in best]
