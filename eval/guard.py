"""The test-set guard: nothing may read evaluation-set embeddings except the one frozen run.

Opening eval embeddings for scoring requires the environment variable KETTLE_EVAL_RUN=1 (set only by
`python -m eval --split dcase-eval`) and a frozen model: models/FROZEN must exist and contain the sha256 of
models/head.json. (Computing eval embeddings with the frozen pretrained encoder needs no head and no labels,
so the embedding job may write them; nothing else may read them.)
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EvalLocked(RuntimeError):
    pass


def frozen_hash() -> str | None:
    p = ROOT / "models" / "FROZEN"
    return p.read_text().split()[0] if p.exists() else None


def assert_eval_allowed() -> None:
    """Raise EvalLocked unless this is the sanctioned eval run with a frozen head."""
    if os.environ.get("KETTLE_EVAL_RUN") != "1":
        raise EvalLocked("Evaluation-set embeddings are locked. Only `python -m eval --split dcase-eval` may open them.")
    import json
    h = json.loads((ROOT / "models" / "head.json").read_text()).get("sha256")
    if frozen_hash() is None or h != frozen_hash():
        raise EvalLocked("The head is not frozen (models/FROZEN missing or its hash differs from models/head.json).")
