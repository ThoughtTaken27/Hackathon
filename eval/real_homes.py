"""Real homes, scored once: TUT Sound Events 2016 "home" recordings (kitchens and living rooms in different homes).

Why: we have no recording of our own kitchen yet (handover v3.3 §4). TUT-SED 2016 (Mesaros, Heittola, Virtanen; Tampere
University of Technology, Zenodo 10.5281/zenodo.45759) has 10 real home recordings, 3-5 minutes each, with every sound event
annotated by the dataset authors, not by us. Nothing in Kettle was tuned on it. This file is the whole test, decided before the
first run (Sun Nov 15, ~4:40 PM CT), and it is reported whatever it says.

What runs: the app's own pipeline in Python (kettle/*), on 10-second windows with a 10-second hop (as the device does):
frozen encoder -> frozen head + novelty -> second opinion -> named sounds (trained sound head, kettle/kinds.py) -> the app's
timeline (kettle/timeline.blocks: smoothing, rules 2b-2d).

What counts (fixed now):
- A sound event is IN a window if it overlaps the window by >= 0.5 s.
- Named sounds, per sound with annotations here:
    tap       <- "water tap running"
    dishes    <- "dishes", "cutlery", "washing dishes"
    cupboard  <- "cupboard", "drawer"
    footsteps <- "people walking"
  precision = named windows that contain the sound / named windows; recall = windows with the sound that were named.
  Shown names (passed the bar) and hidden names (device-only) are reported separately; only shown names reach families.
- Activity: a window is "washing up" truth if "washing dishes" or "water tap running" covers >= 3 s of it. We report what the
  app's timeline called those windows (washing up, kitchen activity, cooking, eating, not sure, other) and, for windows with
  no kitchen event at all, how often the timeline named a kitchen activity anyway.
Wilson 95% intervals; N with every number. Small N: 10 recordings, ~40 minutes.

    python -m eval.real_homes        -> results/real_homes.json     (needs data/raw/tut2016, see docs/DATA-SOURCES.md)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf

from eval.beyond import rate
from kettle import encoders, kinds, model, timeline, witness
from kettle.audio import to_16k_mono
from kettle.labels import CLASSES, MEAL

ROOT = Path(__file__).resolve().parents[1]
TUT = ROOT / "data" / "raw" / "tut2016" / "TUT-sound-events-2016-development"
OUT = ROOT / "results" / "real_homes.json"
WIN, SR = 10.0, 16000
SOUNDS = {"tap": ["water tap running"], "dishes": ["dishes", "cutlery", "washing dishes"], "cupboard": ["cupboard", "drawer"],
          "footsteps": ["people walking"]}
WASH = ["washing dishes", "water tap running"]
KITCHEN_EVENTS = {"dishes", "cutlery", "washing dishes", "water tap running", "cupboard", "drawer", "glass jingling"}


def recordings() -> list[tuple[str, np.ndarray, list[tuple[float, float, str]]]]:
    out = []
    for wav in sorted((TUT / "audio" / "home").glob("*.wav")):
        x, sr = sf.read(wav, dtype="float32", always_2d=True)
        ann = [(float(a), float(b), c.strip()) for a, b, c in (l.split("\t")[:3] for l in (TUT / "meta" / "home" / f"{wav.stem}.ann").read_text().splitlines() if l.strip())]
        out.append((wav.stem, to_16k_mono(x.T, sr), ann))
    return out


def overlap(a0, a1, b0, b1) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def main() -> None:
    enc, head = encoders.load(), model.load(ROOT / "models" / "head.json")
    theta = head["theta"]
    rows, per_rec = [], {}
    for name, wave, ann in recordings():
        n = int(len(wave) // (WIN * SR))
        if not n:
            continue
        W = np.stack([wave[int(i * WIN * SR):int((i + 1) * WIN * SR)] for i in range(n)])
        E, A = [], []
        for i in range(0, n, 16):
            e, a = encoders.embed(enc, W[i:i + 16])
            E.append(e); A.append(a)
        E, A = np.concatenate(E).astype(np.float64), np.concatenate(A).astype(np.float64)
        P, nov = model.predict_proba(head, E.astype(np.float32)), model.novelty(head, E.astype(np.float32)) > head["novelty"]["threshold"]
        events = []
        for i in range(n):
            pr = {c: float(v) for c, v in zip(CLASSES, P[i])}
            events.append({"start": i * WIN, "end": (i + 1) * WIN, "probs": pr, "novel": bool(nov[i]), "sounds": [], "conf": max(pr.values()),
                           "w": witness.opinion(A[i]), "kinds": [k["id"] for k in kinds.named(A[i], emb=E[i])]})
        blks = timeline.blocks(events, theta, gap_s=1)
        for i, ev in enumerate(events):
            t0, t1 = ev["start"], ev["end"]
            inside = {c for a, b, c in ann if overlap(a, b, t0, t1) >= 0.5}
            wash_s = sum(overlap(a, b, t0, t1) for a, b, c in ann if c in WASH)
            mid = (t0 + t1) / 2
            blk = next((b for b in blks if b["start"] <= mid < b["end"]), None)
            lab = "not_sure" if blk is None else (blk["state"] if blk["state"] != "activity" else blk["activity"])
            named_all = kinds.named(A[i], emb=E[i], with_hidden=True)
            rows.append({"rec": name, "t": t0, "events": sorted(inside), "wash": wash_s >= 3.0, "label": lab,
                         "shown": ev["kinds"], "all": [k["id"] for k in named_all]})
        per_rec[name] = {"windows": n, "minutes": round(len(wave) / SR / 60, 2)}
    R = {"about": __doc__.split("\n\n")[0], "source": "TUT Sound Events 2016, development set, home (Zenodo 10.5281/zenodo.45759)",
         "recordings": per_rec, "n_windows": len(rows), "sounds": {}, "activity": {}}
    shown_ids = {k["id"] for k in kinds.CFG["kinds"] if k.get("shown")}
    for k, evs in SOUNDS.items():
        has = np.array([bool(set(r["events"]) & set(evs)) for r in rows])
        named = np.array([k in r["all"] for r in rows])
        R["sounds"][k] = {"shown_to_families": k in shown_ids, "windows_with_sound": int(has.sum()),
                          "recall": rate(named[has]), "precision": rate(has[named]),
                          "false_named_windows": int((named & ~has).sum())}
    wash = [r for r in rows if r["wash"]]
    calls = {}
    for r in wash:
        calls[r["label"]] = calls.get(r["label"], 0) + 1
    clean = [r for r in rows if not (set(r["events"]) & KITCHEN_EVENTS)]
    R["activity"] = {"washing_windows": len(wash), "called": dict(sorted(calls.items(), key=lambda kv: -kv[1])),
                     "named_washing_up": rate(np.array([r["label"] == "dishwashing" for r in wash])),
                     "named_any_kitchen_activity": rate(np.array([r["label"] in MEAL or r["label"] == "kitchen" for r in wash])),
                     "not_sure": rate(np.array([r["label"] == "not_sure" for r in wash])),
                     "windows_without_kitchen_events": len(clean),
                     "kitchen_activity_named_anyway": rate(np.array([r["label"] in MEAL or r["label"] == "kitchen" for r in clean]))}
    R["rows"] = rows
    OUT.write_text(json.dumps(R, indent=1) + "\n")
    print(json.dumps({k: v for k, v in R.items() if k not in ("rows",)}, indent=1))


if __name__ == "__main__":
    main()
