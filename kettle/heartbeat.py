"""The heartbeat: is Kettle hearing the kitchen right now? A rule, never learned.

The point (pain theme 10a): silence must never look like a normal day. "Quiet" (Kettle hears a quiet
kitchen) and "Not listening" (Kettle hears nothing at all) are different states with different words.
"""
from __future__ import annotations

from kettle.timeline import STALE_S

FIRST_LABEL_S = 10        # the first 10-s window needs 10 s of audio


def status(s: dict, now: float) -> dict:
    """Kitchen state dict + now -> {'state', 'since', 'until', 'last_heard'}.

    s keys: consent (bool), off_at, paused_at, paused_until, started_at, last_window_t, mic ('ok'|'blocked'|'none'|None).
    States, checked in this order: never, off, paused, mic_blocked, no_mic, starting, listening, stale.
    """
    last = s.get("last_window_t")
    base = {"since": None, "until": None, "last_heard": last}
    if not s.get("consent"):
        return {**base, "state": "never"}
    if s.get("off_at"):
        return {**base, "state": "off", "since": s["off_at"]}
    if s.get("paused_until") and now < s["paused_until"]:
        return {**base, "state": "paused", "since": s.get("paused_at"), "until": s["paused_until"]}
    if s.get("mic") == "blocked":
        return {**base, "state": "mic_blocked", "since": s.get("mic_at")}
    if s.get("mic") == "none":
        return {**base, "state": "no_mic", "since": s.get("mic_at")}
    started = s.get("started_at")
    if last is None or (started and last < started):
        if started and now - started <= FIRST_LABEL_S + STALE_S:
            return {**base, "state": "starting", "since": started}
        return {**base, "state": "stale", "since": started or last}
    if now - last <= STALE_S:
        return {**base, "state": "listening", "since": started}
    return {**base, "state": "stale", "since": last}
