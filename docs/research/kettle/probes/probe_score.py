"""Probe 2+3 scoring: zero-shot baselines (Apple, AudioSet-label maps, CLAP prompts) and a quick
session-disjoint linear probe per encoder, on the ~300 balanced dev probe clips.

Maps were frozen in maps/*.json before this script was first run. Quick check only: N is tiny
and classes are balanced here (unlike the real data), so these are for choosing an encoder,
not for reporting.
"""
import json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[4]
D = ROOT / "data/raw/sins/probe_dev"
MAPS = Path(__file__).resolve().parent / "maps"
CLASSES = ["absence", "cooking", "dishwashing", "eating", "other", "social_activity",
           "vacuum_cleaner", "watching_tv", "working"]


def labels():
    lab = json.loads((D / "labels.json").read_text())
    keep, seen = [], set()
    for i, x in enumerate(lab):           # the sampler drew with replacement: drop repeats
        if x["file"] not in seen: seen.add(x["file"]); keep.append(i)
    return [lab[i] for i in keep], np.array(keep)


def map_predict(scores, names, amap):
    """Activity score = max over its mapped classes; argmax; all-zero -> absence."""
    col = {n: i for i, n in enumerate(names)}
    act = np.stack([scores[:, [col[c] for c in amap[a]]].max(1) for a in CLASSES], 1)
    pred = act.argmax(1); pred[act.max(1) <= 0] = 0
    return pred


def f1(y, p): return round(100 * f1_score(y, p, labels=range(9), average="macro", zero_division=0), 1)


def main():
    lab, keep = labels()
    y = np.array([CLASSES.index(x["label"]) for x in lab]); fold = np.array([x["fold"] for x in lab])
    out = {"n_clips": len(y), "per_class": int(np.bincount(y).min()), "results": {}}
    R = out["results"]
    R["majority (always 'absence', the most common dev class)"] = f1(y, np.zeros_like(y))

    # Apple SoundAnalysis zero-shot
    amap = json.loads((MAPS / "apple_map.json").read_text())["map"]
    ap = {j["file"]: j["mean"] for j in map(json.loads, open(D / "apple_scores.jsonl"))}
    names = sorted({k for v in ap.values() for k in v})
    S = np.array([[ap[x["file"]].get(n, 0.0) for n in names] for x in lab])
    pa = map_predict(S, names, amap)
    R["apple_soundanalysis_zeroshot"] = f1(y, pa)
    out["apple_confusion"] = confusion_matrix(y, pa, labels=range(9)).tolist()

    asmap = json.loads((MAPS / "audioset_map.json").read_text())["map"]
    from transformers import AutoConfig
    as_names = [AutoConfig.from_pretrained("MIT/ast-finetuned-audioset-10-10-0.4593").id2label[i] for i in range(527)]
    for enc in ["ast", "ced-tiny", "ced-small", "clap"]:
        p = D / f"emb_{enc}.npz"
        if not p.exists(): continue
        z = np.load(p); E, S = z["emb"][keep], z["scores"][keep]
        if enc == "clap":
            R["clap_zeroshot_prompts"] = f1(y, S.argmax(1))
        else:
            R[f"{enc}_zeroshot_audioset_map"] = f1(y, map_predict(S, as_names, asmap))
        # quick linear probe: train on folds 1+2, test on fold 3 and on fold 4 (session-disjoint)
        tr = np.isin(fold, [1, 2]); res = []
        sc = StandardScaler().fit(E[tr])
        clf = LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced").fit(sc.transform(E[tr]), y[tr])
        for t in (3, 4):
            te = fold == t; res.append(f1(y[te], clf.predict(sc.transform(E[te]))))
        R[f"{enc}_linear_probe_train_f12_test_f3_f4"] = res + [round(float(np.mean(res)), 1)]
        out.setdefault("probe_test_n", {t: int((fold == t).sum()) for t in (3, 4)})
        out.setdefault("probe_train_n", int(tr.sum()))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
