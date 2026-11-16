"""Safety alerts: what we measured (plan v3.1, Workstream E, steps E2, E7 and E9).

    python -m eval.safety

1. Detectors (E2/E9). Each danger detector reads CED-tiny's AudioSet scores. Its threshold is chosen on DEVELOPMENT
   clips only: the 99.5th percentile of everything that is not that danger (normal home audio from SINS dev folds 1-2,
   ESC-50 folds 1-3, Nonspeech7k's first half, synthetic seeds 0-29), never below the plan's starting value. It is
   then reported ONCE on held-out clips (SINS folds 3-4, ESC-50 folds 4-5, Nonspeech7k's second half, synthetic
   seeds 30-59): how many dangers it caught, and how often it fires on ordinary sound (per window and per hour).
2. Alarm pattern (E1/E2). The NFPA 72 T3/T4 rhythm detector (kettle/safety.py alarm_pattern) is run on the synthetic
   alarms at four signal-to-noise ratios and, for false alarms, on all 2,000 real ESC-50 clips and 725 Nonspeech7k clips.
3. Scenario simulator (E7). 600 synthetic timelines built from held-out clips only, 60 of each kind: positives
   (cooking -> crash -> groan; crash -> 15 min stillness; smoke alarm during cooking; screaming; repeated crying)
   and hard negatives (TV drama with screaming, dropped pan then cooking, kitchen timer beeps, knocks/dogs/laughter,
   a busy kitchen). Plus every held-out SINS window streamed as one long day of ordinary home sound, to count false
   Urgent alerts per 24 h. Nobody answers the check-in in the positive timelines (the worst case).

Writes results/safety.json, web/public/model/safety.json (thresholds the app uses) and web/public/data/safety.json
(the How sure page). Honest limits are written into the results: no fall (body impact) recordings, no real smoke
alarms, no shouting-for-help clips, no room echo except in the synthetic alarms, no real kitchens.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from eval.beyond import C, load, rate
from kettle import kinds as kinds_mod
from kettle import safety

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results" / "cache"
RNG = np.random.default_rng(0)
QUANTILE = 0.995
QUANTILE_BY = {"gunshot": 1.0}
START = {"gunshot": 0.3, "smoke_alarm": 0.35, "beep": 0.2, "scream": 0.1, "shout": 0.3, "distress": 0.1, "impact": 0.1, "glass": 0.3, "fire": 0.3, "siren": 0.2}   # floors: never below these
DETECTORS = [   # id, name, AudioSet indices (Appendix A), where the positives come from
    ("smoke_alarm", "Smoke or fire alarm", [399, 400], "synthetic T3/T4 alarms"),
    ("beep", "Timer or appliance beep", [481, 398, 395], "synthetic kitchen timers + ESC-50 clock_alarm"),
    ("scream", "Screaming", [14], "Nonspeech7k screaming"),
    ("shout", "Shout or yell", [8, 11, 13], None),
    ("gunshot", "Gunshot", [427, 428, 429, 430, 431], None),
    ("distress", "Groaning, moaning or crying", [38, 25, 22, 24], "Nonspeech7k crying"),
    ("impact", "A crash or thud", [460, 466, 469, 358], None),
    ("glass", "Glass breaking", [443, 470, 441], "ESC-50 glass_breaking"),
    ("fire", "Fire crackle", [298, 299], "ESC-50 crackling_fire"),
    ("siren", "Siren outside", [396, 397, 322], "ESC-50 siren"),
]
MEDIA = [524, 525, 137, 267, 268, 270]
EXCLUDE_NEG = {"distress": {"crying_baby", "yawm"}, "scream": {"crying_baby"}, "beep": {"clock_alarm"}, "smoke_alarm": {"clock_alarm"}}


def half(name: str) -> int:
    return int(hashlib.sha1(name.encode()).hexdigest(), 16) % 2


def sources() -> list[dict]:
    """Every clip as {S (527 scores), cat, src, dev(bool), label (SINS activity or None)}."""
    d = load()
    out = []
    inv = {i: c for c, i in C.items()}
    for s, y, f in zip(d["S"], d["y"], d["fold"]):
        if f in (1, 2, 3, 4):
            out.append({"S": s, "cat": "sins_" + inv[int(y)], "src": "sins", "dev": f in (1, 2), "label": inv[int(y)]})
    e = np.load(CACHE / "ced-tiny_esc50all.npz", allow_pickle=True)
    for s, c, f, fn in zip(e["scores"], e["category"], e["fold"], e["files"]):
        out.append({"S": s.astype(np.float64), "cat": str(c), "src": "esc50", "dev": int(f) <= 3, "label": None, "file": str(fn)})
    n = np.load(CACHE / "ced-tiny_nonspeech7k.npz", allow_pickle=True)
    for s, c, fn in zip(n["scores"], n["category"], n["files"]):
        out.append({"S": s.astype(np.float64), "cat": "ns_" + str(c), "src": "nonspeech7k", "dev": half(str(fn)) == 0, "label": None, "file": str(fn)})
    a = np.load(CACHE / "ced-tiny_synth_alarms.npz", allow_pickle=True)
    for s, k, seed, snr in zip(a["scores"], a["kind"], a["seed"], a["snr"]):
        out.append({"S": s.astype(np.float64), "cat": "synth_" + str(k), "src": "synth", "dev": int(seed) < 30, "label": None,
                    "seed": int(seed), "snr": int(snr), "kind": str(k)})
    return out


def positives(det: str, c: dict) -> bool:
    return {"smoke_alarm": c["cat"] in ("synth_t3", "synth_t4"), "beep": c["cat"] in ("synth_timer", "clock_alarm"),
            "scream": c["cat"] == "ns_screaming", "distress": c["cat"] == "ns_crying", "glass": c["cat"] == "glass_breaking",
            "fire": c["cat"] == "crackling_fire", "siren": c["cat"] == "siren"}.get(det, False)


def per_hour(k: int, n_windows: int) -> float:
    return round(k / max(1, n_windows) * 360, 2)       # 10-s windows: 360 per hour


def calibrate(clips: list[dict]) -> tuple[list[dict], dict]:
    S = np.stack([c["S"] for c in clips])
    dev = np.array([c["dev"] for c in clips])
    sins = np.array([c["src"] == "sins" for c in clips])
    cats = np.array([c["cat"] for c in clips])
    cfg, report = [], {}
    for det, name, idx, posdesc in DETECTORS:
        score = S[:, idx].max(1)
        pos = np.array([positives(det, c) for c in clips])
        excl = np.isin(cats, list(EXCLUDE_NEG.get(det, ())))
        neg = ~pos & ~excl
        if det == "beep":
            neg &= ~np.isin(cats, ["synth_t3", "synth_t4"])          # a smoke alarm beeping is also a beep: not a false fire
        q = QUANTILE_BY.get(det, QUANTILE)                          # gunshot: above every dev negative (PREREGISTER-SAFETY-V35)
        tau = float(max(START[det], np.quantile(score[dev & neg], q)))
        tau = round(tau, 3)
        row = {"name": name, "tau": tau, "indices": idx, "positives_from": posdesc,
               "false_fire_heldout_all": rate(score[~dev & neg] >= tau),
               "false_fire_heldout_home_audio": rate(score[~dev & neg & sins] >= tau),
               "false_per_hour_home_audio": per_hour(int((score[~dev & neg & sins] >= tau).sum()), int((~dev & neg & sins).sum()))}
        if pos.any():
            row["caught_heldout"] = rate(score[~dev & pos] >= tau)
            row["caught_dev"] = rate(score[dev & pos] >= tau)
        else:
            row["caught_heldout"] = None
            row["note"] = "no public recordings of this danger were available to us; threshold set from false fires only"
        worst = {}
        for c in sorted(set(cats[~dev & neg])):
            m = ~dev & neg & (cats == c)
            k = int((score[m] >= tau).sum())
            if k:
                worst[c] = f"{k}/{int(m.sum())}"
        row["false_fires_by_source"] = dict(sorted(worst.items(), key=lambda kv: -int(kv[1].split("/")[0]))[:6])
        report[det] = row
        cfg.append({"id": det, "name": name, "index": idx, "tau": tau})
    # TV / radio / music context: SINS watching_tv windows vs everything else in SINS
    m = S[:, MEDIA].max(1)
    tv = np.array([c["label"] == "watching_tv" for c in clips])
    mtau = round(float(max(0.3, np.quantile(m[dev & sins & ~tv], 0.95))), 3)
    report["media"] = {"tau": mtau, "tv_windows_flagged_heldout": rate(m[~dev & sins & tv] >= mtau),
                       "other_home_windows_flagged_heldout": rate(m[~dev & sins & ~tv] >= mtau)}
    return cfg, {"detectors": report, "media_tau": mtau}


def patterns(clips: list[dict]) -> dict:
    from eval.synth_alarms import synth
    import soundfile as sf
    out = {}
    for kind in ("t3", "t4", "timer", "none"):
        for snr in (20, 10, 0, -5):
            hits = {"t3": 0, "t4": 0}
            n = 0
            for seed in range(30, 60):                                 # held-out seeds
                p = safety.alarm_pattern(safety.envelope_np(synth(kind, seed, snr)))
                n += 1
                hits["t3"] += p["t3"] >= 1
                hits["t4"] += p["t4"] >= 1
            out[f"{kind}@{snr}dB"] = {"n": n, "t3_found": hits["t3"], "t4_found": hits["t4"]}
    folders = [ROOT / "data" / "clips" / f for f in ("esc50_all", "nonspeech7k")]
    if not all(f.exists() for f in folders):             # the pattern detector is unchanged: keep the last full run's count
        prev = json.loads((ROOT / "results" / "safety.json").read_text())["alarm_pattern"]["real_clips_false"]
        return {"synthetic_heldout": out, "real_clips_false": {**prev, "reused": "Nonspeech7k audio not on this machine; "
                "alarm_pattern() is unchanged since the run that measured this, so that run's count is kept."}}
    real = {"t3": 0, "t4": 0, "n": 0, "fired_on": []}
    for folder in ("esc50_all", "nonspeech7k"):
        base = ROOT / "data" / "clips" / folder
        for f in sorted(base.rglob("*")):
            if f.suffix.lower() not in (".flac", ".wav"):
                continue
            x, sr = sf.read(f, dtype="float32", always_2d=False)
            if x.ndim > 1:
                x = x.mean(1)
            if sr != 16000:
                continue
            p = safety.alarm_pattern(safety.envelope_np(x[:160000]))
            real["n"] += 1
            if p["t3"] or p["t4"]:
                real["t3"] += p["t3"] >= 1
                real["t4"] += p["t4"] >= 1
                real["fired_on"].append(f.stem)
    real["fired_on"] = real["fired_on"][:12]
    return {"synthetic_heldout": out, "real_clips_false": real}


# ---------------------------------------------------------------- E7 scenario simulator
def to_window(c: dict, t: float, cfg: dict, pattern=None) -> dict:
    d = safety.detect(c["S"], cfg)
    ks = [k["id"] for k in kinds_mod.named(c["S"])]
    lab = c["label"] or ("absence" if c["src"] == "sins" else "other")
    return {"t": t, **d, "kinds": ks, "label": lab, **({"pattern": pattern} if pattern else {})}


def simulate(clips: list[dict], cfg: dict, split: str = "heldout") -> dict:
    from eval.synth_alarms import synth
    test = [c for c in clips if c["dev"] == (split == "dev")]
    pool = lambda f: [c for c in test if f(c)]                                     # noqa: E731
    cook = pool(lambda c: c["label"] in ("cooking", "dishwashing"))
    quiet = pool(lambda c: c["label"] == "absence")
    tvw = pool(lambda c: c["label"] == "watching_tv")
    talk = pool(lambda c: c["label"] == "social_activity")
    glass = pool(lambda c: c["cat"] == "glass_breaking")
    groan = pool(lambda c: c["cat"] == "ns_crying")
    scream = pool(lambda c: c["cat"] == "ns_screaming")
    alarm = pool(lambda c: c["cat"] in ("synth_t3", "synth_t4") and c["snr"] >= 0)
    timer = pool(lambda c: c["cat"] == "synth_timer")
    misc = pool(lambda c: c["cat"] in ("door_wood_knock", "dog", "laughing", "ns_laugh", "clapping", "footsteps"))
    bangs = pool(lambda c: c["cat"] in ("can_opening", "door_wood_knock", "fireworks", "thunderstorm"))     # gunshot look-alikes
    pick = lambda xs: xs[int(RNG.integers(len(xs)))]                               # noqa: E731

    def stream(seq: list[tuple]) -> list[dict]:
        out, t = [], 8 * 3600.0
        for c, reps, pat in seq:
            for _ in range(reps):
                out.append(to_window(c, t, cfg, pat))
                t += 5
        return out

    def alarm_seq():
        c = pick(alarm)
        p = safety.alarm_pattern(safety.envelope_np(synth(c["kind"], c["seed"], c["snr"])))
        return (c, 2, p)

    kinds = {
        "pos_crash_then_groan": lambda: [(pick(cook), 2, None) for _ in range(10)] + [(pick(glass), 2, None), (pick(groan), 2, None)] + [(pick(quiet), 2, None) for _ in range(12)],
        "pos_crash_then_stillness": lambda: [(pick(cook), 2, None) for _ in range(10)] + [(pick(glass), 2, None)] + [(pick(quiet), 2, None) for _ in range(95)],
        "pos_smoke_alarm_during_cooking": lambda: [(pick(cook), 2, None) for _ in range(6)] + [alarm_seq() for _ in range(4)] + [(pick(cook), 2, None) for _ in range(6)],
        "pos_screaming": lambda: [(pick(quiet), 2, None) for _ in range(4)] + [(pick(scream), 2, None), (pick(quiet), 2, None), (pick(scream), 2, None)] + [(pick(quiet), 2, None) for _ in range(10)],
        "pos_repeated_crying": lambda: [(pick(quiet), 2, None) for _ in range(3)] + sum(([(pick(groan), 2, None)] + [(pick(quiet), 2, None) for _ in range(3)] for _ in range(4)), []) + [(pick(quiet), 2, None) for _ in range(10)],
        "neg_tv_drama_with_screaming": lambda: sum(([(pick(tvw), 2, None) for _ in range(3)] + [(pick(scream), 2, None)] for _ in range(4)), []),
        "neg_dropped_pan_then_cooking": lambda: [(pick(cook), 2, None) for _ in range(8)] + [(pick(glass), 2, None)] + [(pick(cook), 2, None) for _ in range(100)],
        "neg_timer_beeps_while_cooking": lambda: sum(([(pick(cook), 2, None) for _ in range(3)] + [(pick(timer), 2, None)] for _ in range(6)), []),
        "neg_knocks_dogs_laughter": lambda: sum(([(pick(talk), 2, None) for _ in range(2)] + [(pick(misc), 2, None)] for _ in range(10)), []),
        "neg_busy_kitchen": lambda: [(pick(cook), 2, None) for _ in range(60)],
        "neg_cans_knocks_fireworks_while_cooking": lambda: sum(([(pick(cook), 2, None) for _ in range(3)] + [(pick(bangs), 2, None)] for _ in range(8)), []),
    }
    res, types = {}, {}
    for name, build in kinds.items():
        caught = checkins = n = 0
        delays = []
        for _ in range(60):
            ws = stream(build())
            st = safety.new_engine()
            acts = []
            for w in ws:
                acts += safety.step(st, w)
            acts += safety.timeouts(st, ws[-1]["t"] + 120)
            urgent = [a for a in acts if a["do"] == "alert" and a["tier"] == "urgent"]
            types[name] = types.get(name, []) + [a["type"] for a in urgent[:1]]
            n += 1
            caught += bool(urgent)
            checkins += any(a["do"] == "checkin" for a in acts)
            if urgent:
                delays.append(urgent[0]["at"] - ws[0]["t"])
        row = {"n": n, "urgent": caught, "checkins": checkins, "urgent_types": {t: types.get(name, []).count(t) for t in sorted(set(types.get(name, [])))}}
        row["rate"] = rate(np.array([True] * caught + [False] * (n - caught)))
        res[name] = row
    # a long day of ordinary home sound: every held-out SINS window in order
    st = safety.new_engine()
    day = [c for c in test if c["src"] == "sins"]
    acts = []
    t = 0.0
    for c in day:
        for _ in range(2):
            acts += safety.step(st, to_window(c, t, cfg))
            t += 5
    acts += safety.timeouts(st, t + 120)
    hours = t / 3600
    urg = [a for a in acts if a["do"] == "alert" and a["tier"] == "urgent"]
    con = [a for a in acts if a["do"] == "alert" and a["tier"] == "concern"]
    chk = [a for a in acts if a["do"] == "checkin"]
    res["ordinary_home_audio"] = {"hours": round(hours, 1), "windows": len(day), "urgent": len(urg), "checkins": len(chk), "concern": len(con),
                                  "urgent_per_24h": round(len(urg) / hours * 24, 2), "checkins_per_24h": round(len(chk) / hours * 24, 2),
                                  "concern_per_24h": round(len(con) / hours * 24, 2),
                                  "types": sorted({a["type"] for a in urg + chk + con})}
    return res


def main() -> None:
    clips = sources()
    cfg_list, cal = calibrate(clips)
    cfg = {"detectors": cfg_list, "media": {"index": MEDIA, "tau": cal["media_tau"]},
           "source": "eval/safety.py -> results/safety.json (thresholds chosen on development clips only)"}
    pat = patterns(clips)
    sim = simulate(clips, cfg)
    sim_dev = simulate(clips, cfg, "dev")
    n = {s: sum(1 for c in clips if c["src"] == s) for s in ("sins", "esc50", "nonspeech7k", "synth")}
    out = {"clips": n, "quantile": QUANTILE, "detectors": cal["detectors"], "media": cal["detectors"]["media"], "alarm_pattern": pat,
           "scenarios": sim, "scenarios_dev": sim_dev,
           "process_note": ("v3.5 (eval/PREREGISTER-SAFETY-V35.md, written before this run): gunshot detector added (tau above every "
                            "development negative, no gunshot recordings available), shouting rule (3 windows in 60 s), crash-then-stillness "
                            "wait 600 s -> 120 s, and a new negative scenario (cans, knocks, fireworks, thunder while cooking). The new scenario draws "
                            "from the shared random generator before the development run, so scenarios_dev timelines are redrawn (dev screaming "
                            "98.3% -> 90.0% is that resampling: with the shout rule switched off the same timelines give the same count). The script "
                            "was rerun twice more only to edit this note; it is deterministic (seed 0) and the numbers were identical. Then smoke rule U1b "
                            "(a T3 cycle in 2 of the last 3 windows) was pre-registered as an addendum with its dev numbers and this file "
                            "was regenerated once with it. "
                            "Earlier, disclosed: the first held-out run used lower floors (smoke 0.1, glass 0.1, fire 0.1) and showed false smoke alarms "
                            "from screams and timers. The floors were raised to the plan's values (smoke 0.35, glass 0.3, fire 0.3) and the same "
                            "simulator is also reported on development clips (scenarios_dev), so the change can be checked on data not used to report."),
           "limits": ["No recordings of real falls (body hitting a floor): the crash is breaking glass, and a fall that makes little sound will be missed.",
                      "Smoke and CO alarms are synthetic NFPA 72 tones mixed with household noise and simple echo, not recordings of real alarms.",
                      "No shouting-for-help clips: the shout detector has no measured catch rate; it alerts only after 3 shouts in 60 s.",
                      "No gunshot recordings could be fetched: the gunshot detector has no measured catch rate. Its threshold sits above "
                      "every development clip; can openings, door knocks and fireworks are the measured false-alarm risks.",
                      "A crash followed by someone quietly leaving the room now looks like a fall after 2 minutes (was 10).",
                      "Clips are close-microphone public recordings, joined in software; no real kitchen or real room has been measured yet."]}
    (ROOT / "results" / "safety.json").write_text(json.dumps(out, indent=1, default=float))
    (ROOT / "web" / "public" / "model" / "safety.json").write_text(json.dumps(cfg))
    (ROOT / "web" / "public" / "data" / "safety.json").write_text(json.dumps(out, default=float))
    for det, r in cal["detectors"].items():
        if det == "media":
            print(f"media tau {r['tau']}: tv flagged {r['tv_windows_flagged_heldout']}")
            continue
        c = r["caught_heldout"]
        print(f"{det:12s} tau {r['tau']:.3f}  caught {c['k']}/{c['n']} " if c else f"{det:12s} tau {r['tau']:.3f}  caught n/a     ", end="")
        print(f" false {r['false_fire_heldout_all']['k']}/{r['false_fire_heldout_all']['n']}  per hour home {r['false_per_hour_home_audio']}")
    print(json.dumps(pat["synthetic_heldout"]), pat["real_clips_false"]["n"], pat["real_clips_false"]["t3"], pat["real_clips_false"]["t4"])
    for k, v in sim.items():
        print(k, {kk: vv for kk, vv in v.items() if kk != "rate"})


if __name__ == "__main__":
    main()
