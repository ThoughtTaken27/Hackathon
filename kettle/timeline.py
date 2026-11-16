"""Window events -> the day bar's blocks, and the one-line summary sentence.

Rules, in order (all transparent, all unit-tested in tests/test_timeline.py):
1. Each window's raw label is its top activity, or "not_sure" if its top probability is below theta,
   or "talk_or_tv" if TV and Conversation are the top two and within 0.15 of each other.
1b. Second opinion (kettle/witness.py, added Sat Nov 14 after the other-homes test): when the head has no answer,
   clear general kitchen tags may name a kitchen activity; a kitchen label is withdrawn when the tags hear a motor
   or bathroom sound instead.
2. Smoothing (2 of 3): a window shows the label that at least 2 of {previous, itself, next} share.
   If all three differ it shows "not_sure". The first and last window of a run keep their raw label.
2c. Naming kitchen stretches (added Sun Nov 15 after a real-kitchen test showed pots while cooking as "washing up" and
   cutlery as "eating"): windows the general tags rescued say only "kitchen"; after smoothing, each such stretch is named
   from evidence across all of its windows (kettle/witness.py name_kitchen): cooking sounds -> cooking, running water ->
   washing up, chewing -> eating, otherwise "kitchen activity". Head-labelled windows are unchanged.
2b. Bridging: a "Not sure" stretch of at most BRIDGE_S seconds between two windows of the same activity takes that
   activity, so one cooking session reads as one block instead of confetti (the block's "how sure" still averages
   every window in it). Windows flagged as unlike anything Kettle learned are never bridged. Added Sat Nov 14 after
   the frozen held-out run (addendum item 10); measured on dev folds only.
3. Consecutive windows with the same shown label merge into one block.
4. Gaps longer than STALE_S between windows (when not paused) become "Not listening" blocks;
   pause intervals become "Paused" blocks. Smoothing never reaches across a gap.
5. Settle before showing (hold_last): while Kettle is listening, the newest window is held back until the next one
   arrives, because rule 2 can still change it. So nothing on the bar, in the summary or in a check is ever taken
   back: a check that reads "Met" stays met. (Before this rule a lone window could flip a check to Met and back.)
"""
from __future__ import annotations

from kettle import evidence, witness
from kettle.labels import DISPLAY, MEAL, PHRASE, TALK_OR_TV_MARGIN

HOP_S = 2.0
STALE_S = 2 * HOP_S + 30          # no window for longer than this = not listening
BRIDGE_S = 30.0                    # a "Not sure" gap up to this long inside one activity doesn't split its block


def head_label(ev: dict, theta: float) -> str:
    """What Kettle's own head says about one window: an activity, 'talk_or_tv' or 'not_sure'.

    'not_sure' when the top probability is below theta, or when the sound is unlike all 9 activities (ev['novel']).
    """
    if ev.get("novel"):
        return "not_sure"
    probs = ev["probs"]
    top = sorted(probs, key=probs.get, reverse=True)
    if {top[0], top[1]} == {"watching_tv", "social_activity"} and probs[top[0]] - probs[top[1]] < TALK_OR_TV_MARGIN \
            and probs[top[0]] + probs[top[1]] >= theta:
        return "talk_or_tv"
    return top[0] if probs[top[0]] >= theta else "not_sure"


def raw_label(ev: dict, theta: float) -> str:
    """One window's label before smoothing: the head's answer, checked by the second opinion (kettle/witness.py).

    Windows without a second opinion (ev['w'] missing: older data) keep the head's answer unchanged.
    """
    if ev.get("private"):
        return "private"                       # the parent chose not to share this kind of sound
    lab = head_label(ev, theta)
    w = ev.get("w")
    if witness.vetoes(lab, w, MEAL):
        return "not_sure"                      # the head said kitchen; the tags heard a motor or the bathroom
    if witness.rescues(lab, w):
        # the head had no answer; the tags clearly heard kitchen sounds. Since Sun Nov 15 (rule 2c) the window says only
        # "kitchen"; its stretch is named later from evidence across all its windows. Older windows keep the old family.
        return "kitchen" if "cook" in w else w["family"]
    return lab


# Rule 2e (Sun Nov 15, owner's call after a real room showed "Not sure" over typing, a tap and writing the sound tags had
# named correctly). Activity names still need theta. A window still "not_sure" after smoothing and bridging becomes "other"
# ("Some activity") when a person-made everyday sound was heard, "talk_or_tv" when only TV/radio/music was clear,
# "absence" when nothing was heard and the head leans quiet; otherwise it stays "not_sure". Hum and media never count as
# activity, so a fan or a TV left on can't meet an "activity by 10 AM" check. Mirrors web/public/js/core.js describe().
TAU_HEARD = 0.03                   # results/describe_rule.json
QUIET_LEAN = 0.4
AMBIENT = {"Silence", "Rustle", "Mechanical fan", "Air conditioning", "Wind", "Rain", "Bird", "Traffic noise, roadway noise", "Tick-tock", "Clock"}
MEDIA = {"Television", "Radio", "Music", "Background music", "Theme music", "Soundtrack music", "Jingle (music)", "Applause",
         "Cheering", "Crowd"}


