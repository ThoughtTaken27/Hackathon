"""Beyond the frozen head: measure every new on-device layer before the app uses it (improvement plan A2-A7, D1, G2, G4).

Nothing here re-reads the held-out DCASE eval audio and nothing changes models/head.json. Inputs are committed caches:

  results/cache/oof_dev.npz            out-of-fold head probabilities + AudioSet scores for 8,920 SINS dev clips
  results/cache/ced-tiny_dev.npz       CED-tiny embeddings of the same clips (4 channels)
  results/cache/ced-tiny_offlist.npz   200 ESC-50 off-list clips + 60 generated noise/silence clips
  results/cache/ced-tiny_esc50kinds.npz  ESC-50 household + sensitive clips (eval/esc50_kinds.py)

Every threshold is chosen on dev folds 1-2 and reported on folds 3-4 (or on ESC-50, which was never used to choose).

  1. Sound types (A6 + "more sounds"): 15 named household sounds read zero-shot from CED's AudioSet outputs.
  2. Privacy allow-list (D1): how often a sensitive sound (cough, crying, toilet, snoring...) gets any name. Target: rarely.
  (An appliance gate and a quiet gate were measured here first; the merged app uses the second opinion
   (kettle/witness.py) and the silent-microphone rule for those instead, so they were removed.)
  5. Teach-this-kitchen enrolment (A3): a head trained WITHOUT the test microphone (a new kitchen stand-in),
     then 30 s / 1 min / 3 min of that microphone's own quiet, cooking and washing up as on-device prototypes.
  6. Novelty trade-off (A2): what share of real activity vs off-list sound each novelty threshold lets through.

Writes results/beyond.json, web/public/model/kinds.json and web/public/model/enrol.json (the constants the browser uses).
Run: python -m eval.beyond   (~2 min, CPU)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score

from kettle import model
from kettle.labels import CLASSES, MEAL

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results" / "cache"
OUT = ROOT / "results" / "beyond.json"
WEB = ROOT / "web" / "public" / "model"
C = {c: i for i, c in enumerate(CLASSES)}
THETA = 0.66
RNG = np.random.default_rng(0)

# ---------------------------------------------------------------- 1. the named sound types
# id: (what the family reads, AudioSet indices (models/audioset_labels.json), SINS activities that contain it,
#      SINS activities that should NOT contain it (false-fire set), matching ESC-50 categories)
KITCHEN_NOT = ["absence", "working", "watching_tv", "vacuum_cleaner"]
KINDS = {
    "kettle":    ("Kettle or a hot drink", [456, 296, 403, 402], [], KITCHEN_NOT, []),
    "frying":    ("Frying or sizzling", [367, 490], ["cooking"], KITCHEN_NOT, []),
    "chopping":  ("Chopping", [366, 438], ["cooking"], KITCHEN_NOT, []),
    "blender":   ("Blender", [369], ["cooking"], KITCHEN_NOT, []),
    "microwave": ("Microwave", [368], [], KITCHEN_NOT, []),
    "dishes":    ("Dishes and cutlery", [364, 365, 442, 489], ["dishwashing"], KITCHEN_NOT, []),
    "tap":       ("Running water", [370, 371], ["dishwashing"], KITCHEN_NOT, []),
    "cupboard":  ("Cupboards and drawers", [362, 363], [], ["absence", "watching_tv", "vacuum_cleaner"], []),
    "door":      ("A door", [354, 357], [], ["absence", "watching_tv", "vacuum_cleaner"], ["door_wood_creaks"]),
    "alarm":     ("Timer or appliance beep", [481, 398, 395], [], ["absence", "vacuum_cleaner"], ["clock_alarm"]),
    "tv":        ("Talking / TV", [524, 525], ["watching_tv"], ["absence", "vacuum_cleaner", "dishwashing"], []),
    "vacuum":    ("Vacuum cleaner", [377], ["vacuum_cleaner"], [c for c in CLASSES if c != "vacuum_cleaner"], ["vacuum_cleaner"]),
    "typing":    ("Typing", [384, 386], ["working"], ["absence", "cooking", "dishwashing", "vacuum_cleaner", "watching_tv"], ["keyboard_typing"]),
    "footsteps": ("Footsteps", [53], [], ["absence", "vacuum_cleaner"], ["footsteps"]),
    "glass":     ("Glass breaking", [443, 470], [], ["absence", "vacuum_cleaner"], ["glass_breaking"]),
}
# Context rules (handover v3.2, 3.1; eval/PREREGISTER-SOUNDS.md): a name also needs its score to beat these classes in the
# same window ("beat"), and/or a minimum score ("min"). Smoke and fire alarms (399, 400) are never a family sound name.
CONTEXT = {
    "kettle":    {"beat": [367, 490, 370, 371, 364, 365, 442, 489, 377, 412, 413]},   # frying, tap, dishes, vacuum/fan hum (last three chosen on tune)
    "tap":       {"beat": [367, 490]},                                   # frying hiss reads as water
    "microwave": {"min": 0.5, "beat": [377, 412, 413, 343]},             # vacuum, fan, air conditioning, engine hum
}
SHOWN_FILE = ROOT / "results" / "sounds.json"      # eval/sounds.py: which names passed the pre-registered bar (v1 rules)
SHOWN_V2 = ROOT / "results" / "sound_head.json"    # eval/sound_head.py: the trained head (v2), which replaced v1 where it exists


def shown_ids() -> dict:
    """Pass/fail per sound from the last eval/sound_head.py run, else eval/sounds.py (all shown until either has run)."""
    if SHOWN_V2.exists():
        return {k: v["shown"] for k, v in json.loads(SHOWN_V2.read_text())["v2_head"].items()}
    if not SHOWN_FILE.exists():
        return {}
    return {k: v["shown"] for k, v in json.loads(SHOWN_FILE.read_text())["after"].items()}


# Never named, never sent (D1): voices, body and bathroom sounds. Listed on the consent screen.
NEVER = ["Speech", "Conversation", "Laughter", "Singing", "Crying, sobbing", "Baby cry, infant cry", "Cough", "Sneeze",
         "Snoring", "Breathing", "Chewing, mastication", "Toilet flush", "Toothbrush", "Bathtub (filling or washing)"]
MIN_TAU = 0.05
# Privacy veto (D1): when a body or bathroom sound outscores every named type, the window names nothing at all
# (otherwise a toilet flush would be called "Running water").
VETO = [22, 23, 41, 42, 43, 44, 45, 47, 48, 49, 56, 58, 59, 60, 372, 374, 375, 376]
HUM = [412, 413, 368, 377]          # mechanical fan, air conditioning, microwave oven, vacuum cleaner

# ---------------------------------------------------------------- 3. the appliance gate: kitchen evidence for "Cooking"
# Microwave, fan and air-conditioning hum are deliberately NOT evidence (the live test's vacuum was tagged as all three).
COOK_EVIDENCE = [367, 490, 366, 438, 364, 365, 370, 371, 456, 369, 455, 442, 489, 449, 452, 362, 363]


def load() -> dict:
    o = np.load(CACHE / "oof_dev.npz")
    e = np.load(CACHE / "ced-tiny_dev.npz")
    pos = {f: i for i, f in enumerate(e["files"])}
    ix = np.array([pos[f] for f in o["files"]])                  # the two caches list the same clips in different orders
    X4 = e["emb"][ix].astype(np.float64)
    return {"P": o["P0"].astype(np.float64), "S": o["scores"].astype(np.float64), "y": o["y"], "fold": o["fold"],
            "session": o["session"], "node": o["node"], "files": o["files"], "X": X4[:, 0], "X4": X4}


def kind_scores(S: np.ndarray) -> dict:
    return {k: S[:, v[1]].max(1) for k, v in KINDS.items()}


def sound_types(d: dict, esc: dict) -> dict:
    """Choose each type's threshold on folds 1-2 (99th percentile of its false-fire set), report folds 3-4 + ESC-50."""
    ks, tune, test = kind_scores(d["S"]), np.isin(d["fold"], [1, 2]), np.isin(d["fold"], [3, 4])
    eks = kind_scores(esc["S"])
    out, taus = {}, {}
    for k, (name, idx, related, never, esc_cats) in KINDS.items():
        neg = np.isin(d["y"], [C[c] for c in never])
        tau = float(max(MIN_TAU, np.quantile(ks[k][tune & neg], 0.99)))
        taus[k] = round(tau, 3)
        row = {"name": name, "tau": round(tau, 3), "false_fire_dev_test": rate(ks[k][test & neg] >= tau),
               "false_fire_quiet_dev_test": rate(ks[k][test & (d["y"] == C["absence"])] >= tau)}
        if related:
            pos = np.isin(d["y"], [C[c] for c in related])
            row["heard_in_related_dev_test"] = rate(ks[k][test & pos] >= tau) | {"related": related}
        if esc_cats:
            m = np.isin(esc["category"], esc_cats)
            row["esc50_hit"] = rate(eks[k][m] >= tau) | {"categories": esc_cats}
        other = (esc["group"] == "household") & ~np.isin(esc["category"], esc_cats)
        row["esc50_false_fire_other_household"] = rate(eks[k][other] >= tau)
        out[k] = row
    sens = esc["group"] == "sensitive"
    fired_raw = np.stack([eks[k] >= taus[k] for k in KINDS], 1)
    top_named = np.stack([np.where(eks[k] >= taus[k], eks[k], 0) for k in KINDS], 1).max(1)
    vetoed = esc["S"][:, VETO].max(1) >= top_named
    fired = fired_raw & ~vetoed[:, None]
    hh = esc["group"] == "household"
    veto_cost = {"household_named_before": rate(fired_raw[hh].any(1)), "household_named_after": rate(fired[hh].any(1)),
                 "sensitive_named_before_veto": rate(fired_raw[sens].any(1))}
    dveto = d["S"][:, VETO].max(1) >= np.stack([np.where(ks[k] >= taus[k], ks[k], 0) for k in KINDS], 1).max(1)
    for k in KINDS:
        if KINDS[k][2]:
            pos = test & np.isin(d["y"], [C[c] for c in KINDS[k][2]])
            out[k]["heard_in_related_dev_test_after_veto"] = rate((ks[k][pos] >= taus[k]) & ~dveto[pos])
        if KINDS[k][4]:
            m = np.isin(esc["category"], KINDS[k][4])
            out[k]["esc50_hit_after_veto"] = rate((eks[k][m] >= taus[k]) & ~vetoed[m])
    per_cat = {}
    for c in sorted(set(esc["category"][sens])):
        m = esc["category"] == c
        names = [k for j, k in enumerate(KINDS) if fired[m, j].any()]
        per_cat[c] = rate(fired[m].any(1)) | {"named_as": names}
    return {"types": out, "sensitive_any_name": rate(fired[sens].any(1)), "sensitive_by_category": per_cat, "taus": taus,
            "veto": veto_cost}


