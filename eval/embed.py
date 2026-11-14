"""Embed fetched clips once and cache the numbers on disk (data/emb/<encoder>/<split>/shard_*.npz, git-ignored).

Usage:
    python -m eval.embed ced-tiny dev            # all 4 channels (the model Kettle ships)
    python -m eval.embed ast dev --ch0           # baselines / ablations: channel 0 only
    python -m eval.embed ced-tiny dev --follow   # keep embedding new clips while the fetch is still running
Each shard holds: files [n], emb [n, channels, D] float32, scores [n, channels, S] float16 (AudioSet or prompts).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / "data" / "clips"
EMB = ROOT / "data" / "emb"
SHARD = 256


def encoder(name: str, device: str):
    """name -> f(waves [B, 160000]) -> (emb [B, D], scores [B, S] | None)."""
    if name in ("ced-tiny", "ced-tiny-5s"):
        from kettle import encoders
        enc = encoders.load(device)
        if name == "ced-tiny-5s":          # the kitchen chip: the last 5 s of the window
            return lambda x: encoders.embed(enc, x[:, -80000:])
        return lambda x: encoders.embed(enc, x)
    from eval import encoders_extra as ex
    return {"ast": ex.make_ast, "ced-small": ex.make_ced_small, "clap": ex.make_clap, "logmel": ex.make_logmel}[name](device)


def done_files(out: Path) -> set[str]:
    return {str(f) for p in out.glob("shard_*.npz") for f in np.load(p)["files"]}


def read(path: Path, ch0: bool) -> np.ndarray:
    """A clip as float32 [channels, 160000] (padded or cut to exactly 10 s)."""
    x, _ = sf.read(path, dtype="float32", always_2d=True)
    x = x[:160000].T
    if x.shape[1] < 160000:
        x = np.pad(x, ((0, 0), (0, 160000 - x.shape[1])))
    return x[:1] if ch0 else x


def run(name: str, split: str, ch0: bool, device: str, batch: int = 32, only: set[str] | None = None) -> int:
    """Embed every clip in data/clips/<split> not yet in the cache (optionally only the stems in `only`)."""
    out = EMB / name / split
    out.mkdir(parents=True, exist_ok=True)
    have = done_files(out)
    todo = sorted(p for p in (CLIPS / split).glob("*.flac") if p.stem not in have and not p.stem.endswith(".part")
                  and (only is None or p.stem in only))
    if not todo:
        return 0
    f = encoder(name, device)
    n0 = len(list(out.glob("shard_*.npz")))
    for s in range(0, len(todo), SHARD):
        chunk = todo[s:s + SHARD]
        waves = np.stack([read(p, ch0) for p in chunk])              # [n, C, 160000]
        n, C = waves.shape[:2]
        flat = waves.reshape(n * C, -1)
        embs, scs = [], []
        for i in range(0, len(flat), batch):
            e, sc = f(flat[i:i + batch])
            embs.append(e)
            if sc is not None:
                scs.append(sc)
        E = np.concatenate(embs).reshape(n, C, -1).astype(np.float32)
        S = np.concatenate(scs).reshape(n, C, -1).astype(np.float16) if scs else np.zeros((n, C, 0), np.float16)
        np.savez(out / f"shard_{n0 + s // SHARD:04d}.npz", files=np.array([p.stem for p in chunk]), emb=E, scores=S)
        print(f"{time.strftime('%H:%M:%S')} {name}/{split}: +{len(chunk)} ({s + len(chunk)}/{len(todo)})", flush=True)
    return len(todo)


def load(name: str, split: str) -> dict:
    """All cached rows for (encoder, split): {'files': [n], 'emb': [n, C, D], 'scores': [n, C, S]}."""
    if split.startswith("eval"):
        from eval.guard import assert_eval_allowed
        assert_eval_allowed()
    import os
    shards = sorted((EMB / name / split).glob("shard_*.npz"))
    if os.environ.get("KETTLE_USE_CACHE") == "1":   # the notebook: use only what is committed
        shards = []
    cached = ROOT / "results" / "cache" / f"{name}_{split}.npz"
    if not shards and cached.exists():          # the small committed cache (see eval/cache.py)
        c = np.load(cached)
        return {"files": c["files"], "emb": c["emb"].astype(np.float32), "scores": c["scores"]}
    if not shards:
        raise FileNotFoundError(f"no embeddings for {name}/{split}; run python -m eval.embed {name} {split}")
    parts = [np.load(p) for p in shards]
    return {"files": np.concatenate([p["files"] for p in parts]), "emb": np.concatenate([p["emb"] for p in parts]),
            "scores": np.concatenate([p["scores"] for p in parts])}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("encoder")
    ap.add_argument("split")
    ap.add_argument("--ch0", action="store_true")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--follow", action="store_true", help="repeat until the fetch log says done")
    ap.add_argument("--only", help="JSON file with a 'files' list of clip stems to embed (a seeded subset)")
    a = ap.parse_args()
    only = set(json.loads(open(a.only).read())["files"]) if a.only else None
    while True:
        added = run(a.encoder, a.split, a.ch0, a.device, only=only)
        log = ROOT / ".overnight" / "kettle" / "jobs" / f"fetch-{a.split}.log"
        finished = log.exists() and '"requested"' in log.read_text().splitlines()[-1]
        if not a.follow or (finished and added == 0):
            break
        time.sleep(60)
