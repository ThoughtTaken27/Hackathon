"""Model selection and every dev-fold number: fold-wise cross-validation on the official SINS dev folds.

All of this uses dev data only (the eval set is locked; see eval/guard.py). Numbers here are labelled
"dev folds (also used for selection)", because encoder, C, temperature, θ and smoothing were all chosen on them.

Steps:
1. Ours: CED-tiny embeddings, all 4 channels as training examples, logistic head. C chosen per outer fold by
   inner leave-one-fold-out CV on the 3 training folds (session-disjoint). Out-of-fold (OOF) logits for every clip.
2. Temperature fitted on OOF logits (channel 0); θ = lowest threshold whose prevalence-reweighted shown-label
   precision, macro-averaged over the 9 classes, reaches 0.9.
3. Baselines on the same folds: majority, loudness rule, log-mel + LR, AST / CED-small / CLAP linear probes,
   and zero-shot Apple / AST / CED-tiny / CLAP with maps frozen before scoring.
4. Ablations: channels, class balancing, MLP head, leave-one-node-out, 5-s chip windows, smoothing.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from eval import metrics as M
from eval.common import ROOT, apple_map_predict, audioset_map_predict, full_counts, num, table, align
from kettle import model
from kettle.labels import CLASSES

C_GRID = [0.003, 0.01, 0.03, 0.1, 0.3, 1.0]
FOLDS = [1, 2, 3, 4]
NAMES = json.loads((ROOT / "models" / "audioset_labels.json").read_text())


# ---------------------------------------------------------------- helpers

def softmax(L, T=1.0):
    return model.softmax(L.reshape(-1, L.shape[-1]), T).reshape(L.shape)


def fit_head(X: np.ndarray, y: np.ndarray, C: float, balanced: bool = True) -> dict:
    """X [n, channels, D] -> head trained on every channel as its own example."""
    n, ch, d = X.shape
    return model.fit(X.reshape(n * ch, d), np.repeat(y, ch), C=C, balanced=balanced)


def head_logits(h: dict, X: np.ndarray) -> np.ndarray:
    n, ch, d = X.shape
    return model.logits(h, X.reshape(n * ch, d)).reshape(n, ch, -1)


def choose_C(X, y, fold, train_folds, balanced=True) -> float:
    """Inner leave-one-fold-out over the training folds (session-disjoint); best channel-0 macro F1."""
    best, best_c = -1, C_GRID[0]
    for c in C_GRID:
        f1s = []
        for k in train_folds:
            tr = np.isin(fold, [f for f in train_folds if f != k])
            te = fold == k
            h = fit_head(X[tr], y[tr], c, balanced)
            p = head_logits(h, X[te][:, :1]).argmax(-1)[:, 0]
            f1s.append(M.scores(M.confusion(y[te], p))["macro_f1"])
        if np.mean(f1s) > best:
            best, best_c = np.mean(f1s), c
    return best_c


def cv_logits(X, y, fold, C=None, balanced=True, train_channels=None, nested=True, C_per_fold=None) -> tuple[np.ndarray, dict]:
    """Out-of-fold logits [n, channels, 9]; C chosen by inner CV per outer fold unless given (one C, or one per fold)."""
    out = np.zeros((len(y), X.shape[1], len(CLASSES)), np.float32)
    chosen = {}
    for k in FOLDS:
        tr, te = fold != k, fold == k
        Xtr = X[tr] if train_channels is None else X[tr][:, train_channels]
        if C_per_fold:
            c = float(C_per_fold[k] if k in C_per_fold else C_per_fold[str(k)])
        else:
            c = C if C is not None else (choose_C(Xtr, y[tr], fold[tr], [f for f in FOLDS if f != k], balanced) if nested else 1.0)
        chosen[k] = c
        h = fit_head(Xtr, y[tr], c, balanced)
        out[te] = head_logits(h, X[te])
    return out, chosen


def report(y, p, session, w, split, boot=True) -> dict:
    """Macro F1 + per class recall/precision/F1/missed/false alarms with N and session-bootstrap CIs."""
    C = M.confusion(y, p)
    raw = M.scores(C)
    rw = M.scores(C, w)
    n_s = len(np.unique(session))
    ci = M.session_bootstrap(y, p, session, w) if boot else None
    per = []
    for k, c in enumerate(CLASSES):
        sup = int(raw["support"][k])
        sess_k = len(np.unique(session[y == k]))
        per.append({"class": c,
                    "recall": num(rw["recall"][k], split, sup, sess_k, ci["recall"][:, k] if ci else None),
                    "precision": num(rw["precision"][k], split, int((p == k).sum()), n_s, ci["precision"][:, k] if ci else None),
                    "f1": num(rw["f1"][k], split, sup, sess_k, ci["f1"][:, k] if ci else None),
                    "missed": int(raw["missed"][k]), "false_alarms": int(raw["false_alarms"][k]), "support": sup})
    ci_raw = M.session_bootstrap(y, p, session, None, n=300) if boot else None
    return {"macro_f1": num(rw["macro_f1"], split, len(y), n_s, ci["macro_f1"] if ci else None),
            "macro_f1_raw": num(raw["macro_f1"], split + ", not reweighted", len(y), n_s, ci_raw["macro_f1"] if ci_raw else None),
            "per_class": per, "confusion": C.astype(int).tolist()}


def macro(y, p, w) -> float:
    return M.scores(M.confusion(y, p), w)["macro_f1"]


# ---------------------------------------------------------------- θ ("Not sure") and temperature

def theta_curve(P: np.ndarray, y: np.ndarray, w: np.ndarray) -> list[dict]:
    """For each θ: coverage (share of windows shown with a label) and reweighted shown-label precision."""
    conf, pred = P.max(1), P.argmax(1)
    wy = w[y]
    out = []
    for th in np.round(np.arange(0.20, 0.99, 0.01), 2):
        shown = conf >= th
        precs = []
        for k in range(len(CLASSES)):
            m = shown & (pred == k)
            precs.append((wy[m] * (y[m] == k)).sum() / wy[m].sum() if wy[m].sum() > 0 else np.nan)
        out.append({"theta": float(th), "coverage": float((wy * shown).sum() / wy.sum()),
                    "macro_precision_shown": float(np.nanmean(precs)), "classes_shown": int(np.sum(~np.isnan(precs)))})
    return out


def shown_stats(P, y, w, th):
    conf, pred = P.max(1), P.argmax(1)
    wy = w[y]
    shown = conf >= th
    precs = [(wy[shown & (pred == k)] * (y[shown & (pred == k)] == k)).sum() / wy[shown & (pred == k)].sum()
             for k in range(len(CLASSES)) if wy[shown & (pred == k)].sum() > 0]
    return float((wy * shown).sum() / wy.sum()), float(np.mean(precs))


def theta_ci(P, y, w, session, th, split, n=300) -> dict:
    """Coverage and shown-label precision at θ with session-bootstrap 95% CIs."""
    uniq, inv = np.unique(session, return_inverse=True)
    groups = [np.where(inv == i)[0] for i in range(len(uniq))]
    rng = np.random.default_rng(0)
    B = []
    for _ in range(n):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(uniq), len(uniq))])
        B.append(shown_stats(P[idx], y[idx], w, th))
    cov, prec = shown_stats(P, y, w, th)
    B = np.array(B)
    return {"coverage_metric": num(cov, split, len(y), len(uniq), np.percentile(B[:, 0], [2.5, 97.5])),
            "shown_precision_metric": num(prec, split, len(y), len(uniq), np.percentile(B[:, 1], [2.5, 97.5]))}


def pick_theta(curve: list[dict], target: float = 0.9) -> dict:
    ok = [c for c in curve if c["macro_precision_shown"] >= target and c["classes_shown"] == len(CLASSES)]
    return ok[0] if ok else max(curve, key=lambda c: c["macro_precision_shown"])


# ---------------------------------------------------------------- session level (the shipped pipeline)

def session_level(y, p_probs, session, seg, fold, theta, smooth=True, seed=0) -> dict:
    """Stitch each test fold's sessions into a contiguous sequence (clips in segment order, sessions in random
    order) and run the real timeline rules (θ, 2-of-3 smoothing, merge). A true session is caught if a
    same-activity block overlaps >= 50% of it; a predicted activity block that isn't >= 50% inside a same-activity
    session is a false alarm. Each clip = one 10-s window."""
    from kettle import timeline
    rng = np.random.default_rng(seed)
    caught = np.zeros(len(CLASSES)); total = np.zeros(len(CLASSES)); fa = np.zeros(len(CLASSES)); hours = 0.0
    for k in FOLDS:
        idx = np.where(fold == k)[0]
        sess = sorted(set(session[idx]))
        rng.shuffle(sess)
        events, truth, t = [], [], 0.0
        for s in sess:
            ii = idx[session[idx] == s]
            ii = ii[np.argsort(seg[ii])]
            a = t
            for i in ii:
                pr = {c: float(v) for c, v in zip(CLASSES, p_probs[i])}
                events.append({"start": t, "end": t + 10, "t": t + 10, "probs": pr, "sounds": [], "conf": max(pr.values())})
                t += 10
            truth.append((a, t, int(y[ii[0]])))
        hours += t / 3600
        if smooth:
            blks = timeline.blocks(events, theta, gap_s=1)
        else:
            labs = [timeline.raw_label(e, theta) for e in events]
            blks = []
            for e, lab in zip(events, labs):
                if blks and blks[-1]["_lab"] == lab:
                    blks[-1]["end"] = e["end"]
                else:
                    blks.append({"start": e["start"], "end": e["end"], "_lab": lab,
                                 "state": "activity" if lab in CLASSES and lab != "absence" else ("empty" if lab == "absence" else lab),
                                 "activity": lab if lab in CLASSES else None})
        acts = [b for b in blks if b["state"] in ("activity", "empty") and b["activity"]]
        for a, z, c in truth:
            total[c] += 1
            if any(CLASSES.index(b["activity"]) == c and (min(z, b["end"]) - max(a, b["start"])) >= 0.5 * (z - a) for b in acts):
                caught[c] += 1
        for b in acts:
            c = CLASSES.index(b["activity"])
            inside = sum(max(0.0, min(z, b["end"]) - max(a, b["start"])) for a, z, cc in truth if cc == c)
            if inside < 0.5 * (b["end"] - b["start"]):
                fa[c] += 1
    return {"caught": caught.astype(int).tolist(), "sessions": total.astype(int).tolist(), "false_alarm_blocks": fa.astype(int).tolist(),
            "hours": round(hours, 2), "false_alarms_per_hour": round(float(fa.sum() / max(hours, 1e-9)), 2),
            "session_recall_point": round(float(caught.sum() / total.sum()), 3),
            "session_recall": num(float(caught.sum() / total.sum()), "dev folds, activity sessions through the shipped timeline",
                                  int(total.sum()), int(total.sum()), M.wilson(int(caught.sum()), int(total.sum())))}


# ---------------------------------------------------------------- the whole dev study

def run(fast: bool = False, Cs: dict | None = None) -> dict:
    """Everything reported on dev folds. fast=True skips the slow extras (MLP, leave-one-node-out, 5-s chip).
    Cs = {"ours": {fold: C}, "logmel_lr": {fold: C}} reuses C values already chosen by nested CV (the notebook)."""
    Cs = Cs or {}
    plan = json.loads((ROOT / "data" / "meta" / "plan.json").read_text())
    from eval import embed
    train_files = {Path(f).stem for f in plan["train_files"]}
    for enc in ("ced-tiny", "logmel"):                 # required caches: score only clips both have
        train_files &= {str(f) for f in embed.load(enc, "dev")["files"]}
    T = table("ced-tiny", "dev", train_files)
    y, fold, session, node, seg = T["y"], T["fold"], T["session"], T["node"], T["seg"]
    X = T["emb"]
    scored = np.bincount(y, minlength=len(CLASSES))
    w = M.class_weights(full_counts("dev"), scored)
    split = "dev folds (also used for selection)"
    R: dict = {"split": split, "n_clips": int(len(y)), "n_sessions": int(len(np.unique(session))),
               "class_counts_scored": dict(zip(CLASSES, scored.tolist())), "weights": dict(zip(CLASSES, np.round(w, 2).tolist()))}

    # 1. ours
    L, chosen = cv_logits(X, y, fold, C_per_fold=Cs.get("ours"))
    R["C_per_fold"] = chosen
    temp = model.fit_temperature(L[:, 0], y)
    # honest calibration: each fold's temperature is fitted on the other three folds' out-of-fold logits
    P0_cross = np.zeros((len(y), len(CLASSES)))
    for k in FOLDS:
        m = fold == k
        P0_cross[m] = model.softmax(L[m][:, 0], model.fit_temperature(L[~m][:, 0], y[~m]))
    P = softmax(L, temp)
    P_node = P.mean(1)
    P0 = P[:, 0]
    R["temperature"] = temp
    R["ours_node_avg"] = report(y, P_node.argmax(1), session, w, split)
    R["ours_ch0"] = report(y, P0.argmax(1), session, w, split)
    curve = theta_curve(P0, y, w)
    pick = pick_theta(curve)
    R["not_sure"] = {"rule": "lowest θ with reweighted shown-label precision (macro over 9 classes) >= 0.90, channel 0",
                     "theta": pick["theta"], "coverage_point": pick["coverage"], "precision_shown_point": pick["macro_precision_shown"],
                     "curve": curve}
    theta = pick["theta"]
    R["not_sure"].update(theta_ci(P0, y, w, session, theta, split))
    # novelty gate: Mahalanobis distance to the nearest class mean, out-of-fold; threshold = 99th percentile in-distribution
    nov = cv_novelty(X, y, fold, chosen)
    nov_th = float(np.percentile(nov, NOVELTY_PCT))
    shown = (P0.max(1) >= theta) & (nov <= nov_th)
    wy = w[y]
    R["novelty"] = {"rule": f"'Not sure' also when the sound's Mahalanobis distance to every activity is above the {NOVELTY_PCT}th percentile of dev clips (out-of-fold)",
                    "threshold": nov_th,
                    "flagged_in_distribution": num(float((nov > nov_th).mean()), split, len(y), len(np.unique(session)),
                                                   M.wilson(int((nov > nov_th).sum()), len(y)), ),
                    "coverage_with_gate_point": round(float((wy * shown).sum() / wy.sum()), 4)}
    R["_nov"] = nov
    # ECE (calibration) on channel 0
    R["calibration"] = calibration(P0_cross, y, L[:, 0], w, session)
    R["meal_activity"] = meal_metric(y, P0.argmax(1), session, w, split)
    R["per_node"] = {nd: report(y[node == nd], P0.argmax(1)[node == nd], session[node == nd], w, split)["macro_f1"]
                     for nd in sorted(set(node))}

    # session level, through the shipped timeline rules
    R["session_level"] = {"smoothing_on": session_level(y, P0, session, seg, fold, theta, True),
                          "smoothing_off": session_level(y, P0, session, seg, fold, theta, False)}
    R["theta_tradeoff"] = theta_tradeoff(y, P0, session, seg, fold, theta)
    # addendum item 9: the same kitchen sessions under the strict per-class rule, so both definitions are reported
    on = R["session_level"]["smoothing_on"]
    sc, st = sum(on["caught"][k] for k in MEAL_IDX), sum(on["sessions"][k] for k in MEAL_IDX)
    R["meal_sessions_strict"] = {
        "rule": "kitchen session caught only if one block of its own activity (cooking, washing up or eating) covers at least half of it",
        "caught": num(sc / st, split + ", kitchen sessions through the shipped timeline at the shipped θ", st, st, M.wilson(sc, st)),
        "n_caught": int(sc), "n_sessions": int(st)}

    # 2. baselines (same folds, same weights)
    B = {}
    B["majority"] = report(y, np.zeros_like(y), session, w, split)
    lm = table("logmel", "dev", train_files)
    lm = align(T, lm)
    rms = lm["emb"][:, 0, -1]
    B["loudness_rule"] = report(y, loudness_cv(rms, y, fold, w), session, w, split)
    Llm, c_lm = cv_logits(lm["emb"], y, fold, C_per_fold=Cs.get("logmel_lr"))
    B["logmel_lr"] = report(y, Llm[:, 0].argmax(-1), session, w, split)
    B["ced_tiny_zeroshot"] = report(y, audioset_map_predict(T["scores"][:, 0], NAMES), session, w, split)
    stored = {}
    for enc in ("ast", "ced-small", "clap"):
        key = enc.replace("-", "_")
        try:
            E_all = table(enc, "dev", train_files)
        except (FileNotFoundError, KeyError, ValueError) as e:
            for name in (f"{key}_probe", f"{key}_zeroshot"):           # fall back to committed predictions
                sp = stored_probe(name, T["files"])
                if sp is not None:
                    m, pred = sp
                    r = {**report(y[m], pred, session[m], w, split), "from": "committed out-of-fold predictions"}
                    if not m.all():
                        r.update(subset=f"seeded subset: {int(m.sum())} clips",
                                 ours_same_clips=report(y[m], P0.argmax(1)[m], session[m], w, split)["macro_f1"])
                    B[name] = r
            if f"{key}_probe" not in B:
                B[f"{key}_probe"] = {"missing": f"embeddings not cached ({type(e).__name__})"}
            continue
        have = set(E_all["files"])
        sub_file = ROOT / "data" / "meta" / f"{enc}_subset.json"
        if have >= set(T["files"]):
            m = np.ones(len(y), bool)
            note = None
        else:                                  # score on the declared seeded subset only, next to ours on the same clips
            if not sub_file.exists():           # partial caches without a declared seeded subset are not scored
                B[f"{key}_probe"] = {"missing": f"only {len(have)} clips embedded and no seeded subset declared (cut)"}
                continue
            wanted = set(json.loads(sub_file.read_text())["files"])
            m = np.isin(T["files"], list(wanted & have))
            if m.sum() < 500 or not wanted <= have:
                B[f"{key}_probe"] = {"missing": f"only {int(m.sum())} of the {len(wanted)} subset clips embedded"}
                continue
            note = f"seeded subset: {int(m.sum())} clips ({sub_file.name if sub_file.exists() else 'cached clips'})"
        Ts = {k: (v[m] if isinstance(v, np.ndarray) and len(v) == len(y) else v) for k, v in T.items()}
        E = align(Ts, E_all)
        ys, fs, ss = y[m], fold[m], session[m]
        same = report(ys, P0.argmax(1)[m], ss, w, split)["macro_f1"] if note else None
        def entry(pred):
            r = report(ys, pred, ss, w, split)
            return {**r, "subset": note, "ours_same_clips": same} if note else r
        Le, _ = cv_logits(E["emb"], ys, fs, nested=not fast)
        stored[f"{key}_probe"] = Le[:, 0].argmax(-1)
        B[f"{key}_probe"] = entry(stored[f"{key}_probe"])
        if enc == "ast":
            stored["ast_zeroshot"] = audioset_map_predict(E["scores"][:, 0], NAMES)
            B["ast_zeroshot"] = entry(stored["ast_zeroshot"])
        if enc == "clap":
            stored["clap_zeroshot"] = E["scores"][:, 0].argmax(-1)
            B["clap_zeroshot"] = entry(stored["clap_zeroshot"])
        if note:
            stored[f"{key}_files"] = E["files"]
    ap = apple_predictions(T["files"])
    if ap is not None:
        B["apple_zeroshot"] = report(y, ap, session, w, split)
    R["baselines"] = B
    R["C_per_fold_baselines"] = {"logmel_lr": c_lm}
    R["_stored_predictions"] = stored

    # 3. ablations
    A = {}
    Lch0, _ = cv_logits(X, y, fold, train_channels=[0], nested=not fast)
    A["train_ch0_only"] = report(y, Lch0[:, 0].argmax(-1), session, w, split)
    Lnb, _ = cv_logits(X, y, fold, C=float(np.median(list(chosen.values()))), balanced=False)
    A["no_class_balancing"] = report(y, Lnb[:, 0].argmax(-1), session, w, split)
    if not fast:
        A["mlp_head"] = mlp_cv(X, y, fold, session, w, split)
        A["leave_one_node_out"] = lono(X, y, fold, node, w, float(np.median(list(chosen.values()))), nov_th, session)
        try:
            E5 = align(T, table("ced-tiny-5s", "dev", train_files))
            p5 = np.zeros(len(y), int)
            for k in FOLDS:
                tr, te = fold != k, fold == k
                h = fit_head(X[tr], y[tr], chosen[k])
                p5[te] = head_logits(h, E5["emb"][te][:, :1]).argmax(-1)[:, 0]
            A["chip_5s_window"] = report(y, p5, session, w, split)
        except (FileNotFoundError, KeyError, ValueError) as e:
            A["chip_5s_window"] = {"missing": f"5-s embeddings not cached for every clip ({type(e).__name__})"}
    R["ablations"] = A
    R["_oof"] = {"P0": P0, "P_node": P_node, "files": T["files"], "y": y, "scores": T["scores"][:, 0], "session": session,
                 "node": node, "fold": fold}
    return R


NOVELTY_PCT = 99


def cv_novelty(X, y, fold, chosen) -> np.ndarray:
    """Out-of-fold novelty (channel 0): fit the head + class Gaussians on training folds, score the test fold."""
    out = np.zeros(len(y))
    for k in FOLDS:
        tr, te = fold != k, fold == k
        h = fit_head(X[tr], y[tr], chosen[k])
        n, ch, d = X[tr].shape
        nv = model.fit_novelty(X[tr].reshape(n * ch, d), np.repeat(y[tr], ch), h)
        out[te] = model.novelty(h, X[te][:, 0], nv)
    return out


def ece(P, y, bins=10) -> float:
    """Expected calibration error of the top label: sum over confidence bins of share x |accuracy - confidence|."""
    conf, pred = P.max(1), P.argmax(1)
    edges = np.linspace(0, 1, bins + 1)
    out = 0.0
    for a, b in zip(edges[:-1], edges[1:]):
        m = (conf > a) & (conf <= b)
        if m.any():
            out += m.mean() * abs(float((pred[m] == y[m]).mean()) - float(conf[m].mean()))
    return out


def calibration(P, y, L, w, session, bins=10, n_boot=500) -> dict:
    """Reliability table (confidence vs observed accuracy of the top label) and ECE with a session-bootstrap CI,
    before temperature scaling (T = 1) and after (temperature cross-fitted: each fold's T from the other folds)."""
    conf, pred = P.max(1), P.argmax(1)
    rows = []
    edges = np.linspace(0, 1, bins + 1)
    for a, b in zip(edges[:-1], edges[1:]):
        m = (conf > a) & (conf <= b)
        if m.sum():
            rows.append({"bin": [round(a, 1), round(b, 1)], "n": int(m.sum()), "accuracy": round(float((pred[m] == y[m]).mean()), 3),
                         "confidence": round(float(conf[m].mean()), 3)})
    raw = model.softmax(L, 1.0)
    uniq, inv = np.unique(session, return_inverse=True)
    rng = np.random.default_rng(0)
    boots_after, boots_before = [], []
    groups = [np.where(inv == i)[0] for i in range(len(uniq))]
    for _ in range(n_boot):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(uniq), len(uniq))])
        boots_after.append(ece(P[idx], y[idx], bins))
        boots_before.append(ece(raw[idx], y[idx], bins))
    split = "dev folds (out-of-fold, channel 0, unweighted)"
    return {"ece_after_temperature": num(ece(P, y, bins), split, len(y), len(uniq), np.percentile(boots_after, [2.5, 97.5])),
            "ece_before": num(ece(raw, y, bins), split, len(y), len(uniq), np.percentile(boots_before, [2.5, 97.5])),
            "bins": rows, "bins_before": [{"confidence": round(float(raw.max(1)[(raw.max(1) > a) & (raw.max(1) <= b)].mean()), 3),
                                          "accuracy": round(float((raw.argmax(1) == y)[(raw.max(1) > a) & (raw.max(1) <= b)].mean()), 3),
                                          "n": int(((raw.max(1) > a) & (raw.max(1) <= b)).sum())}
                                         for a, b in zip(edges[:-1], edges[1:]) if ((raw.max(1) > a) & (raw.max(1) <= b)).any()],
            "note": "ECE in percentage points; temperature cross-fitted across folds so the 'after' number isn't fitted on itself"}


