"""Named household sound types, in Python (a mirror of web/public/js/sense.js).

Same constants as the browser: web/public/model/kinds.json, written and measured by eval/beyond.py. Used to give the
sample days the same fields a real kitchen laptop sends (kinds).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "web" / "public" / "model" / "kinds.json").read_text())
_HEAD_FILE = ROOT / "web" / "public" / "model" / "sound_head.json"
HEADS = json.loads(_HEAD_FILE.read_text())["heads"] if _HEAD_FILE.exists() else {}


def head_prob(h: dict, emb, scores) -> float:
    """The trained sound head (eval/sound_head.py): logistic regression on emb [192] or emb + log-odds of the 527 scores."""
    x = [float(v) for v in emb]
    if len(h["w"]) > len(x):
        x += [math.log(p / (1 - p)) for p in (min(1 - 1e-4, max(1e-4, float(v))) for v in scores)]
    z = h["b"] + sum(w * ((v - m) / s) for w, v, m, s in zip(h["w"], x, h["mean"], h["std"]))
    return 1 / (1 + math.exp(-z))


def named(scores, off: tuple = (), emb=None, with_hidden: bool = False) -> list[dict]:
    """AudioSet probabilities [527] (+ embedding [192]) -> [{id, name, score}] strongest first; [] when a vetoed sound wins.

    With the embedding, sounds that have a trained head are decided by it (web/public/js/sense.js kindsOf, same order)."""
    out, top = [], 0.0
    for k in CFG["kinds"]:
        s = max(float(scores[i]) for i in k["index"])
        h = HEADS.get(k["id"]) if emb is not None else None
        if h:
            p = head_prob(h, emb, scores)
            if p < h["threshold"]:
                continue
            top = max(top, s)
            if k["id"] not in off and (with_hidden or h["shown"]):
                out.append((1 + p, k["id"], k["name"], round(p, 3)))
            continue
        if s < k["tau"] or s < k.get("min", 0):
            continue
        if k.get("beat") and s <= max(float(scores[i]) for i in k["beat"]):   # context: louder than its look-alikes
            continue
        top = max(top, s)
        if k["id"] not in off and (with_hidden or k.get("shown", True)):
            out.append((s / k["tau"], k["id"], k["name"], round(s, 3)))
    if out and max(float(scores[i]) for i in CFG["veto"]) >= top:
        return []
    return [{"id": i, "name": n, "score": s} for _, i, n, s in sorted(out, key=lambda x: -x[0])]

