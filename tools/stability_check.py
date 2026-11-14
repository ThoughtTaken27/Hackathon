"""Stability check (component-craft law 5): while a sample day plays live, count day-bar nodes that are removed
(a block re-created instead of extended) and measure how far unchanged blocks move. Writes results/stability.json.
Usage: python tools/stability_check.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 8767
BASE = f"http://127.0.0.1:{PORT}"

OBSERVE = """
window.__removed = 0; window.__added = 0;
const bar = document.querySelector('.bar');
new MutationObserver((ms) => { for (const m of ms) { window.__removed += m.removedNodes.length; window.__added += m.addedNodes.length; } })
  .observe(bar, { childList: true });
"""


def main() -> None:
    tmp = tempfile.mkdtemp(prefix="kettle-stab-")
    env = {**os.environ, "KETTLE_PORT": str(PORT), "KETTLE_TIMELINE_DIR": tmp, "HF_HUB_OFFLINE": "1"}
    srv = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(80):
        try:
            urllib.request.urlopen(BASE + "/api/today", timeout=2)
            break
        except OSError:
            time.sleep(0.5)
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1440, "height": 900})
            pg.goto(BASE + "/")
            pg.wait_for_timeout(1500)
            pg.evaluate(OBSERVE)
            pg.get_by_role("button", name="Play a sample day: a usual morning").click()
            pg.wait_for_timeout(4000)
            first = pg.evaluate("[...document.querySelectorAll('.bar .blk')].slice(0,3).map(n => [n.dataset.key, n.getBoundingClientRect().left])")
            pg.wait_for_timeout(14000)                       # the rest of the morning plays
            after = pg.evaluate("Object.fromEntries([...document.querySelectorAll('.bar .blk')].map(n => [n.dataset.key, n.getBoundingClientRect().left]))")
            removed, added = pg.evaluate("[window.__removed, window.__added]")
            b.close()
    finally:
        srv.terminate()
        srv.wait(10)
    shifts = [abs(after[k] - x) for k, x in first if k in after]
    rep = {"blocks_added": added, "blocks_removed": removed, "early_blocks_still_present": f"{len(shifts)} of {len(first)}",
           "max_shift_px_of_unchanged_blocks": round(max(shifts), 2) if shifts else None,
           "note": "Removals happen only when 2-of-3 smoothing relabels the newest window (its block key changes); "
                   "the bar's time axis is fixed for a sample day, so unchanged blocks shouldn't move."}
    (ROOT / "results" / "stability.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
