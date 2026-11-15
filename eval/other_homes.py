"""Other homes: does Kettle work outside the one research home it was trained in? (eval/PREREGISTER-V2.md)

    python -m eval.other_homes --fetch     download DESED public eval, Kitchen20, 13 ESC-50 categories (~1.4 GB) and embed
    python -m eval.other_homes             score the TUNE halves (v1 vs v2) and the SINS dev guard
    python -m eval.other_homes --test      score the TEST halves once; writes results/other_homes.{json,md}
    python -m eval.other_homes --from-cache   rebuild the tables from results/other_homes_predictions.jsonl (no audio)

Every clip is one 10-second window. v1 = the rule shipped until Sat Nov 14 9:45 PM CT (head + "unlike anything
learned" gate + θ). v2 = the same head checked by the second opinion (kettle/witness.py). Nothing here trains anything.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from kettle import model, timeline, witness
from kettle.labels import CLASSES, MEAL

ROOT = Path(__file__).resolve().parents[1]
RAW, EMB, RESULTS = ROOT / "data" / "raw", ROOT / "data" / "emb" / "ced-tiny", ROOT / "results"
PRED = RESULTS / "other_homes_predictions.jsonl"
K20_ACT = ["blender", "boiling-water", "chopping", "clean-dishes", "cutlery", "eat", "frying-pan", "juicer", "peel", "plates"]
K20_NOT = ["fridge", "dishwasher", "sweep", "book", "cupboard", "drawer"]
K20_SEP = ["stove-fan", "microwave", "water-flowing"]
ESC_CATS = ["vacuum_cleaner", "washing_machine", "keyboard_typing", "footsteps", "door_wood_knock", "toilet_flush",
            "brushing_teeth", "clock_tick", "mouse_click", "door_wood_creaks", "pouring_water", "snoring", "coughing"]
DESED_NOT = ["vacuum", "shaver", "speech", "pets_alarms"]


def half(group: str) -> str:
    """'tune' or 'test' for a group id (uploader or source recording): fixed by a hash, so nobody chooses."""
    return "test" if int(hashlib.sha256(("kettle-split:" + str(group)).encode()).hexdigest(), 16) % 2 else "tune"


# ---------------------------------------------------------------- fetch + embed (needs the network once)

def fetch() -> None:
    import subprocess
    import requests
    import soundfile as sf
    from concurrent.futures import ThreadPoolExecutor
    from eval.offlist import BASE, to_10s_16k
    from kettle import encoders
    from kettle.audio import to_16k_mono
    d = RAW / "desed"
    d.mkdir(parents=True, exist_ok=True)
    if not (d / "dataset").exists():
        subprocess.run(["curl", "-sSL", "-o", str(d / "DESEDpublic_eval.tar.gz"),
                        "https://zenodo.org/api/records/3588172/files/DESEDpublic_eval.tar.gz/content"], check=True)
        subprocess.run(["tar", "-xzf", "DESEDpublic_eval.tar.gz"], cwd=d, check=True)
    a = RAW / "audioset"
    a.mkdir(exist_ok=True)
    for name in ("eval_segments", "balanced_train_segments", "unbalanced_train_segments"):
        if not (a / f"{name}.csv").exists():
            (a / f"{name}.csv").write_bytes(requests.get(f"http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/{name}.csv", timeout=600).content)
    if not (RAW / "kitchen20").exists():
        subprocess.run(["git", "clone", "--depth", "1", "-q", "https://github.com/marc-moreaux/kitchen20.git", str(RAW / "kitchen20")], check=True)
    e = RAW / "esc50_house"
    e.mkdir(exist_ok=True)
    rows = [r for r in csv.DictReader(io.StringIO(requests.get(f"{BASE}/meta/esc50.csv", timeout=60).text)) if r["category"] in ESC_CATS]
    (e / "meta.json").write_text(json.dumps(rows))

    def get(r):
        p = e / r["filename"]
        if not p.exists():
            p.write_bytes(requests.get(f"{BASE}/audio/{r['filename']}", timeout=60).content)
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(get, rows))
    enc = encoders.load()

    def run(waves_of, n, out, **meta):
        embs, tags = [], []
        for i in range(0, n, 16):
            em, au = encoders.embed(enc, np.stack([waves_of(j) for j in range(i, min(n, i + 16))]))
            embs.append(em)
            tags.append(au)
        out.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(out, emb=np.concatenate(embs), audioset=np.concatenate(tags), **meta)

    files = sorted(p.name for p in (d / "dataset/audio/eval/public").glob("*.wav"))

    def desed_wave(j):
        x, sr = sf.read(d / "dataset/audio/eval/public" / files[j], dtype="float32", always_2d=True)
        m = to_16k_mono(x.T, sr)[:160000]
        return np.pad(m, (0, 160000 - len(m)))
    run(desed_wave, len(files), EMB / "desed" / "public_eval.npz", files=np.array(files))
    k = list(csv.DictReader(open(RAW / "kitchen20" / "kitchen20.csv")))

    def five(path):
        x, sr = sf.read(path, dtype="float32")
        return to_10s_16k(x, sr)
    run(lambda j: five(RAW / "kitchen20" / k[j]["path"]), len(k), EMB / "kitchen20" / "all.npz",
        files=np.array([r["path"] for r in k]), category=np.array([r["category"] for r in k]), source=np.array([r["usr_id"] for r in k]))
    run(lambda j: five(e / rows[j]["filename"]), len(rows), EMB / "esc50_house" / "all.npz",
        files=np.array([r["filename"] for r in rows]), category=np.array([r["category"] for r in rows]), source=np.array([r["src_file"] for r in rows]))


# ---------------------------------------------------------------- one row per clip

def _desed_groups() -> tuple[dict, dict, set]:
    up = {r["filename"]: r["uploader_id"] for r in csv.DictReader(open(RAW / "desed" / "license_public_eval.tsv"), delimiter="\t")}
    ev: dict = defaultdict(lambda: defaultdict(float))
    for r in csv.DictReader(open(RAW / "desed" / "dataset/metadata/eval/public.tsv"), delimiter="\t"):
        if r["event_label"]:
            ev[r["filename"]][r["event_label"]] += float(r["offset"]) - float(r["onset"])
    aset = set()
    for name in ("eval_segments", "balanced_train_segments", "unbalanced_train_segments"):
        for line in open(RAW / "audioset" / f"{name}.csv"):
            if not line.startswith("#"):
                aset.add(line.split(",", 1)[0])
    return up, ev, aset


def desed_kind(events: dict) -> str:
    """A DESED clip's group from its labelled events (PREREGISTER-V2 'What counts')."""
    kd = sum(events.get(c, 0) for c in ("Frying", "Dishes", "Blender"))
    if kd >= 2:
        return "kitchen"
    if kd > 0:
        return "brief"
    if "Running_water" in events:
        return "water"
    if "Vacuum_cleaner" in events:
        return "vacuum"
    if "Electric_shaver_toothbrush" in events:
        return "shaver"
    if set(events) <= {"Speech"}:
        return "speech"
    return "pets_alarms"