MEAL_IDX = [CLASSES.index(c) for c in ("cooking", "dishwashing", "eating")]


def meal_metric(y, p, session, w, split, n_boot=1000) -> dict:
    """The caregiver's metric: 'kitchen activity' (cooking, washing up, eating merged) vs everything else, per window.
    Missed = a meal-activity window called something else; false alarm = another window called meal activity."""
    ty, py = np.isin(y, MEAL_IDX), np.isin(p, MEAL_IDX)
    wy = w[y]
    rec, prec, far = rates_idx(np.arange(len(y)), ty, py, wy)
    uniq, inv = np.unique(session, return_inverse=True)
    groups = [np.where(inv == i)[0] for i in range(len(uniq))]
    rng = np.random.default_rng(0)
    B = []
    for _ in range(n_boot):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(uniq), len(uniq))])
        B.append(rates_idx(idx, ty, py, wy))
    B = np.array(B)
    ns = len(uniq)
    return {"what": "kitchen activity = cooking, washing up or eating (merged), per 10-s window, single mic",
            "caught": num(rec, split, int(ty.sum()), len(set(session[ty])), np.percentile(B[:, 0], [2.5, 97.5])),
            "right_when_it_says_so": num(prec, split, int(py.sum()), ns, np.percentile(B[:, 1], [2.5, 97.5])),
            "false_alarm_rate": num(far, split, int((~ty).sum()), ns, np.percentile(B[:, 2], [2.5, 97.5])),
            "missed": int((ty & ~py).sum()), "false_alarms": int((~ty & py).sum()), "n_meal": int(ty.sum()), "n_other": int((~ty).sum())}


