"""Shared test cases for the trained sound head: Python (kettle/kinds.py named) answers that sense.js kindsOf must match.

    python tools/export_sound_head_fixtures.py   -> web/test/sound_head_fixtures.json

About 40 real windows from the tune halves (never the test halves): 2 positives of each sound, and 10 ordinary windows.
Values are rounded (6 decimals) before both sides run, so the file stays small and the comparison is exact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval import sound_head  # noqa: E402
from eval.sounds import POS  # noqa: E402
from kettle import kinds  # noqa: E402

OUT = ROOT / "web" / "test" / "sound_head_fixtures.json"


def main() -> int:
    T = sound_head.pooled(sound_head.data(), "tune")
    rnd = np.random.RandomState(1)
    pick = []
    for k in POS:
        pos = np.where(np.isin(T["lab"], POS[k]))[0]
        pick += list(rnd.choice(pos, min(2, len(pos)), replace=False))
    pick += list(rnd.choice(len(T["lab"]), 10, replace=False))
    cases = []
    for i in pick:
        emb, sc = np.round(T["E"][i], 6), np.round(T["S"][i], 6)
        cases.append({"lab": str(T["lab"][i]), "emb": [float(x) for x in emb], "as": [float(x) for x in sc],
                      "shown": [x["id"] for x in kinds.named(sc, emb=emb)],
                      "all": [x["id"] for x in kinds.named(sc, emb=emb, with_hidden=True)]})
    OUT.write_text(json.dumps(cases))
    print(f"{len(cases)} cases -> {OUT.relative_to(ROOT)}; named: {sum(bool(c['all']) for c in cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
