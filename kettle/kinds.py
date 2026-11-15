"""Named household sound types, in Python (a mirror of web/public/js/sense.js).

Same constants as the browser: web/public/model/kinds.json, written and measured by eval/beyond.py. Used to give the
sample days the same fields a real kitchen laptop sends (kinds).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "web" / "public" / "model" / "kinds.json").read_text())


def named(scores, off: tuple = ()) -> list[dict]:
    """AudioSet probabilities [527] -> [{id, name, score}] strongest first; [] when a vetoed (body/bathroom) sound wins."""
    out, top = [], 0.0
    for k in CFG["kinds"]:
        s = max(float(scores[i]) for i in k["index"])
        if s < k["tau"] or s < k.get("min", 0):
            continue
        if k.get("beat") and s <= max(float(scores[i]) for i in k["beat"]):   # context: louder than its look-alikes
            continue
        top = max(top, s)
        if k["id"] not in off and k.get("shown", True):
            out.append((s / k["tau"], k["id"], k["name"], round(s, 3)))
    if out and max(float(scores[i]) for i in CFG["veto"]) >= top:
        return []
    return [{"id": i, "name": n, "score": s} for _, i, n, s in sorted(out, key=lambda x: -x[0])]

