"""Rule 2c (naming a kitchen stretch from evidence across its windows): measured through the app's own timeline code.

Why: on Sun Nov 15 Parth ran Kettle in his own kitchen. Pots and cutlery while his mom cooked were shown as "washing up"
and "eating". The cause: when the head is out of its depth, the second opinion named each 10-s window from its single
loudest kitchen tag, and "Dishes, pots, and pans" meant washing up, "Cutlery" meant eating. Rule 2c names the whole stretch
instead (kettle/witness.py name_kitchen; models/witness.json "_evidence").

What is compared: the same events through kettle/timeline.blocks(), with and without the three evidence numbers. Without
them the code takes the old path, so "before" is exactly what shipped until today.

Sets: SINS dev (the research home; 257 continuous sessions, each one activity; out-of-fold head scores), DESED public eval
(real homes from online video; frying and dishes clips) and Kitchen20 (kitchen sound clips from many uploaders), each split
into TUNE and TEST halves by uploader hash (eval/other_homes.py half()). The thresholds in models/witness.json were picked on
SINS dev and the TUNE halves only (Sun Nov 15, ~11:30 AM CT). TEST halves are scored once, by this script.

Process note: before rule 2c was chosen, an exploratory comparison of other approaches (a bigger tagger, CED-small; and a
trained logistic judge) was scored once on Kitchen20 TEST halves. Neither approach ships. This script's TEST numbers are for
rule 2c, whose thresholds never saw those halves, but the halves were looked at once today, so they are not pristine.
The first version of rule 2c checked cooking evidence before water. Its first TEST run (Kitchen20: right 130 -> 123, wrong
activity 9 -> 14) showed sink clips with a faint "stir" tag named cooking. The rule was changed so each window votes for the
louder of the two, checked on the TUNE halves and SINS dev, and TEST was scored a second time. Both TEST runs are kept in
results/kitchen_naming.json ("first_test_run"). Rule 2d (a short washing-up or eating flip with no water or chewing of its
own, next to cooking, is cooking) was then added after a browser end-to-end run on a frying-and-cutlery clip showed the head
93% sure of "washing up" with no tap; it was chosen on SINS dev and TUNE halves (python -m eval.kitchen_naming --dev), and
TEST was scored a third time for the rule as shipped. The clean measurement is the team's own kitchen recording.

    python -m eval.kitchen_naming      writes results/kitchen_naming.json
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict

import numpy as np

from eval.common import ROOT
from eval.other_homes import EMB, RESULTS, _desed_groups, desed_kind, half, main_sound
from kettle import model, timeline, witness
from kettle.labels import CLASSES

MEAL = {"cooking", "dishwashing", "eating"}
K20 = {"frying-pan": "cooking", "boiling-water": "cooking", "chopping": "cooking", "stove-burner": "cooking", "peel": "cooking",
       "clean-dishes": "dishwashing", "water-flowing": "dishwashing", "eat": "eating",
       "book": "other", "cupboard": "other", "drawer": "other", "fridge": "other", "microwave": "other", "sweep": "other",
       "stove-fan": "other", "dishwasher": "other", "juicer": "other", "blender": "other"}   # cutlery, plates: ambiguous, left out
THETA = None


def event(t, probs, novel, a, evidence: bool) -> dict:
    w = witness.opinion(a)
    if not evidence:
        w = {k: w[k] for k in ("k", "family", "v")}            # the old event shape -> the old rule
    return {"start": t, "end": t + 10, "label": "other", "conf": 0.0, "probs": dict(zip(CLASSES, map(float, probs))),
            "novel": bool(novel), "sounds": [], "w": w}


def shown(evs: list[dict]) -> str | None:
    """The activity covering most windows of this stretch of audio, or None if no activity block."""
    cover = Counter()
    for b in timeline.blocks(evs, THETA):
        if b["state"] == "activity":
            cover[b["activity"]] += b["n_windows"]
    return cover.most_common(1)[0][0] if cover else None


def score(items: list[tuple[str, list]], evidence: bool) -> dict:
    """items: (truth, [(probs, novel, audioset)...]). truth in MEAL, 'other' or 'dishes' (DESED dish clatter: ambiguous)."""
    c = Counter()
    for truth, wins in items:
        p = shown([event(10 * i, *x, evidence) for i, x in enumerate(wins)])
        if truth == "dishes":
            c["dishes"] += 1
            c["dishes_called_washing_or_eating"] += p in ("dishwashing", "eating")
            c["dishes_called_cooking"] += p == "cooking"
            c["dishes_called_kitchen"] += p == "kitchen"
        elif truth in MEAL:
            c["meal"] += 1
            c["right"] += p == truth
            c["wrong_activity"] += p in MEAL and p != truth
            c["kitchen_unnamed"] += p == "kitchen"
        else:
            c["not_meal"] += 1
            c["false_kitchen"] += p in MEAL | {"kitchen"}
    return dict(c)


def sets() -> dict:
    global THETA
    head = model.load(ROOT / "models" / "head.json")
    THETA = head["theta"]
    out: dict = {}
    # SINS dev sessions
    o = np.load(RESULTS / "cache" / "oof_dev.npz", allow_pickle=True)
    d = np.load(RESULTS / "cache" / "ced-tiny_dev.npz", allow_pickle=True)
    pos = {str(f): i for i, f in enumerate(d["files"])}
    idx = np.array([pos[str(f)] for f in o["files"]])
    A = d["scores"][idx, 0].astype(np.float32)
    nov = model.novelty(head, d["emb"][idx, 0].astype(np.float32)) > head["novelty"]["threshold"]
    sess = defaultdict(list)
    for i, f in enumerate(o["files"]):
        m = re.match(r"(DevNode\d+_ex\d+)_(\d+)", str(f))
        sess[m.group(1)].append((int(m.group(2)), i))
    items = []
    for v in sess.values():
        v.sort()
        y = CLASSES[int(o["y"][v[0][1]])]
        items.append((y if y in MEAL else "other", [(o["P0"][i], nov[i], A[i]) for _, i in v]))
    out["sins_dev_sessions"] = items
    # Kitchen20
    q = np.load(EMB / "kitchen20" / "all.npz", allow_pickle=True)
    P, nk = model.predict_proba(head, q["emb"]), model.novelty(head, q["emb"]) > head["novelty"]["threshold"]
    for h in ("tune", "test"):
        out[f"kitchen20_{h}"] = [(K20[str(c)], [(P[i], nk[i], q["audioset"][i])]) for i, c in enumerate(q["category"])
                                 if str(c) in K20 and half(str(q["source"][i])) == h]
    # DESED
    z = np.load(EMB / "desed" / "public_eval.npz", allow_pickle=True)
    up, ev, aset = _desed_groups()
    Pd, nd = model.predict_proba(head, z["emb"]), model.novelty(head, z["emb"]) > head["novelty"]["threshold"]
    for h in ("tune", "test"):
        rows = []
        for i, f in enumerate(z["files"]):
            f = str(f)
            g = up.get(f, f.rsplit("_", 2)[0])
            if f.rsplit("_", 2)[0] in aset or half(g) != h:
                continue
            E = ev.get(f, {})
            k, m = desed_kind(E), main_sound(E)
            t = "cooking" if (k == "kitchen" and m == "Frying") else "dishes" if (k == "kitchen" and m == "Dishes") else \
                "other" if k in ("vacuum", "shaver", "pets_alarms", "speech") else None
            if t:
                rows.append((t, [(Pd[i], nd[i], z["audioset"][i])]))
        out[f"desed_{h}"] = rows
    return out


def main(argv=None) -> int:
    import sys
    S = sets()
    if "--dev" in (argv if argv is not None else sys.argv[1:]):      # development sets only; TEST halves untouched
        for name, items in S.items():
            if not name.endswith("_test"):
                print(f"{name:18s} before {score(items, False)}\n{'':18s} after  {score(items, True)}")
        return 0
    R = {"what": __doc__.split("\n\n")[0], "process": __doc__.split("Process note: ")[1].split("\n\n")[0].replace("\n", " "),
         "thresholds": {k: witness.CFG[k] for k in ("tau_cook", "tau_water", "tau_mouth", "cook_share")},
         "sets": {name: {"n": len(items), "before": score(items, False), "after": score(items, True)} for name, items in S.items()}}
    prev = RESULTS / "kitchen_naming.json"
    if prev.exists() and "first_test_run" in json.loads(prev.read_text()):
        R["first_test_run"] = json.loads(prev.read_text())["first_test_run"]
    prev.write_text(json.dumps(R, indent=1) + "\n")
    for name, r in R["sets"].items():
        print(f"{name:18s} before {r['before']}\n{'':18s} after  {r['after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
