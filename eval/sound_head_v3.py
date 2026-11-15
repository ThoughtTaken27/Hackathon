"""Sound head v3: trained on real homes too, tested once on real homes it never heard (eval/PREREGISTER-SOUNDS-V3.md).

Same method as eval/sound_head.py (v2); more training data (TUT-SED 2016 development homes, DESED tune half) and a fresh
real-home test (TUT-SED 2016 evaluation homes, DESED test half), plus v2's test halves. Adopted on the device only if it beats
v2 under the adoption rule written before the run.

    python -m eval.sound_head_v3 --tune-only   # choices from tune-side CV; touches no test window
    python -m eval.sound_head_v3               # + the one test run -> results/sound_head_v3.json (+ device file if adopted)
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from eval import sound_head as v2
from eval.beyond import rate
from eval.other_homes import half
from eval.sounds import AMBIG, BAR, POS

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
EMB = ROOT / "data" / "emb" / "ced-tiny"
OUT = ROOT / "results" / "sound_head_v3.json"
MODEL = ROOT / "web" / "public" / "model" / "sound_head.json"
KINDS_FILE = ROOT / "web" / "public" / "model" / "kinds.json"
SOUNDS = list(POS)
TUT_MAP = {"tap": ["water tap running"], "dishes": ["dishes", "cutlery", "washing dishes"], "cupboard": ["cupboard", "drawer"],
           "footsteps": ["people walking"]}
TUT_AMBIG = {"tv"}
DESED_MAP = {"dishes": ["Dishes"], "tap": ["Running_water"], "frying": ["Frying"], "blender": ["Blender"], "vacuum": ["Vacuum_cleaner"],
             "alarm": ["Alarm_bell_ringing"]}
DESED_AMBIG = {"tv", "kettle", "microwave", "door", "footsteps", "cupboard"}
MIN_OVERLAP = 0.5


# ---------------------------------------------------------------- data with per-sound positive / ambiguous masks

def from_v2(d: dict) -> dict:
    """A v2 dataset (labels as strings) -> per-sound masks."""
    pos = {k: np.isin(d["lab"], POS[k]) for k in SOUNDS}
    amb = {k: np.isin(d["lab"], AMBIG[k]) for k in SOUNDS}
    return {"S": d["S"], "E": d["E"], "group": d["group"], "pos": pos, "amb": amb}


def embed_windows(waves: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    from kettle import encoders
    enc = encoders.load()
    E, A = [], []
    for i in range(0, len(waves), 16):
        e, a = encoders.embed(enc, np.stack(waves[i:i + 16]))
        E.append(e); A.append(a)
    return np.concatenate(E).astype(np.float64), np.concatenate(A).astype(np.float64)


def tut(root: Path, hop: float, cache: Path) -> dict:
    """TUT-SED 2016 home recordings -> 10-s windows (hop seconds apart) with masks from the annotations."""
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        ev = json.loads(str(z["events"]))
    else:
        from kettle.audio import to_16k_mono
        waves, ev = [], []
        for wav in sorted((root / "audio" / "home").glob("*.wav")):
            x, sr = sf.read(wav, dtype="float32", always_2d=True)
            m = to_16k_mono(x.T, sr)
            ann = [(float(a), float(b), c.strip()) for a, b, c in (l.split("\t")[:3] for l in (root / "meta" / "home" / f"{wav.stem}.ann").read_text().splitlines() if l.strip())]
            t = 0.0
            while t + 10 <= len(m) / 16000 + 1e-6:
                waves.append(m[int(t * 16000):int(t * 16000) + 160000])
                ev.append({"rec": wav.stem, "t": t, "events": sorted({c for a, b, c in ann if min(b, t + 10) - max(a, t) >= MIN_OVERLAP})})
                t += hop
        E, S = embed_windows(waves)
        cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cache, E=E, S=S, events=json.dumps(ev))
        z = {"E": E, "S": S}
    pos = {k: np.array([bool(set(e["events"]) & set(TUT_MAP.get(k, []))) for e in ev]) for k in SOUNDS}
    amb = {k: np.full(len(ev), k in TUT_AMBIG) for k in SOUNDS}
    return {"S": np.asarray(z["S"], np.float64), "E": np.asarray(z["E"], np.float64), "group": np.array([f"tut:{e['rec']}" for e in ev]),
            "pos": pos, "amb": amb, "rec": [e["rec"] for e in ev]}


def desed(cache: Path) -> dict:
    """DESED public evaluation clips (10 s) with masks from its strong labels; part = tune/test by a hash of the file name."""
    d = RAW / "desed" / "dataset"
    files = sorted(p.name for p in (d / "audio" / "eval" / "public").glob("*.wav"))
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        assert list(z["files"]) == files
        E, S = z["E"], z["S"]
    else:
        from kettle.audio import to_16k_mono
        waves = []
        for f in files:
            x, sr = sf.read(d / "audio" / "eval" / "public" / f, dtype="float32", always_2d=True)
            m = to_16k_mono(x.T, sr)[:160000]
            waves.append(np.pad(m, (0, 160000 - len(m))))
        E, S = embed_windows(waves)
        cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cache, E=E, S=S, files=np.array(files))
    ev: dict = {f: set() for f in files}
    for r in csv.DictReader(open(d / "metadata" / "eval" / "public.tsv"), delimiter="\t"):
        if r["event_label"] and r["filename"] in ev and float(r["offset"]) - float(r["onset"]) >= MIN_OVERLAP:
            ev[r["filename"]].add(r["event_label"])
    pos = {k: np.array([bool(ev[f] & set(DESED_MAP.get(k, []))) for f in files]) for k in SOUNDS}
    amb = {k: np.full(len(files), k in DESED_AMBIG) for k in SOUNDS}
    return {"S": np.asarray(S, np.float64), "E": np.asarray(E, np.float64), "group": np.array([f"desed:{f}" for f in files]),
            "pos": pos, "amb": amb, "part": np.array([half(f) for f in files])}


def take(d: dict, m: np.ndarray) -> dict:
    return {"S": d["S"][m], "E": d["E"][m], "group": d["group"][m], "pos": {k: v[m] for k, v in d["pos"].items()},
            "amb": {k: v[m] for k, v in d["amb"].items()}}


def pool(parts: list[dict]) -> dict:
    return {"S": np.concatenate([p["S"] for p in parts]), "E": np.concatenate([p["E"] for p in parts]),
            "group": np.concatenate([p["group"] for p in parts]),
            "pos": {k: np.concatenate([p["pos"][k] for p in parts]) for k in SOUNDS},
            "amb": {k: np.concatenate([p["amb"][k] for p in parts]) for k in SOUNDS}}


def sides() -> tuple[dict, dict, dict]:
    """(tune side, pooled test side, real-home test side)."""
    D = v2.data()
    old_tune = from_v2(v2.pooled(D, "tune"))
    old_test = from_v2(v2.pooled(D, "test"))
    tut_dev = tut(RAW / "tut2016" / "TUT-sound-events-2016-development", 5.0, EMB / "tut2016" / "dev_hop5.npz")
    de = desed(EMB / "desed" / "public_eval_v3.npz")
    tune = pool([old_tune, tut_dev, take(de, de["part"] == "tune")])
    real = pool([tut(RAW / "tut2016eval" / "TUT-sound-events-2016-evaluation", 10.0, EMB / "tut2016" / "eval_hop10.npz"),
                 take(de, de["part"] == "test")])
    return tune, pool([old_test, real]), real


# ---------------------------------------------------------------- method (v2's functions, masks instead of label strings)

def choose(T: dict) -> dict:
    out = {}
    for k in SOUNDS:
        keep = ~T["amb"][k]
        y, g = T["pos"][k][keep].astype(int), T["group"][keep]
        best = None
        for feat in v2.FEATS:
            X = v2.features(T, feat)[keep]
            for C in v2.CS:
                p = v2.oof(X, y, g, C)
                from sklearn.metrics import average_precision_score
                ap = average_precision_score(y, p)
                if best is None or ap > best["ap"]:
                    best = {"feat": feat, "C": C, "ap": round(float(ap), 4), "p": p}
        thr, prec, rec = v2.best_threshold(best["p"], y.astype(bool), v2.TUNE_PRECISION)
        ok = thr is not None and rec >= BAR["recall"]
        out[k] = {"feat": best["feat"], "C": best["C"], "tune_ap": best["ap"], "threshold": thr, "tune_precision": round(prec, 1),
                  "tune_recall": round(rec, 1), "n_pos_tune": int(y.sum()), "passes_tune": bool(ok),
                  "model": v2.fit(v2.features(T, best["feat"])[keep], y, best["C"])}
        print(f"{k:10s} {best['feat']:9s} C={best['C']:<5} AP={best['ap']:.3f} thr={thr} tune P={prec:.1f} R={rec:.1f} (pos {int(y.sum())}) "
              f"{'ok' if ok else 'HIDDEN (fails on tune)'}", flush=True)
    return out


def fired(H: dict, P: dict, cfg: dict) -> dict:
    return v2.head_fired({k: h if h.get("passes_tune", True) else {**h, "threshold": None} for k, h in H.items()},
                         {"S": P["S"], "E": P["E"], "lab": np.zeros(len(P["S"]))}, cfg)


def score(F: dict, P: dict) -> dict:
    out = {}
    for k in SOUNDS:
        f = F.get(k, np.zeros(len(P["S"]), bool))
        pos, neg = P["pos"][k], ~P["pos"][k] & ~P["amb"][k]
        tp, fp = int(f[pos].sum()), int(f[neg].sum())
        out[k] = {"recall": rate(f[pos]), "precision": rate(np.r_[np.ones(tp, bool), np.zeros(fp, bool)]), "true_k": tp, "false_k": fp,
                  "neg_n": int(neg.sum()), "false_per_1000": round(1000 * fp / max(1, int(neg.sum())), 2)}
    return out


def shown(R: dict, passes: dict) -> dict:
    return {k: bool(passes.get(k, True) and v["precision"]["pct"] is not None and v["recall"]["pct"] is not None
                    and v["precision"]["pct"] >= BAR["precision"] and v["recall"]["pct"] >= BAR["recall"]) for k, v in R.items()}


def v2_heads() -> dict:
    m = json.loads(MODEL.read_text())["heads"]
    return {k: {"feat": h["feat"], "threshold": h["threshold"], "passes_tune": True,
                "model": {"mean": np.array(h["mean"]), "std": np.array(h["std"]), "w": np.array(h["w"]), "b": h["b"]}} for k, h in m.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune-only", action="store_true")
    args = ap.parse_args()
    if args.tune_only:
        D = v2.data()
        T = pool([from_v2(v2.pooled(D, "tune")), tut(RAW / "tut2016" / "TUT-sound-events-2016-development", 5.0, EMB / "tut2016" / "dev_hop5.npz"),
                  (lambda de: take(de, de["part"] == "tune"))(desed(EMB / "desed" / "public_eval_v3.npz"))])
        print(f"tune windows: {len(T['S'])}")
        choose(T)
        return
    T, X, RH = sides()
    print(f"tune {len(T['S'])}  test (pooled) {len(X['S'])}  real-home test {len(RH['S'])}")
    H3 = choose(T)
    cfg = json.loads(KINDS_FILE.read_text())
    H2 = v2_heads()
    res = {}
    for name, H in (("v2", H2), ("v3", H3)):
        res[name] = {"pooled": score(fired(H, X, cfg), X), "real_home": score(fired(H, RH, cfg), RH)}
    sh2 = shown(res["v2"]["pooled"], {k: k in H2 for k in SOUNDS})
    sh3 = shown(res["v3"]["pooled"], {k: H3[k]["passes_tune"] for k in SOUNDS})
    ann = [k for k in SOUNDS if int(RH["pos"][k].sum()) > 0]
    true2 = sum(res["v2"]["real_home"][k]["true_k"] for k in ann)
    true3 = sum(res["v3"]["real_home"][k]["true_k"] for k in ann)
    fp = lambda v: 1000 * sum(res[v]["real_home"][k]["false_k"] for k in SOUNDS) / max(1, len(RH["S"]))
    adopt = sum(sh3.values()) >= sum(sh2.values()) and true3 > true2 and fp("v3") <= fp("v2")
    R = {"about": __doc__.split("\n\n")[0], "prereg": "eval/PREREGISTER-SOUNDS-V3.md", "bar": BAR,
         "n": {"tune": int(len(T["S"])), "test_pooled": int(len(X["S"])), "test_real_home": int(len(RH["S"]))},
         "annotated_in_real_home_test": ann,
         "choices": {k: {kk: vv for kk, vv in h.items() if kk != "model"} for k, h in H3.items()},
         "v2": res["v2"], "v3": res["v3"], "shown": {"v2": sh2, "v3": sh3},
         "adoption": {"shown_v2": sum(sh2.values()), "shown_v3": sum(sh3.values()), "real_home_true_names_v2": true2, "real_home_true_names_v3": true3,
                      "real_home_false_per_1000_v2": round(fp("v2"), 2), "real_home_false_per_1000_v3": round(fp("v3"), 2), "adopted": bool(adopt)},
         "process": "Choices from grouped CV on the tune side only; the test side scored once. v2's test halves: third use (disclosed)."}
    OUT.write_text(json.dumps(R, indent=1) + "\n")
    print(json.dumps(R["adoption"], indent=1))
    for k in SOUNDS:
        a, b = res["v2"], res["v3"]
        print(f"{k:10s} pooled P {a['pooled'][k]['precision']['pct']}->{b['pooled'][k]['precision']['pct']} R {a['pooled'][k]['recall']['pct']}->"
              f"{b['pooled'][k]['recall']['pct']}  shown {sh2[k]}->{sh3[k]} | real-home R {a['real_home'][k]['recall']['k']}/{a['real_home'][k]['recall']['n']}->"
              f"{b['real_home'][k]['recall']['k']}/{b['real_home'][k]['recall']['n']} false {a['real_home'][k]['false_k']}->{b['real_home'][k]['false_k']}")
    if adopt:
        MODEL.write_text(json.dumps(v2.export(H3, sh3)).replace("eval/sound_head.py, pre-registered in eval/PREREGISTER-SOUNDS-V2.md",
                                                                  "eval/sound_head_v3.py, pre-registered in eval/PREREGISTER-SOUNDS-V3.md"))
        cfg["kinds"] = [{**k, "shown": bool(sh3.get(k["id"], False))} for k in cfg["kinds"]]
        KINDS_FILE.write_text(json.dumps(cfg))
        print("adopted: wrote", MODEL.relative_to(ROOT), "and kinds.json shown flags")


if __name__ == "__main__":
    main()
