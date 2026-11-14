"""Metric code checked against a tiny example computed by hand."""
import numpy as np

from eval.metrics import class_weights, confusion, scores, session_bootstrap, wilson


def test_hand_computed_three_classes():
    # true:  0 0 0 1 1 2 ; pred: 0 0 1 1 2 2   (only classes 0-2 used; classes 3-8 empty)
    y = np.array([0, 0, 0, 1, 1, 2])
    p = np.array([0, 0, 1, 1, 2, 2])
    C = confusion(y, p)
    assert C[0, 0] == 2 and C[0, 1] == 1 and C[1, 1] == 1 and C[1, 2] == 1 and C[2, 2] == 1
    s = scores(C)
    # class 0: P = 2/2, R = 2/3, F1 = 0.8 ; class 1: P = 1/2, R = 1/2, F1 = 0.5 ; class 2: P = 1/2, R = 1, F1 = 2/3
    assert np.allclose(s["precision"][:3], [1.0, 0.5, 0.5])
    assert np.allclose(s["recall"][:3], [2 / 3, 0.5, 1.0])
    assert np.allclose(s["f1"][:3], [0.8, 0.5, 2 / 3])
    assert np.allclose(s["f1"][3:], 0)                       # empty classes score 0 (DCASE / sklearn convention)
    assert np.isclose(s["macro_f1"], (0.8 + 0.5 + 2 / 3) / 9)
    assert list(s["missed"][:3]) == [1, 1, 0] and list(s["false_alarms"][:3]) == [0, 1, 1]


def test_reweighting_changes_precision_not_recall():
    y = np.array([0, 0, 0, 1, 1, 2])
    p = np.array([0, 0, 1, 1, 2, 2])
    C = confusion(y, p)
    w = np.ones(9)
    w[0] = 10                                                # class 0 is 10x more common in the full split
    s = scores(C, w)
    # class 1 predicted: 10 (from class 0) + 1 (true 1) -> precision 1/11 ; recall unchanged 1/2
    assert np.isclose(s["precision"][1], 1 / 11)
    assert np.isclose(s["recall"][1], 0.5)
    assert list(s["missed"][:3]) == [1, 1, 0]               # counts stay raw


def test_class_weights_cap_and_unscored():
    w = class_weights(np.array([1000, 10, 5] + [0] * 6), np.array([10, 10, 0] + [0] * 6))
    assert w[0] == 50 and w[1] == 1 and w[2] == 1


def test_bootstrap_is_deterministic_and_brackets_point():
    rng = np.random.default_rng(1)
    y = rng.integers(0, 9, 400)
    p = np.where(rng.random(400) < 0.7, y, rng.integers(0, 9, 400))
    sess = rng.integers(0, 40, 400)
    a = session_bootstrap(y, p, sess, n=200)
    b = session_bootstrap(y, p, sess, n=200)
    assert np.allclose(a["macro_f1"], b["macro_f1"])
    point = scores(confusion(y, p))["macro_f1"]
    assert a["macro_f1"][0] <= point <= a["macro_f1"][1]


def test_wilson():
    lo, hi = wilson(8, 10)
    assert 0.49 < lo < 0.50 and 0.94 < hi < 0.95
