"""The team's own kitchens: score the frozen model once on recordings labelled by a teammate who didn't write the code.

Audio: data/private/own_kitchen/ (git-ignored, never committed). Labels: eval/own_kitchen/labels.csv
(file,start_s,end_s,activity,session,notes). Straddle rule (fixed before scoring, see eval/OWN_KITCHEN_GUIDE.md):
a 10-s window is scored only if it lies fully inside one labelled row. Exploratory: small N, session-level Wilson CIs.

Timeline scoring (handover v3.2, 3.4): `python -m eval.own_kitchen --timeline [--session NAME]` runs the whole recording through
the app's own timeline (kettle/timeline.blocks, so rules 2c and 2d apply) twice: with the evidence numbers the device now sends
("new rule") and without them ("old rule", what shipped before Sun Nov 15). Each labelled stretch is scored by the activity
covering most of it: right, wrong activity, "kitchen activity" (unnamed), or nothing; non-meal stretches count false meal blocks.
Plan: the first session is development (look and tune), the second is the test (score once, report whatever it says).
Windows every 5 s (several offsets, as the browser's alignment is arbitrary). On-device web rules (quiet level, voices) are
not applied here. Overrides for a dry run: KETTLE_OWN_AUDIO, KETTLE_OWN_LABELS.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from eval import metrics as M
from eval.common import ROOT, num
from kettle.labels import CLASSES

import os

AUDIO = Path(os.environ.get("KETTLE_OWN_AUDIO", ROOT / "data" / "private" / "own_kitchen"))
LABELS = Path(os.environ.get("KETTLE_OWN_LABELS", ROOT / "eval" / "own_kitchen" / "labels.csv"))
MEAL3 = ("cooking", "dishwashing", "eating")


def read_labels() -> list[dict]:
    with open(LABELS) as f:
        return [{**r, "start_s": float(r["start_s"]), "end_s": float(r["end_s"])} for r in csv.DictReader(f)
                if not r["file"].startswith("EXAMPLE")]


def problems(rows: list[dict]) -> list[str]:
    """Format checks only (never judges a label): names, times, overlaps, files present, >= 10 s rows."""
    out = []
    by = defaultdict(list)
    for i, r in enumerate(rows, 2):
        if r["activity"] not in CLASSES:
            out.append(f"line {i}: '{r['activity']}' is not one of the 9 activity names in the guide")
        if r["end_s"] - r["start_s"] < 10:
            out.append(f"line {i}: this stretch is shorter than 10 seconds, so it can't be scored")
        if not (AUDIO / r["file"]).exists():
            out.append(f"line {i}: audio file {r['file']} isn't in data/private/own_kitchen/")
        by[r["file"]].append((r["start_s"], r["end_s"], i))
    for f, spans in by.items():
        spans.sort()
        for (a0, a1, i), (b0, b1, j) in zip(spans, spans[1:]):
            if b0 < a1:
                out.append(f"lines {i} and {j}: these two stretches of {f} overlap")
    return out


def check() -> None:
    if not LABELS.exists():
        raise SystemExit("eval/own_kitchen/labels.csv doesn't exist yet. Copy labels_template.csv to start.")
    rows = read_labels()
    p = problems(rows)
    print("\n".join(p) if p else f"ready to score: {len(rows)} labelled stretches, {len({r['session'] for r in rows})} sessions")


def score() -> None:
    from eval.guard import frozen_hash
    from kettle import audio, encoders, model
    rows = read_labels()
    if problems(rows):
        raise SystemExit("Fix the label problems first: python -m eval.own_kitchen_check")
    head = model.load(ROOT / "models" / "head.json")
    if frozen_hash() != head["sha256"]:
        raise SystemExit("The head isn't frozen (models/FROZEN); score own-kitchen only with the frozen model.")
    enc = encoders.load()
    ys, ps, sess = [], [], []
    for f, rs in _by_file(rows).items():
        x = _full(AUDIO / f)
        for t0, w in audio.windows(x, hop_s=10):
            inside = [r for r in rs if r["start_s"] <= t0 and t0 + 10 <= r["end_s"]]
            if len(inside) != 1:
                continue
            e, _ = encoders.embed(enc, w[None, :])
            ps.append(int(model.predict_proba(head, e).argmax()))
            ys.append(CLASSES.index(inside[0]["activity"]))
            sess.append(inside[0]["session"])
    y, p, s = np.array(ys), np.array(ps), np.array(sess)
    sc = M.scores(M.confusion(y, p))
    split = "own kitchens (exploratory, laptop mic, labelled by a teammate who didn't write the code)"
    per = []
    for k, c in enumerate(CLASSES):
        m = y == k
        if m.sum():
            lo, hi = M.wilson(int((p[m] == k).sum()), int(m.sum()))
            per.append({"class": c, "recall": num(sc["recall"][k], split, int(m.sum()), len(set(s[m])), (lo, hi)),
                        "missed": int(sc["missed"][k]), "false_alarms": int(sc["false_alarms"][k])})
    present = sorted(set(y) | set(p))           # classes that were true or predicted: a class only ever wrongly predicted counts as F1 = 0
    mf = num(float(np.mean([sc["f1"][k] for k in present])), split, len(y), len(set(s)))
    mf["ci"] = "n/a"
    mf["note"] = "macro F1 over activities present in the labels or the predictions; exploratory, small N"
    out = {"split": split, "macro_f1_present_classes": mf,
           "per_class": per, "confusion": M.confusion(y, p).astype(int).tolist(), "head_sha256": head["sha256"]}
    (ROOT / "results" / "own_kitchen.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out["macro_f1_present_classes"]))


def timeline_score(session: str | None = None, hop_s: float = 5.0) -> dict:
    """The full timeline, old rule vs new rule, per labelled stretch (handover 3.4). Writes results/own_kitchen_timeline.json."""
    from collections import Counter
    from kettle import audio, encoders, kinds, model, timeline, witness
    rows = [r for r in read_labels() if session is None or r["session"] == session]
    if not rows:
        raise SystemExit("no labelled stretches" + (f" for session {session}" if session else ""))
    if problems(rows):
        raise SystemExit("Fix the label problems first: python -m eval.own_kitchen_check")
    head = model.load(ROOT / "models" / "head.json")
    enc = encoders.load()
    out = {"split": "own kitchen (exploratory, laptop mic)", "session": session or "all", "hop_s": hop_s, "rules": {}}
    for rule in ("old", "new"):
        tally, per = Counter(), []
        for f, rs in _by_file(rows).items():
            x = _full(AUDIO / f)
            evs = []
            for t0, w in audio.windows(x, hop_s=hop_s):
                e, a = encoders.embed(enc, w[None, :])
                p = model.predict_proba(head, e)[0]
                o = witness.opinion(a[0])
                if rule == "old":
                    o = {k: o[k] for k in ("k", "family", "v")}
                evs.append({"start": t0, "end": t0 + 10, "probs": dict(zip(CLASSES, map(float, p))), "conf": float(p.max()),
                            "novel": bool(model.novelty(head, e)[0] > head["novelty"]["threshold"]), "sounds": [], "w": o,
                            "kinds": [k["id"] for k in kinds.named(a[0])] if rule == "new" else []})
            blks = timeline.blocks(evs, head["theta"], gap_s=hop_s + 1)
            for r in rs:
                cover = Counter()
                for b in blks:
                    ov = min(r["end_s"], b["end"]) - max(r["start_s"], b["start"])
                    if ov > 0 and b["state"] in ("activity", "empty", "not_sure", "talk_or_tv"):
                        cover[b["activity"] or b["state"]] += ov
                shown = cover.most_common(1)[0][0] if cover else None
                truth = r["activity"]
                if truth in MEAL3:
                    tally["meal"] += 1
                    tally["right"] += shown == truth
                    tally["wrong_activity"] += shown in MEAL3 and shown != truth
                    tally["kitchen_unnamed"] += shown == "kitchen"
                else:
                    tally["not_meal"] += 1
                    tally["false_meal"] += shown in MEAL3 or shown == "kitchen"
                    tally["right_other"] += shown == truth
                per.append({"file": f, "start_s": r["start_s"], "end_s": r["end_s"], "truth": truth, "shown": shown,
                            "cover_s": {k: round(v) for k, v in cover.most_common(3)}})
        out["rules"][rule] = {"tally": dict(tally), "stretches": per}
    name = f"own_kitchen_timeline{'_' + session if session else ''}.json"
    (ROOT / "results" / name).write_text(json.dumps(out, indent=1, default=float))
    for rule in ("old", "new"):
        print(rule, out["rules"][rule]["tally"])
    return out


def _by_file(rows):
    d = defaultdict(list)
    for r in rows:
        d[r["file"]].append(r)
    return d


def _full(path: Path) -> np.ndarray:
    from kettle import audio
    x, sr = audio.decode(path.read_bytes())
    return audio.to_16k_mono(x, sr)


if __name__ == "__main__":
    import sys
    a = sys.argv[1:]
    if "--timeline" in a:
        timeline_score(a[a.index("--session") + 1] if "--session" in a else None)
    else:
        score()
