"""Kitchen state -> what both screens show: heartbeat sentence, day bar blocks, summary, checks.

All user-facing copy for the caregiver view lives here (PRD §9.4), so the words are testable.
Times are written in the kitchen's own time zone ("Dad's time").
"""
from __future__ import annotations

import time

from kettle import heartbeat, live, rules, timeline
from kettle.labels import DISPLAY, PHRASE

PARENT = "Dad"          # how the caregiver refers to the parent (invented persona: Ravi, 79)
CAREGIVER = "Meera"     # the adult child who sees the page (invented persona)


def tz_offset(now: float) -> int:
    """The kitchen laptop's offset from UTC in seconds at time `now`."""
    return time.localtime(now).tm_gmtoff


def local_midnight(now: float) -> float:
    lt = time.localtime(now)
    return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1))


def clock(t: float | None, now: float) -> str:
    return timeline._clock(t, tz_offset(now)) if t else ""


def _ago(seconds: float) -> str:
    s = max(0, int(seconds))
    if s < 60:
        return f"{s} s"
    if s < 3600:
        return f"{s // 60} min"
    return f"{s // 3600} h {s % 3600 // 60} min"


def heartbeat_line(hb: dict, now: float, demo: bool) -> dict:
    """{'state', 'text', 'kitchen'}: the first line on the caregiver view and the kitchen headline."""
    st, since, until = hb["state"], hb["since"], hb["until"]
    c = lambda t: clock(t, now)
    if st == "never":
        text = f"Kettle isn't on yet. It starts when {PARENT} chooses to turn it on."
    elif st == "off":
        text = f"Turned off by {PARENT} at {c(since)}."
    elif st == "starting":
        text = "Starting… the first label appears in about 10 seconds."
    elif st == "listening":
        text = f"Listening · last heard {_ago(now - hb['last_heard'])} ago"
    elif st == "stale":
        text = (f"Not listening since {c(since)} (laptop asleep, closed or off). Nothing is known after that."
                if since else "Not listening. Nothing is known about today yet.")
    elif st == "paused":
        tomorrow = time.localtime(until).tm_mday != time.localtime(now).tm_mday
        tail = f"until tomorrow at {c(until)} at the latest" if tomorrow else f"resumes at {c(until)}"
        if until - now > 300 * 86400:
            tail = f"until {PARENT} answers the weekly question"
        text = f"Paused by {PARENT} at {c(since)} · {tail}"
    elif st == "mic_blocked":
        text = "Not listening: the microphone is blocked on the kitchen laptop."
    elif st == "no_mic":
        text = "Not listening: no microphone was found on the kitchen laptop."
    else:
        text = ""
    return {"state": st, "text": text, "since": since, "until": until, "last_heard": hb["last_heard"],
            "since_text": c(since), "until_text": c(until)}


def block_view(b: dict, now: float) -> dict:
    """Add the words a block needs: its label, time range and evidence-card copy."""
    tz = tz_offset(now)
    rng = timeline.clock_range(b["start"], b["end"], tz)
    out = {**b, "label": timeline.display_name(b), "range": rng}
    if b["state"] in ("activity", "empty"):
        how = "high" if b["conf"] >= 0.8 else "medium"
        out["how_sure"] = how
        out["card"] = (f"Quiet · {rng} · Kettle was listening; the kitchen was quiet." if b["state"] == "empty"
                       else f"{DISPLAY[b['activity']]} · {rng} · {b['n_windows']} windows · how sure: {how}")
    elif b["state"] == "not_sure":
        g = " · ".join(f"{DISPLAY[x['activity']]} {x['p']:.2f}" for x in b["guesses"])
        out["card"] = f"Not sure · {rng} · Kettle heard something but couldn't tell what. Closest guesses: {g}."
    elif b["state"] == "talk_or_tv":
        out["card"] = (f"Talking or TV · {rng} · Kettle heard voices and can't tell talking from the TV here. "
                       "It never keeps words.")
    elif b["state"] == "not_listening":
        out["card"] = f"Not listening · {rng} · Kettle can't say what happened here."
    elif b["state"] == "paused":
        out["label"] = f"Turned off by {PARENT}" if b.get("kind") == "off" else f"Paused by {PARENT}"
        out["card"] = f"{out['label']} · {rng}"
    return out


def today(s: dict, now: float, theta: float, demo: dict | None = None) -> dict:
    """The full payload for GET /api/today and the /ws/state push."""
    day0 = local_midnight(now)
    tz = tz_offset(now)
    hb = heartbeat.status(s, now)
    live_now = hb["state"] in ("listening", "starting")
    events = [e for e in s["events"] if e["end"] >= day0]
    pauses = [[max(p[0], day0), *p[1:]] for p in s["pauses"] if p[1] >= day0]
    if s.get("paused_at") is not None and live.is_paused(s, now):
        pauses.append([max(s["paused_at"], day0), now])
    if s.get("off_at"):
        pauses.append([max(s["off_at"], day0), now, "off"])
    started = max(s["started_at"], day0) if s.get("started_at") else None
    blks = timeline.blocks(events, theta, pauses=pauses, now=now, listening_now=live_now, listening_from=started)
    if hb["state"] in ("stale", "mic_blocked", "no_mic") and not any(b["state"] != "paused" for b in blks):
        a = max(day0, hb["since"] or day0)          # e.g. just after midnight with the laptop asleep
        if now - a > 1:
            blks.append({"start": a, "end": now, "state": "not_listening", "activity": None, "conf": None,
                         "n_windows": 0, "sounds": [], "guesses": []})
    listening_since = min((e["start"] for e in events), default=None)
    chip = s.get("chip")
    chip_text = None
    if chip and live_now and now - chip["t"] < 10:
        probs = chip["probs"]
        top = sorted(probs, key=probs.get, reverse=True)
        if chip["conf"] < theta:
            chip_text = "Not sure what that is"
        elif chip["label"] == "absence":
            chip_text = "Quiet"
        elif {top[0], top[1]} == {"watching_tv", "social_activity"} and probs[top[0]] - probs[top[1]] < 0.15:
            chip_text = "Sounds like talking or TV"
        else:
            chip_text = f"Sounds like {PHRASE[chip['label']]}"
    return {
        "now": now, "now_text": clock(now, now), "day0": day0, "tz_offset": tz,
        "date_text": time.strftime("%A, %B %-d", time.localtime(now)),
        "names": {"parent": PARENT, "caregiver": CAREGIVER},
        "heartbeat": heartbeat_line(hb, now, bool(demo)),
        "blocks": [block_view(b, now) for b in blks],
        "summary": timeline.summary(blks, tz, listening_since if live_now else None),
        "rules": rules.evaluate(s["rules"], blks, now, day0, tz),
        "rule_defs": s["rules"],
        "chip": chip_text,
        "kitchen": {"consent": s["consent"], "off": bool(s.get("off_at")), "paused": live.is_paused(s, now),
                    "pause_reason": s.get("pause_reason") if live.is_paused(s, now) else None,
                    "weekly_due": live.weekly_due(s, now), "consent_text": clock(s.get("consent_at"), now),
                    "consent_day": time.strftime("%A", time.localtime(s["consent_at"])) if s.get("consent_at") else None,
                    "listening_since_text": clock(s.get("started_at"), now)},
        "demo": demo,
        "theta": theta,
    }
