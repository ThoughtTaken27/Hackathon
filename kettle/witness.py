"""Kettle's second opinion: the encoder's own general sound tags, used when the trained head can't be trusted.

Why two opinions. Kettle's head learned 9 activities in ONE research home (SINS). Inside that home it is good
(84 macro F1 on held-out clips). In other homes it mostly isn't: on real-home clips it had never heard, the
shipped rule showed a kitchen activity for about 1 in 12 kitchen clips (eval/other_homes.py). The encoder under
the head, CED-tiny, was pretrained on AudioSet (about 2 million clips from many places), and its 527 general tags
("Frying (food)", "Dishes, pots, and pans", "Vacuum cleaner"...) still work in homes the head has never heard.

So each window carries three numbers, made on the device from those tags and nothing else:
    k       the strongest kitchen tag (0-1)            family  which kitchen activity that tag belongs to
    v       the strongest "this is a motor or the bathroom, not the kitchen" tag (0-1)
kettle/timeline.raw_label() uses them in two plain rules:
    rescue  the head has no answer (unfamiliar sound, or below theta) and k >= TAU_K and k > v  -> show `family`
    veto    the head says a kitchen activity but v >= TAU_V and v > k                            -> show "Not sure"
The lists and thresholds live in models/witness.json (chosen on tuning halves only; see eval/PREREGISTER-V2.md).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CFG: dict = json.loads((ROOT / "models" / "witness.json").read_text())
NAMES: list[str] = json.loads((ROOT / "models" / "audioset_labels.json").read_text())
FAMILIES: tuple[str, ...] = ("cooking", "dishwashing", "eating")
TAU_K: float = CFG["tau_k"]
TAU_V: float = CFG["tau_v"]
KITCHEN_IDX: dict[str, list[int]] = {f: [NAMES.index(n) for n in CFG["kitchen"][f]] for f in FAMILIES}
VETO_IDX: list[int] = [NAMES.index(n) for n in CFG["veto"]]


def opinion(audioset: np.ndarray) -> dict:
    """527 AudioSet probabilities for one window -> {'k', 'family', 'v'} (three numbers and a word; no tag names leave)."""
    fam = [float(audioset[KITCHEN_IDX[f]].max()) for f in FAMILIES]
    best = int(np.argmax(fam))
    return {"k": round(fam[best], 3), "family": FAMILIES[best], "v": round(float(audioset[VETO_IDX].max()), 3)}


def opinions(audioset: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The same for many windows at once: (k [B], family [B] of str, v [B])."""
    fam = np.stack([audioset[:, KITCHEN_IDX[f]].max(1) for f in FAMILIES], 1)
    return fam.max(1), np.array(FAMILIES)[fam.argmax(1)], audioset[:, VETO_IDX].max(1)


def rescues(label: str, w: dict | None) -> bool:
    """True when the head had no answer and the general tags clearly hear a kitchen activity."""
    return bool(w) and label == "not_sure" and w["k"] >= TAU_K and w["k"] > w["v"]


def vetoes(label: str, w: dict | None, kitchen: set[str]) -> bool:
    """True when the head says a kitchen activity but the general tags hear a motor or bathroom sound instead."""
    return bool(w) and label in kitchen and w["v"] >= TAU_V and w["v"] > w["k"]
