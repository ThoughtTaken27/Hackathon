"""End to end on the real pages: set up a home as family, pair the kitchen by code, consent, hear sound through
Chromium's fake microphone, and see the labels arrive on the family view. Run against `node web/dev.mjs`.

    python web/test/e2e.py http://localhost:8787 path/to/fake.wav out_dir
"""
import os
import json
import sys
import time

from playwright.sync_api import sync_playwright

BASE, WAV, OUT = sys.argv[1], sys.argv[2], sys.argv[3]


def main() -> int:
    errors, log = [], []
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=os.environ.get("KETTLE_CHROME") or None, args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", f"--use-file-for-fake-audio-capture={WAV}",
                                     "--autoplay-policy=no-user-gesture-required"])
        fam_ctx = br.new_context(viewport={"width": 393, "height": 852})
        kit_ctx = br.new_context(viewport={"width": 1280, "height": 800}, permissions=["microphone"])
        fam, kit = fam_ctx.new_page(), kit_ctx.new_page()
        for pg, who in ((fam, "family"), (kit, "kitchen")):
            pg.on("pageerror", lambda e, w=who: errors.append(f"{w}: {e}"))
            pg.on("console", lambda m, w=who: m.type == "error" and "Failed to load resource" not in m.text and errors.append(f"{w} console: {m.text}"))

        # 1. family sets up
        fam.goto(BASE + "/start")
        fam.get_by_role("button", name="On my own phone or computer").click()
        fam.get_by_role("button", name="My parent").click()           # v3.1 setup: who, what you call them, which room
        fam.locator("#p").fill("Papa")
        fam.get_by_role("button", name="Kitchen", exact=True).click()
        fam.locator("#c").fill("Asha")
        fam.get_by_role("button", name="Create our Kettle").click()
        fam.wait_for_selector(".code-big")
        code = fam.locator(".code-big").first.inner_text().replace(" ", "")
        fam.wait_for_timeout(800)
        fam.screenshot(path=f"{OUT}/e2e-1-family-code.png", full_page=True)
        log.append(f"code {code}")

        # 2. kitchen pairs with the code
        kit.goto(BASE + "/kitchen")
        if kit.get_by_label("Device name").count():               # v3.6: name this device first (one code, several devices)
            kit.get_by_role("button", name="Kitchen laptop").click()
            kit.get_by_role("button", name="Next").click()
        kit.get_by_label("Six-letter code").first.fill(code)       # the six-box code submits itself when complete
        kit.wait_for_timeout(800)
        if kit.get_by_role("button", name="Connect").count() and "/kitchen" in kit.url and not kit.locator("text=listens for kitchen sounds").count():
            kit.get_by_role("button", name="Connect").click()
        kit.wait_for_selector("text=listens for kitchen sounds.", timeout=15000)
        kit.screenshot(path=f"{OUT}/e2e-2-kitchen-consent.png")
        kit.get_by_role("button", name="Next").click()
        kit.get_by_role("button", name="Yes, Asha can see this").click()
        kit.wait_for_timeout(1000)
        if kit.get_by_role("button", name="Skip setup").count():         # first-time placement guide
            kit.get_by_role("button", name="Skip setup").click()

        # 3. model loads, fake mic plays, labels appear on the kitchen screen
        t0 = time.time()
        try:
            kit.wait_for_selector("text=Listening", timeout=90000)
        except Exception:
            kit.screenshot(path=f"{OUT}/e2e-fail.png")
            print("STUCK:", kit.locator("#head").inner_text(), "|", kit.locator("#body").inner_text()[:300])
            print("errors:", json.dumps(errors, indent=1))
            raise
        log.append(f"listening after {time.time() - t0:.1f}s")
        if kit.get_by_role("button", name="Skip the sound check").count():
            kit.get_by_role("button", name="Skip the sound check").click()
        kit.wait_for_function("() => !document.querySelector('.chip .txt') || !/Waiting/.test(document.querySelector('.chip .txt').textContent)", timeout=60000)
        log.append(f"first label after {time.time() - t0:.1f}s: {kit.locator('.chip .txt').inner_text()}")
        kit.wait_for_timeout(int(os.environ.get("KETTLE_E2E_LISTEN_MS", "22000")))
        kit.screenshot(path=f"{OUT}/e2e-3-kitchen-listening.png")

        # 4. the family view shows them
        fam.goto(BASE + "/family")
        fam.wait_for_function("() => document.querySelectorAll('#bar .blk').length > 0", timeout=30000)
        hb = fam.locator("#hb .text").inner_text()
        log.append(f"family heartbeat: {hb}")
        log.append(f"family blocks: {fam.locator('#bar .blk').count()}; summary: {fam.locator('#summary').inner_text()!r}")
        fam.wait_for_timeout(1500)
        fam.screenshot(path=f"{OUT}/e2e-4-family-live.png", full_page=True)

        # 5. Papa pauses; the family view says so
        kit.get_by_role("button", name="Pause").click()
        kit.get_by_role("button", name="Pause for 15 minutes").click()
        fam.wait_for_function("() => /Paused by Papa/.test(document.querySelector('#hb .text').textContent)", timeout=20000)
        log.append("pause reached family: " + fam.locator("#hb .text").inner_text())
        kit.screenshot(path=f"{OUT}/e2e-5-kitchen-paused.png")

        # 6. delete the home from the family view; both screens lose access
        gone = fam.evaluate("""async () => { const h = Object.values(JSON.parse(localStorage.getItem('kettle.homes.v1')));
          const r = await fetch('/api/h/' + h[0].id, { method: 'DELETE', headers: { authorization: 'Bearer ' + h[0].familyKey } });
          const after = await fetch('/api/h/' + h[0].id + '/state', { headers: { authorization: 'Bearer ' + h[0].familyKey } });
          return [r.status, after.status]; }""")
        log.append(f"delete home: {gone[0]}, afterwards: {gone[1]}")
        if gone != [200, 404]:
            errors.append(f"delete gave {gone}, expected [200, 404]")
        br.close()
    print("\n".join(log))
    print("errors:", json.dumps(errors, indent=1))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