def enrol_sim(d: dict) -> dict:
    """A3: head trained without the test microphone and test fold; enrol k clips per class from that microphone's
    earliest session of each class; test on its other sessions. Hyper-parameters chosen on folds 1-2."""
    enrolled = ["absence", "cooking", "dishwashing"]
    seg = np.array([int(f.rsplit("_", 1)[1]) for f in d["files"]])
    sess = np.array([int(s[1:]) for s in d["session"]])
    cache = {}

    def scenario(f, n):
        if (f, n) not in cache:
            tr = (d["fold"] != f) & (d["node"] != n)
            Xtr = d["X4"][tr].reshape(-1, d["X4"].shape[-1])
            ytr = np.repeat(d["y"][tr], d["X4"].shape[1])
            h = model.fit(Xtr, ytr)
            nv = model.fit_novelty(Xtr, ytr, h)
            ref = model.novelty(h, d["X"][tr], nv)
            h["novelty"] = {**nv, "threshold": float(np.quantile(ref, 0.99))}
            cache[(f, n)] = h
        return cache[(f, n)]

    def run(folds, k, alpha, rho, knn=5):
        ys, before, after, nov_b, nov_a = [], [], [], [], []
        for f in folds:
            for n in np.unique(d["node"]):
                pool = np.where((d["fold"] == f) & (d["node"] == n))[0]
                h = scenario(f, n)
                enrol_idx, enrol_sess = [], set()
                for c in enrolled:
                    cand = pool[d["y"][pool] == C[c]]
                    cand = cand[np.lexsort((seg[cand], sess[cand]))][:k]
                    enrol_idx += list(cand)
                    enrol_sess |= set(d["session"][cand])
                test = pool[~np.isin(d["session"][pool], list(enrol_sess))]
                if not len(test) or not enrol_idx:
                    continue
                P = model.predict_proba(h, d["X"][test])
                nov = model.novelty(h, d["X"][test]) > h["novelty"]["threshold"]
                Pa, nova = adapt(h, d["X"][enrol_idx], d["y"][enrol_idx], d["X"][test], P, nov, alpha, rho, knn)
                ys.append(d["y"][test]), before.append(labels(P, nov)), after.append(labels(Pa, nova))
                nov_b.append(nov), nov_a.append(nova)
        y, b, a = map(np.concatenate, (ys, before, after))
        return {"before": scores(y, b), "after": scores(y, a), "novel_share_before": rate(np.concatenate(nov_b)),
                "novel_share_after": rate(np.concatenate(nov_a))}

    grid = [(a, r) for a in (0.4, 0.6, 0.8) for r in (1.0, 1.5, 2.0)]
    tuned = {g: run([1, 2], 6, *g)["after"]["macro_f1"] for g in grid}
    alpha, rho = max(tuned, key=tuned.get)
    res = {"enrolled": enrolled, "alpha": alpha, "rho": rho, "knn": 5, "tuning_folds": [1, 2], "report_folds": [3, 4],
           "head": "logistic head refit WITHOUT the test microphone (node) and test fold, same recipe as the frozen head",
           "by_minutes": {}}
    for k, label in ((3, "0.5"), (6, "1"), (18, "3")):
        res["by_minutes"][label] = run([3, 4], k, alpha, rho)
    return res


