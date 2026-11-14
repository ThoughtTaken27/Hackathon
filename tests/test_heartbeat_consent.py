"""Heartbeat states and the parent's consent / pause gate on live audio."""
import numpy as np

from kettle import heartbeat, live
from kettle.timeline import STALE_S


def test_never_started():
    assert heartbeat.status(live.new_state(), 100)["state"] == "never"


def test_starting_listening_stale():
    s = live.new_state()
    live.consent(s, 1000)
    assert heartbeat.status(s, 1005)["state"] == "starting"
    s["last_window_t"] = 1012
    assert heartbeat.status(s, 1020)["state"] == "listening"
    hb = heartbeat.status(s, 1012 + STALE_S + 1)
    assert hb["state"] == "stale" and hb["since"] == 1012


def test_silence_is_listening_but_no_input_is_stale():
    """Feeding silence keeps windows coming (listening); stopping input goes stale within 2 hops + 30 s."""
    s = live.new_state()
    live.consent(s, 0)
    s["last_window_t"] = 50                       # a "Quiet" window still counts as heard
    assert heartbeat.status(s, 60)["state"] == "listening"
    assert heartbeat.status(s, 50 + STALE_S + 0.1)["state"] == "stale"


def test_pause_and_off():
    s = live.new_state()
    live.consent(s, 0)
    live.pause(s, 100, 15)
    hb = heartbeat.status(s, 200)
    assert hb["state"] == "paused" and hb["since"] == 100 and hb["until"] == 100 + 900
    live.resume(s, 300)
    assert s["pauses"] == [[100, 300]]
    live.turn_off(s, 400)
    assert heartbeat.status(s, 500)["state"] == "off"


def test_pause_expires_on_tick():
    s = live.new_state()
    live.consent(s, 0)
    live.pause(s, 100, 15)
    live.tick(s, 100 + 901)
    assert not live.is_paused(s, 1100) and s["pauses"] == [[100, 1000]]


def test_until_tomorrow_is_capped_at_8am():
    import time
    now = time.mktime((2026, 11, 14, 21, 0, 0, 0, 0, -1))
    assert time.localtime(live.next_morning(now)).tm_hour == 8
    assert live.next_morning(now) - now == 11 * 3600


def _feed(s, now, seconds=12):
    st = live.new_stream()
    pcm = (np.random.default_rng(0).standard_normal(1600) * 1000).astype(np.int16).tobytes()
    calls = []
    fake_enc = None
    out = []
    import kettle.live as L
    real = L.classify
    L.classify = lambda enc, head, w: calls.append(w.shape) or [{"label": "absence", "conf": 0.9, "probs": {}, "sounds": []}] * len(w)
    try:
        for i in range(int(seconds * 10)):
            out += live.feed(s, st, pcm, now + i * 0.1, fake_enc, None)
    finally:
        L.classify = real
    return out, st


def test_audio_refused_before_consent():
    s = live.new_state()
    out, st = _feed(s, 0)
    assert out == [] and st["total"] == 0 and s["events"] == []


def test_audio_refused_while_paused_and_buffer_emptied():
    s = live.new_state()
    live.consent(s, 0)
    live.pause(s, 0, 60)
    out, st = _feed(s, 1)
    assert out == [] and len(st["ring"]) == 0


def test_audio_accepted_after_consent_ring_is_ten_seconds_max():
    s = live.new_state()
    live.consent(s, 0)
    out, st = _feed(s, 1, seconds=20)
    assert any(e["kind"] == "window10" for e in out)
    assert len(st["ring"]) <= 10 * 16000


def test_weekly_question_then_pause_if_unanswered():
    s = live.new_state()
    live.consent(s, 0)
    week = 7 * 86400
    assert not live.weekly_due(s, week - 1) and live.weekly_due(s, week)
    live.tick(s, week + 86400 + 1)
    assert live.is_paused(s, week + 86400 + 2) and s["pause_reason"] == "weekly"
    live.keep_on(s, week + 86400 + 10)
    assert not live.is_paused(s, week + 86400 + 11)
