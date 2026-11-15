"""Where Kettle breaks (improvement plan A7): the 90 demo clips (SINS dev, 9 sessions held out of training) under
real-kitchen problems the benchmark doesn't have.

  loudness   the whole clip 6, 12 and 18 dB quieter (a laptop across the room, a quiet cook)
  tv         a TV clip from another session mixed underneath at 10, 5 and 0 dB signal-to-TV ratio (TV left on all day)
  room       synthetic room echo (RT60 0.6 s) and a cheap-laptop band (300 Hz - 3.4 kHz), alone and together

Each condition runs the frozen encoder + head + novelty gate (without the second opinion, kettle/witness.py), before
and after teach-this-kitchen. Reported per condition: share of clips given their
true activity, share shown as Not sure, kitchen activity noticed (true cooking/washing up/eating shown as any of the
three). N = 90 clips (80 for the TV mix: TV clips are not mixed with TV), so intervals are wide; this is a slope, not a
benchmark. Writes results/stress_teach.json. (eval/stress.py is the team's main stress test; this file keeps only the teach-this-kitchen rows used on How sure.) Run: python -m eval.stress_teach  (~1 min CPU)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

from eval.beyond import rate
from kettle import encoders, model
from kettle.labels import CLASSES, MEAL

ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / "demo_cache" / "clips"
OUT = ROOT / "results" / "stress_teach.json"
THETA = 0.66


def truth() -> dict:
    lab = {}
    for line in (ROOT / "data" / "meta" / "dev" / "meta.txt").read_text().splitlines():
        f, c, _ = line.split("\t")
        lab[Path(f).stem] = c
    return lab


def rms(x):
    return float(np.sqrt(np.mean(x ** 2)) + 1e-12)


def room(x, rng, rt60=0.6, sr=16000):
    n = int(rt60 * sr)
    t = np.arange(n) / sr
    ir = rng.standard_normal(n) * np.exp(-6.9 * t / rt60) * 0.3
    ir[0] = 1.0
    y = fftconvolve(x, ir)[: len(x)]
    return (y * rms(x) / rms(y)).astype(np.float32)


LAPTOP = butter(4, [300, 3400], btype="bandpass", fs=16000, output="sos")


def laptop(x):
    y = sosfilt(LAPTOP, x)
    return (y * rms(x) / rms(y)).astype(np.float32)


def mix(x, noise, snr_db):
    g = rms(x) / (rms(noise) * 10 ** (snr_db / 20))
    return np.clip(x + g * noise, -1, 1).astype(np.float32)


def decide(enc, head, waves):
    """Frozen head + novelty gate -> label or not_sure for each window."""
    emb, scores = encoders.embed(enc, waves)
    P = model.predict_proba(head, emb)
    nov = model.novelty(head, emb) > head["novelty"]["threshold"]
    out = []
    for i, w in enumerate(waves):
        db = 20 * np.log10(rms(w))
        lab, conf = CLASSES[int(P[i].argmax())], float(P[i].max())
        out.append("not_sure" if nov[i] or conf < THETA else lab)
    return out


def enrolled(enc, head, waves, y, names, cfg):
    """Teach-this-kitchen under the same shift: 1 minute (6 clips) each of the quiet, cooking and washing-up sessions
    recorded under the condition, then the other 72 clips scored before and after (web/public/js/sense.js rule)."""
    from eval.beyond import adapt
    seg = {n: int(n.rsplit("_", 1)[1]) for n in names}
    enrol = [i for i, n in enumerate(names) if y[i] in ("absence", "cooking", "dishwashing") and seg[n] <= 6]
    test = [i for i in range(len(names)) if i not in enrol]
    emb, scores = encoders.embed(enc, waves)
    P = model.predict_proba(head, emb)
    nov = model.novelty(head, emb) > head["novelty"]["threshold"]
    ye = np.array([CLASSES.index(y[i]) for i in enrol])
    Pa, nova = adapt(head, emb[enrol], ye, emb[test], P[test], nov[test], cfg["alpha"], cfg["rho"], cfg["knn"])

    def labels(PP, nv, idx):
        out = []
        for j, i in enumerate(idx):
            lab, conf = CLASSES[int(PP[j].argmax())], float(PP[j].max())
            out.append("not_sure" if nv[j] or conf < THETA else lab)
        return out
    yt = [y[i] for i in test]
    return {"enrol_clips": len(enrol), "before": score(yt, labels(P[test], nov[test], test)), "after": score(yt, labels(Pa, nova, test))}


def score(y, pred) -> dict:
    y, pred = np.array(y), np.array(pred)
    meal = np.isin(y, list(MEAL))
    return {"n": int(len(y)), "right": rate(pred == y), "not_sure": rate(pred == "not_sure"),
            "kitchen_noticed": rate(np.isin(pred[meal], list(MEAL)))}


def main() -> None:
    rng = np.random.default_rng(0)
    lab = truth()
    files = sorted(CLIPS.glob("*.flac"))
    names = [f.stem for f in files]
    X = np.stack([sf.read(f, dtype="float32")[0][:160000] for f in files])
    y = [lab[n] for n in names]
    enc, head = encoders.load(), model.load(ROOT / "models" / "head.json")
    tv_idx = [i for i, c in enumerate(y) if c == "watching_tv"]
    non_tv = [i for i, c in enumerate(y) if c != "watching_tv"]
    R = {"about": __doc__.split("\n\n")[0], "clips": len(files), "theta": THETA, "head_sha256": head["sha256"], "loudness": [], "tv": [], "room": []}
    for g in (0, -6, -12, -18):
        R["loudness"].append({"gain_db": g, **score(y, decide(enc, head, X * 10 ** (g / 20)))})
    for snr in (None, 10, 5, 0):
        Xm = X[non_tv] if snr is None else np.stack([mix(X[i], X[tv_idx[(k * 7) % len(tv_idx)]], snr) for k, i in enumerate(non_tv)])
        R["tv"].append({"snr_db": snr, **score([y[i] for i in non_tv], decide(enc, head, Xm))})
    for name, f in (("clean", lambda x: x), ("room echo", lambda x: room(x, rng)), ("laptop mic", laptop),
                    ("echo + laptop mic", lambda x: laptop(room(x, rng)))):
        R["room"].append({"condition": name, **score(y, decide(enc, head, np.stack([f(x) for x in X])))})
    cfg = json.loads((ROOT / "web" / "public" / "model" / "enrol.json").read_text())
    R["teach"] = []
    shifts = (("clean", X), ("12 dB quieter", X * 10 ** (-12 / 20)), ("room echo", np.stack([room(x, rng) for x in X])),
              ("laptop mic", np.stack([laptop(x) for x in X])), ("echo + laptop mic", np.stack([laptop(room(x, rng)) for x in X])))
    for name, W in shifts:
        R["teach"].append({"condition": name, **enrolled(enc, head, W, y, names, cfg)})
    OUT.write_text(json.dumps(R, indent=1))
    (ROOT / "web" / "public" / "data" / "stress_teach.json").write_text(json.dumps(R))   # the How sure page reads this copy
    for row in R["teach"]:
        print("teach", row["condition"], "right", row["before"]["right"]["pct"], "->", row["after"]["right"]["pct"],
              "not_sure", row["before"]["not_sure"]["pct"], "->", row["after"]["not_sure"]["pct"],
              "kitchen", row["before"]["kitchen_noticed"]["pct"], "->", row["after"]["kitchen_noticed"]["pct"])
    for k in ("loudness", "tv", "room"):
        for row in R[k]:
            print(k, {a: b for a, b in row.items() if a in ("gain_db", "snr_db", "condition")}, "right", row["right"]["pct"],
                  "not_sure", row["not_sure"]["pct"], "kitchen", row["kitchen_noticed"]["pct"])


if __name__ == "__main__":
    main()
