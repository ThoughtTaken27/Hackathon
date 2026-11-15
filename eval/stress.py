"""Stress tests: what happens when the kitchen is quieter (the device is across the room) or a TV is on underneath?

    python -m eval.stress          (~10 min on a laptop CPU; writes results/stress.json and results/stress.md)

Two clip sets, both scored with the shipped rule (head + second opinion, kettle/timeline.raw_label), one 10-s window each:
- research home: a seeded sample of SINS dev kitchen clips (cooking, washing up, eating), channel 0. The head was trained on
  these sessions, so the 0 dB row is optimistic; read the DROP from it, not the level.
- other homes: every DESED public-eval clip whose main sound is frying or dishes (both halves; AudioSet-overlap clips dropped).
Conditions: the clip turned down by 6, 12, 18 and 24 dB; and a SINS dev TV clip mixed underneath so the kitchen sound is
10, 5, 0 and -5 dB relative to the TV (levels by RMS). Nothing is tuned here; it is a description of where the rule breaks.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from eval.other_homes import PRED, RAW
from kettle import encoders, model, timeline, witness
from kettle.audio import to_16k_mono
from kettle.labels import CLASSES, MEAL

ROOT = Path(__file__).resolve().parents[1]
GAINS_DB = [0, -6, -12, -18, -24]
TV_SNR_DB = [10, 5, 0, -5]
PER_CLASS = 100
SEED = 20261114


def load16(path: Path, channel: int | None = 0) -> np.ndarray:
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    m = to_16k_mono(x.T, sr, channel)[:160000]
    return np.pad(m, (0, 160000 - len(m)))


def rms(x: np.ndarray) -> float:
    return float(np.sqrt((x ** 2).mean()) + 1e-9)


def score(enc, head, waves: np.ndarray) -> np.ndarray:
    """[B, samples] -> True where the shipped rule shows a kitchen activity."""
    out = []
    for i in range(0, len(waves), 16):
        emb, tags = encoders.embed(enc, waves[i:i + 16])
        P = model.predict_proba(head, emb)
        nov = model.novelty(head, emb) > head["novelty"]["threshold"]
        for p, n, a in zip(P, nov, tags):
            ev = {"probs": dict(zip(CLASSES, map(float, p))), "novel": bool(n), "w": witness.opinion(a)}
            out.append(timeline.raw_label(ev, head["theta"]) in MEAL)
    return np.array(out)


def main() -> int:
    rng = np.random.default_rng(SEED)
    head = model.load(ROOT / "models" / "head.json")
    enc = encoders.load()
    meta = [line.strip().split("\t") for line in open(ROOT / "data/meta/dev/meta.txt")]
    by = {c: sorted({Path(a).stem for a, lab, _ in meta if lab == c}) for c in list(MEAL) + ["watching_tv"]}
    have = {p.stem: p for p in (ROOT / "data/clips/dev").iterdir()}
    sins = [have[f] for c in sorted(MEAL) for f in rng.choice([f for f in by[c] if f in have], PER_CLASS, replace=False)]
    tv = [have[f] for f in rng.choice([f for f in by["watching_tv"] if f in have], 60, replace=False)]
    desed = [RAW / "desed/dataset/audio/eval/public" / json.loads(line)["file"] for line in PRED.read_text().splitlines()
             if json.loads(line)["set"] == "desed" and json.loads(line)["kind"] == "kitchen" and json.loads(line).get("main") in ("Frying", "Dishes")]
    sets = {"research_home": np.stack([load16(p) for p in sins]), "other_homes": np.stack([load16(p, None) for p in desed])}
    tvw = np.stack([load16(p) for p in tv])
    R = {"made": time.strftime("%a %b %d %Y, %I:%M %p %Z"), "n": {k: len(v) for k, v in sets.items()}, "gain": {}, "tv": {}, "median_dbfs": {}}
    for name, W in sets.items():
        R["median_dbfs"][name] = round(float(np.median([20 * np.log10(rms(w)) for w in W])), 1)
        R["gain"][name] = {str(g): round(100 * float(score(enc, head, W * 10 ** (g / 20)).mean()), 1) for g in GAINS_DB}
        pick = rng.integers(0, len(tvw), len(W))
        R["tv"][name] = {"none": R["gain"][name]["0"]}
        for snr in TV_SNR_DB:
            mix = np.stack([w + tvw[j] * (rms(w) / rms(tvw[j])) * 10 ** (-snr / 20) for w, j in zip(W, pick)])
            R["tv"][name][str(snr)] = round(100 * float(score(enc, head, np.clip(mix, -1, 1)).mean()), 1)
        print(name, R["gain"][name], R["tv"][name], flush=True)
    R["tv_alone_false_kitchen"] = round(100 * float(score(enc, head, tvw).mean()), 1)
    (ROOT / "results" / "stress.json").write_text(json.dumps(R, indent=1))
    L = ["# Stress tests: quieter kitchens and a TV underneath", "", f"Made by `python -m eval.stress` ({R['made']}). Share of kitchen clips the shipped rule shows as a kitchen activity; one 10-s window each.",
         f"Research home: {R['n']['research_home']} SINS dev kitchen clips (the head trained on these sessions: read the drop, not the level). Other homes: {R['n']['other_homes']} DESED frying and dishes clips.", "",
         "| Turned down by | " + " | ".join(f"{-g} dB" for g in GAINS_DB) + " |", "|---|" + "---|" * len(GAINS_DB)]
    for name in sets:
        L.append(f"| {name.replace('_', ' ')} (median level {R['median_dbfs'][name]} dBFS) | " + " | ".join(f"{R['gain'][name][str(g)]}%" for g in GAINS_DB) + " |")
    L += ["", "| TV underneath; kitchen sound relative to TV | no TV | " + " | ".join(f"{s:+d} dB" for s in TV_SNR_DB) + " |", "|---|---|" + "---|" * len(TV_SNR_DB)]
    for name in sets:
        L.append(f"| {name.replace('_', ' ')} | {R['tv'][name]['none']}% | " + " | ".join(f"{R['tv'][name][str(s)]}%" for s in TV_SNR_DB) + " |")
    L += ["", f"TV clips alone shown as a kitchen activity: {R['tv_alone_false_kitchen']}% of {len(tvw)}.", ""]
    (ROOT / "results" / "stress.md").write_text("\n".join(L))
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
