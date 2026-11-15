"""Rule 2g: fewer "Not sure" windows, from the trained sound head (eval/sound_head.py, 8 names that passed the bar).

A window the activity head can't name ("Not sure", including "unlike anything it learned") is named from a SHOWN sound the
trained head heard in it (precision >= 90% on held-out halves):
  kettle, chopping, running water  ->  "kitchen" (then rule 2c names the stretch from evidence across its windows)
  typing                           ->  working ("Typing")
  talking / TV                     ->  watching_tv ("Talking / TV")
Cupboards, footsteps and the timer beep don't name an activity (they happen during everything).

Gate, written before the first run (development sets only, same harness and metrics as eval/confetti.py):
  ship if, on BOTH SINS dev and the Kitchen20 tune half,
    sessions caught does not drop, and false activity blocks per hour rise by at most 0.5,
  and on at least one of them the "Not sure" share drops by 10 points or more.
Then ONE run on the Kitchen20 test half (by uploader), reported whatever it says. That half was used before by
eval/kitchen_naming.py; nothing here was chosen with it.

    python -m eval.sound_fill            -> results/sound_fill.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from eval import confetti
from kettle import kinds, model, timeline, witness
from kettle.labels import CLASSES

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results" / "cache"
OUT = ROOT / "results" / "sound_fill.json"
FILL = {"kettle": "kitchen", "chopping": "kitchen", "tap": "kitchen", "typing": "working", "tv": "watching_tv"}
GATE = {"min_not_sure_drop_pts": 10.0, "max_false_blocks_rise_per_h": 0.5}


def sins_days(seed: int = 0) -> list:
    """confetti.days with each window's named sounds from the trained head (needs the embedding)."""
    D = confetti.days(seed)
    o, d = np.load(CACHE / "oof_dev.npz"), np.load(CACHE / "ced-tiny_dev.npz")
    pos = {str(f): i for i, f in enumerate(d["files"])}
    ix = np.array([pos[str(f)] for f in o["files"]])
    E, A = d["emb"][ix, 0].astype(np.float64), o["scores"].astype(np.float64)
    seg = np.array([int(str(f).rsplit("_", 1)[1]) for f in o["files"]])
    rng = np.random.default_rng(seed)
    out = []
    for k, (events, truth) in zip((1, 2, 3, 4), D):          # same order as confetti.days: rebuild the window index per fold
        idx = np.where(o["fold"] == k)[0]
        sess = sorted(set(o["session"][idx].tolist()))
        rng.shuffle(sess)
        order = []
        for s in sess:
            ii = idx[o["session"][idx] == s]
            order += list(ii[np.argsort(seg[ii])])
        assert len(order) == len(events)
        for e, i in zip(events, order):
            e["kinds"] = [x["id"] for x in kinds.named(A[i], emb=E[i])]
        out.append((events, truth))
    return out


def k20(part: str, seed: int = 0, per: int = 6) -> list:
    """confetti.k20_days for one half, named sounds from the trained head."""
    from eval.other_homes import EMB, half
    head = model.load(ROOT / "models" / "head.json")
    q = np.load(EMB / "kitchen20" / "all.npz", allow_pickle=True)
    P, nov = model.predict_proba(head, q["emb"]), model.novelty(head, q["emb"]) > head["novelty"]["threshold"]
    rng = np.random.default_rng(seed)
    by: dict = {}
    for i, c in enumerate(q["category"]):
        if str(c) in confetti.K20 and half(str(q["source"][i])) == part:
            by.setdefault(str(c), []).append(i)
    sessions = []
    for c, ii in by.items():
        rng.shuffle(ii)
        sessions += [(confetti.K20[c], ii[j:j + per]) for j in range(0, len(ii) - per + 1, per)]
    rng.shuffle(sessions)
    events, truth, t = [], [], 0.0
    for act, ii in sessions:
        a = t
        for i in ii:
            pr = {c: float(v) for c, v in zip(CLASSES, P[i])}
            A = q["audioset"][i].astype(np.float64)
            events.append({"start": t, "end": t + 10, "probs": pr, "novel": bool(nov[i]), "sounds": [], "conf": max(pr.values()),
                           "w": witness.opinion(A), "kinds": [x["id"] for x in kinds.named(A, emb=q["emb"][i].astype(np.float64))]})
            t += 10
        truth.append((a, t, act))
    return [(events, truth)]


_raw = timeline.raw_label


def install(on: bool) -> None:
    """Rule 2g wraps kettle/timeline.raw_label (the app's twin is core.js rawLabel)."""
    def raw_label(ev, theta):
        lab = _raw(ev, theta)
        if on and lab == "not_sure":
            for k in ev.get("kinds") or []:
                if k in FILL:
                    return FILL[k]
        return lab
    timeline.raw_label = raw_label if on else _raw


def run(sets: dict, theta: float) -> dict:
    R = {}
    try:
        for name, on in (("shipped", False), ("+2g sound fill", True)):
            install(on)
            R[name] = {}
            for sname, D in sets.items():
                R[name][sname] = v = confetti.score(D, theta)
                print(f"{sname:15s} {name:16s} caught {v['caught_one_activity_half']}/{v['sessions']} ({v['caught_pct']}%)  pieces/session "
                      f"{v['pieces_per_session']}  not sure {v['not_sure_share_pct']}%  false blocks/h {v['false_activity_blocks_per_hour']}")
    finally:
        install(False)
    return R


def gate(R: dict) -> dict:
    a, b = R["shipped"], R["+2g sound fill"]
    no_loss = all(b[s]["caught_one_activity_half"] >= a[s]["caught_one_activity_half"] for s in a)
    fa_ok = all(b[s]["false_activity_blocks_per_hour"] - a[s]["false_activity_blocks_per_hour"] <= GATE["max_false_blocks_rise_per_h"] for s in a)
    drop = max(a[s]["not_sure_share_pct"] - b[s]["not_sure_share_pct"] for s in a)
    return {"caught_no_drop": no_loss, "false_blocks_ok": fa_ok, "best_not_sure_drop_pts": round(drop, 1),
            "pass": bool(no_loss and fa_ok and drop >= GATE["min_not_sure_drop_pts"])}


def main() -> None:
    theta = model.load(ROOT / "models" / "head.json")["theta"]
    dev = run({"sins_dev": sins_days(), "kitchen20_tune": k20("tune")}, theta)
    g = gate(dev)
    print("gate:", g)
    R = {"about": __doc__.split("\n\n")[0], "rule": FILL, "gate": GATE, "dev": dev, "dev_gate": g}
    if g["pass"]:
        R["test"] = run({"kitchen20_test": k20("test")}, theta)
        R["test_note"] = "One run on the Kitchen20 test half after the dev gate passed; that half was used before by eval/kitchen_naming.py."
    R["decision"] = "shipped (core.js rawLabel, kettle/timeline.raw_label)" if g["pass"] else "not shipped: failed the dev gate"
    OUT.write_text(json.dumps(R, indent=1) + "\n")


if __name__ == "__main__":
    main()
