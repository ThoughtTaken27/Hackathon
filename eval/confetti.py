"""Fewer "Not sure" gaps and broken-up blocks (handover v3.2, 3.3): candidate rules 2e and 2f measured through the app's timeline.
Result (Sun Nov 15): neither moved the dev numbers enough to ship (results/confetti.json); they are applied here only, by wrapping
kettle/timeline.raw_label and bridge, so the app's code is unchanged.

  2e  inside a kitchen stretch, a short gap (<= 30 s) of "unlike anything it learned" windows that all carry kitchen tags
      (second opinion k >= TAU_K) is bridged, like rule 2b already does for ordinary unsure windows.
  2f  a window the head can't name, whose device named "TV or radio" (the one sound that passed results/sounds.json), is TV.

Set: SINS dev, all 4 folds (8,920 windows, 257 sessions, out-of-fold head scores), stitched into one continuous day per fold
as in eval/dev.py session_level (sessions in a seeded random order), each window carrying the fields the device sends:
novelty flag, second-opinion numbers (kettle/witness.py) and named sounds (kettle/kinds.py). Development data only: there is
no held-out continuous recording on this machine; the clean test is the team's own kitchen (eval/own_kitchen.py).

    python -m eval.confetti      writes results/confetti.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from kettle import kinds, model, timeline, witness
from kettle.labels import CLASSES, MEAL

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results" / "cache"
OUT = ROOT / "results" / "confetti.json"
VARIANTS = {"shipped (2b-2d)": (False, False), "+2e bridge novel kitchen gaps": (True, False), "+2f TV": (False, True),
            "+2e +2f": (True, True)}


def days(seed: int = 0) -> list[tuple[list[dict], list[tuple]]]:
    """Per fold: (events, truth sessions [(start, end, activity)])."""
    head = model.load(ROOT / "models" / "head.json")
    o = np.load(CACHE / "oof_dev.npz")
    d = np.load(CACHE / "ced-tiny_dev.npz")
    pos = {str(f): i for i, f in enumerate(d["files"])}
    ix = np.array([pos[str(f)] for f in o["files"]])
    nov = model.novelty(head, d["emb"][ix, 0].astype(np.float32)) > head["novelty"]["threshold"]
    A = o["scores"].astype(np.float32)
    seg = np.array([int(str(f).rsplit("_", 1)[1]) for f in o["files"]])
    rng = np.random.default_rng(seed)
    out = []
    for k in (1, 2, 3, 4):
        idx = np.where(o["fold"] == k)[0]
        sess = sorted(set(o["session"][idx].tolist()))
        rng.shuffle(sess)
        events, truth, t = [], [], 0.0
        for s in sess:
            ii = idx[o["session"][idx] == s]
            ii = ii[np.argsort(seg[ii])]
            a = t
            for i in ii:
                pr = {c: float(v) for c, v in zip(CLASSES, o["P0"][i])}
                events.append({"start": t, "end": t + 10, "probs": pr, "novel": bool(nov[i]), "sounds": [],
                               "conf": max(pr.values()), "w": witness.opinion(A[i]), "kinds": [x["id"] for x in kinds.named(A[i])]})
                t += 10
            truth.append((a, t, CLASSES[int(o["y"][ii[0]])]))
        out.append((events, truth))
    return out


K20 = {"frying-pan": "cooking", "boiling-water": "cooking", "chopping": "cooking", "stove-burner": "cooking", "peel": "cooking",
       "clean-dishes": "dishwashing", "water-flowing": "dishwashing", "eat": "eating", "book": "other", "cupboard": "other",
       "drawer": "other", "fridge": "other", "microwave": "other", "sweep": "other", "stove-fan": "other", "dishwasher": "other",
       "juicer": "other", "blender": "other"}         # as eval/kitchen_naming.py; cutlery and plates are ambiguous, left out


def k20_days(seed: int = 0, per: int = 6) -> list[tuple[list[dict], list[tuple]]]:
    """Kitchen20 TUNE half (by uploader): clips of one category stitched into sessions of `per` windows, sessions shuffled.
    Many uploaders and microphones: most windows are 'unlike anything it learned', the case behind the live confetti."""
    from eval.other_homes import EMB, half
    head = model.load(ROOT / "models" / "head.json")
    q = np.load(EMB / "kitchen20" / "all.npz", allow_pickle=True)
    P, nov = model.predict_proba(head, q["emb"]), model.novelty(head, q["emb"]) > head["novelty"]["threshold"]
    rng = np.random.default_rng(seed)
    by = {}
    for i, c in enumerate(q["category"]):
        if str(c) in K20 and half(str(q["source"][i])) == "tune":
            by.setdefault(str(c), []).append(i)
    sessions = []
    for c, ii in by.items():
        rng.shuffle(ii)
        sessions += [(K20[c], ii[j:j + per]) for j in range(0, len(ii) - per + 1, per)]
    rng.shuffle(sessions)
    events, truth, t = [], [], 0.0
    for act, ii in sessions:
        a = t
        for i in ii:
            pr = {c: float(v) for c, v in zip(CLASSES, P[i])}
            A = q["audioset"][i]
            events.append({"start": t, "end": t + 10, "probs": pr, "novel": bool(nov[i]), "sounds": [], "conf": max(pr.values()),
                           "w": witness.opinion(A), "kinds": [x["id"] for x in kinds.named(A)]})
            t += 10
        truth.append((a, t, act))
    return [(events, truth)]


def score(D, theta: float) -> dict:
    caught = total = frag = fa = 0
    ns_time = heard_time = hours = 0.0
    per = {}
    for events, truth in D:
        blks = timeline.blocks(events, theta, gap_s=1)
        hours += events[-1]["end"] / 3600
        acts = [b for b in blks if b["state"] in ("activity", "empty") and b["activity"]]
        for b in blks:
            if b["state"] in ("activity", "empty", "not_sure", "talk_or_tv"):
                heard_time += b["end"] - b["start"]
                ns_time += (b["end"] - b["start"]) * (b["state"] == "not_sure")
        for a, z, c in truth:
            if c == "absence":
                continue
            ok = [b for b in acts if (b["activity"] == c or (c in MEAL and b["activity"] == "kitchen")) and min(z, b["end"]) > max(a, b["start"])]
            hit = sum(min(z, b["end"]) - max(a, b["start"]) for b in ok if b["activity"] == c) >= 0.5 * (z - a)
            inside = [b for b in blks if b["state"] != "empty" and min(z, b["end"]) - max(a, b["start"]) > 0]
            total += 1
            caught += hit
            frag += len(inside)
            p = per.setdefault(c, [0, 0, 0])
            p[0] += 1; p[1] += hit; p[2] += len(inside)
        for b in acts:
            if b["activity"] == "absence":
                continue
            ins = sum(max(0.0, min(z, b["end"]) - max(a, b["start"])) for a, z, c in truth
                      if c == b["activity"] or (b["activity"] == "kitchen" and c in MEAL))
            fa += ins < 0.5 * (b["end"] - b["start"])
    return {"sessions": total, "caught_one_activity_half": caught, "caught_pct": round(100 * caught / total, 1),
            "pieces_per_session": round(frag / total, 2), "not_sure_share_pct": round(100 * ns_time / heard_time, 1),
            "false_activity_blocks_per_hour": round(fa / hours, 2), "hours": round(hours, 2),
            "per_activity": {c: {"sessions": v[0], "caught": v[1], "pieces_per_session": round(v[2] / v[0], 2)} for c, v in sorted(per.items())}}


_raw, _bridge = timeline.raw_label, timeline.bridge


def variant(bridge_novel_kitchen: bool, tv: bool) -> None:
    """Install (or remove) the candidate rules by wrapping the app's own functions."""
    def raw_label(ev, theta):
        lab = _raw(ev, theta)
        if tv and lab == "not_sure" and "tv" in (ev.get("kinds") or []):
            return "watching_tv"                       # 2f
        return lab

    def bridge(labels, run, max_s=timeline.BRIDGE_S):
        """kettle/timeline.bridge (rule 2b) with candidate 2e: inside a kitchen stretch, novel windows with kitchen tags may be bridged."""
        if not bridge_novel_kitchen:
            return _bridge(labels, run, max_s)
        out, i = list(labels), 1
        while i < len(out):
            if out[i] != "not_sure":
                i += 1
                continue
            j = i
            while j + 1 < len(out) and out[j + 1] == "not_sure":
                j += 1
            before, after = out[i - 1], out[j + 1] if j + 1 < len(out) else None
            short = run[j]["end"] - run[i - 1]["end"] <= max_s
            kitchen_ok = before in MEAL
            novel = any(run[k].get("novel") and not (kitchen_ok and (run[k].get("w") or {}).get("k", 0) >= witness.TAU_K) for k in range(i, j + 1))
            if before == after and before not in ("not_sure", "talk_or_tv") and short and not novel:
                out[i:j + 1] = [before] * (j - i + 1)
            i = j + 1
        return out
    timeline.raw_label, timeline.bridge = raw_label, bridge


def main() -> None:
    theta = model.load(ROOT / "models" / "head.json")["theta"]
    sets = {"sins_dev": days(), "kitchen20_tune": k20_days()}
    R = {"about": __doc__.split("\n\n")[0], "sets": {"sins_dev": "SINS dev, 4 folds stitched (development data)",
         "kitchen20_tune": "Kitchen20 TUNE half by uploader, 6-clip sessions per category, stitched (development data)"},
         "decision": "not shipped: no gain on either development set", "variants": {}}
    try:
        for name, (e, f) in VARIANTS.items():
            variant(e, f)
            R["variants"][name] = {}
            for sname, D in sets.items():
                R["variants"][name][sname] = v = score(D, theta)
                print(f"{sname:15s} {name:32s} caught {v['caught_one_activity_half']}/{v['sessions']} ({v['caught_pct']}%)  pieces/session "
                      f"{v['pieces_per_session']}  not sure {v['not_sure_share_pct']}%  false blocks/h {v['false_activity_blocks_per_hour']}")
    finally:
        timeline.raw_label, timeline.bridge = _raw, _bridge
    OUT.write_text(json.dumps(R, indent=1) + "\n")


if __name__ == "__main__":
    main()
