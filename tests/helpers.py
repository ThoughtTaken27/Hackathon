"""Tiny builders for fake window events, so tests read like a day."""
from kettle.labels import CLASSES


def ev(start: float, label: str, conf: float = 0.9, dur: float = 10.0, second: str | None = None, p2: float = 0.0) -> dict:
    """A window event whose top class is `label` with probability `conf` (optionally a runner-up)."""
    rest = (1 - conf - p2) / (len(CLASSES) - (2 if second else 1))
    probs = {c: rest for c in CLASSES}
    probs[label] = conf
    if second:
        probs[second] = p2
    return {"t": start + dur, "start": start, "end": start + dur, "label": label, "conf": conf, "probs": probs,
            "sounds": [{"name": "Dishes, pots, and pans", "score": 0.3}], "kind": "window10"}


def run_of(start: float, label: str, n: int, conf: float = 0.9, dur: float = 10.0) -> list[dict]:
    return [ev(start + i * dur, label, conf, dur) for i in range(n)]
