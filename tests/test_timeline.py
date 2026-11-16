"""Day-bar rules: not sure, talk-or-TV, 2-of-3 smoothing, merging, gaps and pauses; summary facts == blocks."""
from kettle import timeline
from tests.helpers import ev, run_of, unheard

TH = 0.5


def test_low_confidence_is_not_sure():
    assert timeline.raw_label(ev(0, "cooking", conf=0.4), TH) == "not_sure"
    assert timeline.raw_label(ev(0, "cooking", conf=0.6), TH) == "cooking"


def test_tv_vs_conversation_close_is_talk_or_tv():
    e = ev(0, "watching_tv", conf=0.45, second="social_activity", p2=0.40)
    assert timeline.raw_label(e, TH) == "talk_or_tv"
    e = ev(0, "watching_tv", conf=0.75, second="social_activity", p2=0.20)
    assert timeline.raw_label(e, TH) == "watching_tv"


def test_smoothing_two_of_three():
    assert timeline.smooth(["a", "b", "a"]) == ["a", "a", "a"]          # a lone flicker is absorbed
    assert timeline.smooth(["a", "b", "c"]) == ["a", "not_sure", "c"]   # no majority -> not sure
    assert timeline.smooth(["a", "a", "b", "b"]) == ["a", "a", "b", "b"]


def test_merge_into_blocks_with_evidence():
    events = run_of(0, "cooking", 5) + run_of(50, "dishwashing", 4)
    b = timeline.blocks(events, TH)
    assert [(x["state"], x["activity"], x["n_windows"]) for x in b] == [("activity", "cooking", 5), ("activity", "dishwashing", 4)]
    assert b[0]["start"] == 0 and b[0]["end"] == 50 and b[0]["sounds"][0]["name"] == "Dishes, pots, and pans"


def test_quiet_is_not_the_same_as_not_listening():
    quiet = timeline.blocks(run_of(0, "absence", 6), TH, now=60, listening_now=True)
    assert [x["state"] for x in quiet] == ["empty"]
    gone = timeline.blocks(run_of(0, "absence", 6), TH, now=600, listening_now=False)
    assert [x["state"] for x in gone] == ["empty", "not_listening"]
    assert gone[1]["start"] == 60 and gone[1]["end"] == 600


def test_gap_between_windows_is_not_listening_and_smoothing_does_not_cross_it():
    events = run_of(0, "cooking", 3) + run_of(1000, "cooking", 3)
    b = timeline.blocks(events, TH)
    assert [x["state"] for x in b] == ["activity", "not_listening", "activity"]


def test_pause_is_drawn_and_not_counted_as_not_listening():
    events = run_of(0, "cooking", 3) + run_of(4000, "cooking", 3)
    b = timeline.blocks(events, TH, pauses=[[30, 3600]])
    states = [(x["state"], round(x["start"]), round(x["end"])) for x in b]
    assert ("paused", 30, 3600) in states
    assert ("not_listening", 3600, 4000) in states
    assert not any(s == "not_listening" and a < 3600 for s, a, _ in states)


def test_summary_facts_equal_blocks():
    tz = 0
    day = 8 * 3600
    events = run_of(day, "cooking", 6, dur=300) + run_of(day + 1800, "dishwashing", 2, dur=300) + run_of(day + 3600, "watching_tv", 20, dur=300)
    b = timeline.blocks(events, TH)
    s = timeline.summary(b, tz)
    assert s.startswith("So far today: cooking around 8:00–8:30 AM")
    assert "washing up around 8:30–8:40 AM" in s and "talking / TV from about 9:00 AM" in s      # the block is 8:30-8:40; the summary says the same
    for word in ("ate", "eating", "fine", "normal", "safe"):
        assert word not in s.lower()


def test_summary_never_invents_activity_from_quiet_or_not_sure():
    b = timeline.blocks(run_of(0, "absence", 4) + unheard(run_of(40, "cooking", 4, conf=0.3)), TH)
    assert timeline.summary(b, 0, listening_since=0).startswith("No kitchen activity heard yet today.")


def _unsure_gap(start: float, n: int) -> list[dict]:
    return unheard([ev(start + i * 10, "cooking", conf=0.3) for i in range(n)])   # below θ, nothing placeable -> "not_sure"


def test_short_not_sure_gap_inside_one_activity_is_bridged():
    # addendum item 10: 3 cooking, 30 s of "not sure", 3 cooking -> one cooking block, not three pieces
    events = run_of(0, "cooking", 3) + _unsure_gap(30, 3) + run_of(60, "cooking", 3)
    b = timeline.blocks(events, TH)
    assert [(x["state"], x["activity"], x["n_windows"]) for x in b] == [("activity", "cooking", 9)]
    assert b[0]["conf"] < 0.9                         # the bridged windows still lower "how sure"


