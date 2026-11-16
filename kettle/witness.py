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
# Evidence for naming a kitchen stretch (added Sun Nov 15; see "_evidence" in models/witness.json and name_kitchen()).
EVIDENCE_IDX: dict[str, list[int]] = {g: [NAMES.index(n) for n in CFG["evidence"][g]] for g in ("cook", "water", "mouth")}
TAU_COOK: float = CFG["tau_cook"]
TAU_WATER: float = CFG["tau_water"]
TAU_MOUTH: float = CFG["tau_mouth"]
COOK_SHARE: float = CFG["cook_share"]


DET = CFG.get("detector")
TAU_KD: float = DET["tau"] if DET else 1.0


def detector(audioset: np.ndarray) -> float:
    """P(kitchen activity) from all 527 tags (models/witness.json "detector"); 0 when no detector is configured."""
    if not DET:
        return 0.0
    a = np.clip(np.asarray(audioset, dtype=np.float64), 1e-4, 1 - 1e-4)
    z = float(np.dot(np.log(a / (1 - a)), DET["coef"]) + DET["intercept"])
    return float(1 / (1 + np.exp(-z)))


def opinion(audioset: np.ndarray) -> dict:
    """527 AudioSet probabilities for one window -> {'k', 'family', 'v'} (three numbers and a word; no tag names leave)."""
    fam = [float(audioset[KITCHEN_IDX[f]].max()) for f in FAMILIES]
    best = int(np.argmax(fam))
    out = {"k": round(fam[best], 3), "family": FAMILIES[best], "v": round(float(audioset[VETO_IDX].max()), 3)}
    for g, ix in EVIDENCE_IDX.items():                      # three more numbers: cooking, running-water and chewing evidence
        out[g] = round(float(audioset[ix].max()), 3)
    if DET:
        out["kd"] = round(detector(audioset), 3)              # one more number: the kitchen detector's probability
    return out


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


def name_kitchen(evs: list[dict]) -> str:
    """Name a stretch the general tags called kitchen activity, from evidence across ALL its windows (added Sun Nov 15).

    One loud pot or a fork on a plate in one 10-s window says little; minutes of windows say more. Order matters:
      cooking      windows where cooking sounds (frying, sizzle, boiling, chopping, stirring) beat running water: at least
                   COOK_SHARE of the stretch, and at least as many as the windows where water won
      dishwashing  otherwise, running water (tap or sink) louder than any cooking sound in at least one window
      eating       chewing or crunching in at least one window
      kitchen      none of these: "kitchen activity", without guessing which one
    Windows from before Sun Nov 15 carry no evidence numbers: they keep the old answer (the loudest tag's family).
    """
    ws = [e.get("w") or {} for e in evs]
    if not any("cook" in w for w in ws):
        fams = [w["family"] for w in ws if w.get("family") in FAMILIES]
        return max(FAMILIES, key=lambda f: (fams.count(f), -FAMILIES.index(f))) if fams else "kitchen"
    n = len(ws)
    # each window votes for the louder of its cooking and running-water evidence (a sink at 0.7 beats a faint "stir")
    cook = sum(1 for w in ws if w.get("cook", 0) >= TAU_COOK and w.get("cook", 0) >= w.get("water", 0))
    water = sum(1 for w in ws if w.get("water", 0) >= TAU_WATER and w.get("water", 0) > w.get("cook", 0))
    if cook >= max(1, COOK_SHARE * n) and cook >= water:
        return "cooking"
    if water >= 1:
        return "dishwashing"
    if any(w.get("mouth", 0) >= TAU_MOUTH for w in ws):
        return "eating"
    return "kitchen"


def votes(evs: list[dict]) -> dict:
    """Evidence votes in these windows: cook / water (the louder of the two wins each window) and mouth."""
    ws = [e.get("w") or {} for e in evs]
    return {"cook": sum(1 for w in ws if w.get("cook", 0) >= TAU_COOK and w.get("cook", 0) >= w.get("water", 0)),
            "water": sum(1 for w in ws if w.get("water", 0) >= TAU_WATER and w.get("water", 0) > w.get("cook", 0)),
            "mouth": sum(1 for w in ws if w.get("mouth", 0) >= TAU_MOUTH),
            "has": any("cook" in w for w in ws)}


SHORT_FLIP = 3      # rule 2d: an unsupported washing-up / eating / kitchen stretch this many windows or fewer, next to cooking, is cooking


def unsupported(label: str, evs: list[dict]) -> bool:
    """Rule 2d: washing up with no running water heard, eating with no chewing heard, or unnamed kitchen activity."""
    v = votes(evs)
    if not v["has"]:
        return False
    return (label == "dishwashing" and v["water"] == 0) or (label == "eating" and v["mouth"] == 0) or label == "kitchen"


def detects(label: str, w: dict | None, kitchen: set[str]) -> bool:
    """Rule 2f: the head didn't say a kitchen activity, the kitchen detector is sure enough, and no motor or bathroom
    sound is louder than the kitchen tags (the same guard as the veto). Windows without 'kd' (older data) never fire."""
    return bool(w) and "kd" in w and label not in kitchen and label not in ("private", "kitchen") and w["kd"] >= TAU_KD \
        and not (w["v"] >= TAU_V and w["v"] > w["k"])