def rates_idx(idx, ty, py, wy):
    """Reweighted recall, precision and false-alarm rate of a binary label on the rows idx."""
    t, p_, w_ = ty[idx], py[idx], wy[idx]
    tp = (w_ * (t & p_)).sum()
    return (tp / max(1e-9, (w_ * t).sum()), tp / max(1e-9, (w_ * p_).sum()), (w_ * (~t & p_)).sum() / max(1e-9, (w_ * ~t).sum()))


def theta_tradeoff(y, P0, session, seg, fold, shipped: float | None = None) -> list[dict]:
    """The cost of θ for Meera's check, through the shipped timeline (dev folds, sessions stitched as in session_level).
    Caregiver level: cooking, washing up and eating count as one "kitchen activity". A kitchen session is noticed if any
    kitchen-activity block overlaps it; a kitchen-activity block is a false alarm if under half of it lies inside any
    kitchen session. Reported per 16-hour day of stitched audio, for a grid of θ plus the shipped θ."""
    from kettle import timeline
    grid = sorted(set([0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9] + ([round(shipped, 2)] if shipped else [])))
    meal = set(MEAL_IDX)
    rng0 = np.random.default_rng(0)
    order = {}
    for k in FOLDS:                                   # same session order for every θ
        idx = np.where(fold == k)[0]
        sess = sorted(set(session[idx]))
        rng0.shuffle(sess)
        order[k] = sess
    out = []
    for th in grid:
        noticed = total = fa = 0
        hours = 0.0
        for k in FOLDS:
            idx = np.where(fold == k)[0]
            events, truth, t = [], [], 0.0
            for s in order[k]:
                ii = idx[session[idx] == s]
                ii = ii[np.argsort(seg[ii])]
                a = t
                for i in ii:
                    pr = {c: float(v) for c, v in zip(CLASSES, P0[i])}
                    events.append({"start": t, "end": t + 10, "t": t + 10, "probs": pr, "sounds": [], "conf": max(pr.values())})
                    t += 10
                truth.append((a, t, int(y[ii[0]]) in meal))
            hours += t / 3600
            kb = [b for b in timeline.blocks(events, th, gap_s=1) if b["state"] == "activity" and CLASSES.index(b["activity"]) in meal]
            for a, z, is_meal in truth:
                if is_meal:
                    total += 1
                    noticed += any(min(z, b["end"]) > max(a, b["start"]) for b in kb)
            for b in kb:
                inside = sum(max(0.0, min(z, b["end"]) - max(a, b["start"])) for a, z, m in truth if m)
                fa += inside < 0.5 * (b["end"] - b["start"])
        days = hours / 16
        out.append({"theta": th, "shipped": bool(shipped) and abs(th - round(shipped, 2)) < 1e-9,
                    "meal_sessions": total, "meal_sessions_missed": total - noticed,
                    "meal_false_alarm_blocks": fa, "meal_false_alarms_per_day": round(fa / days, 2), "days": round(days, 2)})
    return out
