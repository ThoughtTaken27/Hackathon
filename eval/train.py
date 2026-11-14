"""Fit the head Kettle ships (models/head.json), using only choices made on the dev folds.

C = the median of the per-fold C values chosen by inner CV; temperature and θ come from the out-of-fold
logits of the dev study. Trained on every fetched dev training clip (all 4 channels); the 9 demo sessions
are not in that set. Usage: python -m eval.train   (then python -m eval.train --freeze to lock it for the eval run)
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

from eval import dev
from eval.common import ROOT, table
from kettle import model


def train(study: dict) -> dict:
    from eval.embed import EMB, done_files
    from pathlib import Path
    plan = json.loads((ROOT / "data" / "meta" / "plan.json").read_text())
    files = {Path(f).stem for f in plan["train_files"]} & done_files(EMB / "ced-tiny" / "dev")
    T = table("ced-tiny", "dev", files)
    C = float(np.median(list(study["C_per_fold"].values())))
    h = dev.fit_head(T["emb"], T["y"], C)
    n, ch, d = T["emb"].shape
    h["novelty"] = {**model.fit_novelty(T["emb"].reshape(n * ch, d), np.repeat(T["y"], ch), h),
                    "threshold": study["novelty"]["threshold"]}
    h.update(temperature=study["temperature"], theta=study["not_sure"]["theta"], encoder="ced-tiny",
             trained_on=f"SINS dev training subset: {len(T['y'])} clips x 4 channels, {len(set(T['session']))} sessions, "
                        f"all 4 folds; 9 demo sessions held out (data/meta/plan.json)",
             trained_at=time.strftime("%Y-%m-%d %H:%M %Z"))
    sha = model.save(h, ROOT / "models" / "head.json")
    print(json.dumps({"sha256": sha, "C": C, "temperature": h["temperature"], "theta": h["theta"], "n": len(T["y"])}))
    return h


def freeze() -> str:
    """Lock the current head for the one eval run: models/FROZEN = its sha256 + time."""
    h = model.load(ROOT / "models" / "head.json")
    (ROOT / "models" / "FROZEN").write_text(f"{h['sha256']} frozen {time.strftime('%Y-%m-%d %H:%M %Z')}\n")
    return h["sha256"]


if __name__ == "__main__":
    if "--freeze" in sys.argv:
        print("frozen", freeze())
    else:
        R = dev.run(fast="--fast" in sys.argv)
        R.pop("_oof", None)
        (ROOT / "results").mkdir(exist_ok=True)
        train(R)
