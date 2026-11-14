"""python -m eval : regenerate every reported number from cached embeddings.

    python -m eval                      dev-fold study + off-list test with the shipped head -> results/
    python -m eval --split dcase-eval   THE ONE frozen run on the official eval sample (needs models/FROZEN)
    python -m eval --rehearse           the dcase-eval code path on a dev stand-in with a dummy head (no eval data)
    python -m eval --split own-kitchen  the team's own kitchens (eval/own_kitchen/labels.csv), frozen head

Writes results/metrics.json (every number with split, N, CI), results/metrics.md, results/confusion_dev.png,
results/failures.md + failures.json. The write-up and the "How sure is Kettle?" page read these files.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

import numpy as np

from eval import dev, metrics as M
from eval.common import ROOT, num
from kettle import evidence, model
from kettle.labels import CLASSES, DISPLAY

RESULTS = ROOT / "results"
PUBLISHED = {
    "source": "https://dcase.community/challenge2018/task-monitoring-domestic-activities-results (opened 2026-11-14)",
    "caveat": "Published systems scored all 72,972 eval clips and trained on all 72,984 dev clips with 4-channel "
              "posterior averaging; ours is a seeded, reweighted subsample with a head trained on <= 1,000 clips per class.",
    "dcase2018_baseline": {"dev_cv": 84.5, "eval_known_mic": 85.0, "eval_unknown_mic": 83.1, "other_class_unknown_mic": 35.0,
                           "what": "official log-mel CNN baseline, 4-mic posterior averaging"},
    "best_entry": {"system": "Inoue_IBM_task5_1", "dev_cv": 90.0, "eval_known_mic": 90.4, "eval_unknown_mic": 88.4,
                   "note": "tied at 88.4 unknown-mic with Tanabe_HIT_task5_1 and _4; the page lists no rank column"},
    "ranking_metric": "macro-averaged F1 on the evaluation set, unknown microphones",
}
PAIRS = [("eating", "cooking"), ("cooking", "eating"), ("other", "absence"), ("absence", "other"),
         ("watching_tv", "social_activity"), ("social_activity", "watching_tv"), ("dishwashing", "cooking"),
         ("cooking", "dishwashing"), ("working", "absence"), ("working", "other")]
LIKELY_CAUSE = {  # written before looking at any example; the evidence printed beside each lets a reader check it
    ("eating", "cooking"): "Eating and cooking share plate, cutlery and tap sounds; the SINS authors note eating is hard to hear.",
    ("cooking", "eating"): "Quiet stretches of cooking (stirring, waiting) sound like a meal at the table.",
    ("other", "absence"): "'Moving about' is often a few soft footsteps or a door in an otherwise quiet room.",
    ("absence", "other"): "A single bump or creak in a quiet room looks like someone moving about.",
    ("watching_tv", "social_activity"): "TV audio is mostly people talking; the model can't always tell a broadcast from a conversation.",
    ("social_activity", "watching_tv"): "A conversation with background music or a raised voice sounds like TV.",
    ("dishwashing", "cooking"): "Taps and clattering pans happen during both cooking and washing up.",
    ("cooking", "dishwashing"): "Rinsing and running water during cooking sounds like washing up.",
    ("working", "absence"): "Slow or quiet typing leaves a window that is mostly room noise.",
    ("working", "other"): "Shuffling papers or moving a chair while working sounds like moving about.",
}


def commit_hash() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except OSError:
        return "unknown"


# ---------------------------------------------------------------- pieces of the report

def failures(oof: dict, k: int = 1) -> list[dict]:
    """The most confident real mistakes for each common confusion (out-of-fold, channel 0)."""
    P, y = oof["P0"], oof["y"]
    pred = P.argmax(1)
    out = []
    for t, p in PAIRS:
        ti, pi = CLASSES.index(t), CLASSES.index(p)
        idx = np.where((y == ti) & (pred == pi))[0]
        if not len(idx):
            continue
        i = idx[np.argsort(-P[idx, pi])[:k]][0]
        top = np.argsort(-P[i])[:3]
        out.append({"clip": str(oof["files"][i]), "session": str(oof["session"][i]), "node": str(oof["node"][i]),
                    "fold": int(oof["fold"][i]), "true": t, "predicted": p,
                    "probs": {CLASSES[j]: round(float(P[i, j]), 3) for j in top},
                    "sounds": evidence.top_sounds(oof["scores"][i]), "likely_cause": LIKELY_CAUSE[(t, p)],
                    "how_many_like_this": int(len(idx))})
    return out


def offlist(head: dict) -> dict:
    """The shipped head on sounds that are none of the 9 activities: how often is it confidently wrong?"""
    from eval.embed import load
    try:
        d = load("ced-tiny", "offlist")
    except FileNotFoundError:
        return {"missing": "run python -m eval.offlist and python -m eval.embed ced-tiny offlist --ch0"}
    labels = {r["file"]: r for r in json.loads((ROOT / "data" / "clips" / "offlist" / "labels.json").read_text())}
    P = model.predict_proba(head, d["emb"][:, 0])
    th = head["theta"]
    gate = model.novelty(head, d["emb"][:, 0]) > head["novelty"]["threshold"] if "novelty" in head else np.zeros(len(P), bool)
    conf_no_gate = P.max(1)
    conf = np.where(gate, 0.0, conf_no_gate)
    cats = np.array([labels[f]["category"] for f in d["files"]])
    src = np.array([labels[f]["source"] for f in d["files"]])
    by = {}
    for c in sorted(set(cats)):
        m = cats == c
        by[c] = {"n": int(m.sum()), "confident": int((conf[m] >= th).sum()),
                 "labelled_as": {DISPLAY[CLASSES[j]]: int(((P[m].argmax(1) == j) & (conf[m] >= th)).sum())
                                 for j in range(9) if ((P[m].argmax(1) == j) & (conf[m] >= th)).sum()}}
    n = len(conf)
    k = int((conf >= th).sum())
    lo, hi = M.wilson(k, n)
    curve = [{"theta": float(t), "share_shown": float((conf >= t).mean())} for t in np.round(np.arange(0.2, 0.99, 0.02), 2)]
    k0 = int((conf_no_gate >= th).sum())
    return {"n": n, "theta": th, "confident_wrong": num(k / n, "off-list (ESC-50 non-activity + noise + silence)", n, n, (lo, hi)),
            "confident_wrong_without_novelty_gate": num(k0 / n, "off-list", n, n, M.wilson(k0, n)),
            "esc50_confident": int(((conf >= th) & (src == "esc50")).sum()), "esc50_n": int((src == "esc50").sum()),
            "by_category": by, "curve": curve,
            "note": "Every label shown here is wrong by construction (none of these are household activities). Wilson 95% CI."}


def confusion_png(C: np.ndarray, path: Path, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    R = C / np.maximum(C.sum(1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(7.2, 6.2), dpi=150)
    ax.imshow(R, cmap="Blues", vmin=0, vmax=1)
    names = [DISPLAY[c].replace(" (typing)", "") for c in CLASSES]
    ax.set_xticks(range(9), names, rotation=40, ha="right", fontsize=8)
    ax.set_yticks(range(9), names, fontsize=8)
    for i in range(9):
        for j in range(9):
            if C[i, j]:
                ax.text(j, i, f"{int(C[i, j])}", ha="center", va="center", fontsize=7, color="white" if R[i, j] > .5 else "#15181C")
    ax.set_xlabel("Kettle said"); ax.set_ylabel("True activity"); ax.set_title(title, fontsize=9)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def markdown(m: dict) -> str:
    d = m["dev"]
    f = lambda x: f"{x['value']:.1f} [{x['ci95'][0]:.1f}, {x['ci95'][1]:.1f}]" if "ci95" in x else f"{x['value']:.1f}"
    L = [f"# Kettle results ({m['generated']}, commit {m['commit'][:10]}, head {m['head_sha256'][:12]})", "",
         f"Primary metric: macro F1 over the 9 SINS activities, 10-s windows. Dev numbers: **{d['split']}**, "
         f"N = {d['n_clips']} clips from {d['n_sessions']} sessions, prevalence-reweighted, 95% session-bootstrap CI.", ""]
    if m.get("dcase_eval") and "ours_node_avg" in m["dcase_eval"]:
        e = m["dcase_eval"]
        L += ["## Held-out test: official DCASE 2018 Task 5 eval sample, run once", "",
              f"Run {e['run']['started']} · commit {e['run']['commit'][:10]} · head {e['run']['head_sha256'][:12]} · N = {e['n_clips']} clips, {e['n_moments']} moments", "",
              "| Slice | Ours, 4-mic node average | Ours, single mic (ch 0) | DCASE baseline | Best entry |", "|---|---|---|---|---|"]
        for name, key, pub in (("All 7 nodes", "all", None), ("Known mics", "known", "eval_known_mic"), ("Unknown mics", "unknown", "eval_unknown_mic")):
            s = e["slices"].get(key)
            if s:
                L.append(f"| {name} | {f(s['node_avg'])} | {f(s['ch0'])} | {PUBLISHED['dcase2018_baseline'].get(pub, '–') if pub else '–'} | {PUBLISHED['best_entry'].get(pub, '–') if pub else '–'} |")
        L += ["", f"Mic mapping: {e['fingerprint_summary']}", ""]
    L += ["## Dev folds: ours vs baselines (macro F1, %)", "", "| System | Macro F1 [95% CI] |", "|---|---|",
          f"| **Kettle: CED-tiny + logistic head, 4-mic node average** | {f(d['ours_node_avg']['macro_f1'])} |",
          f"| **Kettle, single mic (channel 0, what one laptop hears)** | {f(d['ours_ch0']['macro_f1'])} |"]
    for k, v in d["baselines"].items():
        if "macro_f1" in v:
            L.append(f"| {k.replace('_', ' ')} | {f(v['macro_f1'])} |")
    L += [f"| DCASE 2018 baseline (published, dev CV, full data) | {PUBLISHED['dcase2018_baseline']['dev_cv']} |",
          f"| Best DCASE 2018 entry (published, dev CV) | {PUBLISHED['best_entry']['dev_cv']} |", "",
          "## Per activity (dev, single mic): misses and false alarms", "",
          "| Activity | Caught (recall) | Precision | Missed | False alarms | N |", "|---|---|---|---|---|---|"]
    for c in d["ours_ch0"]["per_class"]:
        L.append(f"| {DISPLAY[c['class']]} | {f(c['recall'])} | {f(c['precision'])} | {c['missed']} | {c['false_alarms']} | {c['support']} |")
    ns = d["not_sure"]
    L += ["", f"**Not sure:** θ = {ns['theta']:.2f} (chosen on dev: reweighted shown-label precision ≥ 0.90); "
              f"coverage {100 * ns['coverage']:.1f}% of windows get a label, precision of shown labels {100 * ns['macro_precision_shown']:.1f}%. "
              f"Temperature {d['temperature']:.2f}; ECE {d['calibration']['ece_after_temperature']:.3f}.", ""]
    s_on, s_off = d["session_level"]["smoothing_on"], d["session_level"]["smoothing_off"]
    L += ["## Through the shipped timeline (activity sessions, dev)", "",
          f"With 2-of-3 smoothing: {100 * s_on['session_recall']:.1f}% of {sum(s_on['sessions'])} activity sessions caught, "
          f"{s_on['false_alarms_per_hour']} false-alarm blocks per hour of audio. Without smoothing: {100 * s_off['session_recall']:.1f}% caught, "
          f"{s_off['false_alarms_per_hour']} per hour ({s_on['hours']} h of stitched audio).", ""]
    if "missing" not in m.get("offlist", {"missing": 1}):
        o = m["offlist"]
        L += ["## Off-list sounds (not one of the 9 activities)", "",
              f"{f(o['confident_wrong'])}% of {o['n']} off-list clips got a confident label with θ and the novelty gate "
              f"({f(o['confident_wrong_without_novelty_gate'])}% with θ alone). Every one of those labels is wrong by construction.", ""]
    A = d["ablations"]
    L += ["## Ablations (dev, single mic)", ""]
    for k, v in A.items():
        if isinstance(v, dict) and "macro_f1" in v:
            L.append(f"- {k.replace('_', ' ')}: {f(v['macro_f1'])}")
        elif k == "leave_one_node_out":
            L.append(f"- leave one mic node out: held-out node mean {v['mean_held_out']} vs same nodes {v['mean_same']} ({v['held_out_node_macro_f1']})")
    L += ["", "## Published DCASE 2018 Task 5 numbers", "", PUBLISHED["caveat"], f"Source: {PUBLISHED['source']}", ""]
    return "\n".join(L) + "\n"


def failures_md(fs: list[dict]) -> str:
    L = ["# Where Kettle fails: real mistakes from the dev folds", "",
         "Each is the most confident wrong answer (out-of-fold, single mic) for a common confusion. 'Likely cause' was written "
         "before looking at examples; the sounds the encoder heard are printed so you can judge it.", ""]
    for i, f in enumerate(fs, 1):
        L += [f"## {i}. {DISPLAY[f['true']]} heard as {DISPLAY[f['predicted']]}",
              f"- Clip `{f['clip']}` (session {f['session']}, {f['node']}, fold {f['fold']}); {f['how_many_like_this']} dev clips made this same mistake.",
              f"- Kettle's probabilities: " + ", ".join(f"{DISPLAY[k]} {v:.2f}" for k, v in f["probs"].items()),
              f"- Sounds the encoder heard: " + ", ".join(f"{s['name']} {s['score']:.2f}" for s in f["sounds"]),
              f"- Likely cause: {f['likely_cause']}", ""]
    return "\n".join(L)


# ---------------------------------------------------------------- the default run

def run_default(fast: bool) -> dict:
    t0 = time.time()
    head = model.load(ROOT / "models" / "head.json")
    R = dev.run(fast=fast)
    oof = R.pop("_oof")
    R.pop("_nov", None)
    fs = failures(oof)
    m = {"generated": time.strftime("%Y-%m-%d %H:%M %Z"), "commit": commit_hash(), "head_sha256": head["sha256"],
         "head": {"theta": head["theta"], "temperature": head["temperature"], "trained_on": head.get("trained_on")},
         "primary_metric": "macro F1 over the 9 SINS activities (DCASE 2018 Task 5 metric), 10-s windows, with per-activity missed (FN) and false alarms (FP)",
         "dev": R, "offlist": offlist(head), "published": PUBLISHED}
    prev = RESULTS / "dcase_eval.json"
    m["dcase_eval"] = json.loads(prev.read_text()) if prev.exists() else None
    ok = RESULTS / "own_kitchen.json"
    m["own_kitchen"] = json.loads(ok.read_text()) if ok.exists() else None
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "metrics.json").write_text(json.dumps(m, indent=1, default=float))
    (RESULTS / "metrics.md").write_text(markdown(m))
    (RESULTS / "failures.json").write_text(json.dumps(fs, indent=1))
    (RESULTS / "failures.md").write_text(failures_md(fs))
    confusion_png(np.array(R["ours_ch0"]["confusion"]), RESULTS / "confusion_dev.png",
                  f"Dev folds, single mic, N = {R['n_clips']} clips (counts; colour = share of the true row)")
    print(f"wrote results/ in {time.time() - t0:.0f} s: dev macro F1 node-avg {R['ours_node_avg']['macro_f1']['value']} "
          f"ch0 {R['ours_ch0']['macro_f1']['value']}")
    return m


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "dcase-eval", "own-kitchen"])
    ap.add_argument("--rehearse", action="store_true")
    ap.add_argument("--fast", action="store_true")
    a = ap.parse_args()
    if a.rehearse:
        from eval.dcase import rehearse
        rehearse()
    elif a.split == "dcase-eval":
        os.environ["KETTLE_EVAL_RUN"] = "1"
        from eval.dcase import run_once
        run_once()
    elif a.split == "own-kitchen":
        from eval.own_kitchen import score
        score()
    else:
        run_default(a.fast)
