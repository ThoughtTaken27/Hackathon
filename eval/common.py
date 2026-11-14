"""Shared helpers for evaluation: line up cached embeddings with labels, folds, sessions and nodes."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

from eval import embed
from kettle.data import load_meta
from kettle.labels import CLASSES

ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "docs" / "research" / "kettle" / "probes" / "maps"


def table(encoder: str, split: str, files: list[str] | None = None) -> dict:
    """Cached embeddings for a split, aligned with metadata. Keys: files, y, session, node, fold, emb, scores."""
    d = embed.load(encoder, split)
    meta_split = "eval" if split.startswith("eval") else "dev"
    meta = {Path(r["file"]).stem: r for r in load_meta(meta_split)}
    keep = np.array([f in meta and (files is None or f in files) for f in d["files"]])
    rows = [meta[f] for f in d["files"][keep]]
    order = np.argsort(d["files"][keep], kind="stable")
    sel = lambda a: a[keep][order]
    rows = [rows[i] for i in order]
    return {"files": sel(d["files"]), "y": np.array([CLASSES.index(r["label"]) for r in rows]),
            "session": np.array([r["session"] for r in rows]), "node": np.array([r["node"] for r in rows]),
            "fold": np.array([r["fold"] if r["fold"] is not None else -1 for r in rows]),
            "ex": np.array([r["ex"] for r in rows]), "seg": np.array([r["seg"] for r in rows]),
            "emb": sel(d["emb"]), "scores": sel(d["scores"]).astype(np.float32)}


def align(t: dict, other: dict) -> dict:
    """Restrict table `other` to t's files in t's order (for comparing encoders on the same clips)."""
    idx = {f: i for i, f in enumerate(other["files"])}
    take = np.array([idx[f] for f in t["files"]])
    return {k: (v[take] if isinstance(v, np.ndarray) and len(v) == len(other["files"]) else v) for k, v in other.items()}


def full_counts(split: str) -> np.ndarray:
    """How many clips of each class the whole split has (for prevalence reweighting)."""
    c = Counter(r["label"] for r in load_meta("eval" if split.startswith("eval") else "dev"))
    return np.array([c[k] for k in CLASSES], float)


def audioset_map_predict(scores: np.ndarray, names: list[str]) -> np.ndarray:
    """Frozen zero-shot map (probes/maps/audioset_map.json): activity score = max of its AudioSet labels; ties -> absence."""
    amap = json.loads((MAPS / "audioset_map.json").read_text())["map"]
    col = {n: i for i, n in enumerate(names)}
    act = np.stack([scores[:, [col[c] for c in amap[a] if c in col]].max(1) for a in CLASSES], 1)
    p = act.argmax(1)
    p[act.max(1) <= 0] = 0
    return p


def apple_map_predict(rows: list[dict]) -> np.ndarray:
    """Frozen Apple map (probes/maps/apple_map.json): activity score = max of its mapped classes' mean confidence."""
    amap = json.loads((MAPS / "apple_map.json").read_text())["map"]
    out = []
    for r in rows:
        m = r["mean"]
        act = [max((m.get(c, 0.0) for c in amap[a]), default=0.0) for a in CLASSES]
        out.append(int(np.argmax(act)) if max(act) > 0 else 0)
    return np.array(out)


def num(value: float, split: str, n_clips: int, n_sessions: int, ci=None, unit: str = "%") -> dict:
    """Every reported number carries its split, N and (where applicable) a 95% CI."""
    pct = 100 if unit == "%" else 1
    out = {"value": round(float(value) * pct, 1), "split": split, "n_clips": int(n_clips), "n_sessions": int(n_sessions)}
    if ci is not None:
        out["ci95"] = [round(float(ci[0]) * pct, 1), round(float(ci[1]) * pct, 1)]
    return out
