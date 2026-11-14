"""Window events -> the day bar's blocks, and the one-line summary sentence.

Rules, in order (all transparent, all unit-tested in tests/test_timeline.py):
1. Each window's raw label is its top activity, or "not_sure" if its top probability is below theta,
   or "talk_or_tv" if TV and Conversation are the top two and within 0.15 of each other.
2. Smoothing (2 of 3): a window shows the label that at least 2 of {previous, itself, next} share.
   If all three differ it shows "not_sure". The first and last window of a run keep their raw label.
3. Consecutive windows with the same shown label merge into one block.
4. Gaps longer than STALE_S between windows (when not paused) become "Not listening" blocks;
   pause intervals become "Paused" blocks. Smoothing never reaches across a gap.
"""
from __future__ import annotations

from kettle import evidence
from kettle.labels import DISPLAY, PHRASE, TALK_OR_TV_MARGIN

HOP_S = 2.0
STALE_S = 2 * HOP_S + 30          # no window for longer than this = not listening


def raw_label(ev: dict, theta: float) -> str:
    """One window's label before smoothing: an activity, 'talk_or_tv' or 'not_sure'."""
    probs = ev["probs"]
    top = sorted(probs, key=probs.get, reverse=True)
    if {top[0], top[1]} == {"watching_tv", "social_activity"} and probs[top[0]] - probs[top[1]] < TALK_OR_TV_MARGIN \
            and probs[top[0]] + probs[top[1]] >= theta:
        return "talk_or_tv"
    return top[0] if probs[top[0]] >= theta else "not_sure"


def smooth(labels: list[str]) -> list[str]:
    """2-of-3 majority over each window and its neighbours; no majority -> 'not_sure'."""
    out = []
    for i, lab in enumerate(labels):
        if i == 0 or i == len(labels) - 1:
            out.append(lab)
            continue
        a, b, c = labels[i - 1], lab, labels[i + 1]
        out.append(b if b in (a, c) else a if a == c else "not_sure")
    return out


def runs(events: list[dict], gap_s: float = STALE_S) -> list[list[dict]]:
    """Split time-ordered events into runs with no gap longer than gap_s between them."""
    out: list[list[dict]] = []
    for ev in events:
        if out and ev["start"] - out[-1][-1]["end"] <= gap_s:
            out[-1].append(ev)
        else:
            out.append([ev])
    return out


def _state(label: str) -> str:
    if label == "absence":
        return "empty"
    if label in ("not_sure", "talk_or_tv"):
        return label
    return "activity"


def _block(evs: list[dict], label: str) -> dict:
    """Merge windows sharing a shown label into one block with its evidence."""
    if label in ("not_sure", "talk_or_tv"):
        conf = sum(max(e["probs"].values()) for e in evs) / len(evs)
    else:
        conf = sum(e["probs"].get(label, 0.0) for e in evs) / len(evs)
    guesses = {}
    for e in evs:
        for k, v in e["probs"].items():
            guesses[k] = guesses.get(k, 0.0) + v / len(evs)
    top2 = sorted(guesses, key=guesses.get, reverse=True)[:2]
    return {"start": evs[0]["start"], "end": evs[-1]["end"], "state": _state(label),
            "activity": label if _state(label) in ("activity", "empty") else None,
            "conf": round(conf, 3), "n_windows": len(evs), "sounds": evidence.merge([e["sounds"] for e in evs]),
            "guesses": [{"activity": g, "p": round(guesses[g], 3)} for g in top2]}