def main_sound(events: dict) -> str | None:
    """The kitchen event that lasts longest in a DESED clip ('Frying', 'Dishes' or 'Blender'), or None."""
    k = {c: events.get(c, 0) for c in ("Frying", "Dishes", "Blender")}
    return max(k, key=k.get) if max(k.values()) > 0 else None


def rows_from_embeddings(head: dict) -> list[dict]:
    """Every clip as {set, kind, group, half, probs, novel, w}: the head's output and the second opinion, no audio."""
    out = []

    def add(name, emb, tags, kinds, groups, files, main=None):
        P = model.predict_proba(head, emb)
        nov = model.novelty(head, emb) > head["novelty"]["threshold"]
        for i in range(len(P)):
            out.append({"set": name, "file": str(files[i]), "kind": str(kinds[i]), "group": str(groups[i]), "half": half(groups[i]),
                        "main": main[i] if main else None,
                        "probs": {c: round(float(v), 4) for c, v in zip(CLASSES, P[i])}, "novel": bool(nov[i]),
                        "w": witness.opinion(tags[i])})
    z = np.load(EMB / "desed" / "public_eval.npz")
    up, ev, aset = _desed_groups()
    keep = [i for i, f in enumerate(z["files"]) if str(f).rsplit("_", 2)[0] not in aset]
    f = z["files"][keep]
    add("desed", z["emb"][keep], z["audioset"][keep], [desed_kind(ev.get(str(x), {})) for x in f],
        [up.get(str(x), str(x).rsplit("_", 2)[0]) for x in f], f, main=[main_sound(ev.get(str(x), {})) for x in f])
    for name in ("kitchen20", "esc50_house"):
        q = np.load(EMB / name / "all.npz")
        add(name, q["emb"], q["audioset"], q["category"], q["source"], q["files"])
    return out


