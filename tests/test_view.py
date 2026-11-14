"""The caregiver's words: heartbeat sentences, pause attribution, and no reassurance words anywhere."""
from kettle import live, view
from tests.helpers import run_of

import time
NOW = time.mktime((2026, 11, 14, 12, 0, 0, 0, 0, -1))      # local noon, so no test crosses midnight


def payload(s, now=NOW):
    return view.today(s, now, theta=0.5)


def test_never_started_copy():
    t = payload(live.new_state())
    assert t["heartbeat"]["state"] == "never" and "isn't on yet" in t["heartbeat"]["text"]


def test_listening_vs_stale_copy():
    s = live.new_state()
    live.consent(s, NOW - 600)
    s["events"] = run_of(NOW - 120, "absence", 10)
    s["last_window_t"] = s["events"][-1]["t"]
    t = payload(s, s["last_window_t"] + 20)
    assert t["heartbeat"]["text"].startswith("Listening · last heard 20 s ago")
    t = payload(s, s["last_window_t"] + 3600)
    assert t["heartbeat"]["state"] == "stale" and "Nothing is known after that" in t["heartbeat"]["text"]
    assert any(b["state"] == "not_listening" for b in t["blocks"])


def test_pause_is_attributed_to_the_parent_and_drawn():
    s = live.new_state()
    live.consent(s, NOW - 600)
    live.pause(s, NOW - 60, 60)
    t = payload(s)
    assert t["heartbeat"]["text"].startswith("Paused by Dad at") and "resumes at" in t["heartbeat"]["text"]
    assert any(b["state"] == "paused" and b["label"] == "Paused by Dad" for b in t["blocks"])


def test_no_reassurance_or_diagnosis_words():
    s = live.new_state()
    live.consent(s, NOW - 4000)
    s["events"] = run_of(NOW - 3600, "cooking", 30, dur=60) + run_of(NOW - 1800, "absence", 30, dur=60)
    s["last_window_t"] = s["events"][-1]["t"]
    t = payload(s, s["last_window_t"] + 5)
    words = " ".join([t["heartbeat"]["text"], t["summary"]] + [b.get("card", "") for b in t["blocks"]] +
                     [r["detail"] + (r["note"] or "") for r in t["rules"]]).lower()
    for bad in ("safe", "fine", "normal day", "healthy", "nothing to worry", "!", "dad ate", "monitor"):
        assert bad not in words, bad


def test_after_midnight_a_sleeping_laptop_still_shows_not_listening():
    s = live.new_state()
    live.consent(s, NOW - 86400)
    s["last_window_t"] = NOW - 13 * 3600              # last heard 11 PM yesterday
    t = payload(s)
    assert t["heartbeat"]["state"] == "stale"
    assert [b["state"] for b in t["blocks"]] == ["not_listening"]
