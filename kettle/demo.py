"""'Play a sample day': real SINS clips through the same model, with staged clock times.

Each scenario is a list of segments ("cooking 8:00–8:25 from these 5 clips"). Every clip is decoded,
labelled by the real encoder + head, and its window event is stamped with a staged time so a whole
morning plays in about 15 seconds. The labels are the model's real output (it can be wrong, and then
the sample day shows that); only the clock times are staged, and every screen says "Sample day".
"""
from __future__ import annotations

import json
from pathlib import Path

import soundfile as sf

from kettle import live

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo_cache"
SPEED = 20                 # 10 s of audio plays in 0.5 s


def scenarios() -> dict:
    """{id: {'title', 'started', 'segments'}} from demo_cache/scenarios.json."""
    return {k: v for k, v in json.loads((DEMO / "scenarios.json").read_text()).items() if not k.startswith("_")}


def at(day0: float, hhmm: str) -> float:
    """'08:25' on the day starting at day0 -> unix seconds."""
    h, m = map(int, hhmm.split(":"))
    return day0 + h * 3600 + m * 60


def read_clip(name: str):
    """A committed demo clip as float32 16 kHz mono."""
    x, sr = sf.read(DEMO / "clips" / name, dtype="float32")
    return x[:160000]


def steps(scenario: dict, day0: float) -> list[dict]:
    """The scenario as a flat list of clips with their staged [start, end] times."""
    out = []
    for seg in scenario["segments"]:
        if seg.get("gap"):
            continue
        a, z = at(day0, seg["from"]), at(day0, seg["to"])
        d = (z - a) / len(seg["clips"])
        out += [{"clip": c, "start": a + i * d, "end": a + (i + 1) * d} for i, c in enumerate(seg["clips"])]
    return out


def new_demo(sid: str, day0: float) -> dict:
    """A fresh demo: its own kitchen state (consent given at the staged start) and its virtual clock."""
    sc = scenarios()[sid]
    s = live.new_state()
    t0 = at(day0, sc["started"])
    live.consent(s, t0)
    return {"id": sid, "title": sc["title"], "state": s, "now": t0, "playing": True,
            "steps": steps(sc, day0), "done": 0}


def advance(d: dict, enc: dict, head: dict) -> bool:
    """Label the next clip of the demo and move its virtual clock; returns False when the day is done."""
    if d["done"] >= len(d["steps"]):
        d["playing"] = False
        return False
    st = d["steps"][d["done"]]
    w = live.classify(enc, head, read_clip(st["clip"])[None, :])[0]
    ev = {**w, "t": st["end"], "start": st["start"], "end": st["end"], "kind": "window10", "clip": st["clip"]}
    s = d["state"]
    s["events"].append(ev)
    s["last_window_t"] = st["end"]
    s["chip"] = {**w, "t": st["end"], "kind": "chip5"}
    d["now"] = st["end"]
    d["done"] += 1
    return True


def info(d: dict | None) -> dict | None:
    """What the pages need to know about a running demo."""
    if not d:
        return None
    return {"id": d["id"], "title": d["title"], "playing": d["playing"], "done": d["done"], "total": len(d["steps"])}


def sleep_laptop(d: dict, minutes: int = 20) -> None:
    """Demo control: pretend the kitchen laptop went to sleep; time moves on with nothing heard."""
    d["playing"] = False
    d["now"] = d["now"] + minutes * 60


def wall_seconds_per_step() -> float:
    return 10 / SPEED