def test_long_gap_different_sides_or_novel_sounds_are_not_bridged():
    long_gap = run_of(0, "cooking", 3) + _unsure_gap(30, 4) + run_of(70, "cooking", 3)          # 40 s > BRIDGE_S
    assert [x["state"] for x in timeline.blocks(long_gap, TH)] == ["activity", "not_sure", "activity"]
    two_sides = run_of(0, "cooking", 3) + _unsure_gap(30, 2) + run_of(50, "dishwashing", 3)
    assert [x["state"] for x in timeline.blocks(two_sides, TH)] == ["activity", "not_sure", "activity"]
    novel = run_of(0, "cooking", 3) + [dict(e, novel=True) for e in _unsure_gap(30, 2)] + run_of(50, "cooking", 3)
    assert [x["state"] for x in timeline.blocks(novel, TH)] == ["activity", "not_sure", "activity"]


def test_rule_2c_names_a_kitchen_stretch_from_evidence():
    """Parth's own kitchen, Sun Nov 15: pots and cutlery while cooking were shown as washing up and eating."""
    from kettle.labels import CLASSES as C
    def win(t, fam, **ev):
        p = {c: 0.3 if c == "other" else 0.7 / 8 for c in C}
        return {"start": t, "end": t + 10, "label": "other", "conf": 0.3, "probs": p, "novel": True, "sounds": [],
                "w": {"k": 0.4, "family": fam, "v": 0, "cook": 0, "water": 0, "mouth": 0, **ev}}
    acts = lambda evs: [b["activity"] for b in timeline.blocks(evs, 0.66) if b["state"] == "activity"]
    cooking = [win(i * 10, "dishwashing" if i % 3 else "eating", **({"cook": 0.2} if i in (4, 9) else {})) for i in range(12)]
    assert acts(cooking) == ["cooking"]
    assert acts([win(i * 10, "dishwashing") for i in range(6)]) == ["kitchen"]
    assert acts([win(i * 10, "dishwashing", **({"water": 0.3} if i == 2 else {})) for i in range(6)]) == ["dishwashing"]
    assert acts([win(i * 10, "eating", **({"mouth": 0.3} if i == 3 else {})) for i in range(6)]) == ["eating"]
    old = [{**win(i * 10, "eating"), "w": {"k": 0.4, "family": "eating", "v": 0}} for i in range(4)]
    assert acts(old) == ["eating"]


def test_rule_2d_absorbs_a_short_unsupported_washing_up_flip_into_cooking():
    """The head was 93% sure of washing up on plates between frying, with no tap heard (browser e2e, Sun Nov 15)."""
    from kettle.labels import CLASSES as C
    def e(t, lab, conf, **w):
        p = {c: (1 - conf) / 8 for c in C}
        p[lab] = conf
        return {"start": t, "end": t + 10, "label": lab, "conf": conf, "probs": p, "novel": lab == "other", "sounds": [],
                "w": {"k": 0.5, "family": "cooking", "v": 0, "cook": 0, "water": 0, "mouth": 0, **w}}
    fry = lambda t: e(t, "other", 0.3, cook=0.4)
    plate = lambda t: e(t, "dishwashing", 0.93, cook=0.09, water=0.001)
    tap = lambda t: e(t, "dishwashing", 0.93, water=0.3)
    acts = lambda evs: [b["activity"] for b in timeline.blocks(evs, 0.66) if b["state"] == "activity"]
    assert acts([fry(0), fry(10), fry(20), plate(30), plate(40), fry(50), fry(60), fry(70)]) == ["cooking"]
    assert acts([fry(0), fry(10), fry(20), tap(30), tap(40), fry(50), fry(60), fry(70)]) == ["cooking", "dishwashing", "cooking"]


def test_rule_2e_heard_sounds_say_some_activity_not_not_sure():
    """Sun Nov 15, owner's call: typing, a tap and writing were named correctly, yet the bar said "Not sure"."""
    typing = [dict(e, sounds=[{"name": "Silence", "score": 0.22}, {"name": "Typing", "score": 0.046}, {"name": "Writing", "score": 0.037}])
              for e in run_of(0, "absence", 4, conf=0.35)]          # head leans quiet, below any theta used here
    assert [(x["state"], x["activity"]) for x in timeline.blocks(typing, TH)] == [("activity", "other")]


def test_rule_2e_hum_and_media_never_count_as_activity():
    hum = [dict(e, sounds=[{"name": "Silence", "score": 0.3}, {"name": "Rustle", "score": 0.09}, {"name": "Mechanical fan", "score": 0.2}])
           for e in run_of(0, "cooking", 4, conf=0.3)]
    assert [x["state"] for x in timeline.blocks(hum, TH)] == ["not_sure"]
    tv = [dict(e, sounds=[{"name": "Television", "score": 0.2}]) for e in run_of(0, "cooking", 4, conf=0.3)]
    assert [x["state"] for x in timeline.blocks(tv, TH)] == ["talk_or_tv"]
    quiet = [dict(e, sounds=[{"name": "Silence", "score": 0.4}]) for e in run_of(0, "absence", 4, conf=0.5)]
    assert [x["state"] for x in timeline.blocks(quiet, TH)] == ["empty"]


def test_rule_2e_some_activity_never_meets_a_kitchen_check():
    b = timeline.blocks(run_of(0, "cooking", 4, conf=0.3), TH)          # unsure head, pots heard -> "Some activity"
    assert [x["activity"] for x in b] == ["other"] and not any(x["activity"] in timeline.MEAL for x in b)
