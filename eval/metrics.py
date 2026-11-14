"""Metric code: confusion matrix, per-activity misses and false alarms, macro F1, prevalence
reweighting and the session bootstrap. Checked against a hand-computed example in tests/test_metrics.py.

Why reweighting: we score a class-balanced subset (dev: <= 1,000 clips per class; eval: a seeded sample with a
top-up for rare classes). Precision depends on how common each class is, so each confusion-matrix row is
multiplied by (true count of that class in the full split) / (count we scored), capped at 50, before computing
precision and F1. Recall is unchanged by row weights. Raw and reweighted numbers are both reported.

Why a session bootstrap: 10-s clips from the same session are strongly correlated, so we resample whole
sessions with replacement (1,000 draws, seed 0) and take the 2.5th and 97.5th percentiles.
"""
from __future__ import annotations

import numpy as np

K = 9
WEIGHT_CAP = 50.0


def confusion(y: np.ndarray, p: np.ndarray, k: int = K) -> np.ndarray:
    """Counts: rows = true class, columns = predicted class."""
    C = np.zeros((k, k), dtype=float)
    np.add.at(C, (np.asarray(y, int), np.asarray(p, int)), 1)
    return C


def class_weights(full_counts: np.ndarray, scored_counts: np.ndarray, cap: float = WEIGHT_CAP) -> np.ndarray:
    """Row weights = full-split count / scored count (capped); 1 where a class wasn't scored."""
    full, scored = np.asarray(full_counts, float), np.asarray(scored_counts, float)
    w = np.where(scored > 0, full / np.maximum(scored, 1), 1.0)
    return np.minimum(w, cap)


def scores(C: np.ndarray, w: np.ndarray | None = None) -> dict:
    """Per class precision, recall, F1, missed (FN), false alarms (FP), support; plus macro F1.

    With weights w, rows are scaled before precision/F1 (counts stay raw so N is honest).
    Undefined precision or recall (no predictions / no examples) counts as 0, as in DCASE and sklearn.
    """
    Cw = C * (np.ones(len(C)) if w is None else np.asarray(w))[:, None]
    tp = np.diag(Cw)
    pred = Cw.sum(0)
    true = Cw.sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        prec = np.where(pred > 0, tp / pred, 0.0)
        rec = np.where(true > 0, tp / true, 0.0)
        f1 = np.where(prec + rec > 0, 2 * prec * rec / (prec + rec), 0.0)
    return {"precision": prec, "recall": rec, "f1": f1, "macro_f1": float(f1.mean()),
            "missed": C.sum(1) - np.diag(C), "false_alarms": C.sum(0) - np.diag(C), "support": C.sum(1)}


def session_bootstrap(y: np.ndarray, p: np.ndarray, sessions: np.ndarray, w: np.ndarray | None = None,
                      n: int = 1000, seed: int = 0) -> dict:
    """95% percentile intervals for macro F1 and per-class P/R/F1, resampling whole sessions."""
    y, p, sessions = np.asarray(y, int), np.asarray(p, int), np.asarray(sessions)
    uniq, inv = np.unique(sessions, return_inverse=True)
    per = np.zeros((len(uniq), K, K))
    np.add.at(per, (inv, y, p), 1)
    rng = np.random.default_rng(seed)
    macro, prec, rec, f1 = [], [], [], []
    for _ in range(n):
        pick = rng.integers(0, len(uniq), len(uniq))
        s = scores(per[pick].sum(0), w)
        macro.append(s["macro_f1"]); prec.append(s["precision"]); rec.append(s["recall"]); f1.append(s["f1"])
    q = lambda a: np.percentile(np.asarray(a), [2.5, 97.5], axis=0)
    return {"macro_f1": q(macro), "precision": q(prec), "recall": q(rec), "f1": q(f1), "n_sessions": len(uniq), "draws": n}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% interval for a proportion k/n (used for small own-kitchen counts)."""
    if n == 0:
        return (0.0, 1.0)
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (float(max(0.0, c - h)), float(min(1.0, c + h)))
