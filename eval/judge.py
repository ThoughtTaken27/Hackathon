"""A trained, multi-home "judge" for windows the head can't name (handover v3.2, 3.2), with a ship/no-ship gate.

The head (models/head.json, frozen) was trained in one research home; outside it most windows are "unlike anything it learned"
and the hand-written second opinion (kettle/witness.py) picks which kitchen activity it is. The judge replaces that choice with a
multinomial logistic regression on CED-tiny's 527 AudioSet tags (log(p + 1e-4), standardised), trained across many homes:

  Kitchen20 TUNE half (by uploader): cooking = frying-pan, boiling-water, chopping, stove-burner, peel; dishwashing =
  clean-dishes, water-flowing; eating = eat; other = book, cupboard, drawer, fridge, microwave, sweep, stove-fan, dishwasher,
  juicer, blender (cutlery and plates left out: ambiguous). ESC-50 TUNE half (by source recording): other. SINS dev, all folds:
  cooking / dishwashing / eating, everything else other, weight 0.15 per window so one home doesn't dominate.
  (DESED, in the handover's plan, is not on this machine.)

Integration ("mode A"): the head's own answers are kept; only a window the head can't name (not_sure) is named by the judge,
when its top class is a kitchen activity with p >= TAU. The stretch rules 2c/2d still run afterwards.

Gate (handover 3.2, step 5), on OUT-OF-FOLD development predictions (GroupKFold by uploader / source / session):
  false meal calls on non-meal sounds must not rise above the shipped rule's, and wrong-activity must fall; written before the
  first run, this script also requires that right answers don't fall ("pass"). "handover_gate_pass" records the handover's
  gate alone. Only "pass" ships. (Sun Nov 15 run: no cutoff passes; 0.9 passes the handover gate alone with 6 fewer right.)
Only if it passes is a final judge trained on all development data, written to models/judge.json, and Kitchen20 TEST scored once.

    python -m eval.judge        writes results/judge.json (and models/judge.json only if the gate passes)
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from eval.other_homes import EMB, half
from kettle import model, timeline, witness
from kettle.labels import CLASSES

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results" / "cache"
OUT = ROOT / "results" / "judge.json"
JUDGE = ROOT / "models" / "judge.json"
J = ["cooking", "dishwashing", "eating", "other"]
MEAL3 = {"cooking", "dishwashing", "eating"}
K20 = {"frying-pan": "cooking", "boiling-water": "cooking", "chopping": "cooking", "stove-burner": "cooking", "peel": "cooking",
       "clean-dishes": "dishwashing", "water-flowing": "dishwashing", "eat": "eating", "book": "other", "cupboard": "other",
       "drawer": "other", "fridge": "other", "microwave": "other", "sweep": "other", "stove-fan": "other", "dishwasher": "other",
       "juicer": "other", "blender": "other"}
SINS_W, CS, TAUS = 0.15, [0.01, 0.03, 0.1, 0.3], [0.6, 0.7, 0.8, 0.9]


def feats(A: np.ndarray) -> np.ndarray:
    return np.log(np.asarray(A, np.float64) + 1e-4)


def load() -> dict:
    """Every window: tags A, judge target y (index in J), group, weight, source set, split, plus the head's view for scoring."""
    head = model.load(ROOT / "models" / "head.json")
    rows = defaultdict(list)

    def add(src, A, y, g, w, split, P, nov, extra):
        for i in range(len(A)):
            rows["A"].append(A[i]); rows["y"].append(y[i]); rows["g"].append(f"{src}:{g[i]}"); rows["w"].append(w)
            rows["src"].append(src); rows["split"].append(split[i]); rows["P"].append(P[i]); rows["nov"].append(nov[i]); rows["extra"].append(extra[i])
    q = np.load(EMB / "kitchen20" / "all.npz", allow_pickle=True)
    keep = np.array([str(c) in K20 for c in q["category"]])
    P, nov = model.predict_proba(head, q["emb"]), model.novelty(head, q["emb"]) > head["novelty"]["threshold"]
    add("k20", q["audioset"][keep], [J.index(K20[str(c)]) for c in q["category"][keep]], q["source"][keep], 1.0,
        [half(str(s)) for s in q["source"][keep]], P[keep], nov[keep], [str(c) for c in q["category"][keep]])
    e = np.load(CACHE / "ced-tiny_esc50all.npz")
    srcid = [f.rsplit("_", 1)[-1].split("-")[1] for f in e["files"]]
    Pe, ne = model.predict_proba(head, e["emb"]), model.novelty(head, e["emb"]) > head["novelty"]["threshold"]
    add("esc", e["scores"], [J.index("other")] * len(srcid), srcid, 1.0, [half(s) for s in srcid], Pe, ne, [str(c) for c in e["category"]])
    o = np.load(CACHE / "oof_dev.npz")
    d = np.load(CACHE / "ced-tiny_dev.npz")
    pos = {str(f): i for i, f in enumerate(d["files"])}
    ix = np.array([pos[str(f)] for f in o["files"]])
    ns = model.novelty(head, d["emb"][ix, 0].astype(np.float32)) > head["novelty"]["threshold"]
    ys = [J.index(CLASSES[k]) if CLASSES[k] in MEAL3 else J.index("other") for k in o["y"]]
    add("sins", o["scores"], ys, o["session"], SINS_W, ["dev"] * len(ys), o["P0"], ns, [str(f) for f in o["files"]])
    return {k: (np.array(v, dtype=object) if k == "extra" else np.array(v)) for k, v in rows.items()} | {"theta": head["theta"]}


