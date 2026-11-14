"""The one frozen run on the official DCASE 2018 Task 5 evaluation sample (pre-registered in eval/PREREGISTER.md).

run_once(): refuses if predictions were already written; logs commit, head sha256, pre-registration commit and times
to results/eval_run.json; writes predictions before scoring; then scores per node-average and single mic, per slice.
rehearse(): the same scoring code on a dev stand-in (fold 4 relabelled "eval", dummy head). Touches no eval data.
"""
from __future__ import annotations

import json
import subprocess
import time

import numpy as np

from eval import metrics as M
from eval.common import ROOT, apple_map_predict, audioset_map_predict, full_counts, num, table
from kettle import model
from kettle.labels import CLASSES

RESULTS = ROOT / "results"
RUN = RESULTS / "eval_run.json"
PREREG = "0119c57f1d683126813529236faa330fc2150563"
NAMES = json.loads((ROOT / "models" / "audioset_labels.json").read_text())


def _commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def _slice(y, p, session, w, split) -> dict:
    s = M.scores(M.confusion(y, p), w)
    ci = M.session_bootstrap(y, p, session, w)
    return num(s["macro_f1"], split, len(y), len(np.unique(session)), ci["macro_f1"])


def score_table(T: dict, P: np.ndarray, full: np.ndarray, theta: float, known: list[str], unknown: list[str], split: str) -> dict:
    """Score predictions P [n, 4 channels, 9] on table T: all / known / unknown nodes / per node, node-average and ch0."""
    y, session, node = T["y"], T["session"], T["node"]
    w = M.class_weights(full, np.bincount(y, minlength=9))
    pn, p0 = P.mean(1).argmax(1), P[:, 0].argmax(1)
    out = {"slices": {}, "per_node": {}}
    for name, nodes in (("all", sorted(set(node))), ("known", known), ("unknown", unknown)):
        if not nodes:
            continue
        m = np.isin(node, nodes)
        out["slices"][name] = {"nodes": nodes, "node_avg": _slice(y[m], pn[m], session[m], w, split),
                               "ch0": _slice(y[m], p0[m], session[m], w, split)}
    for nd in sorted(set(node)):
        m = node == nd
        s = M.scores(M.confusion(y[m], pn[m]), w)
        s0 = M.scores(M.confusion(y[m], p0[m]), w)
        out["per_node"][nd] = {"node_avg": round(100 * s["macro_f1"], 1), "ch0": round(100 * s0["macro_f1"], 1), "n_clips": int(m.sum())}
    from eval.dev import report
    focus = np.isin(node, unknown) if unknown else np.ones(len(y), bool)
    out["ours_node_avg"] = report(y[focus], pn[focus], session[focus], w, split)
    out["ours_ch0"] = report(y[focus], p0[focus], session[focus], w, split)
    out["per_class_slice"] = "unknown" if unknown else "all"
    out["not_sure_share_at_theta"] = round(float((P[:, 0].max(1) < theta).mean()), 3)
    out["n_clips"] = int(len(y))
    out["n_moments"] = int(len({(a, b) for a, b in zip(T["ex"], T["seg"])}))
    return out


