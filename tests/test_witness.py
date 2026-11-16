"""The second opinion: when the head can't answer, general kitchen tags may; a motor or bathroom tag withdraws a kitchen label."""
import numpy as np

from kettle import timeline, witness
from tests.helpers import ev

TH = 0.66


def with_w(e, k=0.0, family="cooking", v=0.0, novel=False):
    return {**e, "novel": novel, "w": {"k": k, "family": family, "v": v}}


def test_no_second_opinion_means_the_old_rule():
    assert timeline.raw_label(ev(0, "cooking", conf=0.9), TH) == "cooking"
    assert timeline.raw_label({**ev(0, "cooking", conf=0.9), "novel": True}, TH) == "not_sure"


def test_unfamiliar_sound_with_clear_kitchen_tags_is_rescued():
    e = with_w(ev(0, "watching_tv", conf=0.9), k=0.6, family="dishwashing", novel=True)
    assert timeline.raw_label(e, TH) == "dishwashing"
    assert timeline.by_sounds(e, TH)


def test_low_confidence_with_clear_kitchen_tags_is_rescued():
    e = with_w(ev(0, "other", conf=0.4), k=0.5, family="eating")
    assert timeline.raw_label(e, TH) == "eating"


def test_weak_kitchen_tags_do_not_rescue():
    e = with_w(ev(0, "other", conf=0.4), k=witness.TAU_K - 0.01, novel=True)
    assert timeline.raw_label(e, TH) == "not_sure"


def test_a_motor_louder_than_the_kitchen_tags_blocks_the_rescue():
    e = with_w(ev(0, "other", conf=0.4), k=0.4, v=0.7, novel=True)      # e.g. a vacuum the tags half-hear as frying
    assert timeline.raw_label(e, TH) == "not_sure"


def test_a_confident_head_in_a_familiar_room_is_not_overruled_by_tags():
    e = with_w(ev(0, "watching_tv", conf=0.95), k=0.8, family="cooking")   # a cooking show on TV stays TV
    assert timeline.raw_label(e, TH) == "watching_tv"
    assert not timeline.by_sounds(e, TH)


def test_vacuum_called_cooking_is_withdrawn():
    e = with_w(ev(0, "cooking", conf=0.72), k=0.05, v=0.6)             # the reviewer's vacuum cleaner
    assert timeline.raw_label(e, TH) == "not_sure"
    e = with_w(ev(0, "cooking", conf=0.72), k=0.5, v=0.6)              # frying under a fan: still withdrawn (v > k)
    assert timeline.raw_label(e, TH) == "not_sure"
    e = with_w(ev(0, "cooking", conf=0.72), k=0.7, v=0.4)              # frying louder than the fan: kept
    assert timeline.raw_label(e, TH) == "cooking"


def test_veto_never_touches_non_kitchen_labels():
    e = with_w(ev(0, "vacuum_cleaner", conf=0.99), v=0.95)
    assert timeline.raw_label(e, TH) == "vacuum_cleaner"


def test_opinion_reads_only_the_listed_tags():
    a = np.zeros(527, np.float32)
    a[witness.NAMES.index("Dishes, pots, and pans")] = 0.61
    a[witness.NAMES.index("Vacuum cleaner")] = 0.2
    a[witness.NAMES.index("Blender")] = 0.99          # deliberately not kitchen evidence
    a[witness.NAMES.index("Speech")] = 0.99
    o = witness.opinion(a)
    kd = o.pop("kd")                                   # rule 2f: one kitchen probability, the only number made from all tags
    assert o == {"k": 0.61, "family": "dishwashing", "v": 0.2, "cook": 0.0, "water": 0.0, "mouth": 0.0} and 0 <= kd <= 1
    k, fam, v = witness.opinions(a[None])
    assert round(float(k[0]), 2) == 0.61 and fam[0] == "dishwashing" and round(float(v[0]), 2) == 0.2


def test_sound_context_rules_python_twin():
    """Handover 3.1: kettle/kinds.py named() applies the same context rules and hides sounds that missed the bar."""
    from kettle import kinds
    a = np.zeros(527)
    a[367], a[524] = 0.5, 0.6                      # frying + television: frying hidden (missed the bar), TV shown
    assert [k["id"] for k in kinds.named(a)] == ["tv"]
    b = np.zeros(527)
    b[367], b[456], b[370] = 0.6, 0.3, 0.2         # frying louder than boiling and the tap
    shown = {k["id"]: k.get("shown", True) for k in kinds.CFG["kinds"]}
    for k in kinds.CFG["kinds"]:
        k["shown"] = True
    try:
        ids = [k["id"] for k in kinds.named(b)]
    finally:
        for k in kinds.CFG["kinds"]:
            k["shown"] = shown[k["id"]]
    assert "kettle" not in ids and "tap" not in ids and "frying" in ids


def test_kitchen_detector_never_calls_speech_or_tv_kitchen():
    """Rule 2f reads all 527 tags, so check what matters: voices, TV and music alone can't make a window say kitchen."""
    from eval.kitchen_detector import PROBES
    for names in PROBES:
        a = np.full(527, 0.001, np.float32)
        for n in names:
            a[witness.NAMES.index(n)] = 0.9
        assert witness.opinion(a)["kd"] < witness.TAU_KD, names


def test_kitchen_detector_needs_a_kitchen_tag_heard():
    """Rule 2f guard: a high kd alone (glass breaking, clapping, birds, thunder did this) is not enough."""
    w = {"k": 0.01, "family": "dishwashing", "v": 0.0, "cook": 0.0, "water": 0.0, "mouth": 0.0, "kd": 0.99}
    assert not witness.detects("other", w, {"cooking", "dishwashing", "eating"})
    assert witness.detects("other", dict(w, k=0.2), {"cooking", "dishwashing", "eating"})