def sins_dev_rows(head: dict) -> list[dict]:
    """The research home, dev folds: out-of-fold head probabilities + the frozen head's novelty flag + the second opinion."""
    o = np.load(RESULTS / "cache" / "oof_dev.npz", allow_pickle=True)
    d = np.load(RESULTS / "cache" / "ced-tiny_dev.npz", allow_pickle=True)
    pos = {str(f): i for i, f in enumerate(d["files"])}
    idx = np.array([pos[str(f)] for f in o["files"]])
    nov = model.novelty(head, d["emb"][idx, 0].astype(np.float32)) > head["novelty"]["threshold"]
    k, fam, v = witness.opinions(d["scores"][idx, 0].astype(np.float32))
    y = [CLASSES[int(t)] if not isinstance(t, str) else t for t in o["y"]]
    return [{"set": "sins_dev", "file": str(o["files"][i]), "kind": y[i], "group": str(o["session"][i]), "half": "dev",
             "probs": dict(zip(CLASSES, map(float, o["P0"][i]))), "novel": bool(nov[i]),
             "w": {"k": round(float(k[i]), 3), "family": str(fam[i]), "v": round(float(v[i]), 3)}} for i in range(len(y))]


# ---------------------------------------------------------------- scoring

def shown(row: dict, theta: float, rule: str) -> str:
    ev = {"probs": row["probs"], "novel": row["novel"]}
    return timeline.raw_label({**ev, "w": row["w"]}, theta) if rule == "v2" else timeline.head_label(ev, theta)


def rate(rows: list[dict], theta: float, rule: str, seed: int = 0, n_boot: int = 2000) -> dict:
    """Share of rows shown as a kitchen activity, with a group-bootstrap 95% interval."""
    if not rows:
        return {"value": None, "n": 0, "groups": 0}
    hit = np.array([shown(r, theta, rule) in MEAL for r in rows], float)
    groups = defaultdict(list)
    for i, r in enumerate(rows):
        groups[r["group"]].append(i)
    g = [np.array(v) for v in groups.values()]
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        pick = np.concatenate([g[j] for j in rng.integers(0, len(g), len(g))])
        boots.append(hit[pick].mean())
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"value": round(100 * hit.mean(), 1), "ci": [round(100 * lo, 1), round(100 * hi, 1)], "k": int(hit.sum()), "n": len(rows), "groups": len(g)}


def table(rows: list[dict], theta: float, which: str) -> dict:
    """All pre-registered numbers for one half ('tune' or 'test')."""
    sel = lambda s, kinds: [r for r in rows if r["set"] == s and r["half"] == which and r["kind"] in kinds]
    out = {}
    for rule in ("v1", "v2"):
        t = {"desed_kitchen_caught": rate(sel("desed", ["kitchen"]), theta, rule),
             "desed_false_kitchen": rate(sel("desed", DESED_NOT), theta, rule),
             "desed_brief": rate(sel("desed", ["brief"]), theta, rule),
             "desed_water": rate(sel("desed", ["water"]), theta, rule),
             "k20_activity_caught": rate(sel("kitchen20", K20_ACT), theta, rule),
             "k20_false_kitchen": rate(sel("kitchen20", K20_NOT), theta, rule),
             "esc_false_kitchen": rate(sel("esc50_house", [c for c in ESC_CATS if c != "pouring_water"]), theta, rule),
             "by_kind": {}}
        for s, kinds in (("desed", ["kitchen", "brief", "water"] + DESED_NOT), ("kitchen20", K20_ACT + K20_NOT + K20_SEP), ("esc50_house", ESC_CATS)):
            for kd in kinds:
                t["by_kind"][f"{s}/{kd}"] = rate(sel(s, [kd]), theta, rule, n_boot=200)
        out[rule] = t
    return out


