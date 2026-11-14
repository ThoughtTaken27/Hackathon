"""Screenshot every designed state of Kettle at 1440x900 and 393x852, light and dark, with Playwright.

Starts its own server (port 8766, throwaway labels folder, so the real kitchen timeline is untouched) and a
Chromium whose fake microphone plays held-out SINS clips. Usage:
    python tools/screenshots.py <round> [--only caregiver|kitchen|howsure] [--sizes desktop,phone] [--themes light,dark]
Writes docs/screenshots/round-<n>/<page>-<state>-<size>-<theme>.png and an index.md listing them.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PORT = 8766
BASE = f"http://127.0.0.1:{PORT}"
SIZES = {"desktop": (1440, 900), "phone": (393, 852)}
DENY = "navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('denied', 'NotAllowedError'));"
NOMIC = "navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('none', 'NotFoundError'));"
PENDING = "navigator.mediaDevices.getUserMedia = () => new Promise(() => {});"


def post(path: str, body: dict | None = None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body or {}).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def start_server(tmp: Path):
    env = {**os.environ, "KETTLE_PORT": str(PORT), "KETTLE_TIMELINE_DIR": str(tmp), "HF_HUB_OFFLINE": "1"}
    srv = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for _ in range(80):
        try:
            urllib.request.urlopen(BASE + "/api/today", timeout=2)
            return srv
        except OSError:
            time.sleep(0.5)
    raise SystemExit("server didn't start")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("round")
    ap.add_argument("--only", default="caregiver,kitchen,howsure")
    ap.add_argument("--sizes", default="desktop,phone")
    ap.add_argument("--themes", default="light,dark")
    a = ap.parse_args()
    out = ROOT / "docs" / "screenshots" / f"round-{a.round}"
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="kettle-shots-"))
    from eval.privacy_check import fake_mic, FAKE_MIC
    fake_mic(240)
    srv = start_server(tmp)
    shots = []
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                                        f"--use-file-for-fake-audio-capture={FAKE_MIC}"])
            combos = [(s, th) for s in a.sizes.split(",") for th in a.themes.split(",")]

            def page(size, theme, init=None):
                w, h = SIZES[size]
                ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=theme, device_scale_factor=1 if size == "desktop" else 2)
                if init:
                    ctx.add_init_script(init)
                return ctx, ctx.new_page()

            def snap(pg, name, size, theme, full=False):
                pg.wait_for_timeout(600)
                f = out / f"{name}-{size}-{theme}.png"
                pg.screenshot(path=str(f), full_page=full)
                shots.append(f.name)

            def each(name, url, prep=None, init=None, wait=1200, full=False, route=None):
                for size, theme in combos:
                    ctx, pg = page(size, theme, init)
                    if route:
                        route(pg)
                    pg.goto(BASE + url)
                    pg.wait_for_timeout(wait)
                    if prep:
                        prep(pg)
                    snap(pg, name, size, theme, full)
                    ctx.close()

            only = a.only.split(",")
            if "kitchen" in only:
                each("kitchen-consent-1", "/kitchen")
                each("kitchen-consent-2", "/kitchen", prep=lambda pg: pg.get_by_role("button", name="Next").click())
                each("kitchen-declined", "/kitchen", prep=lambda pg: pg.get_by_role("button", name="Not now").click())
            if "caregiver" in only:
                each("caregiver-never", "/", full=True)
                each("caregiver-never-top", "/")
            if "howsure" in only:
                each("howsure-empty", "/how-sure", route=lambda pg: pg.route("**/api/results", lambda r: r.fulfill(json={"status": "missing"})))
                each("howsure", "/how-sure", full=True, wait=1500)
                each("howsure-top", "/how-sure", wait=1500)
            if "kitchen" in only:
                post("/api/consent")
                each("kitchen-mic-asking", "/kitchen", init=PENDING)
                each("kitchen-mic-denied", "/kitchen", init=DENY)
                each("kitchen-no-mic", "/kitchen", init=NOMIC)
                # live listening with the fake mic: one page, resized and re-themed for every combination
                ctx, live_pg = page("desktop", "light")

                def snap_all(name):
                    for size, theme in combos:
                        live_pg.set_viewport_size({"width": SIZES[size][0], "height": SIZES[size][1]})
                        live_pg.emulate_media(color_scheme=theme)
                        snap(live_pg, name, size, theme)
                    live_pg.set_viewport_size({"width": 1440, "height": 900})
                live_pg.goto(BASE + "/kitchen")
                live_pg.wait_for_timeout(4000)
                snap_all("kitchen-starting")
                live_pg.wait_for_timeout(26000)
                snap_all("kitchen-listening")
                live_pg.get_by_role("button", name="Pause", exact=True).click()
                snap_all("kitchen-pause-menu")
                live_pg.get_by_role("button", name="Pause for 1 hour").click()
                live_pg.wait_for_timeout(1500)
                snap_all("kitchen-paused")
                each("caregiver-live-paused", "/")
                live_pg.get_by_role("button", name="Resume listening").click()
                live_pg.wait_for_timeout(2500)
                snap_all("kitchen-resumed")
                live_pg.wait_for_timeout(12000)
                each("caregiver-live", "/", wait=1500)
                ctx.close()
                post("/api/demo/usual/instant")
                each("kitchen-sample-day", "/kitchen")
                post("/api/demo/week")
                each("kitchen-weekly", "/kitchen")
                each("kitchen-error", "/kitchen", prep=lambda pg: (pg.route("**/api/today", lambda r: r.abort()), pg.wait_for_timeout(4500)))
                post("/api/demo/stop")
            if "caregiver" in only:
                for sid in ("usual", "quiet", "tv"):
                    post(f"/api/demo/{sid}/instant")
                    each(f"caregiver-{sid}", "/")
                    if sid == "usual":
                        each("caregiver-usual-full", "/", full=True)
                        each("caregiver-usual-evidence", "/", prep=lambda pg: (pg.locator(".blk.activity").nth(1).click(), pg.wait_for_timeout(500)))
                        each("caregiver-rules-sheet", "/", prep=lambda pg: (pg.get_by_role("button", name="Change checks").click(), pg.wait_for_timeout(500)))
                        post("/api/pause", {"minutes": 60})
                        each("caregiver-paused", "/")
                        post("/api/resume")
                post("/api/demo/sleep")
                each("caregiver-stale", "/")
                each("caregiver-error", "/", prep=lambda pg: (pg.route("**/api/today", lambda r: r.abort()), pg.wait_for_timeout(4500)))
                post("/api/demo/stop")
                for sample in ("washing-up.flac", "unclear.flac", "white-noise.wav", "not-audio.txt"):
                    if not (ROOT / "demo_cache" / "try" / sample).exists():
                        continue
                    key = sample.split(".")[0]

                    def tr(pg, s=sample):
                        pg.locator("#try-section").scroll_into_view_if_needed()
                        pg.locator("#samples button", has_text={"washing-up.flac": "Washing up", "unclear.flac": "An unclear clip",
                                                                 "white-noise.wav": "White noise", "not-audio.txt": "isn't audio"}[s]).click()
                        pg.wait_for_timeout(2500)
                    each(f"caregiver-try-{key}", "/", prep=tr)
            b.close()
    finally:
        srv.terminate()
        srv.wait(10)
        shutil.rmtree(tmp, ignore_errors=True)
    (out / "index.md").write_text("# Screenshots, round " + a.round + "\n\n" + "\n".join(f"- {s}" for s in sorted(shots)) + "\n")
    print(f"{len(shots)} screenshots -> {out}")


if __name__ == "__main__":
    main()