def loudness_cv(rms_log, y, fold, w) -> np.ndarray:
    """No-AI floor: loud (log RMS above a threshold chosen on the training folds) -> 'other', else 'absence'."""
    p = np.zeros_like(y)
    for k in FOLDS:
        tr, te = fold != k, fold == k
        best, bt = -1, 0
        for th in np.quantile(rms_log[tr], np.linspace(0.05, 0.95, 19)):
            f = macro(y[tr], np.where(rms_log[tr] > th, CLASSES.index("other"), 0), w)
            if f > best:
                best, bt = f, th
        p[te] = np.where(rms_log[te] > bt, CLASSES.index("other"), 0)
    return p


def mlp_cv(X, y, fold, session, w, split) -> dict:
    """Ablation: a 1-hidden-layer MLP (256 units) instead of logistic regression, same folds, channels and data."""
    from sklearn.neural_network import MLPClassifier
    p = np.zeros_like(y)
    for k in FOLDS:
        tr, te = fold != k, fold == k
        n, ch, d = X[tr].shape
        mu, sd = X[tr].reshape(-1, d).mean(0), X[tr].reshape(-1, d).std(0) + 1e-6
        clf = MLPClassifier(hidden_layer_sizes=(256,), alpha=1e-3, max_iter=60, early_stopping=True, random_state=0)
        clf.fit((X[tr].reshape(-1, d) - mu) / sd, np.repeat(y[tr], ch))
        p[te] = clf.predict((X[te][:, 0] - mu) / sd)
    return report(y, p, session, w, split)


