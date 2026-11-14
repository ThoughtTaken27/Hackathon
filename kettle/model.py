"""The trained part of Kettle: a logistic-regression head on CED-tiny embeddings.

Saved as plain JSON (numbers only, no pickle) so anyone can read it and nothing can execute on load.
  probability = softmax((standardised embedding @ coef.T + intercept) / temperature)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from kettle.labels import CLASSES


def fit(X: np.ndarray, y: np.ndarray, C: float = 1.0, balanced: bool = True, seed: int = 0) -> dict:
    """Fit a standardiser and a multinomial logistic regression; return the head as a plain dict."""
    from sklearn.linear_model import LogisticRegression
    mean, std = X.mean(0), X.std(0) + 1e-6
    lr = LogisticRegression(C=C, max_iter=3000, class_weight="balanced" if balanced else None,
                            random_state=seed)
    lr.fit((X - mean) / std, y)
    coef = np.zeros((len(CLASSES), X.shape[1]))
    intercept = np.full(len(CLASSES), -1e4)       # a class never seen in training can never win
    coef[lr.classes_] = lr.coef_
    intercept[lr.classes_] = lr.intercept_
    return {"classes": list(CLASSES), "mean": mean.tolist(), "std": std.tolist(), "coef": coef.tolist(),
            "intercept": intercept.tolist(), "C": C, "balanced": balanced, "temperature": 1.0, "theta": 0.5}


def logits(head: dict, X: np.ndarray) -> np.ndarray:
    """Raw class scores [B, 9] before temperature and softmax."""
    z = (X - np.asarray(head["mean"])) / np.asarray(head["std"])
    return z @ np.asarray(head["coef"]).T + np.asarray(head["intercept"])


def softmax(L: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """Row-wise softmax of L / temperature."""
    L = L / temperature
    L = L - L.max(1, keepdims=True)
    e = np.exp(L)
    return e / e.sum(1, keepdims=True)


def predict_proba(head: dict, X: np.ndarray) -> np.ndarray:
    """Embeddings [B, D] -> calibrated probabilities [B, 9] in CLASSES order."""
    return softmax(logits(head, X), head.get("temperature", 1.0))


def fit_temperature(L: np.ndarray, y: np.ndarray) -> float:
    """The temperature that minimises negative log-likelihood on held-out logits (grid search, 0.25-5)."""
    best, best_t = np.inf, 1.0
    for t in np.round(np.arange(0.25, 5.01, 0.05), 2):
        p = softmax(L, t)
        nll = -np.log(np.clip(p[np.arange(len(y)), y], 1e-12, None)).mean()
        if nll < best:
            best, best_t = nll, float(t)
    return best_t


def sha256(head: dict) -> str:
    """Fingerprint of the head's numbers (excluding the sha256 field itself)."""
    body = json.dumps({k: v for k, v in head.items() if k != "sha256"}, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()


def save(head: dict, path: Path) -> str:
    """Write the head as JSON with its sha256; returns the hash."""
    head = dict(head)
    head["sha256"] = sha256(head)
    Path(path).write_text(json.dumps(head))
    return head["sha256"]


def load(path: Path) -> dict:
    """Read a head written by save() and check its hash still matches its numbers."""
    head = json.loads(Path(path).read_text())
    if head.get("sha256") != sha256(head):
        raise ValueError(f"{path}: sha256 does not match its contents")
    return head