def describe(ev: dict) -> str:
    """What a window Kettle couldn't name still honestly says (rule 2e)."""
    if ev.get("private"):
        return "private"
    loud = [x for x in ev.get("sounds") or [] if x["score"] >= TAU_HEARD]
    w = ev.get("w") or {}
    if ev.get("kinds") or any(x["name"] not in AMBIENT and x["name"] not in MEDIA for x in loud) \
            or max(w.get("k", 0), w.get("v", 0)) >= TAU_HEARD:
        return "other"
    if any(x["name"] in MEDIA for x in loud):
        return "talk_or_tv"
    p = ev.get("probs") or {}
    top = sorted(p, key=p.get, reverse=True)[0] if p else None
    return "absence" if top == "absence" and p["absence"] >= QUIET_LEAN else "not_sure"


def settle(labels: list[str], run: list[dict]) -> list[str]:
    return [describe(run[i]) if lab == "not_sure" else lab for i, lab in enumerate(labels)]


def by_sounds(ev: dict, theta: float) -> bool:
    """True when this window's label came from the second opinion, not from the head."""
    return witness.rescues(head_label(ev, theta), ev.get("w"))


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


def bridge(labels: list[str], run: list[dict], max_s: float = BRIDGE_S) -> list[str]:
    """Relabel a short 'not_sure' stretch to the activity on both sides of it (rule 2b); novel windows stay 'not_sure'."""
    out = list(labels)
    i = 1
    while i < len(out):
        if out[i] != "not_sure":
            i += 1
            continue
        j = i
        while j + 1 < len(out) and out[j + 1] == "not_sure":
            j += 1
        before = out[i - 1]
        after = out[j + 1] if j + 1 < len(out) else None
        short = run[j]["end"] - run[i - 1]["end"] <= max_s
        novel = any(run[k].get("novel") for k in range(i, j + 1))
        if before == after and before not in ("not_sure", "talk_or_tv") and short and not novel:
            out[i:j + 1] = [before] * (j - i + 1)
        i = j + 1
    return out


def name_stretches(labels: list[str], run: list[dict]) -> list[str]:
    """Rule 2c: each stretch of "kitchen" windows takes one name from evidence across the whole stretch (witness.name_kitchen).

    A stretch named "cooking" next to a head-labelled cooking stretch then joins it into one block (rule 3)."""
    out = list(labels)
    i = 0
    while i < len(out):
        if out[i] != "kitchen":
            i += 1
            continue
        j = i
        while j + 1 < len(out) and out[j + 1] == "kitchen":
            j += 1
        name = witness.name_kitchen(run[i:j + 1])
        for k in range(i, j + 1):
            out[k] = name
        i = j + 1
    return _absorb(out, run)


def _segments(labels: list[str]) -> list[tuple[int, int]]:
    segs, i = [], 0
    while i < len(labels):
        j = i
        while j + 1 < len(labels) and labels[j + 1] == labels[i]:
            j += 1
        segs.append((i, j))
        i = j + 1
    return segs


def _absorb(labels: list[str], run: list[dict]) -> list[str]:
    """Rule 2d (added Sun Nov 15): a washing-up, eating or unnamed kitchen stretch with no evidence of its own
    (no running water, no chewing) is cooking when it is at most SHORT_FLIP windows long and sits next to cooking.
    The case: the head was 93% sure of "washing up" on plates and cutlery between frying, with no tap heard.
    (A wider version, renaming long unsupported washing-up stretches when cooking sounds outvote water, cost 3 of
    132 research-home sessions on dev and was dropped.)"""
    out = list(labels)
    segs = _segments(out)
    for n, (i, j) in enumerate(segs):
        lab = out[i]
        if lab not in ("dishwashing", "eating", "kitchen") or not witness.unsupported(lab, run[i:j + 1]):
            continue
        near = [out[segs[m][0]] for m in (n - 1, n + 1) if 0 <= m < len(segs)]
        if j - i + 1 <= witness.SHORT_FLIP and "cooking" in near:
            for k in range(i, j + 1):
                out[k] = "cooking"
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
    if label in ("not_sure", "talk_or_tv", "private"):
        return label
    return "activity"


WHY_ORDER = ("veto", "novel", "close", "mixed", "low")
WHY_TEXT = {"veto": "a machine or bathroom sound was louder than any kitchen sound", "novel": "a sound unlike anything it learned",
            "close": "two activities sounded alike", "mixed": "the sounds kept changing", "low": "it wasn't sure enough"}


