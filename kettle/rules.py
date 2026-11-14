"""Caregiver-set checks ("Kitchen activity by 10:00 AM"). Rules decide; the model only labels.

These are rules Meera sets, never something Kettle learns. Each check reads only the day bar's blocks.
The safety rule: when Kettle wasn't listening for more than a quarter of the check's window, the answer
is "Can't tell", never "Missed" and never "Met". Unknown is never fine, and never alarming either.
"""
from __future__ import annotations

from kettle.labels import ACTIVE, MEAL, PHRASE
from kettle.timeline import _clock, clock_range

MAX_RULES = 3
CANT_TELL_SHARE = 0.25     # unheard share of the window above which a check says "Can't tell"
WINDOW_START_H = 6         # "by 10:00 AM" checks the stretch from 6:00 AM

DEFAULT_RULES = [
    {"id": "r1", "type": "kitchen_by", "time": "10:00"},
    {"id": "r2", "type": "tv_over", "hours": 4},
]


def title(rule: dict) -> str:
    """The check's name as the caregiver wrote it."""
    if rule["type"] == "tv_over":
        h = rule["hours"]
        return f"TV on for more than {h:g} hour{'s' if h != 1 else ''}"
    what = "Kitchen activity" if rule["type"] == "kitchen_by" else "Some sound of activity"
    return f"{what} by {_hhmm(rule['time'])}"


def _hhmm(s: str) -> str:
    h, m = map(int, s.split(":"))
    return f"{(h % 12) or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"


def _counts(rule: dict, b: dict) -> bool:
    """Does this block satisfy the check? Only confident activity blocks count; 'Not sure' never does."""
    if rule["type"] == "kitchen_by":
        return b["state"] == "activity" and b["activity"] in MEAL
    return (b["state"] == "activity" and b["activity"] in ACTIVE) or b["state"] == "talk_or_tv"


def unheard(blocks: list[dict], a: float, z: float) -> list[tuple[float, float]]:
    """Stretches inside [a, z] that no heard block covers (Kettle off, asleep, paused or not yet on)."""
    heard = sorted((max(a, b["start"]), min(z, b["end"])) for b in blocks
                   if b["state"] not in ("not_listening", "paused") and b["end"] > a and b["start"] < z)
    gaps, t = [], a
    for s, e in heard:
        if s > t + 1:
            gaps.append((t, s))
        t = max(t, e)
    if z > t + 1:
        gaps.append((t, z))
    return gaps


def _dur(seconds: float) -> str:
    m = int(round(seconds / 60))
    h, m = divmod(m, 60)
    return f"{h} h {m} min" if h and m else f"{h} h" if h else f"{m} min"


def evaluate(rules: list[dict], blocks: list[dict], now: float, day0: float, tz: int) -> list[dict]:
    """Every rule -> {'id', 'type', 'title', 'state', 'at', 'detail', 'note'}.

    day0 = local midnight today (unix s); tz = local offset from UTC in seconds (for clock text).
    States: met, not_yet, missed, cant_tell (by-time checks); over, under, cant_tell (TV check).
    """
    out = []
    for r in rules[:MAX_RULES]:
        out.append({"id": r["id"], "type": r["type"], "title": title(r), **_one(r, blocks, now, day0, tz)})
    return out


