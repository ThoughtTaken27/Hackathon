"""Named everyday sounds: precision and recall before vs after the context rules (handover v3.2, 3.1).

Pre-registered in eval/PREREGISTER-SOUNDS.md (bar: precision >= 90% and recall >= 40% on the TEST halves, else hidden).
Same decision as the app: kettle/kinds.py named() / web/public/js/sense.js kindsOf(), vectorised here, with the privacy veto.

  before = results/cache/kinds_before_v32.json (the rules shipped at 05bf6ea)
  after  = web/public/model/kinds.json (written by eval/beyond.py from KINDS + CONTEXT)

Data (all CED-tiny AudioSet scores, 10-s windows): Kitchen20 (data/emb/ced-tiny/kitchen20/all.npz, made like
eval/other_homes.py fetch()), ESC-50 all 2,000 clips, SINS dev 8,920 windows, 960 synthetic alarms, 725 Nonspeech7k body sounds.

Run: python -m eval.beyond && python -m eval.sounds && python -m eval.beyond   (the second beyond run writes shown: true/false)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from eval.beyond import rate
from eval.other_homes import half
from kettle.labels import CLASSES

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results" / "cache"
OUT = ROOT / "results" / "sounds.json"
BAR = {"precision": 90.0, "recall": 40.0}

# Positives: windows that contain the sound. Ambiguous: may or may not contain it (left out). Everything else is a negative.
POS = {
    "kettle": ["k20:boiling-water"],
    "frying": ["k20:frying-pan"],
    "chopping": ["k20:chopping"],
    "blender": ["k20:blender"],
    "microwave": ["k20:microwave"],
    "dishes": ["k20:plates", "k20:cutlery", "k20:clean-dishes"],
    "tap": ["k20:water-flowing", "k20:clean-dishes"],
    "cupboard": ["k20:cupboard", "k20:drawer"],
    "door": ["esc:door_wood_creaks"],
    "alarm": ["esc:clock_alarm", "syn:timer"],
    "tv": ["sins:watching_tv"],
    "vacuum": ["esc:vacuum_cleaner", "sins:vacuum_cleaner"],
    "typing": ["esc:keyboard_typing", "sins:working"],
    "footsteps": ["esc:footsteps"],
    "glass": ["esc:glass_breaking"],
}
SINS_KITCHEN = ["sins:cooking", "sins:dishwashing", "sins:eating", "sins:other"]
AMBIG = {
    "kettle": ["k20:stove-burner"] + SINS_KITCHEN,
    "frying": ["k20:stove-burner", "k20:peel"] + SINS_KITCHEN,
    "chopping": ["k20:peel"] + SINS_KITCHEN,
    "blender": ["k20:juicer"],
    "microwave": [],
    "dishes": ["k20:eat", "k20:dishwasher", "k20:frying-pan", "k20:stove-burner", "esc:can_opening"] + SINS_KITCHEN,
    "tap": ["k20:dishwasher", "esc:pouring_water", "esc:water_drops"] + SINS_KITCHEN,
    "cupboard": ["k20:fridge"] + SINS_KITCHEN,
    "door": ["esc:door_wood_knock", "k20:cupboard", "k20:fridge", "k20:drawer"] + SINS_KITCHEN,
    "alarm": ["k20:microwave", "k20:dishwasher"],
    "tv": ["sins:social_activity"],
    "vacuum": [],
    "typing": ["esc:mouse_click"],
    "footsteps": ["sins:other", "k20:sweep"],
    "glass": ["k20:plates"],
}


def data() -> dict:
    """{name: (S [N,527], label per window, 'tune'/'test' per window)}."""
    out = {}
    k = np.load(ROOT / "data" / "emb" / "ced-tiny" / "kitchen20" / "all.npz")
    out["kitchen20"] = (k["audioset"].astype(np.float64), np.char.add("k20:", k["category"]), np.array([half(s) for s in k["source"]]))
    e = np.load(CACHE / "ced-tiny_esc50all.npz")
    src = [f.rsplit("_", 1)[-1].split("-")[1] for f in e["files"]]
    out["esc50"] = (e["scores"].astype(np.float64), np.char.add("esc:", e["category"]), np.array([half(s) for s in src]))
    o = np.load(CACHE / "oof_dev.npz")
    out["sins_dev"] = (o["scores"].astype(np.float64), np.array(["sins:" + CLASSES[y] for y in o["y"]]),
                       np.where(np.isin(o["fold"], [1, 2]), "tune", "test"))
    a = np.load(CACHE / "ced-tiny_synth_alarms.npz")
    out["synth_alarms"] = (a["scores"].astype(np.float64), np.char.add("syn:", a["kind"]), np.where(a["seed"] % 2 == 0, "tune", "test"))
    n = np.load(CACHE / "ced-tiny_nonspeech7k.npz")
    out["nonspeech7k"] = (n["scores"].astype(np.float64), np.char.add("ns7k:", n["category"]), np.array([half(f) for f in n["files"]]))
    return out


def fired(cfg: dict, S: np.ndarray) -> dict:
    """{kind id: bool [N]} after thresholds, context rules and the privacy veto (kettle/kinds.py named(), vectorised)."""
    raw, score = {}, {}
    for k in cfg["kinds"]:
        s = S[:, k["index"]].max(1)
        ok = (s >= k["tau"]) & (s >= k.get("min", 0))
        if k.get("beat"):
            ok &= s > S[:, k["beat"]].max(1)
        raw[k["id"]], score[k["id"]] = ok, np.where(ok, s, 0)
    top = np.stack(list(score.values()), 1).max(1)
    vetoed = S[:, cfg["veto"]].max(1) >= top
    return {i: v & ~vetoed for i, v in raw.items()}


def measure(cfg: dict, D: dict, part: str) -> dict:
    lab = np.concatenate([D[n][1][D[n][2] == part] for n in D])
    F = [fired(cfg, D[n][0][D[n][2] == part]) for n in D]
    out = {}
    for k in POS:
        f = np.concatenate([x[k] for x in F])
        pos, amb = np.isin(lab, POS[k]), np.isin(lab, AMBIG[k])
        neg = ~pos & ~amb
        tp, fp = int(f[pos].sum()), int(f[neg].sum())
        worst = {}
        for c in np.unique(lab[neg & f]):
            worst[str(c)] = int((f & (lab == c)).sum())
        out[k] = {"recall": rate(f[pos]), "false_per_1000": round(1000 * fp / max(1, int(neg.sum())), 2), "false_k": fp, "neg_n": int(neg.sum()),
                  "precision": rate(np.r_[np.ones(tp, bool), np.zeros(fp, bool)]),
                  "top_false": dict(sorted(worst.items(), key=lambda kv: -kv[1])[:5])}
    return out


def main() -> None:
    D = data()
    before = json.loads((CACHE / "kinds_before_v32.json").read_text())
    after = json.loads((ROOT / "web" / "public" / "model" / "kinds.json").read_text())
    R = {"about": __doc__.split("\n\n")[0], "prereg": "eval/PREREGISTER-SOUNDS.md", "bar": BAR,
         "n_windows": {n: {"tune": int((v[2] == "tune").sum()), "test": int((v[2] == "test").sum())} for n, v in D.items()},
         "tune": {"before": measure(before, D, "tune"), "after": measure(after, D, "tune")}}
    test_before, test_after = measure(before, D, "test"), measure(after, D, "test")
    for k, v in test_after.items():
        p, r = v["precision"]["pct"], v["recall"]["pct"]
        v["shown"] = bool(p is not None and r is not None and p >= BAR["precision"] and r >= BAR["recall"])
    R["before"], R["after"] = test_before, test_after
    OUT.write_text(json.dumps(R, indent=1))
    for k in POS:
        b, a = test_before[k], test_after[k]
        print(f"{k:10s} recall {b['recall']['pct']}->{a['recall']['pct']} (n={a['recall']['n']})  precision {b['precision']['pct']}->{a['precision']['pct']}"
              f"  false/1000 {b['false_per_1000']}->{a['false_per_1000']}  shown={a['shown']}  top_false={a['top_false']}")


if __name__ == "__main__":
    main()