def adapt(h, Xe, ye, X, P, nov, alpha, rho, knn):
    """The browser's enrolment rule (web/public/js/sense.js applyEnrolment), in numpy: for a window the head could
    not name (novel or below theta) that lies near this kitchen's setup windows, the k nearest vote with weight alpha.
    A confident head is never overridden (an earlier version that always blended lowered macro F1; see DECISIONS)."""
    mean, std = np.asarray(h["mean"]), np.asarray(h["std"])
    Ze, Z = (Xe - mean) / std, (X - mean) / std
    De = np.linalg.norm(Ze[:, None] - Ze[None], axis=2)
    np.fill_diagonal(De, np.inf)
    same = ye[:, None] == ye[None]
    nn_same = np.where(same, De, np.inf).min(1)
    radius = rho * float(np.median(nn_same[np.isfinite(nn_same)]))
    D = np.linalg.norm(Z[:, None] - Ze[None], axis=2)
    order = np.argsort(D, 1)[:, :knn]
    near = D.min(1) <= radius
    q = np.zeros_like(P)
    for j in range(order.shape[1]):
        q[np.arange(len(X)), ye[order[:, j]]] += 1 / order.shape[1]
    unsure = nov | (P.max(1) < THETA)                       # only windows the head could not name are helped
    use = near & unsure
    Pa = np.where(use[:, None], (1 - alpha) * P + alpha * q, P)
    return Pa, nov & ~use