def lono(X, y, fold, node, w, C, nov_th=None, session=None) -> dict:
    """Leave-one-node-out: train on 3 dev nodes (training folds), test on the 4th node (test fold), channel 0.
    Also: what share of the unseen microphone's windows the novelty gate flags (a proxy for a new kitchen's mic)."""
    out, flagged = {}, {}
    nodes = sorted(set(node))
    for nd in nodes:
        ys, ps, sess_l = [], [], []
        for k in FOLDS:
            tr = (fold != k) & (node != nd)
            te = (fold == k) & (node == nd)
            h = fit_head(X[tr], y[tr], C)
            ps.append(head_logits(h, X[te][:, :1]).argmax(-1)[:, 0])
            ys.append(y[te])
            sess_l.append(session[te])
            if nov_th is not None:
                n_, ch_, d_ = X[tr].shape
                nv = model.fit_novelty(X[tr].reshape(n_ * ch_, d_), np.repeat(y[tr], ch_), h)
                flagged.setdefault(nd, []).extend((model.novelty(h, X[te][:, 0], nv) > nov_th).tolist())
        yy, pp = np.concatenate(ys), np.concatenate(ps)
        ss = np.concatenate(sess_l)
        out[nd] = report(yy, pp, ss, w, "dev folds, microphone node left out of training")["macro_f1"]
    same = []
    for nd in nodes:
        ys, ps = [], []
        for k in FOLDS:
            tr, te = (fold != k), (fold == k) & (node == nd)
            h = fit_head(X[tr], y[tr], C)
            ps.append(head_logits(h, X[te][:, :1]).argmax(-1)[:, 0]); ys.append(y[te])
        same.append(round(100 * macro(np.concatenate(ys), np.concatenate(ps), w), 1))
    return {"held_out_node_macro_f1": out, "same_nodes_macro_f1_point": dict(zip(nodes, same)),
            "mean_held_out": round(float(np.mean([v["value"] for v in out.values()])), 1), "mean_same": round(float(np.mean(same)), 1),
            "novelty_flagged_share_held_out_node": {k: round(float(np.mean(v)), 3) for k, v in flagged.items()},
            "note": "channel 0, reweighted, fixed C; train folds x 3 nodes -> test fold x held-out node"}


