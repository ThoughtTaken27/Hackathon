"""Smoke test: the golden path, offline, in well under 60 seconds.

Runs the real app in-process (FastAPI TestClient, no network, no microphone, no keys):
pages load; consent gate; a sample day plays through the real model; the caregiver view shows the
heartbeat, blocks and checks; pause shows "Paused by your parent"; "Try your own sound" handles a real clip,
an unclear clip, silence, white noise and a non-audio file; live audio over the WebSocket is refused
before consent and labelled after it.
Usage: python smoke_test.py   (exit code 0 = pass)
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
ROOT = Path(__file__).resolve().parent
T0 = time.time()


def check(cond: bool, what: str) -> None:
    print(("  ok   " if cond else "  FAIL ") + what)
    if not cond:
        sys.exit(1)


def main() -> None:
    import numpy as np
    import soundfile as sf
    from fastapi.testclient import TestClient

    import app as kettle_app
    kettle_app.TIMELINE = Path(os.environ.get("KETTLE_SMOKE_TIMELINE", "/nonexistent-kettle-smoke"))
    kettle_app.persist = lambda rec: None          # the smoke test writes nothing at all

    with TestClient(kettle_app.app) as c:
        print(f"app loaded in {time.time() - T0:.1f} s")
        for page in ("/", "/today", "/kitchen", "/how-sure"):
            r = c.get(page)
            check(r.status_code == 200 and "Prototype, not medical advice" in r.text, f"page {page} loads with the disclaimer")
        t = c.get("/api/today").json()
        check(t["heartbeat"]["state"] == "never", "before consent the heartbeat says Kettle isn't on yet")

        # live audio is refused before consent
        clip, _ = sf.read(ROOT / "demo_cache" / "clips" / "DevNode1_ex56_1.flac", dtype="int16")
        with c.websocket_connect("/ws/audio") as ws:
            for i in range(0, 16000 * 4, 1600):
                ws.send_bytes(clip[i:i + 1600].tobytes())
        time.sleep(0.2)
        check(len(kettle_app.APP["state"]["events"]) == 0, "audio before consent is dropped (no labels)")

        # sample day 1: a usual morning
        t = c.post("/api/demo/usual/instant").json()
        acts = [b["activity"] for b in t["blocks"] if b["state"] == "activity"]
        check(t["demo"]["title"] == "A usual morning" and len(t["blocks"]) >= 3, f"sample day plays: {len(t['blocks'])} blocks")
        check(t["heartbeat"]["state"] == "listening", f"heartbeat: {t['heartbeat']['text']}")
        print("  blocks:", ", ".join(f"{b['label']} {b['range']}" for b in t["blocks"]))
        print("  summary:", t["summary"])
        for r in t["rules"]:
            print(f"  check: {r['title']} -> {r['state']}: {r['detail']}")
        check(len(t["rules"]) >= 1 and all(r["state"] for r in t["rules"]), "checks evaluate")
        check(any(a in ("cooking", "dishwashing", "eating") for a in acts), "a kitchen activity is heard on the usual morning")

        # the parent's pause, seen by the caregiver
        t = c.post("/api/pause", json={"minutes": 60}).json()
        check(t["heartbeat"]["state"] == "paused" and "Paused by your parent" in t["heartbeat"]["text"], f"pause: {t['heartbeat']['text']}")
        t = c.post("/api/resume").json()
        check(t["heartbeat"]["state"] != "paused", "resume")

        for sid in ("quiet", "tv"):
            t = c.post(f"/api/demo/{sid}/instant").json()
            print(f"  {sid}: " + " | ".join(f"{r['state']}: {r['detail']}" for r in t["rules"]))
            check(len(t["blocks"]) >= 1, f"sample day '{sid}' plays")
        t = c.post("/api/demo/sleep").json()
        check(t["heartbeat"]["state"] == "stale", f"laptop lid closed: {t['heartbeat']['text']}")
        c.post("/api/demo/stop")

        # try your own sound: a real clip, garbage, not audio, too short
        def try_bytes(name: str, data: bytes) -> dict:
            return c.post("/api/try", content=data, headers={"X-Filename": name, "Content-Type": "application/octet-stream"}).json()
        for name in sorted(n for n in os.listdir(ROOT / "demo_cache" / "try") if not n.endswith(".json")):
            r = try_bytes(name, (ROOT / "demo_cache" / "try" / name).read_bytes())
            print(f"  try {name}: {r['status']}" + (f" -> {[w['display'] for w in r['windows']]}" if r["status"] == "ok" else ""))
            check(r["status"] in ("ok", "unreadable", "too_short"), f"try {name} gives a designed result")
        r = try_bytes("short.wav", _wav(np.zeros(16000 * 3, dtype=np.float32)))
        check(r["status"] == "too_short", "a 3-second clip says it's too short")
        r = try_bytes("photo.jpg", b"\xff\xd8\xff\xe0" + os.urandom(2000))
        check(r["status"] == "unreadable", "a JPEG says it isn't audio")

        # live audio after consent produces labels (real mic path, fed from a demo clip)
        c.post("/api/consent")
        with c.websocket_connect("/ws/audio") as ws:
            for i in range(0, 16000 * 10, 1600):
                ws.send_bytes(clip[i:i + 1600].tobytes())
        time.sleep(0.3)
        evs = kettle_app.APP["state"]["events"]
        check(len(evs) >= 1, f"live audio after consent is labelled: {evs[-1]['label'] if evs else None}")
        t = c.get("/api/today").json()
        check(t["heartbeat"]["state"] == "listening", f"live heartbeat: {t['heartbeat']['text']}")
        check(c.get("/api/results").status_code == 200, "results endpoint answers")
    took = time.time() - T0
    check(took < 60, f"smoke test took {took:.1f} s (< 60 s)")
    print("PASS")


def _wav(x) -> bytes:
    import io
    import soundfile as sf
    b = io.BytesIO()
    sf.write(b, x, 16000, format="WAV", subtype="PCM_16")
    return b.getvalue()


if __name__ == "__main__":
    main()