def labels(P, nov):
    lab = P.argmax(1)
    return np.where(nov | (P.max(1) < THETA), -1, lab)


def scores(y, pred) -> dict:
    meal_t, meal_p = np.isin(y, [C[c] for c in MEAL if c in C]), np.isin(pred, [C[c] for c in MEAL if c in C])
    return {"n_windows": int(len(y)), "macro_f1": round(100 * f1_score(y, pred, labels=list(range(len(CLASSES))), average="macro", zero_division=0), 1),
            "kitchen_noticed": rate(meal_p[meal_t]), "false_kitchen": rate(meal_p[~meal_t]), "not_sure_share": rate(pred == -1),
            "recall": {c: rate(pred[y == C[c]] == C[c])["pct"] for c in ("absence", "cooking", "dishwashing", "eating")}}


def novelty_tradeoff(d: dict, head: dict, off: dict) -> dict:
    """A2: share of dev windows (out-of-fold) and of off-list ESC-50 clips accepted at each novelty threshold."""
    nd = model.novelty(head, d["X"])
    no = model.novelty(head, off["X"])
    curve = []
    for q in (0.9, 0.95, 0.99, 0.995, 0.999):
        th = float(np.quantile(nd, q))
        curve.append({"threshold": round(th, 2), "dev_accepted_pct": round(100 * float((nd <= th).mean()), 1),
                      "offlist_accepted_pct": round(100 * float((no[off["esc"]] <= th).mean()), 1)})
    return {"frozen_threshold": round(head["novelty"]["threshold"], 2), "curve": curve,
            "note": "dev distances are in-sample for the frozen head (it was fit on these clips), so dev acceptance is optimistic;"
                    " no real-kitchen data exists yet to set a better threshold, so the frozen one stays and enrolment relaxes it per kitchen"}