def _subtract(a: float, b: float, cuts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """The parts of [a, b] not covered by any interval in cuts."""
    parts = [(a, b)]
    for c0, c1 in cuts:
        nxt = []
        for p0, p1 in parts:
            if c1 <= p0 or c0 >= p1:
                nxt.append((p0, p1))
                continue
            if c0 > p0:
                nxt.append((p0, c0))
            if c1 < p1:
                nxt.append((c1, p1))
        parts = nxt
    return [(p0, p1) for p0, p1 in parts if p1 - p0 > 1]


def blocks(events: list[dict], theta: float, pauses: list = (),
           listening_from: float | None = None, now: float | None = None, listening_now: bool = False,
           gap_s: float = STALE_S) -> list[dict]:
    """All blocks for the day bar, in time order: activities, not sure, quiet, not listening, paused.

    pauses: [start, end] or [start, end, "off"] stretches when the parent paused or turned Kettle off.
    listening_from: when Kettle was switched on (so the time between that and the first window is not
    'not listening'); now + listening_now: whether the stretch after the last window is still live.
    """
    events = sorted(events, key=lambda e: e["end"])
    out: list[dict] = []
    for run in runs(events, gap_s):
        labs = smooth([raw_label(e, theta) for e in run])
        i = 0
        while i < len(run):
            j = i
            while j + 1 < len(run) and labs[j + 1] == labs[i]:
                j += 1
            out.append(_block(run[i:j + 1], labs[i]))
            i = j + 1
    for p in pauses:
        out.append({"start": p[0], "end": p[1], "state": "paused", "activity": None, "conf": None,
                    "n_windows": 0, "sounds": [], "guesses": [], "kind": p[2] if len(p) > 2 else "pause"})
    pauses = [(p[0], p[1]) for p in pauses]
    # gaps between runs, and after the last window if Kettle is no longer hearing anything
    heard = sorted((b["start"], b["end"]) for b in out if b["state"] != "paused")
    edges = []
    for (a0, a1), (b0, b1) in zip(heard, heard[1:]):
        if b0 - a1 > gap_s:
            edges.append((a1, b0))
    if heard and now is not None and not listening_now and now - heard[-1][1] > gap_s:
        edges.append((heard[-1][1], now))
    if listening_from is not None and heard and heard[0][0] - listening_from > gap_s + 10:
        edges.append((listening_from, heard[0][0]))
    for a, b in edges:
        for p0, p1 in _subtract(a, b, pauses):
            out.append({"start": p0, "end": p1, "state": "not_listening", "activity": None, "conf": None,
                        "n_windows": 0, "sounds": [], "guesses": []})
    return sorted(out, key=lambda b: b["start"])


# ---------------------------------------------------------------- summary sentence

def _round15(t: float) -> float:
    return round(t / 900) * 900


def _clock(t: float, tz_offset_s: int) -> str:
    """Unix seconds -> '8:15 AM' in the viewer's time zone (offset from UTC in seconds)."""
    s = int(t + tz_offset_s) % 86400
    h, m = divmod(s // 60, 60)
    return f"{(h % 12) or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"


def clock_range(a: float, z: float, tz: int) -> str:
    """'8:00–8:30 AM', or '11:45 AM–12:15 PM' when the range crosses noon."""
    ca, cz = _clock(a, tz), _clock(z, tz)
    return f"{ca[:-3]}–{cz}" if ca[-2:] == cz[-2:] else f"{ca}–{cz}"


def _span(b: dict, tz: int) -> str:
    """One summary item: 'cooking around 8:00–8:30 AM', 'washing up around 8:45 AM', 'TV from about 9:15 AM'."""
    a, z = _round15(b["start"]), _round15(b["end"])
    name = PHRASE[b["activity"]]
    if b["activity"] == "watching_tv" and z - a >= 3600:
        return f"TV from about {_clock(a, tz)}"
    if z - a < 900:
        return f"{name} around {_clock(a, tz)}"
    return f"{name} around {clock_range(a, z, tz)}"


def summary(blks: list[dict], tz_offset_s: int, listening_since: float | None = None) -> str:
    """The calm one-line summary built only from the blocks (never invents an activity).

    "So far today: cooking around 8:00–8:30, washing up around 8:45, TV from about 9:15."
    Only activity blocks count; Quiet, Not sure, Talking or TV, gaps and pauses are left out.
    Same activity within 15 minutes is merged; at most the 3 most recent items are listed.
    """
    acts = [b for b in blks if b["state"] == "activity"]
    merged: list[dict] = []
    for b in acts:
        if merged and merged[-1]["activity"] == b["activity"] and b["start"] - merged[-1]["end"] <= 900:
            merged[-1] = {**merged[-1], "end": b["end"]}
        else:
            merged.append(dict(b))
    if not merged:
        unsure = sum(b["end"] - b["start"] for b in blks if b["state"] == "not_sure")
        if unsure >= 20 * 60:
            return f"Kettle wasn't sure about {int(unsure // 60)} minutes of sound today."
        if listening_since is not None:
            return f"No kitchen activity heard yet today. Kettle has been listening since {_clock(listening_since, tz_offset_s)}."
        return ""
    items = [_span(b, tz_offset_s) for b in merged[-3:]]
    more = len(merged) - 3
    text = "So far today: " + ", ".join(items)
    return text + (f", and {more} more." if more > 0 else ".")


def label_name(label: str) -> str:
    """A window label in words: an activity name, 'Not sure' or 'Talking or TV'."""
    return {"not_sure": "Not sure", "talk_or_tv": "Talking or TV"}.get(label) or DISPLAY[label]


def display_name(b: dict) -> str:
    """The label drawn on a block."""
    return {"not_sure": "Not sure", "talk_or_tv": "Talking or TV", "not_listening": "Not listening",
            "paused": "Paused"}.get(b["state"]) or DISPLAY[b["activity"]]
