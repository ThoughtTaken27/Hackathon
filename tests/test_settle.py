"""Rule 5, settle before showing: while listening, nothing on the bar or in a check is ever taken back."""
import random

from kettle import rules, timeline
from kettle.labels import MEAL
from tests.helpers import ev

TH = 0.66
LABELS = ["absence", "cooking", "working", "other", "dishwashing", "watching_tv"]


def shown_kitchen(blks):
    return [(b["start"], b["activity"]) for b in blks if b["state"] == "activity" and b["activity"] in MEAL]


def test_the_reviewers_sequence_never_flips_the_check_back():
    """typing, cooking, typing, cooking, cooking: before rule 5 the 10 AM check read Met, then Not yet, then Met."""
    day0, seq = 0.0, ["working", "cooking", "working", "cooking", "cooking", "cooking"]
    events, states = [], []
    for i, lab in enumerate(seq):
        events.append(ev(8 * 3600 + i * 10, lab, conf=0.9))
        now = events[-1]["end"] + 1
        blks = timeline.blocks(events, TH, now=now, listening_now=True, hold_last=True)
        states.append(rules.evaluate([{"id": "r1", "type": "kitchen_by", "time": "10:00"}], blks, now, day0, 0)[0]["state"])
    met = [s == "met" for s in states]
    assert met == sorted(met), states            # once met, always met
    assert met[-1]


def test_random_days_never_take_back_a_kitchen_block_or_a_met_check():
    rng = random.Random(7)
    for _ in range(200):
        seq = [rng.choice(LABELS) for _ in range(rng.randint(3, 40))]
        confs = [rng.choice([0.5, 0.7, 0.9]) for _ in seq]
        events, was_met, seen = [], False, set()
        for i, (lab, c) in enumerate(zip(seq, confs)):
            events.append(ev(7 * 3600 + i * 10, lab, conf=c))
            now = events[-1]["end"] + 1
            blks = timeline.blocks(events, TH, now=now, listening_now=True, hold_last=True)
            met = rules.evaluate([{"id": "r1", "type": "kitchen_by", "time": "10:00"}], blks, now, 0.0, 0)[0]["state"] == "met"
            assert met or not was_met, (seq, confs, i)
            was_met = met
            covered = {e["end"] for b in blks if b["state"] == "activity" and b["activity"] in MEAL
                       for e in events if b["start"] <= e["start"] and e["end"] <= b["end"]}
            assert seen <= covered, (seq, confs, i)      # a window once shown as kitchen stays kitchen
            seen = covered


def test_the_newest_window_appears_once_it_is_no_longer_live():
    events = [ev(0, "cooking"), ev(10, "cooking"), ev(20, "cooking")]
    live = timeline.blocks(events, TH, now=31, listening_now=True, hold_last=True)
    assert live[-1]["end"] == 20 and live[-1]["n_windows"] == 2
    done = timeline.blocks(events, TH, now=600, listening_now=False)
    assert done[0]["end"] == 30 and done[0]["n_windows"] == 3


def test_summary_only_names_activities_that_are_on_the_bar():
    rng = random.Random(3)
    for _ in range(100):
        events = [ev(8 * 3600 + i * 10, rng.choice(LABELS), conf=rng.choice([0.5, 0.9])) for i in range(rng.randint(2, 30))]
        blks = timeline.blocks(events, TH, now=events[-1]["end"] + 1, listening_now=True, hold_last=True)
        text = timeline.summary(blks, 0)
        on_bar = {timeline.PHRASE[b["activity"]] for b in blks if b["state"] == "activity"}
        for name in timeline.PHRASE.values():
            if name != "quiet" and f"{name} around" in text or f"{name} from about" in text:
                assert name in on_bar, (text, on_bar)
