"""Shared test cases for the safety layer: Python (kettle/safety.py) answers, which web/test/safety.test.mjs must match.

    python tools/export_safety_fixtures.py      -> web/test/safety_fixtures.json

Each scenario is a stream of hand-made windows every 5 s (detector hits, a TV flag, named sounds, loudness) plus
optional answers on the screen; the expected output is every action the engine returns, with its window time.
Each Urgent rule has a positive case and the hard negatives from the plan (TV scream, a dropped pan then cooking,
a microwave beep, a doorbell, a paused period). Pattern cases are envelopes built from the NFPA 72 timings.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kettle import safety  # noqa: E402

OUT = ROOT / "web" / "test" / "safety_fixtures.json"
HOP = 5


def win(t, hits=(), kinds=(), label="absence", db=-60.0, media=False, pattern=None):
    scores = {d["id"]: (0.9 if d["id"] in hits else 0.01) for d in safety.CFG["detectors"]}
    return {"t": t, "hits": list(hits), "scores": scores, "media": media, "kinds": list(kinds), "label": label, "db": db, "floor": -50.0,
            **({"pattern": pattern} if pattern else {})}


def quiet(t0, n, **kw):
    return [win(t0 + i * HOP, **kw) for i in range(n)]


def cooking(t0, n):
    return [win(t0 + i * HOP, kinds=("frying",) if i % 2 else ("dishes",), label="cooking", db=-30) for i in range(n)]


T0 = 8 * 3600


def scenarios() -> list[dict]:
    S = []
    def add(name, windows, answers=None, opts=None):
        S.append({"name": name, "windows": windows, "answers": answers or [], "opts": opts or {}})
    # U1 smoke alarm: 3 windows, and a single window (a toaster's brief beep) that must not fire
    add("smoke_alarm", quiet(T0, 4) + [win(T0 + 20 + i * HOP, hits=("smoke_alarm",), db=-20) for i in range(4)] + quiet(T0 + 40, 4))
    add("smoke_one_window_no", quiet(T0, 4) + [win(T0 + 20, hits=("smoke_alarm",), db=-20)] + quiet(T0 + 25, 6))
    add("smoke_t3_pattern", quiet(T0, 2) + [win(T0 + 10, pattern={"t3": 2, "t4": 0}, db=-25)])
    add("smoke_while_paused_opt_in", [win(T0 + i * HOP, hits=("smoke_alarm",)) for i in range(3)], opts={"paused": True, "smokeWhilePaused": True})
    add("smoke_while_paused_no", [win(T0 + i * HOP, hits=("smoke_alarm",)) for i in range(3)], opts={"paused": True})
    # U2 CO alarm
    add("co_alarm", quiet(T0, 2) + [win(T0 + 10 + i * HOP, pattern={"t3": 0, "t4": 1}) for i in range(3)])
    # U3 possible fall: crash then groan -> check-in -> no answer
    fall = cooking(T0, 20) + [win(T0 + 100, hits=("impact",), db=-15)] + [win(T0 + 105, db=-45), win(T0 + 110, hits=("distress",), db=-35)]
    fall += quiet(T0 + 115, 16)
    add("fall_groan_no_answer", fall)
    add("fall_groan_answer_ok", fall, answers=[{"t": T0 + 130, "reply": "ok"}])
    add("fall_groan_answer_help", fall, answers=[{"t": T0 + 130, "reply": "help"}])
    # crash then 10 minutes of stillness, after activity
    add("fall_stillness", cooking(T0, 20) + [win(T0 + 100, hits=("glass",), db=-15)] + quiet(T0 + 105, 130))
    # hard negative: a dropped pan, then normal cooking within 2 minutes
    add("dropped_pan_then_cooking_no", cooking(T0, 20) + [win(T0 + 100, hits=("impact",), db=-15)] + quiet(T0 + 105, 4) + cooking(T0 + 125, 140))
    # hard negative: crash with no activity before it (nobody home) and silence after: no check-in
    add("crash_nobody_before_no", quiet(T0, 10) + [win(T0 + 50, hits=("impact",))] + quiet(T0 + 55, 130))
    # U4 screaming twice, no media -> check-in 30 s
    add("scream_twice", quiet(T0, 4) + [win(T0 + 20, hits=("scream",), db=-15)] + quiet(T0 + 25, 4) + [win(T0 + 45, hits=("scream",), db=-15)] + quiet(T0 + 50, 10))
    # hard negative: a TV drama with screaming -> only a Worth-a-look note
    add("scream_tv_drama", [win(T0 + i * HOP, label="watching_tv", media=True, db=-30) for i in range(4)] + [win(T0 + 20, hits=("scream",), media=True)]
        + [win(T0 + 25 + i * HOP, media=True, label="watching_tv") for i in range(4)] + [win(T0 + 45, hits=("scream",), media=True)] + quiet(T0 + 50, 4, media=True))
    # one scream heard in two overlapping windows only: not two separate screams
    add("scream_once_overlap_no", quiet(T0, 4) + [win(T0 + 20, hits=("scream",)), win(T0 + 25, hits=("scream",))] + quiet(T0 + 30, 10))
    # U5 repeated groaning with nothing else going on
    add("distress_repeated", quiet(T0, 4) + sum(([win(T0 + 20 + 40 * i, hits=("distress",), db=-35)] + quiet(T0 + 25 + 40 * i, 7) for i in range(4)), []))
    # hard negative: laughter/shouting during a meal (distress-like sounds while cooking)
    add("distress_while_cooking_no", sum(([win(T0 + 40 * i, hits=("distress",), label="cooking", kinds=("dishes",), db=-30)] + cooking(T0 + 5 + 40 * i, 7) for i in range(4)), []))
    # microwave beep and a doorbell are not alarms
    add("microwave_beep_no", cooking(T0, 6) + [win(T0 + 30, hits=("beep",), kinds=("microwave",))] + cooking(T0 + 35, 6))
    add("doorbell_no", quiet(T0, 4) + [win(T0 + 20, kinds=("doorbell",), db=-25)] + quiet(T0 + 25, 6))
    # paused: no person alerts at all
    add("paused_scream_no", quiet(T0, 2) + [win(T0 + 10, hits=("scream",)), win(T0 + 30, hits=("scream",))], opts={"paused": True})
    # the parent turned safety alerts off
    add("urgent_off_no", [win(T0 + i * HOP, hits=("smoke_alarm",)) for i in range(3)], opts={"urgent": False})
    # C6 stove maybe left on: frying for 45 minutes with nothing else
    add("stove_left_on", [win(T0 + i * 60, kinds=("frying",), label="cooking", db=-30) for i in range(46)])
    add("stove_with_cook_present_no", [win(T0 + i * 60, kinds=("frying",) if i % 4 else ("chopping",), label="cooking") for i in range(46)])
    # C7 beeping ignored, C9 water left running
    add("beep_ignored", [win(T0 + i * 30, hits=("beep",)) for i in range(12)])
    add("water_running", [win(T0 + i * 30, kinds=("tap",), db=-30) for i in range(45)])
    add("water_short_no", [win(T0 + i * 30, kinds=("tap",)) for i in range(10)] + quiet(T0 + 300, 40))
    # v3.5 U8 gunshot: one window, no media -> urgent at once; with the TV on -> only a note; never while paused
    add("gunshot", quiet(T0, 4) + [win(T0 + 20, hits=("gunshot",), db=-10), win(T0 + 25, hits=("gunshot",), db=-15)] + quiet(T0 + 30, 6))
    add("gunshot_tv_note", [win(T0 + i * HOP, label="watching_tv", media=True) for i in range(3)] + [win(T0 + 15, hits=("gunshot",), media=True)] + quiet(T0 + 20, 3))
    add("gunshot_paused_no", quiet(T0, 2) + [win(T0 + 10, hits=("gunshot",))], opts={"paused": True})
    # v3.5 U9 shouting: 3 separate windows in 60 s -> check-in; one shout, or shouts 40 s apart, are nothing
    add("shout_three", quiet(T0, 2) + sum(([win(T0 + 10 + 15 * i, hits=("shout",), db=-20)] + quiet(T0 + 15 + 15 * i, 2) for i in range(3)), []) + quiet(T0 + 60, 10))
    add("shout_once_no", quiet(T0, 2) + [win(T0 + 10, hits=("shout",)), win(T0 + 15, hits=("shout",))] + quiet(T0 + 20, 10))
    add("shout_spread_no", sum(([win(T0 + 40 * i, hits=("shout",))] + quiet(T0 + 5 + 40 * i, 7) for i in range(3)), []))
    add("shout_with_tv_no", sum(([win(T0 + 15 * i, hits=("shout",), media=True)] + quiet(T0 + 5 + 15 * i, 2, media=True) for i in range(4)), []))
    # v3.5 crash then 2 minutes of stillness (was 10), and still nothing at 90 s
    add("fall_stillness_2min", cooking(T0, 20) + [win(T0 + 100, hits=("impact",), db=-15)] + quiet(T0 + 105, 26))
    add("fall_stillness_90s_no", cooking(T0, 20) + [win(T0 + 100, hits=("impact",), db=-15)] + quiet(T0 + 105, 18))
    # U6 help button and U7 stillness check-in
    add("help_button", quiet(T0, 3), answers=[{"t": T0 + 7, "reply": "help"}])
    add("stillness_checkin_no_answer", quiet(T0, 2), answers=[{"t": T0 + 6, "reply": "ask_stillness"}] + [], opts={})
    S[-1]["windows"] += quiet(T0 + 10, 16)
    return S


def run(sc: dict) -> list[dict]:
    st = safety.new_engine()
    out = []
    answers = sorted(sc["answers"], key=lambda a: a["t"])
    o = sc["opts"]
    kw = {"urgent": o.get("urgent", True), "concern": o.get("concern", True), "paused": o.get("paused", False),
          "smoke_while_paused": o.get("smokeWhilePaused", False)}
    for w in sc["windows"]:
        while answers and answers[0]["t"] <= w["t"]:
            a = answers.pop(0)
            acts = safety.ask_stillness(st, a["t"]) if a["reply"] == "ask_stillness" else safety.answer(st, a["t"], a["reply"])
            out += [{"t": a["t"], **x} for x in acts]
        out += [{"t": w["t"], **x} for x in safety.step(st, w, **kw)]
    return out


def envelope_case(kind: str, seed: int) -> list[float]:
    """An envelope (dB per 50 ms, 10 s) of an alarm pattern over noise, built from the NFPA 72 timings."""
    rnd = random.Random(seed)
    on = []
    if kind == "t3":
        cyc = [1] * 10 + [0] * 10 + [1] * 10 + [0] * 10 + [1] * 10 + [0] * 30     # 0.5 on/off x3, 1.5 off (frames of 50 ms)
    elif kind == "t4":
        cyc = ([1, 1, 0, 0] * 4)[:-2] + [0] * 100                                  # 4 x 100 ms, then 5 s off
    elif kind == "timer":
        cyc = [1] * 5 + [0] * 3 + [1] * 5 + [0] * 3 + [1] * 5 + [0] * 79          # three 0.25-s beeps, then quiet
    else:
        cyc = [0]
    start = rnd.randrange(len(cyc))
    for i in range(200):
        on.append(cyc[(start + i) % len(cyc)])
    return [round((-20.0 if b else -50.0) + rnd.uniform(-2, 2), 2) for b in on]


def main() -> int:
    cases = [{**sc, "expect": run(sc)} for sc in scenarios()]
    pats = []
    for kind in ("t3", "t4", "timer", "none"):
        for seed in range(6):
            env = envelope_case(kind, seed)
            pats.append({"kind": kind, "seed": seed, "env": env, "expect": safety.alarm_pattern(env)})
    rnd = random.Random(7)
    wave = [math.sin(2 * math.pi * 3100 * i / 16000) * (0.3 if (i // 8000) % 2 == 0 else 0.0) + rnd.uniform(-0.01, 0.01) for i in range(32000)]
    wave = [round(x, 5) for x in wave]
    scores = [round(rnd.random() * 0.2, 4) for _ in range(527)]
    for i in (399, 14, 460):
        scores[i] = [0.55, 0.16, 0.05][[399, 14, 460].index(i)]
    data = {"scenarios": cases, "patterns": pats, "envelope": {"wave": wave, "expect": [round(x, 6) for x in safety.envelope(wave)]},
            "detect": {"scores": scores, "expect": safety.detect(scores)},
            "cough": [{"days": d, "today": t, "expect": safety.cough_concern(d, t)} for d, t in
                      [([4, 5, 3, 6, 4, 5, 4], 20), ([4, 5, 3], 10), ([1, 1], 50), ([0, 0, 0, 1], 7), ([10, 12, 11, 9], 25)]]}
    OUT.write_text(json.dumps(data))
    hit = sum(1 for c in cases if c["expect"])
    print(f"{len(cases)} scenarios ({hit} with actions), {len(pats)} pattern cases -> {OUT.relative_to(ROOT)}")
    for c in cases:
        print(f"  {c['name']:32s} " + ", ".join(f"{a['do']}:{a.get('tier', a.get('rule'))}:{a['type']}" for a in c["expect"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
