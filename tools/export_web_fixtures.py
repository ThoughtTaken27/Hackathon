"""Everything the browser version of Kettle needs from the Python one, plus parity fixtures for its tests.

    python tools/export_web_fixtures.py

Writes
  web/public/model/head.json       the frozen head (numbers only), same sha256 as models/head.json
  web/public/model/evidence.json   which of CED's 527 AudioSet outputs may be shown, and their names
  web/public/model/witness.json    the second opinion: tag positions and thresholds (models/witness.json, as indices)
  web/public/js/sounds.js          the same allow-list as a module, so the sync server can drop any other sound name
  web/public/data/sample-days.json the three sample days: real model labels on held-out clips, times as offsets from midnight
  web/test/fixtures.json           Python's view.today() for many states, which web/test/core.test.mjs must reproduce
"""
from __future__ import annotations

import copy
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["TZ"] = "America/Chicago"
time.tzset()

from kettle import demo, encoders, evidence, kinds, live, model, view, witness  # noqa: E402

WEB = ROOT / "web"


def main() -> int:
    head = model.load(ROOT / "models" / "head.json")
    (WEB / "public" / "model").mkdir(parents=True, exist_ok=True)
    (WEB / "public" / "data").mkdir(parents=True, exist_ok=True)
    keep = ("classes", "mean", "std", "coef", "intercept", "temperature", "theta", "novelty", "sha256", "trained_on")
    (WEB / "public" / "model" / "head.json").write_text(json.dumps({k: head[k] for k in keep}))
    (WEB / "public" / "model" / "evidence.json").write_text(json.dumps(
        {"shown": evidence.SHOWN, "index": [int(i) for i in evidence._IDX]}))

    (WEB / "public" / "model" / "witness.json").write_text(json.dumps(
        {"kitchen": witness.KITCHEN_IDX, "veto": witness.VETO_IDX, "tau_k": witness.TAU_K, "tau_v": witness.TAU_V}))
    (WEB / "public" / "js" / "sounds.js").write_text(
        "// Made by tools/export_web_fixtures.py from kettle/evidence_labels.json. The only sound names Kettle may send or store.\n"
        f"export const SHOWN_SOUNDS = new Set({json.dumps(evidence.SHOWN)});\n")

    enc = encoders.load()
    day0 = time.mktime((2026, 11, 10, 0, 0, 0, 0, 0, -1))       # a fixed Tuesday, Chicago time
    theta = head["theta"]
    days, fixtures = {}, []
    for sid, sc in demo.scenarios().items():
        d = demo.new_demo(sid, day0)
        while demo.advance(d, enc, head):
            pass
        s = d["state"]
        evs = [{k: e[k] for k in ("start", "end", "label", "conf", "probs", "novel", "w", "sounds")} for e in s["events"]]
        for e, src in zip(evs, s["events"]):        # the named sound types a kitchen device would add (web/public/js/sense.js)
            _, scores = encoders.embed(enc, demo.read_clip(src["clip"])[None, :])
            e["kinds"] = [x["id"] for x in kinds.named(scores[0])]
        pauses = [[demo.at(day0, g["from"]) - day0, demo.at(day0, g["to"]) - day0] for g in sc["segments"] if g.get("pause")]
        days[sid] = {"title": d["title"], "started": demo.at(day0, sc["started"]) - day0,
                     "events": [{**e, "start": round(e["start"] - day0, 1), "end": round(e["end"] - day0, 1)} for e in evs],
                     **({"pauses": pauses} if pauses else {})}
        end = s["events"][-1]["end"]
        # the states both screens must agree on, each with Python's answer
        cases = [("live", s, end + 5), ("stale", s, end + 2 * 3600), ("evening", s, day0 + 20 * 3600)]
        p = copy.deepcopy(s)
        live.pause(p, end + 5, 15)
        cases.append(("paused", p, end + 60))
        o = copy.deepcopy(s)
        live.turn_off(o, end + 5)
        cases.append(("off", o, end + 120))
        for name, st, now in cases:
            fixtures.append({"case": f"{sid}/{name}", "now": now, "day0": day0, "tz": view.tz_offset(now),
                             "state": {k: v for k, v in st.items() if k not in ("chip", "log")},
                             "expect": strip(view.today(st, now, theta))})
    never = live.new_state()
    fixtures.append({"case": "never", "now": day0 + 9 * 3600, "day0": day0, "tz": view.tz_offset(day0 + 9 * 3600),
                     "state": {k: v for k, v in never.items() if k not in ("chip", "log")},
                     "expect": strip(view.today(never, day0 + 9 * 3600, theta))})
    (WEB / "public" / "data" / "sample-days.json").write_text(json.dumps(days))
    (WEB / "test").mkdir(exist_ok=True)
    (WEB / "test" / "fixtures.json").write_text(json.dumps({"theta": theta, "cases": fixtures}))
    print(f"{len(days)} sample days, {len(fixtures)} parity cases")
    return 0


def strip(t: dict) -> dict:
    """The parts of view.today() the web screens show."""
    return {"heartbeat": {k: t["heartbeat"][k] for k in ("state", "text")},
            "summary": t["summary"],
            "blocks": [{k: b.get(k) for k in ("start", "end", "state", "activity", "label", "range", "conf", "n_windows", "card")}
                       for b in t["blocks"]],
            "rules": [{k: r[k] for k in ("id", "state", "title", "detail", "note")} for r in t["rules"]]}


if __name__ == "__main__":
    raise SystemExit(main())
