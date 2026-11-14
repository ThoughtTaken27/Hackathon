"""Run Apple's SoundAnalysis classifier on channel 0 of every fetched clip of a split; cache the scores.

macOS only. Output: results/baselines/apple_<split>.jsonl (one line per clip: file stem + 303 mean confidences),
so the Apple baseline numbers can be recomputed anywhere without a Mac.
AVAudioFile can't open the 4-channel FLACs, so each batch writes channel 0 as temporary mono WAVs into
data/raw/apple_tmp/ (git-ignored, public dataset clips only) and deletes them right after.
Usage: python tools/apple_baseline/run.py dev    (eval: only inside the frozen run)
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
CLI = Path(__file__).with_name("apple_classify")
TMP = ROOT / "data" / "raw" / "apple_tmp"
BATCH = 200


def run(split: str) -> int:
    out = ROOT / "results" / "baselines" / f"apple_{split}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    have = {json.loads(l)["file"] for l in open(out)} if out.exists() else set()
    todo = sorted(p for p in (ROOT / "data" / "clips" / split).glob("*.flac") if p.stem not in have)
    for s in range(0, len(todo), BATCH):
        TMP.mkdir(parents=True, exist_ok=True)
        paths = []
        for p in todo[s:s + BATCH]:
            x, sr = sf.read(p, dtype="int16", always_2d=True)
            q = TMP / f"{p.stem}.wav"
            sf.write(q, x[:, 0], sr, subtype="PCM_16")
            paths.append(str(q))
        res = subprocess.run([str(CLI), *paths], capture_output=True, text=True, timeout=1200).stdout.splitlines()
        with open(out, "a") as f:
            for line in res:
                r = json.loads(line)
                if "mean" in r:
                    f.write(json.dumps({"file": Path(r["file"]).stem, "windows": r["windows"], "mean": r["mean"]}) + "\n")
        shutil.rmtree(TMP)
        print(f"apple {split}: {s + len(paths)}/{len(todo)}", flush=True)
    return len(todo)


if __name__ == "__main__":
    split = sys.argv[1]
    if split.startswith("eval"):
        from eval.guard import assert_eval_allowed
        assert_eval_allowed()
    run(split)