def sins_guard(rows: list[dict], theta: float) -> dict:
    out = {}
    for rule in ("v1", "v2"):
        out[rule] = {"kitchen_caught": rate([r for r in rows if r["kind"] in MEAL], theta, rule, n_boot=500),
                     "false_kitchen": rate([r for r in rows if r["kind"] not in MEAL], theta, rule, n_boot=500),
                     "right_label": round(100 * float(np.mean([shown(r, theta, rule) == r["kind"] for r in rows])), 1),
                     "not_sure": round(100 * float(np.mean([shown(r, theta, rule) == "not_sure" for r in rows])), 1)}
    return out


def fmt(x: dict) -> str:
    return "n/a (no clips)" if x.get("value") is None else f"{x['value']}% [{x['ci'][0]}, {x['ci'][1]}] ({x['k']} of {x['n']}, {x['groups']} sources)"


def markdown(R: dict) -> str:
    L = ["# Other homes: Kettle outside the research home", "",
         f"Made by `python -m eval.other_homes` ({R['made']}). Rules and metrics were fixed in `eval/PREREGISTER-V2.md` before the test halves were scored.",
         "One clip = one 10-second window, no smoothing. v1 = the rule shipped until Sat Nov 14 9:45 PM CT. v2 = v1 checked by the second opinion (`kettle/witness.py`).",
         f"Leakage audit: {R['dropped_audioset']} DESED clips whose videos are also in AudioSet (the encoder's pretraining data) were dropped.", ""]
    names = [("desed_kitchen_caught", "Real-home kitchen clips shown as a kitchen activity (DESED: frying, dishes, blender)"),
             ("desed_false_kitchen", "Real-home NON-kitchen clips shown as a kitchen activity (vacuum, shaver, speech, pets, alarms)"),
             ("k20_activity_caught", "Kitchen20 activity clips shown as a kitchen activity (10 categories)"),
             ("k20_false_kitchen", "Kitchen20 non-activity clips shown as kitchen (fridge, dishwasher, sweep, book, cupboard, drawer)"),
             ("esc_false_kitchen", "ESC-50 household non-kitchen clips shown as kitchen (12 categories)"),
             ("desed_brief", "DESED clips with under 2 s of kitchen sound (in neither group)"),
             ("desed_water", "DESED running water, no kitchen event (tap or shower; in neither group)")]
    for which in ("test", "tune"):
        if which not in R:
            continue
        L += [f"## {'TEST halves (scored once)' if which == 'test' else 'Tune halves (used to choose τ_k and the tag lists)'}", "",
              "| | v1 (shipped before) | v2 (second opinion) |", "|---|---|---|"]
        for key, title in names:
            L.append(f"| {title} | {fmt(R[which]['v1'][key])} | {fmt(R[which]['v2'][key])} |")
        L += ["", "Per category, v1 → v2 (share shown as a kitchen activity; n):", ""]
        for kd, x in R[which]["v2"]["by_kind"].items():
            a = R[which]["v1"]["by_kind"][kd]
            if x["n"]:
                L.append(f"- {kd}: {a['value']}% → {x['value']}% (n = {x['n']})")
        L.append("")
    if "test" in R:
        a, b = R["tune"]["v2"]["desed_kitchen_caught"], R["test"]["v2"]["desed_kitchen_caught"]
        fk = R["test"]["v2"]["desed_false_kitchen"]
        gap = round(a["value"] - b["value"], 1)
        L += ["## Read this before quoting the numbers", "",
              (f"- **The test half came in lower than we wrote we expected.** PREREGISTER-V2 expected 'caught' within about 10 points of the tune value "
               f"({a['value']}%). The test value is {b['value']}% [{b['ci'][0]}, {b['ci'][1]}]: {gap} points lower, with a wide interval ({b['n']} clips, {b['groups']} uploaders). "
               f"We did not retune. {b['value']}% is the number to quote." if gap > 10 else
               f"- The test half ({b['value']}%) is within about 10 points of the tune half ({a['value']}%), as PREREGISTER-V2 expected."),
              f"- The false-kitchen bar (at most 5% on DESED test non-kitchen clips) was {'met' if fk['value'] <= 5 else 'MISSED'}: {fk['k']} of {fk['n']}.",
              "- v2 still misses many single 10-second kitchen windows in other homes. A real meal is many windows; whether that adds up to "
              "'the meal was noticed' is what the own-kitchen recordings measure.",
              "- Known misses by design: blenders and juicers (the tags can't tell them from a vacuum cleaner). Known false kitchen labels: footsteps on a "
              "crunchy surface (heard as 'Crunch') and running water outside the kitchen."]
        if R.get("post_hoc"):
            ph = R["post_hoc"]
            L += ["- **Post hoc (looked at after the test run, so a description and not a result):** by the clip's main kitchen sound, v2 caught "
                  + "; ".join(f"{k.lower()} {ph['test'][k]['k']} of {ph['test'][k]['n']} on the test half (tune: {ph['tune'][k]['k']} of {ph['tune'][k]['n']})" for k in ("Frying", "Dishes", "Blender"))
                  + ". The two halves hold different shares of blender clips, which is where the gap between them comes from.",
                  f"- {ph['novel']['k']} of the {ph['novel']['n']} real-home clips were flagged 'unlike anything it learned' by the head's own check: "
                  "outside the research home, the second opinion does almost all of the work."]
        L.append("")
    g = R["sins_dev"]
    L += ["## Guard: the research home (SINS dev, out-of-fold; used for tuning, so this is not a test)", "",
          "| | v1 | v2 |", "|---|---|---|",
          f"| Kitchen windows shown as a kitchen activity | {fmt(g['v1']['kitchen_caught'])} | {fmt(g['v2']['kitchen_caught'])} |",
          f"| Other windows shown as a kitchen activity | {fmt(g['v1']['false_kitchen'])} | {fmt(g['v2']['false_kitchen'])} |",
          f"| Windows shown with their true label | {g['v1']['right_label']}% | {g['v2']['right_label']}% |",
          f"| Windows shown as Not sure | {g['v1']['not_sure']}% | {g['v2']['not_sure']}% |", "",
          "## What this does not show",
          "These are 10-second clips from YouTube and Freesound: other homes and other microphones, but often close to the sound, and close to what the "
          "encoder was pretrained on. It is not a laptop across a real kitchen for a morning. Our own kitchens are the real test (eval/OWN_KITCHEN_GUIDE.md).", ""]
    return "\n".join(L)


