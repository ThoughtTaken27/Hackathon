"""A trained sound head for named everyday sounds: one small logistic regression per sound (pre-registered v2).

Pre-registered in eval/PREREGISTER-SOUNDS-V2.md. Positives / ambiguous / negatives are eval/sounds.py POS and AMBIG.
Everything is chosen on the TUNE halves (grouped 5-fold cross-validation); the TEST halves are scored once, same bar as v1
(precision >= 90% and recall >= 40%), next to v1's rules on the same windows.

  python -m eval.sound_head --tune-only   # choices and tune numbers only; touches no test half
  python -m eval.sound_head               # + the one test run -> results/sound_head.json, web/public/model/sound_head.json

The device (web/public/js/sense.js soundHead) and Python (kettle/kinds.py) compute the same thing:
  z = (x - mean) / std,  p = sigmoid(w . z + b),  named if p >= threshold (and the privacy veto doesn't fire).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedGroupKFold

from eval.beyond import rate
from eval.other_homes import half
from eval.sounds import AMBIG, BAR, POS, fired
from kettle.labels import CLASSES

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results" / "cache"
OUT = ROOT / "results" / "sound_head.json"
MODEL = ROOT / "web" / "public" / "model" / "sound_head.json"
TUNE_PRECISION = 92.0
CS = (0.01, 0.1, 1.0)
FEATS = ("emb", "emb+logit")
SEED = 0


def data() -> dict:
    """{dataset: dict(S [N,527], E [N,192], lab, part 'tune'/'test', group)} from the same caches as eval/sounds.py."""
    out = {}
    k = np.load(ROOT / "data" / "emb" / "ced-tiny" / "kitchen20" / "all.npz")
    out["kitchen20"] = dict(S=k["audioset"], E=k["emb"], lab=np.char.add("k20:", k["category"]),
                            part=np.array([half(s) for s in k["source"]]), group=np.char.add("k20:", k["source"]))
    e = np.load(CACHE / "ced-tiny_esc50all.npz")
    src = np.array([f.rsplit("_", 1)[-1].split("-")[1] for f in e["files"]])
    out["esc50"] = dict(S=e["scores"], E=e["emb"], lab=np.char.add("esc:", e["category"]),
                        part=np.array([half(s) for s in src]), group=np.char.add("esc:", src))
    o, d = np.load(CACHE / "oof_dev.npz"), np.load(CACHE / "ced-tiny_dev.npz")
    pos = {f: i for i, f in enumerate(d["files"])}
    ix = np.array([pos[f] for f in o["files"]])                 # the two caches list the same clips in different orders
    out["sins_dev"] = dict(S=o["scores"], E=d["emb"][ix, 0], lab=np.array(["sins:" + CLASSES[y] for y in o["y"]]),
                           part=np.where(np.isin(o["fold"], [1, 2]), "tune", "test"), group=np.char.add("sins:", o["session"]))
    a = np.load(CACHE / "ced-tiny_synth_alarms.npz")
    out["synth_alarms"] = dict(S=a["scores"], E=a["emb"], lab=np.char.add("syn:", a["kind"]),
                               part=np.where(a["seed"] % 2 == 0, "tune", "test"), group=np.array([f"syn:{s}" for s in a["seed"]]))
    n = np.load(CACHE / "ced-tiny_nonspeech7k.npz")
    out["nonspeech7k"] = dict(S=n["scores"], E=n["emb"], lab=np.char.add("ns7k:", n["category"]),
                              part=np.array([half(f) for f in n["files"]]), group=np.char.add("ns7k:", n["files"]))
    for v in out.values():
        v["S"], v["E"] = v["S"].astype(np.float64), v["E"].astype(np.float64)
    return out


def pooled(D: dict, part: str) -> dict:
    keys = ("S", "E", "lab", "group")
    return {k: np.concatenate([D[n][k][D[n]["part"] == part] for n in D]) for k in keys}


def logit(S: np.ndarray) -> np.ndarray:
    p = np.clip(S, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def features(P: dict, feat: str) -> np.ndarray:
    return P["E"] if feat == "emb" else np.hstack([P["E"], logit(P["S"])])


def best_threshold(p: np.ndarray, y: np.ndarray, target: float) -> tuple[float | None, float, float]:
    """Lowest threshold whose precision (on these scores) is >= target. -> (threshold, precision %, recall %)."""
    order = np.argsort(-p)
    ps, ys = p[order], y[order]
    tp = np.cumsum(ys)
    prec = 100 * tp / np.arange(1, len(ys) + 1)
    best = None
    for i in range(len(ps)):
        if i + 1 < len(ps) and ps[i + 1] == ps[i]:
            continue                                               # a threshold sits between distinct scores
        if prec[i] >= target and tp[i] > 0:
            best = i
    if best is None:
        return None, 0.0, 0.0
    return float(ps[best]), float(prec[best]), float(100 * tp[best] / max(1, ys.sum()))


def oof(X: np.ndarray, y: np.ndarray, g: np.ndarray, C: float) -> np.ndarray:
    """Out-of-fold probabilities from grouped, stratified 5-fold CV (no group in two folds)."""
    out = np.zeros(len(y))
    for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=SEED).split(X, y, g):
        m = fit(X[tr], y[tr], C)
        out[te] = predict(m, X[te])
    return out


def fit(X: np.ndarray, y: np.ndarray, C: float) -> dict:
    mu, sd = X.mean(0), X.std(0) + 1e-6
    lr = LogisticRegression(C=C, class_weight="balanced", max_iter=4000, random_state=SEED).fit((X - mu) / sd, y)
    return {"mean": mu, "std": sd, "w": lr.coef_[0], "b": float(lr.intercept_[0])}


def predict(m: dict, X: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-(((X - m["mean"]) / m["std"]) @ m["w"] + m["b"])))


def choose(T: dict) -> dict:
    """Per sound: features, C and threshold from tune-half cross-validation only."""
    out = {}
    for k in POS:
        y_all = np.isin(T["lab"], POS[k])
        keep = ~np.isin(T["lab"], AMBIG[k])
        y, g = y_all[keep].astype(int), T["group"][keep]
        best = None
        for feat in FEATS:
            X = features(T, feat)[keep]
            for C in CS:
                p = oof(X, y, g, C)
                ap = average_precision_score(y, p)
                if best is None or ap > best["ap"]:
                    best = {"feat": feat, "C": C, "ap": round(float(ap), 4), "p": p}
        thr, prec, rec = best_threshold(best["p"], y.astype(bool), TUNE_PRECISION)
        ok = thr is not None and rec >= BAR["recall"]
        m = fit(features(T, best["feat"])[keep], y, best["C"])
        out[k] = {"feat": best["feat"], "C": best["C"], "tune_ap": best["ap"], "threshold": thr,
                  "tune_precision": round(prec, 1), "tune_recall": round(rec, 1), "n_pos_tune": int(y.sum()),
                  "passes_tune": bool(ok), "model": m}
        print(f"{k:10s} {best['feat']:9s} C={best['C']:<5} AP={best['ap']:.3f}  thr={thr}  tune P={prec:.1f} R={rec:.1f}  "
              f"(pos {int(y.sum())})  {'ok' if ok else 'HIDDEN (fails on tune)'}")
    return out


VETO_FROM = ROOT / "web" / "public" / "model" / "kinds.json"


def head_fired(H: dict, P: dict, cfg: dict) -> dict:
    """{sound: bool [N]}: trained head, then the privacy veto (same rule as kettle/kinds.py named())."""
    idx = {k["id"]: k["index"] for k in cfg["kinds"]}
    raw, top = {}, np.zeros(len(P["lab"]))
    for k, h in H.items():
        if h["threshold"] is None:
            raw[k] = np.zeros(len(P["lab"]), bool)
            continue
        raw[k] = predict(h["model"], features(P, h["feat"])) >= h["threshold"]
        top = np.maximum(top, np.where(raw[k], P["S"][:, idx[k]].max(1), 0))
    vetoed = P["S"][:, cfg["veto"]].max(1) >= np.where(top > 0, top, np.inf)
    return {k: v & ~vetoed for k, v in raw.items()}


def score(F: dict, lab: np.ndarray) -> dict:
    out = {}
    for k in POS:
        f = F[k]
        pos, amb = np.isin(lab, POS[k]), np.isin(lab, AMBIG[k])
        neg = ~pos & ~amb
        tp, fp = int(f[pos].sum()), int(f[neg].sum())
        worst = {str(c): int((f & (lab == c)).sum()) for c in np.unique(lab[neg & f])}
        out[k] = {"recall": rate(f[pos]), "false_per_1000": round(1000 * fp / max(1, int(neg.sum())), 2), "false_k": fp,
                  "neg_n": int(neg.sum()), "precision": rate(np.r_[np.ones(tp, bool), np.zeros(fp, bool)]),
                  "top_false": dict(sorted(worst.items(), key=lambda kv: -kv[1])[:5])}
    return out


def export(H: dict, shown: dict) -> dict:
    """The device file: per sound, the inputs it reads, standardisation, weights, bias, threshold, shown."""
    r = lambda a, n=5: [round(float(x), n) for x in a]
    return {"about": "Trained sound head (eval/sound_head.py, pre-registered in eval/PREREGISTER-SOUNDS-V2.md). "
                     "p = sigmoid(w . ((x - mean) / std) + b); x = embedding [192], or embedding + log-odds of the 527 AudioSet scores.",
            "heads": {k: {"feat": h["feat"], "threshold": round(h["threshold"], 6), "shown": bool(shown.get(k, False)),
                          "mean": r(h["model"]["mean"]), "std": r(h["model"]["std"]), "w": r(h["model"]["w"]), "b": round(h["model"]["b"], 6)}
                      for k, h in H.items() if h["threshold"] is not None and h["passes_tune"]}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune-only", action="store_true")
    args = ap.parse_args()
    D = data()
    T = pooled(D, "tune")
    print(f"tune windows: {len(T['lab'])}")
    H = choose(T)
    if args.tune_only:
        return
    cfg = json.loads(VETO_FROM.read_text())
    X = pooled(D, "test")
    v1 = fired(cfg, X["S"])
    v2 = head_fired({k: h if h["passes_tune"] else {**h, "threshold": None} for k, h in H.items()}, X, cfg)
    before, after = score(v1, X["lab"]), score(v2, X["lab"])
    shown = {}
    for k, v in after.items():
        p, rc = v["precision"]["pct"], v["recall"]["pct"]
        shown[k] = bool(H[k]["passes_tune"] and p is not None and rc is not None and p >= BAR["precision"] and rc >= BAR["recall"])
        v["shown"] = shown[k]
    R = {"about": __doc__.split("\n\n")[0], "prereg": "eval/PREREGISTER-SOUNDS-V2.md", "bar": BAR, "tune_precision_target": TUNE_PRECISION,
         "process": "Every choice (inputs, C, threshold) from grouped 5-fold CV on the tune halves. The test halves were scored once "
                    "before with v1's rules (results/sounds.json); this is their second use, by a head that never saw them.",
         "n_test_windows": int(len(X["lab"])),
         "choices": {k: {kk: vv for kk, vv in h.items() if kk != "model"} for k, h in H.items()},
         "v1_rules": before, "v2_head": after}
    OUT.write_text(json.dumps(R, indent=1))
    MODEL.write_text(json.dumps(export(H, shown)))
    cfg["kinds"] = [{**k, "shown": bool(shown.get(k["id"], False))} for k in cfg["kinds"]]   # what eval/beyond.py shown_ids() also reads
    VETO_FROM.write_text(json.dumps(cfg))
    print("\nTEST (once)")
    for k in POS:
        b, a = before[k], after[k]
        print(f"{k:10s} recall {b['recall']['pct']}->{a['recall']['pct']} (n={a['recall']['n']})  precision {b['precision']['pct']}->"
              f"{a['precision']['pct']}  false/1000 {b['false_per_1000']}->{a['false_per_1000']}  shown={a['shown']}  {a['top_false']}")


if __name__ == "__main__":
    main()
