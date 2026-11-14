"""Fill the numbers in docs/WRITEUP.md and README.md from results/metrics.json (never by hand).

Replaces the text between <!-- results:start --> and <!-- results:end --> (and <!-- lead:start/end -->) markers.
Usage: python tools/writeup_numbers.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kettle.labels import DISPLAY  # noqa: E402


def f(x) -> str:
    return f"{x['value']:.1f} [{x['ci95'][0]:.1f}, {x['ci95'][1]:.1f}]" if "ci95" in x else f"{x['value']:.1f}"


def blocks(m: dict) -> dict:
    d, e, pub = m["dev"], m.get("dcase_eval"), m["published"]
    ma = d["meal_activity"]
    apple_dev = d["baselines"].get("apple_zeroshot", {}).get("macro_f1")
    apple_eval = (e or {}).get("baselines", {}).get("apple_zeroshot") if e else None
    held = (e["slices"].get("unknown") or e["slices"]["all"]) if e else None
    lead = []
    if apple_eval and "value" in apple_eval and held:
        lead.append(f"Your Mac already hears a kettle. Asked which of 9 household activities is happening, Apple's built-in sound "
                    f"classifier scores **{apple_eval['value']:.1f}** macro F1 on the official DCASE 2018 test clips; Kettle, on one "
                    f"microphone, scores **{held['ch0']['value']:.1f}** (95% CI {held['ch0']['ci95'][0]:.1f}–{held['ch0']['ci95'][1]:.1f}, "
                    f"{held['ch0']['n_clips']:,} clips, run once with a frozen model).")
    elif apple_dev:
        lead.append(f"Your Mac already hears a kettle. Asked which of 9 household activities is happening, Apple's built-in sound "
                    f"classifier scores **{apple_dev['value']:.1f}** macro F1 on our development clips; Kettle scores "
                    f"**{d['ours_ch0']['macro_f1']['value']:.1f}** on the same clips.")
    rows = ["| System | Macro F1 [95% CI] | Data |", "|---|---|---|"]
    if e:
        for name, key in (("all 7 eval microphones", "all"), ("known microphones", "known"), ("unseen microphones", "unknown")):
            s = e["slices"].get(key)
            if s:
                rows.append(f"| **Kettle, one mic** ({name}) | **{f(s['ch0'])}** | held-out test, N = {s['ch0']['n_clips']:,} clips / {s['ch0']['n_sessions']} sessions |")
                rows.append(f"| Kettle, 4-mic average ({name}) | {f(s['node_avg'])} | held-out test |")
        for k, label in (("apple_zeroshot", "Apple SoundAnalysis, zero-shot"), ("ast_zeroshot", "AST, zero-shot"),
                         ("ced_tiny_zeroshot", "CED-tiny, zero-shot"), ("majority", "Always 'Quiet'")):
            v = e.get("baselines", {}).get(k)
            if v and "value" in v:
                rows.append(f"| {label} | {f(v)} | held-out test, same clips |")
    rows.append(f"| Kettle, one mic | {f(d['ours_ch0']['macro_f1'])} | dev folds, N = {d['n_clips']:,} clips / {d['n_sessions']} sessions |")
    for k, label in (("logmel_lr", "Log-mel statistics + logistic regression (no deep model)"), ("ast_probe", "AST + same head"),
                     ("apple_zeroshot", "Apple SoundAnalysis, zero-shot"), ("ast_zeroshot", "AST, zero-shot"), ("majority", "Always 'Quiet'")):
        v = d["baselines"].get(k, {})
        if "macro_f1" in v:
            sub = f"; {v['subset']}, Kettle {v['ours_same_clips']['value']:.1f} on the same clips" if v.get("subset") else ""
            rows.append(f"| {label} | {f(v['macro_f1'])} | dev folds{sub} |")
    rows.append(f"| DCASE 2018 baseline (published) | {pub['dcase2018_baseline']['eval_known_mic']} known mics · {pub['dcase2018_baseline']['eval_unknown_mic']} unseen mics | full eval set, all dev data |")
    rows.append(f"| Best DCASE 2018 entry (published) | {pub['best_entry']['eval_known_mic']} · {pub['best_entry']['eval_unknown_mic']} | full eval set |")
    per = (e or d)["ours_ch0"]["per_class"] if e and "ours_ch0" in e else d["ours_ch0"]["per_class"]
    per_rows = ["| Activity | Caught | Missed | False alarms | N |", "|---|---|---|---|---|"]
    for c in per:
        per_rows.append(f"| {DISPLAY[c['class']]} | {f(c['recall'])} | {c['missed']} | {c['false_alarms']} | {c['support']} |")
    meal = (f"**For Meera's check (any kitchen activity: cooking, washing up or eating), dev folds:** caught {f(ma['caught'])}% "
            f"of {ma['n_meal']:,} windows (missed {ma['missed']}); wrongly called kitchen activity on {f(ma['false_alarm_rate'])}% "
            f"of {ma['n_other']:,} other windows ({ma['false_alarms']}).")
    o = m.get("offlist", {})
    extra = []
    if "confident_wrong" in o:
        extra.append(f"On {o['n']} sounds that aren't household activities (dogs, sirens, alarms, noise, silence), Kettle gave a confident "
                     f"label to {f(o['confident_wrong'])}% (vs {f(o['confident_wrong_without_novelty_gate'])}% without its "
                     f"'unlike anything it learned' check).")
    sl = d["session_level"]
    extra.append(f"Through the day bar (2-of-3 smoothing), {100 * sl['smoothing_on']['session_recall']:.0f}% of "
                 f"{sum(sl['smoothing_on']['sessions'])} activity sessions were caught with {sl['smoothing_on']['false_alarms_per_hour']} "
                 f"false-alarm blocks per hour ({sl['smoothing_off']['false_alarms_per_hour']} without smoothing).")
    split = (f"Held-out numbers: the official DCASE 2018 Task 5 evaluation set, a pre-registered seeded sample "
             f"({e['n_clips']:,} clips, {e['n_moments']:,} moments × 7 microphones), run once on {e['run']['started']} with the frozen model "
             f"(commit {e['run']['commit'][:7]}, model {e['run']['head_sha256'][:8]}), reweighted to the true class counts. "
             f"{e['fingerprint_summary'].capitalize()}.") if e else "The held-out run hasn't happened yet."
    fails = json.loads((ROOT / "results" / "failures.json").read_text())
    pick = [x for want in (("cooking", "dishwashing"), ("watching_tv", "social_activity"), ("other", "absence"))
            for x in fails if (x["true"], x["predicted"]) == want]
    fl = []
    for i, x in enumerate(pick, 1):
        probs = ", ".join(f"{DISPLAY[k]} {v:.2f}" for k, v in list(x["probs"].items())[:2])
        snd = ", ".join(s["name"].split(",")[0].lower() for s in x["sounds"])
        fl.append(f"{i}. **{DISPLAY[x['true']]} heard as {DISPLAY[x['predicted']].lower()}** ({x['how_many_like_this']} dev clips; e.g. "
                  f"`{x['clip']}`: {probs}; it heard {snd}). {x['likely_cause']}")
    tt = d["theta_tradeoff"]
    shipped = min(tt, key=lambda r: abs(r["theta"] - d["not_sure"]["theta"]))
    lo = tt[0]
    trade = (f"Below θ = {d['not_sure']['theta']:.2f} confidence Kettle says \"Not sure\" (chosen on dev folds so shown labels are right "
             f"{100 * d['not_sure']['macro_precision_shown']:.0f}% of the time; {100 * d['not_sure']['coverage']:.0f}% of windows get a label). "
             f"A false \"kitchen activity\" could hide a skipped breakfast; a missed one costs Meera an unnecessary call. We lean toward fewer "
             f"false ones: through the day bar, θ = {shipped['theta']:.2f} gives {shipped['meal_false_alarms_per_day']} false kitchen-activity "
             f"blocks per 16-hour day and misses {shipped['meal_sessions_missed']} of {shipped['meal_sessions']} meal sessions, versus "
             f"{lo['meal_false_alarms_per_day']} and {lo['meal_sessions_missed']} at θ = {lo['theta']:.2f} (dev folds).")
    return {"lead": "\n".join(lead), "results": "\n".join([split, "", *rows, "", meal, "", *per_rows, "", *extra]),
            "failures": "\n".join(fl), "tradeoff": trade}


def fill(path: Path, parts: dict) -> None:
    t = path.read_text()
    for k, v in parts.items():
        t = re.sub(rf"<!-- {k}:start -->.*?<!-- {k}:end -->", f"<!-- {k}:start -->\n{v}\n<!-- {k}:end -->", t, flags=re.S)
    path.write_text(t)


if __name__ == "__main__":
    m = json.loads((ROOT / "results" / "metrics.json").read_text())
    parts = blocks(m)
    for p in (ROOT / "docs" / "WRITEUP.md", ROOT / "README.md"):
        fill(p, parts)
    print(parts["lead"])