def _one(r: dict, blocks: list[dict], now: float, day0: float, tz: int) -> dict:
    if r["type"] == "tv_over":
        return _tv(r, blocks, now, day0, tz)
    h, m = map(int, r["time"].split(":"))
    deadline = day0 + h * 3600 + m * 60
    start = min(day0 + WINDOW_START_H * 3600, deadline - 3600)
    first = next((b for b in sorted(blocks, key=lambda b: b["start"])
                  if _counts(r, b) and b["start"] < deadline and b["start"] <= now), None)
    if first:
        what = PHRASE[first["activity"]] if first["activity"] else "talking or TV"
        return {"state": "met", "at": first["start"], "detail": f"Met at {_clock(first['start'], tz)} ({what})",
                "note": None}
    end = min(now, deadline)
    gaps = unheard(blocks, start, end) if end > start else []
    missing = sum(b - a for a, b in gaps)
    if now < deadline:
        left = deadline - now
        return {"state": "not_yet", "at": None, "detail": f"Not yet · checks in {_dur(left)}", "note": None}
    if missing > CANT_TELL_SHARE * (deadline - start):
        heard = [b for b in blocks if b["state"] not in ("not_listening", "paused")]
        first = min((b["start"] for b in heard), default=None)
        if first is None:
            return {"state": "cant_tell", "at": None, "detail": "Can't tell: Kettle hasn't heard anything yet today.", "note": None}
        if first >= deadline:                             # Kettle only started after this check's time
            return {"state": "cant_tell", "at": None,
                    "detail": f"Can't tell: Kettle started at {_clock(first, tz)}, after this check's time.", "note": None}
        a, b = max(gaps, key=lambda g: g[1] - g[0])
        return {"state": "cant_tell", "at": None,
                "detail": f"Can't tell: Kettle wasn't listening from {clock_range(a, b, tz)}.", "note": None}
    later = next((b for b in sorted(blocks, key=lambda b: b["start"]) if _counts(r, b) and b["start"] >= deadline), None)
    whole = "Kettle was listening the whole time." if missing < 60 else \
        f"Kettle was listening for {round(100 * (1 - missing / (deadline - start)))}% of that time."
    note = f"First heard at {_clock(later['start'], tz)}." if later else "You might call to say hello."
    return {"state": "missed", "at": deadline, "detail": f"Not heard by {_hhmm(r['time'])}. {whole}", "note": note}


def _tv(r: dict, blocks: list[dict], now: float, day0: float, tz: int) -> dict:
    tv = [b for b in blocks if b["state"] == "activity" and b["activity"] == "watching_tv"]
    total = sum(b["end"] - b["start"] for b in tv)
    if total > r["hours"] * 3600:
        return {"state": "over", "at": None,
                "detail": f"TV for {_dur(total)} today (from {_clock(tv[0]['start'], tz)})", "note": None}
    start = day0 + WINDOW_START_H * 3600
    gaps = unheard(blocks, start, now) if now > start else []
    missing = sum(b - a for a, b in gaps)
    if now > start and missing > CANT_TELL_SHARE * (now - start):
        heard = [b for b in blocks if b["state"] not in ("not_listening", "paused")]
        first = min((b["start"] for b in heard), default=None)
        lead = ("Can't tell: Kettle hasn't heard anything yet today." if first is None else
                f"Can't tell yet: Kettle has only been listening since {_clock(first, tz)}." if first - start > 0.5 * (now - start)
                else f"Can't tell: Kettle wasn't listening for {_dur(missing)} today.")
        return {"state": "cant_tell", "at": None,
                "detail": lead,
                "note": f"TV heard for {_dur(total)}." if total else None}
    return {"state": "under", "at": None,
            "detail": f"TV for {_dur(total)} so far today" if total else "No TV heard today", "note": None}


def validate(rules: list[dict]) -> list[dict]:
    """Clean rules from the caregiver page: at most 3, known types, sane times. Raises ValueError."""
    if not isinstance(rules, list) or len(rules) > MAX_RULES:
        raise ValueError("up to 3 checks")
    out = []
    for i, r in enumerate(rules):
        t = r.get("type")
        if t in ("kitchen_by", "any_by"):
            h, m = map(int, str(r["time"]).split(":"))
            if not (0 <= h < 24 and 0 <= m < 60):
                raise ValueError("bad time")
            out.append({"id": f"r{i + 1}", "type": t, "time": f"{h:02d}:{m:02d}"})
        elif t == "tv_over":
            h = float(r["hours"])
            if not 0.5 <= h <= 16:
                raise ValueError("bad hours")
            out.append({"id": f"r{i + 1}", "type": t, "hours": h})
        else:
            raise ValueError("unknown check")
    return out