def run_once() -> None:
    from eval.guard import assert_eval_allowed
    from eval.sample import load_sample
    prev = json.loads(RUN.read_text()) if RUN.exists() else {"attempts": []}
    if any(a.get("predictions_written") for a in prev["attempts"]):
        raise SystemExit("The eval run already wrote predictions. It runs once; results/eval_run.json has the record.")
    assert_eval_allowed()
    head = model.load(ROOT / "models" / "head.json")
    attempt = {"started": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "commit": _commit(), "head_sha256": head["sha256"],
               "preregister_commit": PREREG, "predictions_written": False}
    prev["attempts"].append(attempt)
    RESULTS.mkdir(exist_ok=True)
    RUN.write_text(json.dumps(prev, indent=1))
    rows = load_sample()
    files = {r["file"][:-4] for r in rows}
    T = table("ced-tiny", "eval", files)
    if len(T["files"]) != len(files):
        attempt["crashed"] = f"only {len(T['files'])} of {len(files)} eval clips embedded; nothing predicted"
        RUN.write_text(json.dumps(prev, indent=1))
        raise SystemExit(attempt["crashed"])
    fp = json.loads((RESULTS / "fingerprint.json").read_text())
    n, ch, d = T["emb"].shape
    P = model.predict_proba(head, T["emb"].reshape(n * ch, d)).reshape(n, ch, 9)
    with open(RESULTS / "eval_predictions.jsonl", "w") as f:
        for i in range(n):
            f.write(json.dumps({"file": str(T["files"][i]), "node": str(T["node"][i]), "true": CLASSES[T["y"][i]],
                                "node_avg": CLASSES[int(P[i].mean(0).argmax())], "ch0": CLASSES[int(P[i, 0].argmax())],
                                "ch0_conf": round(float(P[i, 0].max()), 3)}) + "\n")
    attempt["predictions_written"] = True
    attempt["predictions_at"] = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    RUN.write_text(json.dumps(prev, indent=1))

    split = "DCASE 2018 Task 5 eval sample (held-out test, run once)"
    out = score_table(T, P, full_counts("eval"), head["theta"], fp["known"], fp["unknown"], split)
    out["fingerprint_summary"] = (f"confirmed by the unlabelled mic-fingerprint rule: known {fp['known']}, unknown {fp['unknown']}"
                                  if fp["confirmed"] else "NOT confirmed by the mic-fingerprint rule; per-node numbers only")
    # baselines on the same clips (channel 0), maps frozen before scoring
    w = M.class_weights(full_counts("eval"), np.bincount(T["y"], minlength=9))
    focus = np.isin(T["node"], fp["unknown"]) if fp["unknown"] else np.ones(n, bool)
    B = {"majority": _slice(T["y"][focus], np.zeros(focus.sum(), int), T["session"][focus], w, split)}
    B["ced_tiny_zeroshot"] = _slice(T["y"][focus], audioset_map_predict(T["scores"][focus][:, 0], NAMES), T["session"][focus], w, split)
    try:
        A = table("ast", "eval", files)
        assert list(A["files"]) == list(T["files"])
        B["ast_zeroshot"] = _slice(T["y"][focus], audioset_map_predict(A["scores"][focus][:, 0], NAMES), T["session"][focus], w, split)
    except (FileNotFoundError, AssertionError, KeyError) as e:
        B["ast_zeroshot"] = {"missing": type(e).__name__}
    try:
        from tools.apple_baseline.run import run as apple_run
        apple_run("eval")
        a = {json.loads(l)["file"]: json.loads(l) for l in open(RESULTS / "baselines" / "apple_eval.jsonl")}
        B["apple_zeroshot"] = _slice(T["y"][focus], apple_map_predict([a[f] for f in T["files"][focus]]), T["session"][focus], w, split)
    except Exception as e:  # macOS-only; the run must still finish
        B["apple_zeroshot"] = {"missing": f"{type(e).__name__}: {e}"[:200]}
    out["baselines"] = B
    out["baselines_slice"] = "unknown" if fp["unknown"] else "all"
    out["run"] = attempt
    attempt["ended"] = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    RUN.write_text(json.dumps(prev, indent=1))
    (RESULTS / "dcase_eval.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: v for k, v in out["slices"].items()}, indent=1))


def rehearse() -> None:
    """Dry run of score_table on dev fold 4 with a dummy head: proves the harness works before the real run."""
    from eval.embed import EMB, done_files
    T = table("ced-tiny", "dev", done_files(EMB / "ced-tiny" / "dev"))
    m = T["fold"] == 4
    T = {k: (v[m] if isinstance(v, np.ndarray) else v) for k, v in T.items()}
    rng = np.random.default_rng(0)
    dummy = {"mean": [0.0] * 192, "std": [1.0] * 192, "coef": rng.standard_normal((9, 192)).tolist(), "intercept": [0.0] * 9, "temperature": 1.0}
    n, ch, d = T["emb"].shape
    P = model.predict_proba(dummy, T["emb"].reshape(n * ch, d)).reshape(n, ch, 9)
    out = score_table(T, P, full_counts("dev"), 0.5, ["DevNode1", "DevNode2"], ["DevNode3", "DevNode4"], "REHEARSAL: dev fold 4, dummy head")
    out["note"] = "Rehearsal only: dummy random head on dev fold 4; checks the code path. Not a result."
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "rehearsal.json").write_text(json.dumps(out, indent=1, default=float))
    print("rehearsal ok:", {k: v["node_avg"]["value"] for k, v in out["slices"].items()})


def score_saved_predictions() -> dict:
    """Recompute the held-out numbers from results/eval_predictions.jsonl + the public eval labels (no audio,
    no embeddings): what the reproduce notebook shows."""
    from kettle.data import load_meta
    meta = {r["file"][:-4]: r for r in load_meta("eval")}
    rows = [json.loads(l) for l in open(RESULTS / "eval_predictions.jsonl")]
    fp = json.loads((RESULTS / "fingerprint.json").read_text())
    y = np.array([CLASSES.index(meta[r["file"]]["label"]) for r in rows])
    session = np.array([meta[r["file"]]["session"] for r in rows])
    node = np.array([r["node"] for r in rows])
    pn = np.array([CLASSES.index(r["node_avg"]) for r in rows])
    p0 = np.array([CLASSES.index(r["ch0"]) for r in rows])
    w = M.class_weights(full_counts("eval"), np.bincount(y, minlength=9))
    split = "DCASE 2018 Task 5 eval sample (held-out test, run once)"
    out = {"slices": {}}
    for name, nodes in (("all", sorted(set(node))), ("known", fp["known"]), ("unknown", fp["unknown"])):
        if nodes:
            m = np.isin(node, nodes)
            out["slices"][name] = {"node_avg": _slice(y[m], pn[m], session[m], w, split), "ch0": _slice(y[m], p0[m], session[m], w, split)}
    return out
