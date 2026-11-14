"""Kettle's server: one process serves the three pages, a small JSON API and the kitchen mic WebSocket.

Run:  python app.py            (then open http://localhost:8000/kitchen on the kitchen laptop
                                and http://localhost:8000/ for the caregiver view)
No keys, no accounts, no network: the model weights and the sample-day clips are in the repo.

Who can do what:
- Only the kitchen laptop itself (requests from 127.0.0.1) can give consent, pause, resume, turn Kettle
  off or send microphone audio. The caregiver's phone on the home network or a private VPN can read
  the day and set checks, but it can never start, resume or hide listening.
- The only file the server writes is data/timeline/<date>.jsonl: labels, scores and times, never audio.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from kettle import audio, demo, encoders, live, model, rules, timeline, view

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
TIMELINE = Path(os.environ.get("KETTLE_TIMELINE_DIR", ROOT / "data" / "timeline"))
RESULTS = ROOT / "results"
MAX_UPLOAD = 10 * 1024 * 1024
KITCHEN_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}

APP: dict = {"enc": None, "head": None, "state": None, "demo": None, "demo_task": None,
             "runtime": {"first_audio_t": None, "windows": 0, "infer_s": []}}


# ---------------------------------------------------------------- labels-only persistence

def _day_file(t: float) -> Path:
    return TIMELINE / (time.strftime("%Y-%m-%d", time.localtime(t)) + ".jsonl")


def persist(rec: dict) -> None:
    """Append one record (a window's labels or a consent/pause event) to today's labels file."""
    TIMELINE.mkdir(parents=True, exist_ok=True)
    with open(_day_file(rec.get("t", time.time())), "a") as f:
        f.write(json.dumps(rec) + "\n")


def restore() -> dict:
    """Rebuild the kitchen state from the last 8 days of label files (consent, pauses, checks, today's windows)."""
    s = live.new_state()
    if not TIMELINE.exists():
        return s
    files = sorted(TIMELINE.glob("*.jsonl"))[-8:]
    today = _day_file(time.time()).name
    for f in files:
        for line in open(f):
            try:
                live.replay(s, json.loads(line), keep_windows=(f.name == today))
            except (ValueError, KeyError):
                continue
    return s


# ---------------------------------------------------------------- app setup

@asynccontextmanager
async def lifespan(_app: FastAPI):
    APP["enc"] = encoders.load()
    APP["head"] = model.load(ROOT / "models" / "head.json")
    APP["state"] = restore()
    task = asyncio.create_task(_ticker())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


async def _ticker() -> None:
    """Once a second: end pauses that ran out and run the weekly 'Keep it on?' rule."""
    while True:
        s = APP["state"]
        before = len(s["log"])
        live.tick(s, time.time())
        for rec in s["log"][before:]:
            persist({"kind": "log", **rec})
        await asyncio.sleep(1)


def _theta() -> float:
    return float(APP["head"].get("theta", 0.5))


def _kitchen_only(request: Request) -> None:
    """Refuse parent-only actions unless they come from the kitchen laptop itself."""
    if (request.client.host if request.client else "") not in KITCHEN_HOSTS:
        raise HTTPException(403, "Only the kitchen laptop can do this.")


def _active() -> tuple[dict, float]:
    """The state shown on every page right now: the sample day if one is open, otherwise the real kitchen."""
    d = APP["demo"]
    if d:
        return d["state"], d["now"]
    return APP["state"], time.time()


# ---------------------------------------------------------------- pages

@app.get("/")
def caregiver_page():
    return FileResponse(STATIC / "index.html")


@app.get("/kitchen")
def kitchen_page():
    return FileResponse(STATIC / "kitchen.html")


@app.get("/how-sure")
def how_sure_page():
    return FileResponse(STATIC / "how-sure.html")


# ---------------------------------------------------------------- read API

@app.get("/api/today")
def api_today():
    s, now = _active()
    out = view.today(s, now, _theta(), demo.info(APP["demo"]))
    out["head"] = {"sha256": APP["head"].get("sha256", "")[:12], "trained_on": APP["head"].get("trained_on", "")}
    return out


@app.get("/api/runtime")
def api_runtime():
    """How fast labelling runs on this machine (seconds per 2-s hop, including the 5-s chip and the 10-s window)."""
    rt = APP["runtime"]
    xs = sorted(rt["infer_s"])
    return {"first_audio_t": rt["first_audio_t"], "windows": rt["windows"], "n_hops": len(xs),
            "median_s": xs[len(xs) // 2] if xs else None, "p90_s": xs[int(len(xs) * 0.9)] if xs else None}


@app.get("/api/results/{name}.png")
def api_results_png(name: str):
    """The plots python -m eval draws (confusion matrix, reliability, θ trade-off)."""
    p = (RESULTS / f"{name}.png").resolve()
    if p.parent != RESULTS.resolve() or not p.exists():
        raise HTTPException(404)
    return FileResponse(p)


@app.get("/api/results")
def api_results():
    """results/metrics.json for the 'How sure is Kettle?' page; a designed empty state if missing."""
    p = RESULTS / "metrics.json"
    if not p.exists():
        return {"status": "missing"}
    out = json.loads(p.read_text())
    for extra in ("failures.json", "privacy_check.json", "eval_run.json", "runtime.json"):
        q = RESULTS / extra
        if q.exists():
            out[extra.split(".")[0]] = json.loads(q.read_text())
    out["status"] = "ok"
    return out


# ---------------------------------------------------------------- parent's controls (kitchen laptop only)

async def _body(request: Request) -> dict:
    try:
        return await request.json()
    except ValueError:
        return {}


def _act(fn, *args) -> dict:
    """Apply a parent action to the shown state; persist it if it's the real kitchen."""
    s, now = _active()
    rec = fn(s, now, *args)
    if not APP["demo"]:
        persist({"kind": "log", **rec})
    return api_today()


@app.post("/api/consent")
def api_consent(request: Request):
    _kitchen_only(request)
    return _act(live.consent)


@app.post("/api/pause")
async def api_pause(request: Request):
    _kitchen_only(request)
    minutes = (await _body(request)).get("minutes")
    if minutes not in (15, 60, None):
        raise HTTPException(400, "minutes must be 15, 60 or null")
    return _act(live.pause, minutes)


@app.post("/api/resume")
def api_resume(request: Request):
    _kitchen_only(request)
    return _act(live.resume)


@app.post("/api/off")
def api_off(request: Request):
    _kitchen_only(request)
    return _act(live.turn_off)


@app.post("/api/start")
def api_start(request: Request):
    _kitchen_only(request)
    return _act(live.start)


@app.post("/api/keep-on")
def api_keep_on(request: Request):
    _kitchen_only(request)
    return _act(live.keep_on)


@app.post("/api/mic")
async def api_mic(request: Request):
    """The kitchen page reports the microphone: 'ok', 'blocked' (permission denied) or 'none' (no device)."""
    _kitchen_only(request)
    state = (await _body(request)).get("state")
    if state not in ("ok", "blocked", "none"):
        raise HTTPException(400, "bad mic state")
    return _act(live.set_mic, state)


# ---------------------------------------------------------------- caregiver's checks

@app.post("/api/rules")
async def api_rules(request: Request):
    try:
        clean = rules.validate((await _body(request)).get("rules"))
    except (ValueError, KeyError, TypeError):
        raise HTTPException(400, "Up to 3 checks, each with a time or a number of hours.")
    s, now = _active()
    s["rules"] = clean
    if not APP["demo"]:
        persist({"kind": "rules", "t": now, "rules": clean})
    return api_today()


# ---------------------------------------------------------------- try your own sound (in memory only)

@app.post("/api/try")
async def api_try(request: Request):
    """Label an uploaded clip. Reads the raw body into RAM (no multipart, so nothing is spooled to disk)."""
    body = await request.body()
    name = request.headers.get("x-filename", "your sound")[:80]
    if len(body) > MAX_UPLOAD:
        return {"status": "too_big", "file": name}
    try:
        x, seconds, cut = audio.read_upload(body)
    except audio.AudioError as e:
        return {"status": e.reason, "file": name, "seconds": e.seconds}
    del body
    wins = audio.windows(x)
    res = live.classify(APP["enc"], APP["head"], np.stack([w for _, w in wins]))
    events = [{**r, "start": t0, "end": t0 + 10, "t": t0 + 10, "kind": "window10"} for (t0, _), r in zip(wins, res)]
    blks = timeline.blocks(events, _theta(), gap_s=1)
    theta = _theta()
    labs = [timeline.raw_label(e, theta) for e in events]
    out_windows = [{"start": e["start"], "end": e["end"], "label": lab, "display": timeline.label_name(lab),
                    "conf": e["conf"], "sounds": e["sounds"], "probs": e["probs"]} for e, lab in zip(events, labs)]
    return {"status": "ok", "file": name, "seconds": round(seconds, 1), "cut": cut, "windows": out_windows,
            "blocks": [{**b, "label": timeline.display_name(b)} for b in blks],
            "all_not_sure": all(w["label"] == "not_sure" for w in out_windows)}


@app.get("/api/try-samples")
def api_try_samples():
    """The sample files offered under 'Try your own sound' (a clear clip, an unclear one, noise, not audio)."""
    d = ROOT / "demo_cache" / "try"
    return [{"name": p.name} for p in sorted(d.iterdir()) if not p.name.startswith(".") and p.suffix != ".json"]


@app.get("/api/try-samples/{name}")
def api_try_sample(name: str):
    p = (ROOT / "demo_cache" / "try" / name).resolve()
    if p.parent != (ROOT / "demo_cache" / "try").resolve() or not p.exists():
        raise HTTPException(404)
    return FileResponse(p)


# ---------------------------------------------------------------- sample days

async def _play(d: dict) -> None:
    step = demo.wall_seconds_per_step()
    while APP["demo"] is d and d["playing"]:
        t0 = time.time()
        if not demo.advance(d, APP["enc"], APP["head"]):
            break
        await asyncio.sleep(max(0.0, step - (time.time() - t0)))


@app.post("/api/demo/{sid}")
async def api_demo(sid: str):
    if sid == "stop":
        APP["demo"] = None
        return api_today()
    if sid == "sleep":
        if APP["demo"]:
            demo.sleep_laptop(APP["demo"])
        return api_today()
    if sid == "week":
        if APP["demo"]:          # sample-day control: pretend a week has passed since Dad said yes
            APP["demo"]["state"]["last_confirm"] = APP["demo"]["now"] - live.WEEK_S
        return api_today()
    if sid not in demo.scenarios():
        raise HTTPException(404, "no such sample day")
    d = demo.new_demo(sid, view.local_midnight(time.time()))
    APP["demo"] = d
    APP["demo_task"] = asyncio.create_task(_play(d))
    return api_today()


@app.post("/api/demo/{sid}/instant")
def api_demo_instant(sid: str):
    """Play a whole sample day at once (for tests and screenshots)."""
    if sid not in demo.scenarios():
        raise HTTPException(404)
    d = demo.new_demo(sid, view.local_midnight(time.time()))
    while demo.advance(d, APP["enc"], APP["head"]):
        pass
    APP["demo"] = d
    return api_today()


# ---------------------------------------------------------------- kitchen microphone

@app.websocket("/ws/audio")
async def ws_audio(sock: WebSocket):
    """16 kHz Int16 PCM from the kitchen page -> labels. Audio stays in this connection's RAM buffer."""
    if (sock.client.host if sock.client else "") not in KITCHEN_HOSTS:
        await sock.close(code=4403)
        return
    await sock.accept()
    st = live.new_stream()
    rt = APP["runtime"]
    try:
        while True:
            pcm = await sock.receive_bytes()
            s, now = APP["state"], time.time()
            t0 = time.perf_counter()
            evs = live.feed(s, st, pcm, now, APP["enc"], APP["head"])
            if evs:
                rt["infer_s"] = (rt["infer_s"] + [round(time.perf_counter() - t0, 4)])[-500:]
            if live.can_listen(s, now) and rt["first_audio_t"] is None:
                rt["first_audio_t"] = now
            for ev in evs:
                if ev["kind"] == "window10":
                    rt["windows"] += 1
                    persist({"kind": "window", **ev})
            del pcm
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("KETTLE_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=int(os.environ.get("KETTLE_PORT", "8000")), log_level="warning")