def rate(mask) -> dict:
    mask = np.asarray(mask, bool)
    n, k = int(mask.size), int(mask.sum())
    if not n:
        return {"k": 0, "n": 0, "pct": None, "ci95": None}
    p = k / n
    z = 1.96
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return {"k": k, "n": n, "pct": round(100 * p, 1), "ci95": [round(100 * max(0, c - h), 1), round(100 * min(1, c + h), 1)]}


def main() -> None:
    head = model.load(ROOT / "models" / "head.json")
    d = load()
    e = np.load(CACHE / "ced-tiny_esc50kinds.npz")
    esc = {"S": e["scores"].astype(np.float64), "X": e["emb"].astype(np.float64), "category": e["category"],
           "group": e["group"], "rms_db": e["rms_db"]}
    o = np.load(CACHE / "ced-tiny_offlist.npz")
    files = o["files"]
    off = {"X": o["emb"][:, 0].astype(np.float64), "esc": np.char.startswith(files, "esc50")}
    silence = {"n": int(np.char.startswith(files, "gen_silence").sum()), "note": "generated digital silence: RMS = -inf dBFS, always below"}
    R = {"about": __doc__.split("\n\n")[0], "theta": THETA, "head_sha256": head["sha256"]}
    R["sound_types"] = sound_types(d, esc)
    R["never_named"] = NEVER
    R["novelty"] = novelty_tradeoff(d, head, off)
    R["enrolment"] = enrol_sim(d)
    OUT.write_text(json.dumps(R, indent=1))
    (ROOT / "web" / "public" / "data" / "beyond.json").write_text(json.dumps(R))   # the How sure page reads this copy
    shown = shown_ids()
    WEB.joinpath("kinds.json").write_text(json.dumps({
        "kinds": [{"id": k, "name": v[0], "index": v[1], "tau": R["sound_types"]["taus"][k], **CONTEXT.get(k, {}),
                   "shown": shown.get(k, True)} for k, v in KINDS.items()],
        "never": NEVER, "veto": VETO, "source": "eval/beyond.py -> results/beyond.json"}))
    en = R["enrolment"]
    WEB.joinpath("enrol.json").write_text(json.dumps({"alpha": en["alpha"], "rho": en["rho"], "knn": en["knn"],
                                                      "source": "eval/beyond.py -> results/beyond.json"}))
    print(json.dumps({"types": {k: (v["tau"], v.get("esc50_hit", {}).get("pct"), v["false_fire_dev_test"]["pct"]) for k, v in R["sound_types"]["types"].items()},
                      "sensitive_any_name": R["sound_types"]["sensitive_any_name"],
                      "enrol": {m: (v["before"], v["after"]) for m, v in en["by_minutes"].items()}, "alpha_rho": (en["alpha"], en["rho"])}, indent=1))


if __name__ == "__main__":
    main()
