"""Build notebooks/kettle_reproduce.ipynb (then execute it with nbconvert so outputs are saved).

Usage: python tools/make_notebook.py && jupyter nbconvert --to notebook --execute --inplace notebooks/kettle_reproduce.ipynb
"""
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]

CELLS = [
    ("md", """# Kettle: reproduce every number (about 3 minutes on a CPU, no keys, no network)

This notebook recomputes Kettle's reported results from the small cache committed in `results/cache/` (embeddings of the
SINS / DCASE 2018 Task 5 development clips, ~25 MB), so you don't need to download the 46 GB dataset (fetching our
8,920-clip subset from Zenodo takes ~76 minutes at its rate limit).

It retrains the logistic head on the official session-disjoint folds, then rebuilds the headline tables and plots:
macro F1 with session-bootstrap 95% CIs, missed vs false-alarm counts per activity, the caregiver's "kitchen activity"
metric, calibration, the "not sure" trade-off, slices, baselines, and the one held-out run on the official eval sample
(from its saved predictions). At the end it checks the numbers against `results/metrics.json`.

*This project is a prototype and is not medical advice.*"""),
    ("code", """# Setup. In Colab this clones the repo; locally it uses the folder this notebook is in.
import os, sys, time, json, subprocess
T0 = time.time()
if "google.colab" in sys.modules:
    REPO_URL = "https://github.com/OWNER/REPO"   # set to the team's public repo URL after pushing
    if not os.path.exists("kettle-repo"):
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, "kettle-repo"], check=True)
    os.chdir("kettle-repo")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"], check=True)
ROOT = os.path.abspath("." if os.path.exists("eval") else "..")
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["KETTLE_USE_CACHE"] = "1"      # use only the committed cache, even if local shards exist
os.environ["HF_HUB_OFFLINE"] = "1"
print("repo:", ROOT)
print({p: f"{os.path.getsize(os.path.join('results/cache', p)) / 1e6:.1f} MB" for p in sorted(os.listdir("results/cache"))})"""),
    ("md", "## 1. Development folds: retrain the head and score it\nThe C values below were chosen by nested (inner leave-one-fold-out) CV in `python -m eval`; reusing them keeps this notebook fast. Set `NESTED = True` to choose them again (~5 more minutes)."),
    ("code", """from eval import dev
from eval.__main__ import markdown, reliability_png, tradeoff_png, confusion_png, failures, PUBLISHED
import numpy as np
saved = json.load(open("results/metrics.json"))
NESTED = False
Cs = None if NESTED else {"ours": saved["dev"]["C_per_fold"], "logmel_lr": saved["dev"]["C_per_fold_baselines"]["logmel_lr"]}
R = dev.run(fast=True, Cs=Cs)
oof = R.pop("_oof"); R.pop("_nov", None); R.pop("_stored_predictions", None)
print(f"{R['n_clips']} clips, {R['n_sessions']} sessions; C per fold {R['C_per_fold']}; temperature {R['temperature']}")
for name in ("ours_ch0", "ours_node_avg"):
    m = R[name]["macro_f1"]; print(f"{name:14s} macro F1 {m['value']} [{m['ci95'][0]}, {m['ci95'][1]}]")"""),
    ("md", "## 2. Per activity: missed and false alarms, counted separately (single microphone)"),
    ("code", """from kettle.labels import DISPLAY
print(f"{'activity':18s} {'caught':>16s} {'missed':>7s} {'false alarms':>13s} {'precision':>16s} {'N':>5s}")
for c in R["ours_ch0"]["per_class"]:
    r, p = c["recall"], c["precision"]
    print(f"{DISPLAY[c['class']]:18s} {r['value']:5.1f} [{r['ci95'][0]:4.1f},{r['ci95'][1]:5.1f}] {c['missed']:7d} {c['false_alarms']:13d} {p['value']:5.1f} [{p['ci95'][0]:4.1f},{p['ci95'][1]:5.1f}] {c['support']:5d}")"""),
    ("md", "## 3. The caregiver's metric: any kitchen activity (cooking, washing up or eating)"),
    ("code", """ma = R["meal_activity"]
for k in ("caught", "right_when_it_says_so", "false_alarm_rate"):
    print(f"{k:22s} {ma[k]['value']:5.1f}%  95% CI {ma[k]['ci95']}  N={ma[k]['n_clips']}")
print("missed windows:", ma["missed"], " false-alarm windows:", ma["false_alarms"])"""),
    ("md", "## 4. Baselines on the same clips and folds\nZero-shot maps were frozen before any score was computed (`docs/research/kettle/probes/maps/`). AST, CED-small and CLAP baselines come from committed out-of-fold predictions (their embeddings are too big to commit); Apple's from its committed per-activity scores."),
    ("code", """rows = [("Kettle, single mic", R["ours_ch0"]["macro_f1"]), ("Kettle, 4-mic average", R["ours_node_avg"]["macro_f1"])]
rows += [(k, v["macro_f1"]) for k, v in R["baselines"].items() if "macro_f1" in v]
for name, m in rows:
    print(f"{name:28s} {m['value']:5.1f}  [{m['ci95'][0]:5.1f}, {m['ci95'][1]:5.1f}]")
print(f"{'DCASE 2018 baseline (pub.)':28s} {PUBLISHED['dcase2018_baseline']['dev_cv']:5.1f}  (all data; not strictly comparable)")"""),
    ("md", "## 5. How much to trust \"how sure\": calibration and the cost of the \"not sure\" threshold"),
    ("code", """from IPython.display import Image, display
os.makedirs("results/notebook", exist_ok=True)
reliability_png(R["calibration"], __import__("pathlib").Path("results/notebook/reliability_dev.png"))
tradeoff_png(R["theta_tradeoff"], R["not_sure"]["theta"], __import__("pathlib").Path("results/notebook/theta_tradeoff_dev.png"))
display(Image("results/notebook/reliability_dev.png", width=420)); display(Image("results/notebook/theta_tradeoff_dev.png", width=520))
print("ECE before / after temperature:", R["calibration"]["ece_before"]["value"], "/", R["calibration"]["ece_after_temperature"]["value"], "points")
print("theta", R["not_sure"]["theta"], "coverage", round(R["not_sure"]["coverage"], 3), "shown-label precision", round(R["not_sure"]["macro_precision_shown"], 3))"""),
    ("md", "## 6. Slices we can check\nSINS is one person in one home, so age and sex can't be tested. Microphone positions and activities can; the team's own kitchens are added on Sunday (`python -m eval --split own-kitchen`)."),
    ("code", """for nd, m in R["per_node"].items():
    print(f"{nd}: {m['value']} [{m['ci95'][0]}, {m['ci95'][1]}]  N={m['n_clips']}")
cm = np.array(R["ours_ch0"]["confusion"])
confusion_png(cm, __import__("pathlib").Path("results/notebook/confusion_dev.png"), f"Dev folds, single mic, N = {R['n_clips']}")
display(Image("results/notebook/confusion_dev.png", width=520))"""),
    ("md", "## 7. The held-out test: the official DCASE 2018 eval sample, run once\nRecomputed from the saved predictions (`results/eval_predictions.jsonl`) and the dataset's public labels. The run itself (commit, model hash, time) is recorded in `results/eval_run.json`."),
    ("code", """from eval.dcase import score_saved_predictions
if os.path.exists("results/eval_predictions.jsonl"):
    E = score_saved_predictions()
    print(json.dumps(E["slices"], indent=1)[:1500])
    print(json.load(open("results/eval_run.json"))["attempts"])
else:
    print("The held-out run hasn't happened yet.")"""),
    ("md", "## 8. Check: do these numbers match `results/metrics.json`?"),
    ("code", """def same(a, b): return abs(a["value"] - b["value"]) < 0.05
checks = {"ours_ch0": same(R["ours_ch0"]["macro_f1"], saved["dev"]["ours_ch0"]["macro_f1"]),
          "ours_node_avg": same(R["ours_node_avg"]["macro_f1"], saved["dev"]["ours_node_avg"]["macro_f1"]),
          "meal caught": same(R["meal_activity"]["caught"], saved["dev"]["meal_activity"]["caught"]),
          "theta": R["not_sure"]["theta"] == saved["dev"]["not_sure"]["theta"]}
for k in ("logmel_lr", "apple_zeroshot", "majority", "ast_zeroshot", "ced_tiny_zeroshot", "clap_zeroshot"):
    if k in R["baselines"] and "macro_f1" in R["baselines"][k] and "macro_f1" in saved["dev"]["baselines"].get(k, {}):
        checks[k] = same(R["baselines"][k]["macro_f1"], saved["dev"]["baselines"][k]["macro_f1"])
print(checks)
print("ALL MATCH" if all(checks.values()) else "MISMATCH: see above")
print(f"notebook ran in {time.time() - T0:.0f} s")"""),
]


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb["metadata"] = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                      "language_info": {"name": "python"}}
    nb["cells"] = [nbf.v4.new_markdown_cell(s) if k == "md" else nbf.v4.new_code_cell(s) for k, s in CELLS]
    out = ROOT / "notebooks" / "kettle_reproduce.ipynb"
    out.parent.mkdir(exist_ok=True)
    nbf.write(nb, out)
    print(out)


if __name__ == "__main__":
    main()
