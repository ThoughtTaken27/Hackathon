"""Leakage checks on the data split: official folds are session-disjoint; demo sessions never train."""
from collections import defaultdict

from kettle.data import load_meta, load_plan


def test_dev_folds_are_session_disjoint():
    meta = load_meta("dev")
    fold_of_session = defaultdict(set)
    for r in meta:
        fold_of_session[r["session"]].add(r["fold"])
    assert all(len(f) == 1 for f in fold_of_session.values())        # no session in two folds


def test_all_node_copies_of_a_moment_share_a_fold():
    meta = load_meta("dev")
    folds = defaultdict(set)
    for r in meta:
        folds[(r["ex"], r["seg"])].add(r["fold"])
    assert all(len(f) == 1 for f in folds.values())


def test_demo_sessions_are_held_out_of_training():
    plan = load_plan()
    meta = {r["file"]: r for r in load_meta("dev")}
    demo = set(plan["demo_sessions"].values())
    assert not any(meta[f]["session"] in demo for f in plan["train_files"])
    assert all(meta[f]["session"] in demo for f in plan["demo_files"])


def test_eval_sample_is_disjoint_from_dev_files():
    import json
    from pathlib import Path
    ev = json.loads((Path(__file__).resolve().parents[1] / "eval" / "sample_eval.json").read_text())["files"]
    dev_names = {r["file"] for r in load_meta("dev")}
    assert not set(ev) & dev_names
