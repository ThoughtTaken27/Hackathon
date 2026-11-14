"""Live listening: the parent's consent and pause gate, a RAM-only ring buffer, and window events.

Audio arrives as 16 kHz Int16 chunks from the kitchen page. It lives only in a numpy array of the last
10 seconds, which is overwritten as new audio comes in and emptied on pause. Nothing is written to disk
or sent anywhere; only labels, scores and times leave this module.
"""
from __future__ import annotations

import time

import numpy as np

from kettle import encoders, evidence, model
from kettle.labels import CLASSES
from kettle.rules import DEFAULT_RULES

SR = 16000
WIN_S = 10          # the timeline window (the unit SINS is labelled in)
CHIP_S = 5          # the faster "Sounds like..." chip on the kitchen screen
HOP_S = 2           # a new label every 2 s
WEEK_S = 7 * 86400


def new_state() -> dict:
    """A kitchen with nobody's consent yet. Plain dict so every field is visible."""
    return {"consent": False, "consent_at": None, "last_confirm": None, "off_at": None,
            "paused_at": None, "paused_until": None, "pause_reason": None, "pauses": [],
            "started_at": None, "last_window_t": None, "mic": None, "mic_at": None,
            "events": [], "chip": None, "rules": [dict(r) for r in DEFAULT_RULES], "log": []}


def new_stream() -> dict:
    """Per-connection audio buffer: at most the last 10 s of samples, in RAM only."""
    return {"ring": np.zeros(0, dtype=np.float32), "since_hop": 0, "total": 0, "prev_end": None}


# ---------------------------------------------------------------- the parent's controls

def _log(s: dict, now: float, kind: str, **extra) -> dict:
    rec = {"t": now, "type": kind, **extra}
    s["log"].append(rec)
    return rec


def consent(s: dict, now: float) -> dict:
    """The parent pressed 'Yes, Meera can see this' on the kitchen laptop."""
    s.update(consent=True, consent_at=now, last_confirm=now, off_at=None, started_at=now)
    return _log(s, now, "consent")


def turn_off(s: dict, now: float) -> dict:
    """The parent turned Kettle off. Listening stops until they press Start again."""
    _close_pause(s, now)
    s.update(off_at=now, paused_at=None, paused_until=None)
    return _log(s, now, "off")


def start(s: dict, now: float) -> dict:
    """The parent pressed Start after turning Kettle off (consent was already given)."""
    if s.get("off_at"):
        s["pauses"].append([s["off_at"], now, "off"])
    s.update(off_at=None, started_at=now)
    return _log(s, now, "start")


def next_morning(now: float, hour: int = 8) -> float:
    """Unix time of the next 8:00 AM (local), used as the cap for 'Pause until tomorrow morning'."""
    lt = time.localtime(now)
    today8 = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, hour, 0, 0, 0, 0, -1))
    return today8 if today8 > now else time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday + 1, hour, 0, 0, 0, 0, -1))


def pause(s: dict, now: float, minutes: int | None, reason: str = "parent") -> dict:
    """Pause for 15 or 60 minutes, or until tomorrow morning (minutes=None, capped at 8 AM)."""
    until = now + minutes * 60 if minutes else next_morning(now)
    if not is_paused(s, now):
        s["paused_at"] = now
    s.update(paused_until=until, pause_reason=reason)
    return _log(s, now, "pause", until=until, reason=reason)


def _close_pause(s: dict, now: float) -> None:
    if s.get("paused_at") is not None:
        s["pauses"].append([s["paused_at"], min(now, s["paused_until"] or now)])


def resume(s: dict, now: float) -> dict:
    """The parent pressed 'Resume listening'."""
    _close_pause(s, now)
    s.update(paused_at=None, paused_until=None, pause_reason=None, started_at=now)
    return _log(s, now, "resume")


def is_paused(s: dict, now: float) -> bool:
    return bool(s.get("paused_until")) and now < s["paused_until"]


def tick(s: dict, now: float) -> None:
    """Housekeeping each second: end pauses that ran out; pause if the weekly question went unanswered."""
    if s.get("paused_until") and now >= s["paused_until"]:
        s["pauses"].append([s["paused_at"], s["paused_until"]])
        _log(s, s["paused_until"], "resume", auto=True)
        s.update(paused_at=None, paused_until=None, pause_reason=None, started_at=now)
    if weekly_due(s, now) and now - s["last_confirm"] > WEEK_S + 86400 and not is_paused(s, now):
        pause(s, now, minutes=None, reason="weekly")
        s["paused_until"] = now + 365 * 86400        # until the parent answers "Keep it on?"