def fit(X, y, w, C):
    mu, sd = X.mean(0), X.std(0) + 1e-6
    m = LogisticRegression(C=C, max_iter=3000)
    m.fit((X - mu) / sd, y, sample_weight=w)
    return {"mean": mu, "std": sd, "coef": m.coef_, "intercept": m.intercept_, "classes": [J[c] for c in m.classes_]}


def proba(j, X):
    L = ((X - j["mean"]) / j["std"]) @ j["coef"].T + j["intercept"]
    L -= L.max(1, keepdims=True)
    E = np.exp(L)
    return E / E.sum(1, keepdims=True)


def oof(D, dev, C, folds=5):
    X, y, w, g = feats(D["A"][dev]), D["y"][dev], D["w"][dev], D["g"][dev]
    out = np.zeros((dev.sum(), len(J)))
    for tr, te in GroupKFold(folds).split(X, y, g):
        j = fit(X[tr], y[tr], w[tr], C)
        out[te] = proba(j, X[te])
    return out


def event(i, t, D, jp=None, tau=None) -> dict:
    pr = dict(zip(CLASSES, map(float, D["P"][i])))
    w = witness.opinion(D["A"][i])
    if jp is not None:
        k = int(np.argmax(jp))
        w["jf"], w["jp"] = J[k], round(float(jp[k]), 3)
    return {"start": t, "end": t + 10, "label": "other", "conf": 0.0, "probs": pr, "novel": bool(D["nov"][i]), "sounds": [], "w": w}


def judged_raw(tau):
    raw = timeline.raw_label

    def f(ev, theta):
        lab = timeline.head_label(ev, theta)
        w = ev.get("w") or {}
        if lab == "not_sure" and w.get("jf") in MEAL3 and w.get("jp", 0) >= tau and not ev.get("private"):
            return w["jf"]                         # mode A: the judge names only windows the head can't
        if lab == "not_sure" and "jf" in w:
            return "not_sure"                      # the judge replaces the hand-written rescue
        return raw(ev, theta)
    return f


def shown(evs, theta) -> str | None:
    cover = Counter()
    for b in timeline.blocks(evs, theta):
        if b["state"] == "activity":
            cover[b["activity"]] += b["n_windows"]
    return cover.most_common(1)[0][0] if cover else None


def tally(items, theta) -> dict:
    c = Counter()
    for truth, evs in items:
        p = shown(evs, theta)
        if truth in MEAL3:
            c["meal"] += 1; c["right"] += p == truth; c["wrong_activity"] += p in MEAL3 and p != truth; c["kitchen_unnamed"] += p == "kitchen"
        else:
            c["not_meal"] += 1; c["false_meal"] += p in MEAL3 | {"kitchen"}
    return dict(c)


def items_for(D, idx, P=None, tau=None, sins_sessions=False):
    """Kitchen20/ESC: one window per item. SINS: one item per session (its windows in order)."""
    if not sins_sessions:
        return [(J[D["y"][i]], [event(i, 0, D, None if P is None else P[n])]) for n, i in enumerate(idx)]
    by = defaultdict(list)
    for n, i in enumerate(idx):
        f = D["extra"][i]
        by[f.rsplit("_", 1)[0]].append((int(f.rsplit("_", 1)[1]), n, i))
    out = []
    for v in by.values():
        v.sort()
        out.append((J[D["y"][v[0][2]]], [event(i, 10 * k, D, None if P is None else P[n]) for k, (_, n, i) in enumerate(v)]))
    return out


def run_sets(D, P_by_set, tau, theta) -> dict:
    keep = timeline.raw_label
    out = {}
    try:
        for name, (idx, sess) in P_by_set["idx"].items():
            timeline.raw_label = keep
            before = tally(items_for(D, idx, sins_sessions=sess), theta)
            timeline.raw_label = judged_raw(tau)
            after = tally(items_for(D, idx, P_by_set["P"][name], tau, sess), theta)
            out[name] = {"n": len(idx), "shipped_rule": before, "judge": after}
    finally:
        timeline.raw_label = keep
    return out