def why_not_sure(evs: list[dict], theta: float) -> str:
    """Why a Not sure block couldn't be named, by majority of its windows (plan F10): one of WHY_ORDER."""
    votes = dict.fromkeys(WHY_ORDER, 0)
    for e in evs:
        p = sorted(e["probs"].values(), reverse=True)
        if witness.vetoes(head_label(e, theta), e.get("w"), MEAL):
            votes["veto"] += 1
        elif e.get("novel"):
            votes["novel"] += 1
        elif p[0] >= theta:
            votes["mixed"] += 1
        elif p[0] - p[1] < TALK_OR_TV_MARGIN:
            votes["close"] += 1
        else:
            votes["low"] += 1
    return max(WHY_ORDER, key=lambda k: (votes[k], -WHY_ORDER.index(k)))


def _block(evs: list[dict], label: str, theta: float | None = None) -> dict:
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
            "guesses": [{"activity": g, "p": round(guesses[g], 3)} for g in top2],
            "by_sounds": 0 if theta is None else sum(by_sounds(e, theta) for e in evs),
            **({"why": why_not_sure(evs, theta)} if label == "not_sure" and theta is not None else {})}


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
           gap_s: float = STALE_S, bridge_s: float = BRIDGE_S, hold_last: bool = False) -> list[dict]:
    """All blocks for the day bar, in time order: activities, not sure, quiet, not listening, paused.

    pauses: [start, end] or [start, end, "off"] stretches when the parent paused or turned Kettle off.
    listening_from: when Kettle was switched on (so the time between that and the first window is not
    'not listening'); now + listening_now: whether the stretch after the last window is still live.
    hold_last: rule 5; the newest window of the day is left off until the next one arrives (use while listening).
    """
    events = sorted(events, key=lambda e: e["end"])
    out: list[dict] = []
    all_runs = runs(events, gap_s)
    for r, run in enumerate(all_runs):
        labs = smooth([raw_label(e, theta) for e in run])
        if hold_last and r == len(all_runs) - 1:        # rule 5: the newest window isn't settled yet; its neighbour
            labs, run = labs[:-1], run[:-1]             # already used it for 2-of-3, and bridging must not lean on it
        labs = settle(name_stretches(bridge(labs, run, bridge_s), run), run)   # rule 2e last
        n = len(run)
        i = 0
        while i < n:
            j = i
            while j + 1 < n and labs[j + 1] == labs[i]:
                j += 1
            out.append(_block(run[i:j + 1], labs[i], theta))
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

SUMMARY_ROUND_S = 300      # the summary rounds to 5 minutes, so "cooking around 8:05" agrees with a bar that starts at 8:05


def _round5(t: float) -> float:
    """Nearest 5 minutes. (It was 15 until Sat Nov 14: a reviewer saw "typing around 8:00-8:15" over a bar showing cooking from 8:05.)"""
    return round(t / SUMMARY_ROUND_S) * SUMMARY_ROUND_S


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
    """One summary item: 'cooking around 8:05–8:25 AM', 'washing up around 8:45 AM', 'TV from about 9:15 AM'."""
    a, z = _round5(b["start"]), _round5(b["end"])
    name = PHRASE[b["activity"]]
    if b["activity"] == "watching_tv" and z - a >= 3600:
        return f"talking / TV from about {_clock(a, tz)}"
    if z - a < 600:
        return f"{name} around {_clock(a, tz)}"
    return f"{name} around {clock_range(a, z, tz)}"


def summary(blks: list[dict], tz_offset_s: int, listening_since: float | None = None) -> str:
    """The calm one-line summary built only from the blocks (never invents an activity).

    "So far today: cooking around 8:00–8:30, washing up around 8:45, TV from about 9:15."
    Only activity blocks count; Quiet, Not sure, Talking / TV, gaps and pauses are left out.
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
    items = []
    for i, b in enumerate(merged[-3:]):
        text = _span(b, tz_offset_s)
        prev = merged[-3:][i - 1] if i else None
        if prev is not None and prev["activity"] == b["activity"]:      # "TV from about 12:45 PM and again from about 2:45 PM"
            text = "again " + text.split(" ", 1)[1]
        items.append(text)
    more = len(merged) - 3
    text = "So far today: " + ", ".join(items[:-1]) + (" and " if len(items) > 1 else "") + items[-1] + "."
    if more > 0:
        text += f" {'One earlier activity is' if more == 1 else f'{more} earlier activities are'} on the bar."
    return text


def label_name(label: str) -> str:
    """A window label in words: an activity name, 'Not sure' or 'Talking or TV'."""
    return {"not_sure": "Not sure", "talk_or_tv": "Talking / TV"}.get(label) or DISPLAY[label]


def display_name(b: dict) -> str:
    """The label drawn on a block."""
    return {"not_sure": "Not sure", "talk_or_tv": "Talking / TV", "not_listening": "Not listening", "private": "Private",
            "paused": "Paused"}.get(b["state"]) or DISPLAY[b["activity"]]