def main(argv: list[str]) -> int:
    head = model.load(ROOT / "models" / "head.json")
    theta = head["theta"]
    if "--fetch" in argv:
        fetch()
    run_log = RESULTS / "other_homes_run.json"
    if "--from-cache" in argv:
        rows = [json.loads(line) for line in PRED.read_text().splitlines()]
        prev = json.loads((RESULTS / "other_homes.json").read_text())
        dropped, test = prev["dropped_audioset"], "test" in prev
    else:
        rows = rows_from_embeddings(head)
        z = np.load(EMB / "desed" / "public_eval.npz")
        dropped = int(len(z["files"]) - sum(r["set"] == "desed" for r in rows))
        test = "--test" in argv
        if test and run_log.exists():
            raise SystemExit("The test halves were already scored (results/other_homes_run.json). Use --from-cache to rebuild the tables.")
    sins = sins_dev_rows(head)
    R = {"made": time.strftime("%a %b %d %Y, %I:%M %p %Z"), "theta": theta, "tau_k": witness.TAU_K, "tau_v": witness.TAU_V,
         "head_sha256": head["sha256"], "dropped_audioset": dropped, "tune": table(rows, theta, "tune"), "sins_dev": sins_guard(sins, theta)}
    if test:
        R["test"] = table(rows, theta, "test")
        d = [r for r in rows if r["set"] == "desed"]
        R["post_hoc"] = {h: {k: {"k": sum(shown(r, theta, "v2") in MEAL for r in d if r["half"] == h and r["kind"] == "kitchen" and r.get("main") == k),
                                 "n": sum(1 for r in d if r["half"] == h and r["kind"] == "kitchen" and r.get("main") == k)} for k in ("Frying", "Dishes", "Blender")}
                         for h in ("tune", "test")}
        R["post_hoc"]["novel"] = {"k": sum(r["novel"] for r in d), "n": len(d)}
        if "--from-cache" not in argv:
            run_log.write_text(json.dumps({"scored_at": R["made"], "head_sha256": head["sha256"], "tau_k": witness.TAU_K, "tau_v": witness.TAU_V,
                                           "witness_sha256": hashlib.sha256((ROOT / "models" / "witness.json").read_bytes()).hexdigest()}, indent=1))
            PRED.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        (RESULTS / "other_homes.json").write_text(json.dumps(R, indent=1))
        (RESULTS / "other_homes.md").write_text(markdown(R))
    print(markdown(R))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
