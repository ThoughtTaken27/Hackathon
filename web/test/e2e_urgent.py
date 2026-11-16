"""Urgent alert end to end (handover v3.5 success test, automated): a home is set up through the API, the room page listens
to Chromium's fake microphone playing an alarm WAV, and the family page must turn red. Measures the delay. Run against
`node web/dev.mjs`:

    python web/test/e2e_urgent.py http://localhost:8787 alarm.wav out_dir [expected kind, default smoke]
"""
import json
import os
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

BASE, WAV, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
KIND = sys.argv[4] if len(sys.argv) > 4 else "smoke"


def api(path, body=None, key=None, method=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None, method=method or ("POST" if body is not None else "GET"),
                                 headers={"content-type": "application/json", **({"authorization": f"Bearer {key}"} if key else {})})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def main() -> int:
    errors, log, out = [], [], {"wav": os.path.basename(WAV), "expected": KIND}
    h = api("/api/households", {"parent": "Papa", "caregiver": "Asha", "tz": "America/Chicago", "as": "family", "room": {"type": "kitchen"}})
    kitchen_key = api("/api/pair", {"code": h["code"]})["key"]
    hid, fkey = h["id"], h["familyKey"]
    try:
        with sync_playwright() as p:
            br = p.chromium.launch(executable_path=os.environ.get("KETTLE_CHROME") or None, args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", f"--use-file-for-fake-audio-capture={WAV}",
                                         "--autoplay-policy=no-user-gesture-required"])
            fam = br.new_context(viewport={"width": 393, "height": 852}).new_page()
            kit = br.new_context(viewport={"width": 1280, "height": 800}, permissions=["microphone"]).new_page()
            for pg, who in ((fam, "family"), (kit, "kitchen")):
                pg.on("pageerror", lambda e, w=who: errors.append(f"{w}: {e}"))
            fam.goto(f"{BASE}/family#f={hid}.{fkey}")
            kit.goto(f"{BASE}/kitchen#k={hid}.{kitchen_key}")
            kit.get_by_role("button", name="Next").click()
            kit.get_by_role("button", name="Yes, Asha can see this").click()
            kit.wait_for_timeout(1000)
            if kit.get_by_role("button", name="Skip setup").count():
                kit.get_by_role("button", name="Skip setup").click()
            t0 = time.time()
            kit.wait_for_selector("text=Listening", timeout=120000)
            log.append(f"listening after {time.time() - t0:.1f}s")
            if kit.get_by_role("button", name="Skip the sound check").count():
                kit.get_by_role("button", name="Skip the sound check").click()
            t1 = time.time()
            try:
                kit.wait_for_selector('#status[data-state="urgent"]', timeout=90000)
                out["room_urgent_after_s"] = round(time.time() - t1, 1)
                log.append(f"room screen urgent after {out['room_urgent_after_s']}s of listening: {kit.locator('#head').inner_text()!r}")
            except Exception:
                errors.append("room screen never turned urgent")
            kit.screenshot(path=f"{OUT}/urgent-1-room.png")
            t2 = time.time()
            try:
                fam.wait_for_selector(".urgent", timeout=20000)
                out["family_red_after_room_s"] = round(time.time() - t2, 1)
                log.append(f"family red {out['family_red_after_room_s']}s later: {fam.locator('.urgent .u-h').first.inner_text()!r}; title {fam.title()!r}")
            except Exception:
                errors.append("family page never showed the urgent banner")
            fam.screenshot(path=f"{OUT}/urgent-2-family.png", full_page=False)
            st = api(f"/api/h/{hid}/state", key=fkey)
            kinds = [a["kind"] for a in st["state"].get("alerts", [])]
            out["server_alert_kinds"] = kinds
            log.append(f"server alerts: {kinds}")
            if KIND not in kinds:
                errors.append(f"expected a {KIND} alert, got {kinds}")
            br.close()
    finally:
        api(f"/api/h/{hid}", {}, key=fkey, method="DELETE")
    out.update({"errors": errors, "ran_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
                "note": "Chromium fake microphone playing the WAV; family page polls every 5 s (push not tested headless)."})
    with open(f"{OUT}/e2e_urgent.json", "w") as f:
        json.dump(out, f, indent=1)
    print("\n".join(log))
    print("errors:", json.dumps(errors, indent=1))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
