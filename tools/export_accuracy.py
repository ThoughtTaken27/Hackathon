"""The detection-accuracy results the How sure page shows, copied from results/*.json (never typed by hand).

    python tools/export_accuracy.py      writes web/public/data/accuracy.json from
    results/kitchen_naming.json (rules 2c/2d), results/sounds.json (named sounds), results/judge.json and results/confetti.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = lambda n: json.loads((ROOT / "results" / n).read_text())


def main() -> None:
    kn, so, ju, co = R("kitchen_naming.json"), R("sounds.json"), R("judge.json"), R("confetti.json")
    out = {"kitchen_naming": {k: {"n": v["n"], "before": v["before"], "after": v["after"]} for k, v in kn["sets"].items()},
           "kitchen_naming_process": kn["process"],
           "sounds": {"bar": so["bar"], "before": so["before"], "after": so["after"]},
           "judge": {"decision": ju["decision"], "dev": {t: v["_gate"] for t, v in ju["dev"].items()}},
           "confetti": {"decision": co["decision"], "variants": co["variants"]},
           "source": "tools/export_accuracy.py"}
    (ROOT / "web" / "public" / "data" / "accuracy.json").write_text(json.dumps(out))
    print("wrote web/public/data/accuracy.json")
    fill_writeup(out)


def fill_writeup(A: dict) -> None:
    """docs/WRITEUP.md blocks from results files: accuracy (naming + sound names), crosshome, calibration, privacy."""
    import re
    K, S = A["kitchen_naming"], A["sounds"]
    names = {k["id"]: k["name"] for k in json.loads((ROOT / "web" / "public" / "model" / "kinds.json").read_text())["kinds"]}
    sd, kt, dt = K["sins_dev_sessions"], K["kitchen20_test"], K["desed_test"]
    pc = lambda r: "–" if r["pct"] is None else f"{r['pct']:.1f}%"
    b, a = S["before"], S["after"]
    shown = [k for k, v in a.items() if v["shown"]]
    naming = "\n".join([
        "**Naming a kitchen stretch from evidence across its windows (rules 2c, 2d), same events before → after:**", "",
        "| Set (unit) | Measure | Before | After | Denominator |", "|---|---|---|---|---|",
        f"| Research home, dev (one session heard by one microphone node) | right activity | {sd['before']['right']} | {sd['after']['right']} | "
        f"{sd['before']['meal']} kitchen-activity recordings ({sd['before']['meal'] // 4} sessions × 4 microphone nodes; {sd['n']:,} recordings in all) |",
        f"| Research home, dev | false kitchen activity | {sd['before']['false_kitchen']} | {sd['after']['false_kitchen']} | {sd['before']['not_meal']} other recordings |",
        f"| Kitchen20, test half (one clip each) | wrong activity | {kt['before']['wrong_activity']} | {kt['after']['wrong_activity']} | "
        f"{kt['before']['meal']} kitchen-activity clips (of {kt['n']}; {kt['before']['not_meal']} others) |",
        f"| DESED real homes, test half (one 10-s clip each) | dish clatter called washing up or eating | {dt['before']['dishes_called_washing_or_eating']} | "
        f"{dt['after']['dishes_called_washing_or_eating']} | {dt['before']['dishes']} dish-clatter clips (of {dt['n']}) |",
    ])
    sounds = "\n".join([
        f"**Everyday sound names, held-out halves (pre-registered bar: precision ≥ {S['bar']['precision']:.0f}% and recall ≥ {S['bar']['recall']:.0f}%):**", "",
        "| Sound | Precision before → after | False names per 1,000 other windows, before → after | Recall after | Positives / other windows | Shown |",
        "|---|---|---|---|---|---|",
        *[f"| {names[k]} | {pc(b[k]['precision'])} → {pc(a[k]['precision'])} | {b[k]['false_per_1000']} → {a[k]['false_per_1000']} | "
          f"{pc(a[k]['recall'])} | {a[k]['recall']['n']} / {a[k]['neg_n']:,} | {'yes' if a[k]['shown'] else 'hidden'} |"
          for k in ("kettle", "tap", "microwave", "tv")],
        "", f"{len(shown)} of {len(a)} names passed ({', '.join(names[k] for k in shown)}); the other {len(a) - len(shown)} are hidden from families "
        "(all 15 rows: `results/sounds.json`).",
    ])
    o = json.loads((ROOT / "results" / "other_homes.json").read_text())
    t1, t2, u2 = o["test"]["v1"], o["test"]["v2"], o["tune"]["v2"]
    nov = o["post_hoc"]["novel"]
    em = json.loads((ROOT / "results" / "metrics.json").read_text())["dcase_eval"]["meal_activity"]
    raw_home, home_n = 100 * (em["n_meal"] - em["missed"]) / em["n_meal"], em["n_meal"]
    ci = lambda r: f"{r['value']}% [{r['ci'][0]}, {r['ci'][1]}] ({r['k']} of {r['n']})"
    cross = "\n".join([
        "| Real-home kitchen clips (DESED; split by uploader, test half scored once) | Shown as kitchen activity | False kitchen activity on other DESED clips |",
        "|---|---|---|",
        f"| Head alone | {ci(t1['desed_kitchen_caught'])} | {t1['desed_false_kitchen']['k']} of {t1['desed_false_kitchen']['n']} |",
        f"| Head + second opinion (tags), as shipped | **{ci(t2['desed_kitchen_caught'])}** (tune half: {u2['desed_kitchen_caught']['value']}%) | "
        f"{t2['desed_false_kitchen']['k']} of {t2['desed_false_kitchen']['n']} |",
        "", f"For comparison, in the research home's held-out test the top label caught {raw_home:.1f}% of kitchen-activity windows (raw; "
        f"{home_n:,} windows); in other homes, {t2['desed_kitchen_caught']['value']}% of real-home kitchen clips. It fails safe: "
        f"{nov['k']} of {nov['n']} other-home clips were flagged "
        "\"unlike anything it learned\" and shown as \"Not sure\", not as a wrong activity. One 10-s clip each, no smoothing; scored Sat Nov 14 "
        "(`results/other_homes.json`), before the stretch-naming rules, which change which activity is named, not whether one is.",
    ])
    e = json.loads((ROOT / "results" / "beyond.json").read_text())["enrolment"]
    m3 = e["by_minutes"]["3"]
    calib = (f"**What \"Teach Kettle this kitchen\" does (3-minute kitchen calibration):** the parent is told to keep quiet (40 s), run the tap "
             f"(1 min) and cook (1 min); the step they were asked to do is the label (no manual labelling). The device keeps the encoder's "
             f"192-number summary of each window from those steps (never the audio) and the kitchen's quiet loudness. Afterwards, only for a "
             f"window the head can't name, the {e['knn']} nearest setup windows vote (weight {e['alpha']}) if they're within {e['rho']}× the "
             f"setup windows' own spread; a confident head is never overruled. The frozen head, θ and the novelty threshold don't change; "
             f"nothing is sent. Simulated on dev (a head trained without the test microphone, then 3 minutes of that microphone): kitchen activity "
             f"noticed {m3['before']['kitchen_noticed']['pct']}% → {m3['after']['kitchen_noticed']['pct']}% (N = {m3['after']['kitchen_noticed']['n']:,} windows), "
             f"\"Not sure\" {m3['before']['not_sure_share']['pct']}% → {m3['after']['not_sure_share']['pct']}%, false kitchen activity "
             f"{m3['before']['false_kitchen']['pct']}% → {m3['after']['false_kitchen']['pct']}% (`results/beyond.json`). A small gain, measured on the "
             f"research home's own microphones, not in a new kitchen. In the web app the kitchen's quiet level also marks any window at or "
             f"below it as Quiet (added Sun Nov 15 after a live test; checked only on generated room tone, `results/sound_check_web.json`).")
    pv = json.loads((ROOT / "results" / "privacy_check.json").read_text())
    c = pv["checks"]
    zero = lambda k: len(c[k])
    priv = (f"**Privacy, verified for the Python app:** `python -m eval.privacy_check` listened through the browser microphone for "
            f"{pv['seconds_listened']} s ({pv['windows_labelled']} windows labelled) while watching the disk and the network: "
            f"{zero('python_write_opens_outside_labels_file')} file writes outside the labels file (Python audit hook), "
            f"{zero('lsof_write_handles_outside_labels_file')} open write handles (lsof), "
            f"{zero('new_or_changed_audio_extension_files')} new audio files by extension, "
            f"{zero('new_or_changed_files_with_audio_magic_bytes')} by audio file signature, and "
            f"{zero('outbound_connections')} outbound connections (`results/privacy_check.json`). **The browser version has not had an "
            "equivalent network audit:** there, privacy is by design (only labels, scores, times and allowed sound names are posted; the server drops any other "
            "field) and checked by code review and tests, not by watching traffic.")
    blocks = {"accuracy": naming + "\n\n" + sounds, "crosshome": cross, "calibration": calib, "privacy": priv}
    p = ROOT / "docs" / "WRITEUP.md"
    t = p.read_text()
    for k, v in blocks.items():
        t = re.sub(rf"<!-- {k}:start -->.*?<!-- {k}:end -->", f"<!-- {k}:start -->\n{v}\n<!-- {k}:end -->", t, flags=re.S)
    p.write_text(t)
    print("filled docs/WRITEUP.md blocks:", ", ".join(blocks))

if __name__ == "__main__":
    main()
