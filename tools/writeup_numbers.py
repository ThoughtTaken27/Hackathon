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
    bl, best = pub["dcase2018_baseline"], pub["best_entry"]
    ma = d["meal_activity"]
    lead, held, dev_rows, extra = [], [], [], []
    if e:
        a = e["slices"]["all"]
        apple = e.get("baselines", {}).get("apple_zeroshot", {})
        lead.append(
            f"On the official DCASE 2018 test set (run once with a frozen model; {e['n_moments']:,} moments × 7 microphones = "
            f"{e['n_clips']:,} clips from {a['ch0']['n_sessions']} sessions), Kettle scores **{a['ch0']['value']:.1f}** macro F1 "
            f"(95% CI {a['ch0']['ci95'][0]:.1f}–{a['ch0']['ci95'][1]:.1f}) on one microphone and {a['node_avg']['value']:.1f} on four: level with the "
            f"official 2018 baseline ({bl['eval_known_mic']} known / {bl['eval_unknown_mic']} unseen microphones, full set) and below the best "
            f"entry ({best['eval_known_mic']} / {best['eval_unknown_mic']}). A Mac already hears a kettle, but Apple's built-in sound classifier "
            f"scores {apple.get('value', float('nan')):.1f} on the same clips. Our contribution isn't the leaderboard: it's publishing every "
            f"activity's misses and false alarms, and a \"Not sure\", consent and pause design built around them.")
        held += ["**Held-out test (official DCASE 2018 eval sample, run once, all 7 microphones; macro F1, 95% session-bootstrap CI):**", "",
                 "| System | Macro F1 | N |", "|---|---|---|",
                 f"| **Kettle, one microphone** | **{f(a['ch0'])}** | {a['ch0']['n_clips']:,} clips / {e['n_moments']:,} moments / {a['ch0']['n_sessions']} sessions |",
                 f"| Kettle, 4-microphone average | {f(a['node_avg'])} | same |"]
        for k, label in (("apple_zeroshot", "Apple SoundAnalysis, zero-shot"), ("ced_tiny_zeroshot", "Same encoder, zero-shot label map"),
                         ("majority", "Always \"Quiet\"")):
            v = e.get("baselines", {}).get(k, {})
            if "value" in v:
                held.append(f"| {label} | {f(v)} | same clips |")
        held.append(f"| DCASE 2018 official baseline (published) | {bl['eval_known_mic']} known mics · {bl['eval_unknown_mic']} unseen mics | full eval set, all dev data |")
        held.append(f"| DCASE 2018 best entry (published) | {best['eval_known_mic']} · {best['eval_unknown_mic']} | full eval set |")
        held += ["", f"CIs resample the {a['ch0']['n_sessions']} test sessions (the lower end is pessimistic: some resamples lack a rare activity). "
                     "Sample, scoring and microphone rule were pre-registered before any test audio was fetched; the rule couldn't identify the 3 unseen "
                     "microphones, so we report all 7 together and claim no unseen-microphone number.", ""]
        per = e["ours_ch0"]["per_class"]
        held += ["**Held-out, per activity (one microphone): misses and false alarms counted separately**", "",
                 "| Activity | Caught (recall) | Missed | False alarms | N clips |", "|---|---|---|---|---|"]
        for c in per:
            held.append(f"| {DISPLAY[c['class']]} | {f(c['recall'])} | {c['missed']} | {c['false_alarms']} | {c['support']:,} |")
        dper = {c["class"]: c for c in d["ours_ch0"]["per_class"]}
        drops = [(c, dper[c["class"]]["recall"]["value"] - c["recall"]["value"]) for c in per]
        big = [f"{DISPLAY[c['class']].lower()} {dper[c['class']]['recall']['value']:.0f}% → {c['recall']['value']:.0f}%" for c, dd in sorted(drops, key=lambda x: -x[1]) if dd >= 5]
        if big:
            held += ["", f"Recall fell from dev to held-out for {', '.join(big)} (a different stretch of the week and other microphones; one run can't separate the causes)."]
        em = e.get("meal_activity")
        if em:
            held += ["", f"**Meera's check (any kitchen activity), held-out:** caught {f(em['caught'])}% of {em['n_meal']:,} windows "
                         f"(**missed {em['missed']}**); **false alarms** on {f(em['false_alarm_rate'])}% of {em['n_other']:,} other windows "
                         f"({em['false_alarms']}). Computed after the run from its saved predictions (not in the pre-registration)."]
    dev_rows += ["", "**Development folds (session-disjoint, 4-fold; optimistic: the same folds chose the model):**", "",
                 "| System | Macro F1 | Notes |", "|---|---|---|",
                 f"| **Kettle, one microphone** | **{f(d['ours_ch0']['macro_f1'])}** | N = {d['n_clips']:,} clips / {d['n_sessions']} sessions |"]
    for k, label in (("logmel_lr", "Log-mel statistics + logistic regression (no deep model)"), ("ced_small_probe", "CED-small (4× bigger) + same head"),
                     ("ast_probe", "AST (16× bigger) + same head"), ("apple_zeroshot", "Apple SoundAnalysis, zero-shot"),
                     ("ast_zeroshot", "AST, zero-shot label map"), ("majority", "Always \"Quiet\"")):
        v = d["baselines"].get(k, {})
        if "macro_f1" in v:
            sub = f"{v['subset']}; Kettle {v['ours_same_clips']['value']:.1f} on the same clips" if v.get("subset") else ""
            dev_rows.append(f"| {label} | {f(v['macro_f1'])} | {sub} |")
    dev_rows += ["", f"Dev, Meera's check: caught {f(ma['caught'])}% of {ma['n_meal']:,} kitchen windows (missed {ma['missed']}); "
                     f"false alarms on {f(ma['false_alarm_rate'])}% of {ma['n_other']:,} others ({ma['false_alarms']})."]
    o = m.get("offlist", {})
    if "confident_wrong" in o:
        extra.append(f"On {o['n']} sounds that aren't household activities (dogs, sirens, alarms, noise, silence), Kettle gave a confident "
                     f"label to {f(o['confident_wrong'])}% (vs {f(o['confident_wrong_without_novelty_gate'])}% without its "
                     f"'unlike anything it learned' check).")
    sl = d["session_level"]["smoothing_on"]
    extra.append(f"Through the day bar (dev, 2-of-3 smoothing, {sl['hours']} h of stitched audio): {f(sl['session_recall'])}% of "
                 f"{sum(sl['sessions'])} activity sessions were caught as one block covering at least half of them, with "
                 f"{sl['false_alarms_per_hour']} false-alarm blocks per hour across all activities "
                 f"({d['session_level']['smoothing_off']['false_alarms_per_hour']} without smoothing).")
    split = ""
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
    shipped = next((r for r in tt if r.get("shipped")), tt[0])
    lo = tt[0]
    missed_all = {r["meal_sessions_missed"] for r in tt}
    fa_range = (min(r["meal_false_alarm_blocks"] for r in tt), max(r["meal_false_alarm_blocks"] for r in tt))
    trade = (f"**The \"Not sure\" bar θ.** Below θ = {d['not_sure']['theta']:.2f} confidence Kettle says \"Not sure\". We chose θ on dev folds "
             f"so that shown labels are right {d['not_sure']['shown_precision_metric']['value']:.0f}% of the time "
             f"({d['not_sure']['coverage_metric']['value']:.0f}% of windows get a label). For Meera's check it barely matters on dev: across "
             f"{lo['meal_sessions']} kitchen sessions ({lo['days']} days of stitched audio) "
             + ("no kitchen session went unnoticed at any θ from 0.30 to 0.90" if missed_all == {0} else "kitchen sessions missed varied with θ")
             + f", and θ only moved the count of false kitchen-activity blocks between {fa_range[0]} and {fa_range[1]} "
             f"({shipped['meal_false_alarms_per_day']} per 16-hour day at the chosen θ, {lo['meal_false_alarms_per_day']} at θ = {lo['theta']:.2f}). "
             f"Those are kitchen-level false alarms; the \"per hour\" figure above counts every activity confusion, including cooking vs washing up. "
             f"The cost of a high θ shows up elsewhere: {e['not_sure_share_at_theta']['value']:.0f}% of held-out windows were \"Not sure\"." if e else "")
    lm, ap = d["baselines"]["logmel_lr"]["macro_f1"], d["baselines"].get("ast_probe", {})
    dev_line = (f"Development folds (optimistic; they chose the model): Kettle {f(d['ours_ch0']['macro_f1'])}, log-mel statistics + logistic "
                f"regression (no deep model) {f(lm)}"
                + (f", AST (16× bigger) + the same head {f(ap['macro_f1'])} on a 2,700-clip subset where Kettle scores {ap['ours_same_clips']['value']:.1f}" if "macro_f1" in ap else "")
                + f"; N = {d['n_clips']:,} clips / {d['n_sessions']} sessions.")
    short = held + ["", dev_line]
    fl_short = [f"{i}. **{DISPLAY[x['true']]} → {DISPLAY[x['predicted']].lower()}** ({x['how_many_like_this']} dev clips): {x['likely_cause']}"
                for i, x in enumerate(pick, 1)]
    trade_short = (f"\"Not sure\" below θ = {d['not_sure']['theta']:.2f} (chosen on dev so shown labels are right "
                   f"{d['not_sure']['shown_precision_metric']['value']:.0f}% of the time). On dev, no kitchen session went unnoticed at any θ "
                   f"from 0.30 to 0.90; θ only moved false kitchen blocks ({lo['meal_false_alarms_per_day']} → {shipped['meal_false_alarms_per_day']} "
                   f"per 16-hour day). Its cost: {e['not_sure_share_at_theta']['value']:.0f}% of held-out windows were \"Not sure\"." if e and missed_all == {0} else trade)
    return {"lead": "\n".join(lead), "results": "\n".join(held + dev_rows + [""] + extra),
            "results_short": "\n".join(short), "failures": "\n".join(fl), "tradeoff": trade,
            "failures_short": "\n".join(fl_short), "tradeoff_short": trade_short}


def fill(path: Path, parts: dict) -> None:
    t = path.read_text()
    for k, v in parts.items():
        t = re.sub(rf"<!-- {k}:start -->.*?<!-- {k}:end -->", f"<!-- {k}:start -->\n{v}\n<!-- {k}:end -->", t, flags=re.S)
    path.write_text(t)


if __name__ == "__main__":
    m = json.loads((ROOT / "results" / "metrics.json").read_text())
    parts = blocks(m)
    fill(ROOT / "README.md", parts)
    fill(ROOT / "docs" / "SUBMISSION-DRAFT.md", {"lead": parts["lead"]})
    wp = dict(parts)
    wp["results"], wp["failures"], wp["tradeoff"] = parts["results_short"], parts["failures_short"], parts["tradeoff_short"]
    fill(ROOT / "docs" / "WRITEUP.md", wp)
    print(parts["lead"])
