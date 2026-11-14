"""Pre-registered sample of the official DCASE 2018 Task 5 evaluation set (fixed before any eval audio is fetched).

Recipe (docs/PRD.md §13.2), unchanged after this file is committed:
- A "moment" is one 10-s segment of one session; the eval set has 10,425 moments, each heard by 7 sensor nodes.
- Draw 1,000 moments uniformly at random with seed 20261114.
- Top up: for any activity with fewer than 50 sampled moments, add random moments of that activity (same seed)
  until it has 50 (or all of them).
- Keep all 7 node copies of every chosen moment.
- Scores are reweighted to the true eval class counts (eval/metrics.py), so precision is comparable to the full set.
Usage: python -m eval.sample   (writes eval/sample_eval.json; the list of files only, no audio)
"""
from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from kettle.data import load_meta
from kettle.labels import CLASSES

SEED = 20261114
N_MOMENTS = 1000
MIN_PER_CLASS = 50
OUT = Path(__file__).with_name("sample_eval.json")


def draw(seed: int = SEED) -> list[dict]:
    """The sampled eval clips (all 7 node copies of each chosen moment) as metadata rows."""
    rows = load_meta("eval")
    moments = defaultdict(list)
    for r in rows:
        moments[(r["ex"], r["seg"])].append(r)
    keys = sorted(moments)
    rng = random.Random(seed)
    chosen = set(rng.sample(keys, N_MOMENTS))
    label = {k: moments[k][0]["label"] for k in keys}
    for c in CLASSES:
        have = [k for k in chosen if label[k] == c]
        pool = sorted(k for k in keys if label[k] == c and k not in chosen)
        rng.shuffle(pool)
        chosen.update(pool[: max(0, MIN_PER_CLASS - len(have))])
    return [r for k in sorted(chosen) for r in sorted(moments[k], key=lambda r: r["node"])]


def write() -> dict:
    rows = draw()
    summary = {"seed": SEED, "n_moments": len({(r["ex"], r["seg"]) for r in rows}), "n_clips": len(rows),
               "moments_per_class": dict(Counter(r["label"] for r in rows if r["node"] == "EvalNode1")),
               "clips_per_node": dict(Counter(r["node"] for r in rows))}
    OUT.write_text(json.dumps({"summary": summary, "files": [r["file"] for r in rows]}, indent=0))
    return summary


def load_sample() -> list[dict]:
    """The committed sample as full metadata rows (labels are joined from data/meta/eval at load time)."""
    files = set(json.loads(OUT.read_text())["files"])
    return [r for r in load_meta("eval") if r["file"] in files]


if __name__ == "__main__":
    print(json.dumps(write(), indent=1))
