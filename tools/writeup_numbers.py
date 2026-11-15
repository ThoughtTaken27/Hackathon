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
            f"(95% CI {a['ch0']['ci95'][0]:.1f}–{a['ch0']['ci95'][1]:.1f}) on one microphone and {a['node_avg']['value']:.1f} on four. That is close to the official 2018 baseline's "
            f"published {bl['eval_known_mic']} (known microphones) / {bl['eval_unknown_mic']} (unseen), but not directly comparable: they scored the full "
            f"test set and trained on all development data; we scored a pre-registered sample. The best entry scored {best['eval_known_mic']} / "
            f"{best['eval_unknown_mic']}. Our contribution isn't the leaderboard: it's publishing every activity's misses and false alarms "
            f"separately, a \"Not sure\" that gave a confident label to only {m['offlist']['confident_wrong']['value']:.1f}% of {m['offlist']['n']} off-list sounds, and a consent and pause "
            f"design built around them. These are recordings from one research home replayed through the app, not yet a real kitchen. "
            f"(For context only: Apple's built-in sound classifier, zero-shot with a different label set, scores "
            f"{apple.get('value', float('nan')):.1f} on the same clips.)")
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
        na = e.get("node_activity_recall")
        if na:
            rng = lambda c: (min(na[n][c]["value"] for n in na), max(na[n][c]["value"] for n in na))
            wk, mv = rng("working"), rng("other")
            worst_node = min(na, key=lambda n: na[n]["working"]["value"])
            held += ["", f"Every held-out moment was heard by all 7 microphones, so differences between microphones on the same activity come "
                         f"from the microphone alone, its position or hardware (a post-hoc slice of the saved predictions, `results/metrics.md`): {DISPLAY['working'].lower()} "
                         f"ranged from {wk[0]:.0f}% on {worst_node.replace('EvalNode', 'node ')} to {wk[1]:.0f}%, while {DISPLAY['other'].lower()} was "
                         f"{mv[0]:.0f}–{mv[1]:.0f}% on every microphone, so its drop isn't a microphone effect."]
        em = e.get("meal_activity")
        if em:
            hit = em['n_meal'] - em['missed']
            held += ["", f"**Meera's check (any kitchen activity), held-out:** the top label caught **{hit:,} of {em['n_meal']:,}** kitchen-activity windows "
                         f"(**missed {em['missed']}**): {100 * hit / em['n_meal']:.1f}% raw, **{em['caught']['value']}%** [{em['caught']['ci95'][0]}, {em['caught']['ci95'][1]}] reweighted. **False alarms** on "
                         f"**{em['false_alarms']} of {em['n_other']:,}** other windows: {100 * em['false_alarms'] / em['n_other']:.2f}% raw, "
                         f"**{em['false_alarm_rate']['value']}%** [{em['false_alarm_rate']['ci95'][0]}, {em['false_alarm_rate']['ci95'][1]}] reweighted. Counts are raw; reweighted percentages re-scale each activity to the full test "
                         f"set's activity mix (the sample topped rare activities up to at least 50 moments each, which over-represents them), as pre-registered. "
                         f"Computed after the run from its saved predictions (not in the pre-registration)."]
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
    rt_path = ROOT / "results" / "runtime.json"
    if rt_path.exists():
        rt = json.loads(rt_path.read_text())
        if rt.get("median_change_to_label_s") is not None:
            extra.append(f"Live, on a laptop CPU (privacy-check run, {rt['seconds']} s through the browser's microphone, {rt['n_changes']} activity changes): "
                         f"a new activity reached the timeline after a median {rt['median_change_to_label_s']:.1f} s (a 10-s window must fill with "
                         f"the new sound); each 2-s update took {rt['per_hop_s_median'] * 1000:.0f} ms (90th percentile "
                         f"{rt['per_hop_s_p90'] * 1000:.0f} ms) and the server used {rt['server_cpu_percent_mean']:.0f}% CPU on average.")
    sl = d["session_level"]["smoothing_on"]
    extra.append(f"Through the day bar (dev, 2-of-3 smoothing and the 30-s bridging rule, {sl['hours']} h of stitched audio): {f(sl['session_recall'])}% of "
                 f"{sum(sl['sessions'])} activity sessions were caught as one block covering at least half of them, with "
                 f"{sl['false_alarms_per_hour']} false-alarm blocks per hour across all activities "
                 f"({d['session_level']['smoothing_off']['false_alarms_per_hour']} without smoothing).")
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
    lo = tt[0]
    ks = d["kitchen_sessions"]
    w, wo = ks["with_bridging"], ks["without_bridging"]
    pc = lambda x: f"{x['caught']['value']:.0f}% (95% CI {x['caught']['ci95'][0]:.0f}–{x['caught']['ci95'][1]:.0f})"
    trade = (f"**The \"Not sure\" bar θ and the day bar.** Below θ = {d['not_sure']['theta']:.2f} confidence Kettle says \"Not sure\"; we chose "
             f"θ on dev folds so shown labels are right {d['not_sure']['shown_precision_metric']['value']:.0f}% of the time. Through the day bar "
             f"on dev ({w['n_sessions']} kitchen sessions, {lo['days']} days of stitched audio), kitchen-activity blocks covered at least half of "
             f"{w['merged']['n_caught']} of {w['n_sessions']} sessions. The stricter test, one block of the right activity covering half the session, "
             f"first caught only {wo['strict']['n_caught']}: the right activity was there, split into pieces by short \"Not sure\" stretches. "
             f"A timeline rule added after the frozen test run (a \"Not sure\" gap of up to {ks['bridge_s']:.0f} s inside one activity no longer splits "
             f"it; θ and the model unchanged) raised that to {w['strict']['n_caught']} of {w['n_sessions']}, {pc(w['strict'])}, and cut false "
             f"kitchen blocks from {wo['false_kitchen_blocks_per_day']} to {w['false_kitchen_blocks_per_day']} per 16-hour day. Raising θ trades "
             f"false kitchen blocks ({lo['meal_false_alarms_per_day']} per day at θ = {lo['theta']:.2f}) for more \"Not sure\": "
             f"{e['not_sure_share_at_theta']['value']:.0f}% of held-out windows were \"Not sure\" at the chosen θ." if e else "")
    lm, ap = d["baselines"]["logmel_lr"]["macro_f1"], d["baselines"].get("ast_probe", {})
    dev_line = (f"Development folds (optimistic; they chose the model): Kettle {f(d['ours_ch0']['macro_f1'])}, log-mel statistics + logistic "
                f"regression (no deep model) {f(lm)}"
                + (f", AST (16× bigger) + the same head {f(ap['macro_f1'])} on a 2,700-clip subset where Kettle scores {ap['ours_same_clips']['value']:.1f}" if "macro_f1" in ap else "")
                + f"; N = {d['n_clips']:,} clips / {d['n_sessions']} sessions.")
    short = held + ["", dev_line]
    fl_short = [f"{i}. **{DISPLAY[x['true']]} → {DISPLAY[x['predicted']].lower()}** ({x['how_many_like_this']} dev clips): {x['likely_cause']}"
                for i, x in enumerate(pick, 1)]
    trade_short = (f"\"Not sure\" below θ = {d['not_sure']['theta']:.2f} (chosen on dev so shown labels are right "
                   f"{d['not_sure']['shown_precision_metric']['value']:.0f}% of the time). On dev, kitchen-activity blocks covered at least half of "
                   f"{w['merged']['n_caught']} of {w['n_sessions']} kitchen sessions, but the right activity formed one such block in only "
                   f"{wo['strict']['n_caught']}: short \"Not sure\" stretches split it. A timeline rule added after the frozen test run (bridge a "
                   f"\"Not sure\" gap of up to {ks['bridge_s']:.0f} s inside one activity; model and θ unchanged) raised that to "
                   f"{w['strict']['n_caught']} of {w['n_sessions']} and cut false kitchen blocks from {wo['false_kitchen_blocks_per_day']} to "
                   f"{w['false_kitchen_blocks_per_day']} per 16-hour day. Its cost: {e['not_sure_share_at_theta']['value']:.0f}% of held-out windows were \"Not sure\"." if e else trade)
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
    # the one-page write-up keeps the tables, Meera's check and the dev line; the long explanations stay in the README
    keep = [ln for ln in wp["results"].split("\n") if not ln.startswith(("CIs resample", "Recall fell", "Every held-out moment"))]
    wp["results"] = re.sub(r"\n{3,}", "\n\n", "\n".join(keep))
    fill(ROOT / "docs" / "WRITEUP.md", wp)
    print(parts["lead"])
