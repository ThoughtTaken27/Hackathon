"""python -m eval.check_metrics : every reported metric in results/metrics.json carries its split and N (and a CI
where one applies). Lists any bare number that looks like a metric. Exit 1 if any is found.

A "metric" is any dict with a "value" key (it must also have "split" and "n_clips"; "ci95" unless marked
"ci": "n/a"), or any float under a key that names a score (f1, recall, precision, accuracy, ece, rate, macro).
Counts (missed, false alarms, support), settings (theta, C, temperature) and published numbers are allowed as plain
numbers because they are either raw counts with their N alongside or quoted from a cited source.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = re.compile(r"(f1|recall|precision|accuracy|ece|_rate$|macro|share|coverage)", re.I)
ALLOWED_PARENTS = ("published", "curve", "bins", "bins_before", "weights", "class_counts_scored", "C_per_fold", "theta_tradeoff",
                   "runtime", "privacy_check", "fingerprint", "run", "head")


def walk(x, path="", out=None):
    out = [] if out is None else out
    if isinstance(x, dict):
        if "value" in x and isinstance(x["value"], (int, float)):
            missing = [k for k in ("split", "n_clips") if k not in x]
            if "ci95" not in x and x.get("ci") != "n/a":
                missing.append("ci95")
            if missing:
                out.append((path, f"metric without {', '.join(missing)}"))
            return out
        for k, v in x.items():
            walk(v, f"{path}.{k}" if path else k, out)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            walk(v, f"{path}[{i}]", out)
    elif isinstance(x, float):
        key = path.split(".")[-1]
        if key.endswith("_point"):          # a convenience copy of a metric reported in full next to it
            return out
        if SCORE.search(key) and not any(f".{a}" in f".{path}" or path.startswith(a) for a in ALLOWED_PARENTS):
            out.append((path, f"bare score {x}"))
    return out


if __name__ == "__main__":
    m = json.loads((ROOT / "results" / "metrics.json").read_text())
    problems = walk(m)
    for p, why in problems:
        print(f"{p}: {why}")
    print(f"{len(problems)} problems")
    sys.exit(1 if problems else 0)