def weekly_due(s: dict, now: float) -> bool:
    """True when a week has passed since the parent last said yes: the kitchen screen asks 'Keep it on?'."""
    return bool(s.get("consent")) and not s.get("off_at") and now - (s.get("last_confirm") or now) >= WEEK_S


def keep_on(s: dict, now: float) -> dict:
    """The parent answered 'Keep it on' to the weekly question."""
    s["last_confirm"] = now
    if s.get("pause_reason") == "weekly":
        resume(s, now)
    return _log(s, now, "keep_on")


def can_listen(s: dict, now: float) -> bool:
    """The gate: audio is accepted only after consent, when not turned off and not paused."""
    return bool(s.get("consent")) and not s.get("off_at") and not is_paused(s, now)


# ---------------------------------------------------------------- hearing

def classify(enc: dict, head: dict, waves: np.ndarray) -> list[dict]:
    """float32 [B, samples] -> per window {'label', 'conf', 'probs', 'sounds'} (the model's output only)."""
    emb, audioset = encoders.embed(enc, waves)
    P = model.predict_proba(head, emb)
    out = []
    for p, a in zip(P, audioset):
        k = int(p.argmax())
        out.append({"label": CLASSES[k], "conf": round(float(p[k]), 3),
                    "probs": {c: round(float(v), 4) for c, v in zip(CLASSES, p)},
                    "sounds": evidence.top_sounds(a)})
    return out


def feed(s: dict, st: dict, pcm: bytes, now: float, enc: dict, head: dict) -> list[dict]:
    """Add one Int16 chunk from the kitchen mic; every HOP_S return new events (chip and/or window).

    Refuses audio (returns [] and empties the buffer) unless consent is given and Kettle isn't paused/off.
    """
    if not can_listen(s, now):
        st.update(ring=np.zeros(0, dtype=np.float32), since_hop=0, total=0, prev_end=None)
        return []
    x = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    st["ring"] = np.concatenate([st["ring"], x])[-WIN_S * SR:]
    st["since_hop"] += len(x)
    st["total"] += len(x)
    if st["since_hop"] < HOP_S * SR:
        return []
    st["since_hop"] = 0
    out = []
    if st["total"] >= CHIP_S * SR:
        chip = classify(enc, head, st["ring"][None, -CHIP_S * SR:])[0]
        s["chip"] = {**chip, "t": now, "kind": "chip5"}
        out.append(s["chip"])
    if st["total"] >= WIN_S * SR:
        w = classify(enc, head, st["ring"][None, :])[0]
        start = st["prev_end"] if st["prev_end"] and now - st["prev_end"] < 3 * HOP_S else now - WIN_S
        ev = {**w, "t": now, "start": start, "end": now, "kind": "window10"}
        st["prev_end"] = now
        s["events"].append(ev)
        s["last_window_t"] = now
        out.append(ev)
    return out


def set_mic(s: dict, now: float, state: str) -> dict:
    """The kitchen page reports the microphone: 'ok', 'blocked' (permission denied) or 'none' (no device)."""
    s.update(mic=state, mic_at=now)
    if state == "ok":
        s["started_at"] = now
    return _log(s, now, "mic", state=state)


def replay(s: dict, rec: dict, keep_windows: bool = True) -> None:
    """Re-apply one saved record (from data/timeline/*.jsonl) after a restart, so nothing is lost."""
    t = rec.get("t", 0)
    if rec.get("kind") == "window":
        if keep_windows:
            ev = {k: v for k, v in rec.items() if k != "kind"}
            s["events"].append(ev)
            s["last_window_t"] = ev["t"]
        return
    if rec.get("kind") == "rules":
        s["rules"] = rec["rules"]
        return
    kind = rec.get("type")
    if kind == "consent":
        consent(s, t)
    elif kind == "pause":
        if not is_paused(s, t):
            s["paused_at"] = t
        s.update(paused_until=rec["until"], pause_reason=rec.get("reason", "parent"))
    elif kind == "resume":
        resume(s, t)
    elif kind == "off":
        turn_off(s, t)
    elif kind == "start":
        start(s, t)
    elif kind == "keep_on":
        keep_on(s, t)
    elif kind == "mic":
        set_mic(s, t, rec["state"])