def apple_predictions(files) -> np.ndarray | None:
    """Apple zero-shot predictions with the frozen map: from the raw scores if present, else the committed
    per-activity scores (results/baselines/apple_dev_activity.csv = the same map already applied)."""
    raw = ROOT / "results" / "baselines" / "apple_dev.jsonl"
    if raw.exists():
        a = {json.loads(l)["file"]: json.loads(l) for l in open(raw)}
        if all(f in a for f in files):
            return apple_map_predict([a[f] for f in files])
    csv = ROOT / "results" / "baselines" / "apple_dev_activity.csv"
    if csv.exists():
        rows = {l.split(",")[0]: np.array(l.strip().split(",")[1:], float) for l in list(open(csv))[1:]}
        if all(f in rows for f in files):
            S = np.stack([rows[f] for f in files])
            p = S.argmax(1)
            p[S.max(1) <= 0] = 0
            return p
    return None


def stored_probe(name: str, files) -> tuple[np.ndarray, np.ndarray] | None:
    """Committed out-of-fold predictions of a big-encoder baseline (results/cache/probes_dev.npz).
    Returns (mask over `files` that the baseline covered, predictions for those rows)."""
    p = ROOT / "results" / "cache" / "probes_dev.npz"
    if not p.exists():
        return None
    z = np.load(p)
    if name not in z.files:
        return None
    idx = {f: i for i, f in enumerate(z[name + "__files"])}
    m = np.array([f in idx for f in files])
    return m, z[name][[idx[f] for f in np.asarray(files)[m]]]