def main() -> None:
    D = load()
    theta = D["theta"]
    dev = D["split"] != "test"
    # 1. C by group-CV log loss on development windows
    cv = {}
    for C in CS:
        P = oof(D, dev, C)
        yy, ww = D["y"][dev], D["w"][dev]
        cv[C] = float(-(ww * np.log(P[np.arange(len(yy)), yy] + 1e-9)).sum() / ww.sum())
    C = min(cv, key=cv.get)
    P = oof(D, dev, C)
    dev_idx = np.where(dev)[0]
    pos = {i: n for n, i in enumerate(dev_idx)}
    sets = {"kitchen20_tune": (D["src"] == "k20") & dev, "esc50_tune": (D["src"] == "esc") & dev, "sins_dev_sessions": D["src"] == "sins"}
    per = {"idx": {k: (np.where(m)[0], k == "sins_dev_sessions") for k, m in sets.items()},
           "P": {k: P[[pos[i] for i in np.where(m)[0]]] for k, m in sets.items()}}
    R = {"about": __doc__.split("\n\n")[0], "C_by_cv_logloss": cv, "C": C, "sins_weight": SINS_W, "dev": {}}
    for tau in TAUS:
        R["dev"][str(tau)] = run_sets(D, per, tau, theta)
    # 2. gate on development (out-of-fold): no more false meal calls anywhere, fewer wrong-activity calls overall
    passing = []
    for tau in TAUS:
        r = R["dev"][str(tau)]
        fm_ok = all(r[s]["judge"].get("false_meal", 0) <= r[s]["shipped_rule"].get("false_meal", 0) for s in r)
        wa_b = sum(r[s]["shipped_rule"].get("wrong_activity", 0) for s in r)
        wa_a = sum(r[s]["judge"].get("wrong_activity", 0) for s in r)
        right_b = sum(r[s]["shipped_rule"].get("right", 0) for s in r)
        right_a = sum(r[s]["judge"].get("right", 0) for s in r)
        R["dev"][str(tau)]["_gate"] = {"false_meal_not_higher": fm_ok, "wrong_activity": [wa_b, wa_a], "right": [right_b, right_a],
                                       "handover_gate_pass": bool(fm_ok and wa_a < wa_b),
                                       "pass": bool(fm_ok and wa_a < wa_b and right_a >= right_b)}
        if R["dev"][str(tau)]["_gate"]["pass"]:
            passing.append(tau)
        print(f"tau {tau}: " + "  ".join(f"{s}: {r[s]['shipped_rule']} -> {r[s]['judge']}" for s in r if not s.startswith("_")) +
              f"  GATE {R['dev'][str(tau)]['_gate']}")
    R["gate_pass_taus"] = passing
    if not passing:
        R["decision"] = ("not shipped: no cutoff passed the development gate written before the run (fewer false meal calls, fewer "
                         "wrong activities, and no fewer right answers); see handover_gate_pass for the handover's gate alone")
        OUT.write_text(json.dumps(R, indent=1, default=float) + "\n")
        print("GATE FAILED: judge not shipped")
        return
    tau = max(passing, key=lambda t: sum(R["dev"][str(t)][s]["judge"].get("right", 0) for s in R["dev"][str(t)] if not s.startswith("_")))
    j = fit(feats(D["A"][dev]), D["y"][dev], D["w"][dev], C)
    JUDGE.write_text(json.dumps({"classes": j["classes"], "mean": j["mean"].round(5).tolist(), "std": j["std"].round(5).tolist(),
                                 "coef": j["coef"].round(5).tolist(), "intercept": j["intercept"].round(5).tolist(), "tau": tau,
                                 "features": "log(audioset + 1e-4), standardised", "source": "eval/judge.py -> results/judge.json"}))
    # 3. held-out once: Kitchen20 TEST half (looked at before today: see results/kitchen_naming.json process note)
    test = (D["src"] == "k20") & (D["split"] == "test")
    Pt = proba(j, feats(D["A"][test]))
    R["test_kitchen20"] = run_sets(D, {"idx": {"kitchen20_test": (np.where(test)[0], False)}, "P": {"kitchen20_test": Pt}}, tau, theta)
    R["tau"], R["decision"] = tau, "shipped (gate passed on development data)"
    OUT.write_text(json.dumps(R, indent=1, default=float) + "\n")
    print("TEST kitchen20:", R["test_kitchen20"])


if __name__ == "__main__":
    main()
