"""Caregiver checks on scripted days. The safety property: not listening -> "Can't tell", never "Missed" or "Met"."""
from kettle import rules, timeline
from tests.helpers import run_of, unheard

TH = 0.5
DAY0 = 0.0          # local midnight (tz offset 0 for the tests)
H = 3600
KITCHEN = [{"id": "r1", "type": "kitchen_by", "time": "10:00"}]
TV = [{"id": "r2", "type": "tv_over", "hours": 4}]


def day(*runs):
    events = [e for r in runs for e in r]
    return events


def blocks(events, now, pauses=()):
    return timeline.blocks(events, TH, pauses=pauses, now=now, listening_now=True, listening_from=6 * H)


def state(rs, b, now):
    return rules.evaluate(rs, b, now, DAY0, 0)[0]


def test_normal_day_met_at_first_cooking():
    ev = day(run_of(6 * H, "absence", 12, dur=600), run_of(8 * H, "cooking", 4, dur=300))
    r = state(KITCHEN, blocks(ev, 11 * H), 11 * H)
    assert r["state"] == "met" and r["at"] == 8 * H and "8:00 AM" in r["detail"]


def test_not_yet_before_deadline():
    ev = run_of(6 * H, "absence", 18, dur=600)
    r = state(KITCHEN, blocks(ev, 9 * H), 9 * H)
    assert r["state"] == "not_yet" and "1 h" in r["detail"]


def test_late_start_is_missed_when_listening_the_whole_time():
    ev = day(run_of(6 * H, "absence", 27, dur=600), run_of(int(10.5 * H), "cooking", 3, dur=300))
    r = state(KITCHEN, blocks(ev, 11 * H), 11 * H)
    assert r["state"] == "missed" and "listening the whole time" in r["detail"]
    assert "10:30 AM" in r["note"]


def test_not_listening_gives_cant_tell_never_missed():
    ev = day(run_of(6 * H, "absence", 6, dur=600), run_of(int(9.9 * H), "absence", 3, dur=600))   # 7:00-9:54 unheard
    r = state(KITCHEN, blocks(ev, 11 * H), 11 * H)
    assert r["state"] == "cant_tell" and "wasn't listening" in r["detail"]


def test_paused_time_counts_as_unheard():
    ev = day(run_of(6 * H, "absence", 3, dur=600), run_of(10 * H, "absence", 6, dur=600))
    b = blocks(ev, 11 * H, pauses=[[6.5 * H, 10 * H]])
    assert state(KITCHEN, b, 11 * H)["state"] == "cant_tell"


def test_not_sure_never_satisfies_a_check():
    ev = day(run_of(6 * H, "absence", 12, dur=600), run_of(8 * H, "cooking", 6, conf=0.3, dur=600))
    r = state(KITCHEN, blocks(ev, 11 * H), 11 * H)
    assert r["state"] != "met"


def test_tv_over_and_under():
    ev = run_of(12 * H, "watching_tv", 54, dur=300)            # 4.5 h
    assert state(TV, blocks(ev, 17 * H), 17 * H)["state"] == "over"
    ev = day(run_of(6 * H, "absence", 72, dur=300), run_of(12 * H, "watching_tv", 12, dur=300))
    r = state(TV, blocks(ev, 13 * H), 13 * H)
    assert r["state"] == "under" and "1 h" in r["detail"]


def test_validate():
    ok = rules.validate([{"type": "kitchen_by", "time": "9:30"}, {"type": "tv_over", "hours": 3}])
    assert ok == [{"id": "r1", "type": "kitchen_by", "time": "09:30"}, {"id": "r2", "type": "tv_over", "hours": 3.0}]
    for bad in ([{"type": "x"}], [{"type": "tv_over", "hours": 99}], [{"type": "any_by", "time": "25:00"}], [{}] * 4):
        try:
            rules.validate(bad)
            assert False, bad
        except (ValueError, KeyError):
            pass


def test_started_after_the_check_says_so_and_is_still_cant_tell():
    ev = run_of(13 * H, "absence", 6, dur=600)                  # Kettle first heard anything at 1 PM
    b = timeline.blocks(ev, TH, now=14 * H, listening_now=True, listening_from=13 * H)
    r = state(KITCHEN, b, 14 * H)
    assert r["state"] == "cant_tell" and "started at 1:00 PM, after this check's time" in r["detail"]


def test_never_started_says_nothing_heard_yet():
    for rs in (KITCHEN, TV):
        r = state(rs, [], 14 * H)
        assert r["state"] == "cant_tell" and "hasn't heard anything yet today" in r["detail"]


def test_unnamed_sounds_before_deadline_say_so_not_heard_nothing():
    ev = day(run_of(6 * H, "absence", 20, dur=600), unheard(run_of(int(9.4 * H), "cooking", 6, conf=0.3, dur=300)),
             run_of(int(10.5 * H), "cooking", 3, dur=300))
    r = state(KITCHEN, blocks(ev, 11 * H), 11 * H)
    assert r["state"] == "missed" and r["detail"].startswith("No clear kitchen activity by 10:00 AM.")
    assert "couldn't name" in r["detail"] and "You might call to say hello." in r["note"]


def test_met_says_how_sure():
    ev = day(run_of(6 * H, "absence", 12, dur=600), run_of(8 * H, "cooking", 4, conf=0.7, dur=300))
    assert "how sure: medium" in state(KITCHEN, blocks(ev, 11 * H), 11 * H)["detail"]
