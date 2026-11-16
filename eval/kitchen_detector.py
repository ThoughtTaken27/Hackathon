"""Rule 2f: the kitchen detector (Sun Nov 15, 2026, ~8:45 PM CT).

Why: in Parth's own kitchen, loud pots and cutlery came out as "Some activity". The head (trained in one SINS home) says
"other" or isn't sure, and the second opinion only fires when one kitchen tag reaches 0.15; a 0.2-second clink averaged over
10 seconds scores far lower (one DESED clip: "Dishes, pots, and pans" 0.007 averaged over 10 s vs 0.10 in its loudest second).
Products that do this well (Ubicoustics, Apple Sound Recognition) use a dedicated detector per context, not one tag.

What: a logistic regression on the log-odds of all 527 CED-tiny AudioSet scores the device already computes, kitchen
activity vs anything else. No new model file, no new audio leaves the device: the window gains one number, kd.

Data (all cached, no audio needed):
  train   TUNE halves of DESED public eval (no AudioSet overlap), Kitchen20 and ESC-50 household clips, plus SINS dev
  choose  C and tau on a held-back half of TUNE (by file name hash): best recall with false kitchen <= 3%
  test    TEST halves of the same three sets and the 7,791-window SINS eval set, each read once per reported number

    python -m eval.kitchen_detector          # writes models/witness.json "detector" and results/kitchen_detector.json
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.kitchen_naming import K20                                       # noqa: E402
from eval.other_homes import _desed_groups, desed_kind, half, main_sound  # noqa: E402
from kettle.labels import MEAL                                            # noqa: E402

EMB = ROOT / "data" / "emb" / "ced-tiny"
MAX_FALSE = 0.03
# Voices, TV, music and typing alone must never read as kitchen (shouting is a safety sound, not cooking). A setting is
# only eligible if each of these probes (one tag at 0.9, the rest at 0.001) stays below its tau. tests/test_witness.py checks it.
PROBES = (["Speech"], ["Speech", "Conversation"], ["Television"], ["Music"], ["Shout", "Yell"], ["Typing", "Computer keyboard"],
          ["Screaming"], ["Laughter"], ["Radio"])


def probe_ok(m, tau: float) -> bool:
    names = json.loads((ROOT / "models" / "audioset_labels.json").read_text())
    for p in PROBES:
        a = np.full(527, 0.001)
        for n in p:
            a[names.index(n)] = 0.9
        if m.predict_proba(logit(a[None]))[0, 1] >= tau:
            return False
    return True


def logit(s: np.ndarray) -> np.ndarray:
    s = np.clip(np.asarray(s, np.float64), 1e-4, 1 - 1e-4)
    return np.log(s / (1 - s))


def open_sets() -> list[tuple[str, str, str, bool, np.ndarray]]:
    """(set, file, half, is_kitchen, 527 scores) for every DESED / Kitchen20 / ESC-50 clip with a clear answer."""
    up, ev, aset = _desed_groups()
    rows = []
    z = np.load(EMB / "desed" / "public_eval.npz", allow_pickle=True)
    for f, s in zip(map(str, z["files"]), z["audioset"]):
        if f.rsplit("_", 2)[0] in aset:
            continue                                   # in AudioSet's own training data: CED has heard it
        E = ev.get(f, {})
        k = desed_kind(E)
        y = True if k == "kitchen" and main_sound(E) in ("Dishes", "Frying") else \
            False if k in ("vacuum", "shaver", "pets_alarms", "speech") else None
        if y is not None:
            rows.append(("desed", f, half(up.get(f, f.rsplit("_", 2)[0])), y, s))
    z = np.load(EMB / "kitchen20" / "all.npz", allow_pickle=True)
    for f, c, src, s in zip(map(str, z["files"]), map(str, z["category"]), map(str, z["source"]), z["audioset"]):
        if c in K20:
            rows.append(("k20", f, half(src), K20[c] != "other", s))
    z = np.load(EMB / "esc50_house" / "all.npz", allow_pickle=True)
    for f, c, src, s in zip(map(str, z["files"]), map(str, z["category"]), map(str, z["source"]), z["audioset"]):
        if c != "pouring_water":
            rows.append(("esc", f, half(src), False, s))
    return sorted(rows, key=lambda r: (r[0], r[1]))


def sins(split: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """SINS windows (channel 0): 527 scores, is-kitchen, activity name."""
    if split == "dev":
        c = np.load(ROOT / "results" / "cache" / "ced-tiny_dev.npz", allow_pickle=True)
        meta = {l.split("\t")[0].split("/")[-1][:-4]: l.split("\t")[1] for l in open(ROOT / "data/meta/dev/meta.txt") if l.strip()}
        y = [meta.get(str(f).split("/")[-1].replace(".wav", "")) for f in c["files"]]
        ok = [i for i, t in enumerate(y) if t]
        return c["scores"][ok, 0].astype(np.float32), np.array([y[i] in MEAL for i in ok]), [y[i] for i in ok]
    meta = {l.split("\t")[0].split("/")[-1][:-4]: l.split("\t")[1] for l in open(ROOT / "data/meta/eval/meta.txt") if l.strip()}
    F, S = [], []
    for f in sorted(glob.glob(str(EMB / "eval" / "*"))):
        a = np.load(f, allow_pickle=True)
        F += list(a["files"])
        S.append(a["scores"][:, 0].astype(np.float32))
    y = [meta[str(f)] for f in F]
    return np.concatenate(S), np.array([t in MEAL for t in y]), y


def fit(X: np.ndarray, y: np.ndarray, Xs: np.ndarray, ys: np.ndarray, C: float) -> LogisticRegression:
    """SINS dev (one home, thousands of windows) weighs as much as all the open-set clips together."""
    w = np.concatenate([np.ones(len(X)), np.full(len(Xs), len(X) / len(Xs))])
    return LogisticRegression(C=C, max_iter=3000, class_weight="balanced").fit(
        np.concatenate([logit(X), logit(Xs)]), np.concatenate([y, ys]), sample_weight=w)


def main() -> int:
    rows = open_sets()
    S = np.stack([r[4] for r in rows])
    y = np.array([r[3] for r in rows])
    hv = np.array([r[2] for r in rows])
    sub = np.array([int(hashlib.sha256(f"kdet-sub:{r[1]}".encode()).hexdigest(), 16) % 2 for r in rows])
    Sd, yd, _ = sins("dev")
    A, B = (hv == "tune") & (sub == 0), (hv == "tune") & (sub == 1)
    cands = []
    for C in (0.01, 0.03, 0.1, 0.3):
        mA, mAll = fit(S[A], y[A], Sd, yd, C), fit(S[hv == "tune"], y[hv == "tune"], Sd, yd, C)
        p = mA.predict_proba(logit(S[B]))[:, 1]
        for tau in np.round(np.arange(0.5, 0.96, 0.05), 2):
            fa, rec = float((p[~y[B]] >= tau).mean()), float((p[y[B]] >= tau).mean())
            if fa <= MAX_FALSE and probe_ok(mAll, tau):
                cands.append((rec, -fa, C, float(tau)))
    rec, nfa, C, tau = max(cands)
    tr = hv == "tune"
    m = fit(S[tr], y[tr], Sd, yd, C)

    cfg_path = ROOT / "models" / "witness.json"
    cfg = json.loads(cfg_path.read_text())
    cfg["detector"] = {
        "_what": "Kitchen detector (rule 2f, eval/kitchen_detector.py): logistic regression on the log-odds of all 527 CED-tiny "
                 "AudioSet scores, kitchen activity vs anything else. Trained on the TUNE halves of DESED public eval, Kitchen20 and "
                 "ESC-50 household clips plus SINS dev; C and tau chosen on a held-back half of TUNE (false kitchen <= 3%). Fires only "
                 "when the head did not already say a kitchen activity, a kitchen tag was heard (k >= tau_k = 0.03, rule 2e's 'heard' bar; added after it fired on 10% of off-list sounds) and no motor or bathroom sound is louder.",
        "tau": tau, "tau_k": 0.03, "C": C, "intercept": round(float(m.intercept_[0]), 6), "coef": [round(float(c), 6) for c in m.coef_[0]]}
    cfg_path.write_text(json.dumps(cfg))
    print(f"chosen on the held-back TUNE half: C={C} tau={tau} recall {100 * rec:.0f}% false {-100 * nfa:.1f}%")
    out = {"what": "Rule 2f head-to-head through the app's own window rules (kettle/timeline.py raw_label + describe), one 10-s window "
                   "per clip, before day-bar smoothing. 'now' = the app before rule 2f; 'with_2f' = with the kitchen detector.",
           "chosen": {"C": C, "tau": tau, "tune_heldback_recall_pct": round(100 * rec, 1), "tune_heldback_false_pct": round(-100 * nfa, 1)},
           **report(rows)}
    (ROOT / "results" / "kitchen_detector.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k not in ("what",)}, indent=1))
    return 0


def report(rows) -> dict:
    """Now vs with rule 2f on the TEST halves and SINS eval, through kettle/timeline.py (reloads the detector just written)."""
    import importlib
    from kettle import evidence, model, timeline, witness
    from kettle.labels import CLASSES
    importlib.reload(witness)
    importlib.reload(timeline)
    head = model.load(ROOT / "models" / "head.json")
    th = head["theta"]
    kit = lambda lab: lab in MEAL or lab == "kitchen"
    sets = {}
    for name in ("desed", "k20", "esc"):
        f = {"desed": EMB / "desed" / "public_eval.npz", "k20": EMB / "kitchen20" / "all.npz", "esc": EMB / "esc50_house" / "all.npz"}[name]
        z = np.load(f, allow_pickle=True)
        idx = {str(x): i for i, x in enumerate(z["files"])}
        sel = [r for r in rows if r[0] == name and r[2] == "test"]
        E = np.stack([z["emb"][idx[r[1]]] for r in sel])
        sets[f"{name}_test"] = (E, np.stack([r[4] for r in sel]), np.array([r[3] for r in sel]), None)
    F, Ee, Se = [], [], []
    for f in sorted(glob.glob(str(EMB / "eval" / "*"))):
        a = np.load(f, allow_pickle=True)
        F += list(a["files"])
        Ee.append(a["emb"][:, 0])
        Se.append(a["scores"][:, 0].astype(np.float32))
    meta = {l.split("\t")[0].split("/")[-1][:-4]: l.split("\t")[1] for l in open(ROOT / "data/meta/eval/meta.txt") if l.strip()}
    yl = np.array([meta[str(f)] for f in F])
    sets["sins_eval"] = (np.concatenate(Ee).astype(np.float32), np.concatenate(Se), np.isin(yl, list(MEAL)), yl)
    det = witness.DET
    res = {}
    for key, (E, S, y, names) in sets.items():
        P = model.predict_proba(head, E)
        N = model.novelty(head, E) > head["novelty"]["threshold"]
        res[key] = {}
        for mode in ("now", "with_2f"):
            witness.DET = det if mode == "with_2f" else None
            labs = []
            for i in range(len(S)):
                e = {"probs": dict(zip(CLASSES, map(float, P[i]))), "novel": bool(N[i]), "w": witness.opinion(S[i]),
                     "sounds": evidence.top_sounds(S[i]), "kinds": []}
                lab = timeline.raw_label(e, th)
                labs.append(timeline.describe(e) if lab == "not_sure" else lab)
            k = np.array([kit(l) for l in labs])
            r = {"kitchen_caught_pct": round(100 * float(k[y].mean()), 1) if y.any() else None, "n_kitchen": int(y.sum()),
                 "false_kitchen_pct": round(100 * float(k[~y].mean()), 2), "n_not_kitchen": int((~y).sum()),
                 "some_activity_pct": round(100 * float(np.mean([l == "other" for l in labs])), 1)}
            if names is not None:
                r["false_kitchen_by_activity_pct"] = {c: round(100 * float(k[names == c].mean()), 1) for c in sorted(set(names)) if c not in MEAL}
                r["caught_by_activity_pct"] = {c: round(100 * float(k[names == c].mean()), 1) for c in sorted(MEAL) if c in set(names)}
            res[key][mode] = r
    witness.DET = det
    return res


def app_meal_metric() -> dict:
    """What the app itself shows, scored with the team's own pre-registered kitchen metric (eval/dev.py meal_metric: per
    10-s window, single mic, reweighted to the full test set's activity mix, 95% CI by session bootstrap).

    The landing page used the model's top guess; the app never shows that (below theta it says Not sure / Some activity).
    Here every held-out SINS eval window goes through the shipped rules (kettle/timeline.py raw_label, rule 2c naming,
    rule 2e describe), before and after rule 2f. Writes web/public/data/app.json for the landing page."""
    from eval import dev
    from eval import metrics as M
    from eval.common import full_counts
    from kettle import evidence, model, timeline, witness
    from kettle.data import load_meta
    from kettle.labels import CLASSES
    head = model.load(ROOT / "models" / "head.json")
    meta = {r["file"][:-4]: r for r in load_meta("eval")}
    F, E, S = [], [], []
    for f in sorted(glob.glob(str(EMB / "eval" / "*"))):
        a = np.load(f, allow_pickle=True)
        F += [str(x) for x in a["files"]]
        E.append(a["emb"][:, 0])
        S.append(a["scores"][:, 0].astype(np.float32))
    E, S = np.concatenate(E).astype(np.float32), np.concatenate(S)
    y = np.array([CLASSES.index(meta[f]["label"]) for f in F])
    s = np.array([meta[f]["session"] for f in F])
    w = M.class_weights(full_counts("eval"), np.bincount(y, minlength=9))
    P = model.predict_proba(head, E)
    N = model.novelty(head, E) > head["novelty"]["threshold"]
    split = "DCASE 2018 Task 5 eval sample (held-out); the app's shipped window rules on cached CED-tiny outputs"
    det, out = witness.DET, {}
    for key, d in (("app_before_rule_2f", None), ("app_live", det)):
        witness.DET = d
        labs = []
        for i in range(len(S)):
            e = {"probs": dict(zip(CLASSES, map(float, P[i]))), "novel": bool(N[i]), "w": witness.opinion(S[i]),
                 "sounds": evidence.top_sounds(S[i]), "kinds": []}
            lab = timeline.raw_label(e, head["theta"])
            if lab == "kitchen":
                lab = witness.name_kitchen([e])
            labs.append(timeline.describe(e) if lab == "not_sure" else lab)
        kit = np.array([l in MEAL or l == "kitchen" for l in labs])
        p = np.where(kit, CLASSES.index("cooking"), CLASSES.index("other"))       # meal_metric only reads kitchen yes/no
        out[key] = dev.meal_metric(y, p, s, w, split)
        out[key]["not_sure_pct"] = round(100 * float(np.mean([l == "not_sure" for l in labs])), 1)
    witness.DET = det
    out["what"] = ("Kitchen activity caught / wrongly called, per 10-s window, single mic, through the app's own rules; the team's "
                   "meal_metric (reweighted to the full test mix, CI by session bootstrap). Made by python -m eval.kitchen_detector --app.")
    (ROOT / "web" / "public" / "data" / "app.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    if "--app" in sys.argv:
        r = app_meal_metric()
        for k in ("app_before_rule_2f", "app_live"):
            print(k, {m: (r[k][m]["value"], [round(x, 1) for x in r[k][m]["ci95"]]) for m in ("caught", "false_alarm_rate", "right_when_it_says_so")}, "not sure", r[k]["not_sure_pct"])
        raise SystemExit(0)
    raise SystemExit(main())
