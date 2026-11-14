"""Addendum item 9: the θ trade-off counts kitchen sessions at the caregiver level (cooking, washing up and eating merged).

The first version reused the strict per-class session rule (the right class, as one block covering at least half of the
session), so a cooking session drawn as "washing up" counted as a missed kitchen session: 17 of 33 looked missed while
95% of kitchen windows were caught. These tests pin the caregiver-level definition the table and write-up state."""
import numpy as np

from eval.dev import theta_tradeoff
from kettle.labels import CLASSES


def _probs(label: str, conf: float = 0.9) -> np.ndarray:
    p = np.full(len(CLASSES), (1 - conf) / (len(CLASSES) - 1))
    p[CLASSES.index(label)] = conf
    return p


def _day(sessions: list[tuple[str, str]]):
    """sessions: (true label, predicted label) per 6-window session, all in fold 1."""
    y, P, session, seg = [], [], [], []
    for s, (truth, pred) in enumerate(sessions):
        for j in range(6):
            y.append(CLASSES.index(truth)); P.append(_probs(pred)); session.append(s); seg.append(j)
    n = len(y)
    return np.array(y), np.array(P), np.array(session), np.array(seg), np.ones(n, dtype=int)


def _shipped_row(rows):
    return next(r for r in rows if r["shipped"])


def test_cooking_drawn_as_washing_up_is_still_a_noticed_kitchen_session():
    y, P, session, seg, fold = _day([("cooking", "dishwashing"), ("watching_tv", "watching_tv")])
    r = _shipped_row(theta_tradeoff(y, P, session, seg, fold, shipped=0.66))
    assert r["meal_sessions"] == 1 and r["meal_sessions_missed"] == 0 and r["meal_false_alarm_blocks"] == 0


def test_cooking_drawn_as_tv_is_missed_and_tv_drawn_as_eating_is_a_false_alarm():
    y, P, session, seg, fold = _day([("cooking", "watching_tv"), ("watching_tv", "eating")])
    r = _shipped_row(theta_tradeoff(y, P, session, seg, fold, shipped=0.66))
    assert r["meal_sessions"] == 1 and r["meal_sessions_missed"] == 1 and r["meal_false_alarm_blocks"] == 1


def test_below_theta_is_not_sure_and_never_notices_a_session():
    y, P, session, seg, fold = _day([("cooking", "cooking")])
    P[:] = _probs("cooking", conf=0.5)
    r = _shipped_row(theta_tradeoff(y, P, session, seg, fold, shipped=0.66))
    assert r["meal_sessions_missed"] == 1
