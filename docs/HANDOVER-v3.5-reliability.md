# Kettle v3.5 handover: reliability, urgent alerts, and the last 5 hours

Written Sun 15 Nov 2026, ~5:55 PM CT, by Parth's Aside agent, for Shaurya's or Amrutha's Claude. Parth's usage is almost gone.
**Read this whole file before touching code.** Handovers v3.1 to v3.4 still hold for anything not mentioned here.

**Deadline: 10:59 PM CT tonight (11:59 PM ET). Late entries are not accepted. Team target: submitted by 9:30 PM CT.**
Nothing below is worth missing the deadline. If it's 8:30 PM and a task isn't green, drop it and ship what works.

---

## 0. TL;DR for the next Claude

Parth's two asks, in his words: (1) "it gives false alarms, it gives false readings, it doesn't identify it... I want it as
solid and reliable as it can possibly be", with **few categories**, since the family only wants to know whether the day looks okay;
(2) **"If there is a thud, an alarm (fire alarm, smoke detector), shouting, screaming, gunshots or anything similar, it should
immediately mark it red and notify the other person."** He also wants a clean UI for that, and **it has to actually work.**

What I found (all verified by reading the code at `origin/main` 408fb46, not by assumption):

| # | Finding | Where | Severity |
|---|---|---|---|
| F1 | **Family is never notified unless the family page is already open.** Web Push code exists (`web/src/push.js`, `sw.js`, `pushclient.js`, tests pass) but **the server never calls `sendPush`**, and there is no subscribe route or button. The red banner only shows on a family tab that is open and polling (every 5 s). | `web/src/router.js`, `web/src/household.js`, `web/public/js/family.js` | **Critical**: this is the "notify the other person" ask |
| F2 | **Screaming and crash-then-cry don't alert immediately.** The kitchen screen asks "Are you OK?" for **30 s (scream) / 60 s (fall)**, and the family hears nothing until that runs out. Parth wants red at once. | `kitchen.js handleSafety()` L203-219, `safety.js CHECKIN_S` | **Critical** |
| F3 | **Carbon monoxide alarms are detected but never sent.** `WIRED = ["smoke","fall","fall_still","scream","help"]` doesn't include `"co"`, so a CO alert is dropped silently. | `kitchen.js` L204 | **Bug, 1-line fix** |
| F4 | **No gunshot detector at all.** AudioSet indices exist in the model output (426 Explosion, 427 Gunshot/gunfire, 428 Machine gun, 429 Fusillade, 430 Artillery fire, 431 Cap gun; confusers 432 Fireworks, 433 Firecracker, 434 Burst/pop, 436 Boom). | `safety.json`, `safety.js`, `kettle/safety.py`, `eval/safety.py DETECTORS` | **High**: explicit ask |
| F5 | **Shouting never raises an alert.** The `shout` detector (indices 8 Shout, 11 Yell, 13 Children shouting, tau 0.3) is computed but no rule uses it, and it has no measured catch rate. | `safety.js step()` | **High**: explicit ask |
| F6 | **The smoke-alarm AudioSet score catches only 4.2%** (10/240) of synthetic alarms. The T3 beep-rhythm detector does the real work: 25-26/30 at 10-20 dB SNR, **2/30 at 0 dB**. End to end, a smoke alarm during cooking alerts in **68.3%** (41/60) of held-out scenarios. Synthetic tones only, no real alarm recordings. | `results/safety.json` | **High** |
| F7 | **Stove left on (C6), beeping ignored (C7), water left running (C9) never fire,** because the kitchen calls `safetyStep(..., { urgent: true, concern: false })`. | `kitchen.js` L268 | Medium: decide on purpose, don't leave it accidental |
| F8 | **A thud alone can't be red without flooding the family.** The impact detector fires on **1.06 windows per hour** of ordinary home audio (13/4416 held-out windows; 8 of those were dishwashing). Red on every thud is about **25 false urgent alerts a day**. See §3.4 for the design. | `results/safety.json detectors.impact` | Design decision |
| F9 | **Crash then stillness catches 31.7%** (19/60) of held-out scenarios, because it waits 10 minutes and needs prior activity. | `results/safety.json scenarios` | Medium |
| F10 | **Activity labels: the model isn't the problem.** Swapping encoders was already tested on Kitchen20 cooking/washing/eating (balanced accuracy): CED-tiny 73.5, CED-small 66.7, AST 73.7, CLAP zero-shot 74.9. **Don't spend time swapping models.** What goes wrong is turning sound tags into activities, and showing labels we can't back up. | `HANDOVER-v3.2.md`, `results/kitchen_naming.json` | Guides §4 |
| F11 | **"Not sure" covers most of a real day**: 42% of windows in the TUT-SED real home, 80.9% on Kitchen20 tune. Most of the family's bar is grey. | `results/real_homes.json`, `results/sound_fill.json` | High (UX + trust) |
| F12 | **The write-up is 3,169 words.** The rule is one page (about 550 words). A cold Haiku judge scored us about 64/100 and called this the most damaging problem. | `docs/WRITEUP.md` | **Critical, cheap** |
| F13 | **The repo is private.** Judges get a 404 on the code link and on every GitHub link on /credits. Making it public needs Parth's explicit OK. `docs/AI-USAGE-LOG.md` names teammates, which breaks blind judging. | GitHub settings | **Critical, needs Parth** |

Priority order for tonight: **§3 (urgent alerts) → §5 (write-up to one page, humans) → §6 (video, humans) → §4 (activity reliability) → §7 (deploy, submit).**
§4 is last for the code agent because its gains are smaller and riskier per hour. The alerts are the demo, and the demo is the video.

---

## 1. Ground rules (don't skip)

- **Repo:** `ThoughtTaken27/Hackathon`, branch `main`. Two agents may be pushing (Parth's UI agent edits CSS/HTML and
  family/landing visuals). **Always `git fetch && git rebase origin/main` right before you push. Fast-forward only, never force.**
- **The UI agent owns** `web/public/css/*` (except a new `css/urgent.css` you may create), landing/how-sure/credits HTML, `fx.js`, `landing.js`, `chrome.js`, `ui.js`.
  You may edit: `safety.js`, `kettle/safety.py`, `kitchen.js` (safety and check-in parts), `family.js drawUrgent()` and a new push-enable
  control, `web/src/*`, `sw.js`, `model/safety.json`, `eval/safety.py`, `core.js` display mapping (§4). If you must touch a UI-owned file, keep the diff tiny and say so in the commit.
- **Python twin parity:** `kettle/safety.py` must give the same answers as `web/public/js/safety.js` on `web/test/safety_fixtures.json`
  (checked by `web/test/safety.test.mjs`). If you change engine rules, change both, then regenerate fixtures with
  `.venv-probe/bin/python tools/export_web_fixtures.py`.
- **Test-set discipline (the 15 "testing and honesty" points):** pick thresholds on dev clips only. **Write the gate in the
  results file or a PREREGISTER note BEFORE the first held-out run.** Run held-out once. If you rerun, say so in the results JSON
  (`process_note`), the way `results/safety.json` already does. Never round up, never cherry-pick.
- **No audio leaves the device, ever.** Only alert kind and time go to the server. Don't log raw scores to the server.
- Every number that reaches How sure, the write-up, or the video must come from a `results/*.json` file. Run `python -m eval.check_metrics` after changes.
- Health framing: "prototype, not medical advice" and **"not a replacement for a real smoke/CO detector or 911"** on any alert UI.
- Commit small. Add a row to `docs/AI-USAGE-LOG.md` for each change (no personal names; see F13).

## 2. Environment (Parth's Mac quirks; on your own machine, adapt)

- Python with torch + soundfile: `/Users/parth/Hackathon/.venv-probe/bin/python` (`.venv` lacks them). Elsewhere: `pip install -r requirements.txt` plus `soundfile torch`.
- Tests:
  ```bash
  cd web && npm test && cd ..                      # 142 pass at 408fb46
  .venv-probe/bin/python -m pytest -q tests        # 79 pass; run as `-q tests` (bare pytest picks up data/raw/kitchen20/tests and errors)
  .venv-probe/bin/python smoke_test.py             # PASS
  .venv-probe/bin/python -m eval.check_metrics     # 0 problems
  ```
- Dev server: `cd web && npm install && node dev.mjs`, which serves on 8787. If 8787 is taken, use `PORT=8790 node dev.mjs` and a separate `web/.data` folder.
- Seeding a test home through the API: POST `/api/households` → POST `/api/h/<id>/action {type:"consent"}` (kitchen key as Bearer) →
  POST `/api/h/<id>/events` (each event ≤ 600 s long, ≤ 24 h old). Delete afterwards: `DELETE /api/h/<id>`.
  A saved home in localStorage from a deleted test household makes `/family` say "This home isn't available"; clear it.
- e2e: `KETTLE_E2E_LISTEN_MS=... python web/test/e2e.py http://localhost:8787 web/.data/test/fake-kitchen.wav <out>`; on the Mac it needs `PLAYWRIGHT_BROWSERS_PATH=/Users/parth/Library/Caches/ms-playwright`.
- Embedding caches (527 AudioSet scores + embeddings per clip) live in `results/cache/*.npz`: `ced-tiny_dev`, `ced-tiny_esc50all`,
  `ced-tiny_nonspeech7k`, `ced-tiny_synth_alarms`, `ced-tiny_offlist`. `eval/beyond.py load()` reads them; `eval/safety.py sources()` builds the clip list.
- **Deploy (Cloudflare Worker, Parth's account):** only Parth's machine has the wrangler login. From a clean export:
  `git archive <sha> web | tar -x -C /tmp/kdeploy && cd /tmp/kdeploy/web && HOME=/Users/parth /Users/parth/.npm/_npx/c943b712072b77c4/node_modules/.bin/wrangler deploy`.
  A bare `npx wrangler` hangs or exits silently in that sandbox. Live site: https://kettle.parth-dev.workers.dev. **Deploying needs Parth's go.**
  Bump `CACHE` in `web/public/sw.js` whenever shipped JS/CSS changes, or phones keep the old build.

---

## 3. P0: urgent alerts that really work (target 6:05 to 7:30 PM CT)

Success test for the whole section, run by hand at the end: **on the dev server, open the family view on a phone (or a second browser) with
push enabled and the tab closed. Play a smoke alarm (real test button or §3.6 clip) next to the kitchen laptop. Within 15 s the phone shows
a red notification, and opening it shows a red banner with the time. Pressing "I'm OK" on the kitchen screen updates the banner to amber.**
Record that run on screen. It's the best 15 seconds of the video.

### 3.1 Fix F3 (CO dropped) and decide F7: 5 min
- `kitchen.js`: `const WIRED = ["smoke", "co", "fall", "fall_still", "scream", "help", "gunshot", "shout"]` (add the new types from 3.3/3.4 as you create them).
- `web/src/household.js SAFETY_TYPES`: add the same new types (`gunshot`, `shout`). The server rejects unknown kinds with 400.
- `family.js` uses `SAFETY_TEXT[a.kind]`, so add `TEXT.gunshot = "what sounded like a gunshot"` and `TEXT.shout = "shouting for a while"` in **both** `safety.js` and `kettle/safety.py`.
- F7: leave `concern: false` on (C6/C7/C9 off) unless you have time to wire "Worth a look" notes. **Write a comment saying it's deliberate**, and say so on How sure. Don't silently turn them on: they've never been checked end to end.

### 3.2 Fix F2: red at once, then ask: 25 min
New flow (UI layer only, so engine parity stays intact):
1. When the engine returns `{do:"checkin"}` for fall/scream/distress: **send the alert to the family right away**
   (`act("alert", { kind: a.type, at: a.at, checkin: "asking" })`), **and** show the "Are you OK?" screen on the kitchen device as now.
2. If the person presses **I'm OK**: send `act("alert", { kind, at: <same at>, checkin: "ok" })`. If **I need help**: `checkin: "help"`. If nobody answers: the engine's `timeouts()` already emits an alert with `since: c.at`, so send `{ at: since, checkin: "no_answer" }`.
3. Server (`household.js` `type === "alert"`): accept `checkin ∈ ["asking","ok","help","no_answer","none"]`. Id is `a${Math.round(at)}`; **if an alert with that id exists, update its `checkin` (and keep `seen`) instead of appending a new one.** Same `at`, same id: that's the whole trick.
4. Family banner (`family.js drawUrgent`), wording driven by `checkin`:
   - `asking` / `none` / `no_answer` / `help` → **red**: "Urgent · 6:42 PM · Kettle heard screaming." Second line by state: asking → "Asking on the kitchen screen now."; no_answer → "No answer on the kitchen screen."; help → "They pressed I need help."
   - `ok` → **amber**: "6:42 PM · Kettle heard screaming. They pressed I'm OK at 6:43." Keep it visible until marked seen.
   - Buttons: **Call** (tel: link if a phone number is in setup; otherwise leave it out) and **Seen**. Always show the line "Kettle is a prototype. It doesn't replace a smoke or CO detector or 911."
   - Also on the family day bar: a red tick at the alert time so it's visible later (reuse the stretch marker style; ask the UI agent if it needs CSS in their files).
5. Kitchen screen copy after alerting: keep "Are you OK?" with a countdown, but change the line to "**{Caregiver} has been told.** Press I'm OK to let them know you're fine."
6. Smoke, CO and gunshot: **no check-in at all**, straight to red (smoke/CO already do this).
7. Tests: add cases in `web/test/api.test.mjs` (alert update by same id; bad checkin → 400) and `web/test/fixes.test.mjs` (kitchen sends `asking` then `ok`). Run `npm test`.

### 3.3 Fix F1: real notifications (Web Push): 45 min
Follow `docs/PUSH-INTEGRATION.md` exactly; it lists the whole server contract. Summary:
1. **VAPID keys:** `makeVapidKeys()` once, stored in the `Codes` Durable Object storage (no env secret, nothing in git). Add `getVapid()` to the `Codes` class in `web/src/worker.js` and expose it to the router the same way `put/get/miss` are.
2. **Routes** in `web/src/router.js`: `GET /api/push/key` → `{publicKey}`; `POST /api/h/:id/push` (family role) body `{subscription}` → `validSubscription()`, dedupe by endpoint, keep ≤ 10 in household state (`s.push`); `DELETE /api/h/:id/push` `{endpoint}`.
3. **Send:** in the household DO, after storing or updating an urgent alert (states `asking`, `no_answer`, `help`, `none`; send `ok` as a normal-urgency update), call `sendPush` for every sub with
   payload `{ title: "Kettle: urgent", body: "Heard <text> at <time>. Open to see.", tier: "urgent", tag: "kettle-<id>", url: "/family?h=<id>", alertId, home }`.
   Run it inside `ctx.waitUntil(...)` so the kitchen's POST returns fast. Drop subs whose result says `gone`. **Never put the family key in the payload.** The URL has only the home id; the key stays in the page's localStorage/hash.
4. **Family page:** a clear "Turn on alerts" control near the urgent area (it must be a tap: `subscribe(publicKey)` then POST). Show its state: on / blocked / "iPhone: add to Home Screen first" (`pushSupport().why`). Add a **"Send a test alert"** button (server `type:"test"` alert, tier `test`) so the family can check it works. That's also the reliability proof in the video.
5. On family page load, handle `?ack=<alertId>` (mark seen, then `history.replaceState` to strip it). The sw.js `notificationclick` already builds that URL.
6. Also, when the family tab is **open**: on a new urgent alert, vibrate (`navigator.vibrate([300,100,300])`), set `document.title = "● Urgent · Kettle"`, and show `new Notification(...)` if permission is granted.
7. Tests: `push.test.mjs` already checks crypto. Add an api test that alert → `sendPush` is called with a fake `fetchImpl`. Manual check on Parth's Android Chrome (the PWA is installed there): notification arrives with the tab closed.
8. If push wiring isn't green by **7:30 PM**, ship 3.2 plus the open-tab vibration/title/Notification from step 6, and say on How sure "push is built but not yet switched on". Honest beats broken.

### 3.4 F4 + F5 + F8: gunshot, shouting, thud: 35 min
Do it in `eval/safety.py` the same way the other detectors are done (dev picks the threshold, held-out reported once):
- **Gunshot detector** `("gunshot", "Gunshot", [427, 428, 429, 430, 431], <positives>)`. Start the floor at 0.3. Confusers to report separately: fireworks/firecracker (432, 433), door slams, dropped pans, balloon pops.
  **Rule:** a gunshot hit in **1 window** with no TV/radio/music in the last 3 windows → **urgent at once, no check-in**. With media on → amber "Worth a look" (action-movie TV is the obvious false alarm; there are 60 "TV drama" negatives in the simulator to reuse).
  **Positives (verify the licence before use, credit it on /credits):** UrbanSound8K `gun_shot` class (374 clips, CC BY-NC 3.0, https://urbansounddataset.weebly.com/urbansound8k.html), or FSD50K's "Gunshot_and_gunfire" class (https://zenodo.org/records/4060432, per-clip CC licences). **Unverified:** whether a Hugging Face mirror allows downloading just that class through the datasets-server `/filter` API. Try it, but don't burn more than 15 min on data. ESC-50 has no gunshot class.
- **Shouting:** make `shout` count. **Rule:** shout hits in **3 separate windows within 60 s** with no media → urgent (with check-in, same as scream). A single shout stays nothing (people raise voices). Positives: AudioSet "Shout"/"Yell" don't come as audio here. If no clips are found in 15 min, keep the threshold set from false fires only (as now), and say "**catch rate not measured**" on How sure. Don't claim a number.
- **Thud (Parth asked for red):** a thud alone is about 25 false reds a day (F8), which is exactly the false-alarm problem he hates. Ship this instead, and tell Parth in one line why:
  - thud/crash/glass, then a cry, groan or scream within 60 s → **red at once** (today it's 30-60 s later via the check-in; with 3.2 it's immediate);
  - thud, then **no sound at all for 2 minutes** when the person was active in the 30 min before → **red** (today it's 10 min; change `FALL_STILL_S` 600 → 120 in **both** engines and rerun the scenario sim once, disclosed);
  - a thud alone → a small amber marker on the day bar ("a loud bang at 6:42"), **no notification**.
- After the changes: `python -m eval.safety`, which rewrites `results/safety.json`, `web/public/model/safety.json` and `web/public/data/safety.json`. Check that **ordinary home audio still gives 0 urgent / 24 h** (currently 0 over 12.3 h held-out). If it doesn't, raise the threshold on dev and say so.

### 3.5 Smoke alarm reliability (F6): 20 min
- Real smoke alarms are loud (around 85 dB at 3 m), so in a real kitchen they're usually at high SNR, where T3 works 25-26/30. The gap is reverb plus far rooms.
- Cheap wins: (a) also accept **`Alarm` (388) + `Smoke detector` (399) + `Fire alarm` (400) + `Beep` (481) together above threshold in 3 of the last 4 windows**, with a loud level (`db ≥ floor + 15`) as a second path. Pick the threshold on dev synth alarms + home audio. (b) Loosen T3 timing tolerances a little for echo (`near(segs, 0.35, 0.7)` → `0.3, 0.8`) **only if** dev false fires on the 2,000 ESC-50 clips stay ≤ 2.
- **Real measurement, needs a human, 10 minutes, highest value:** press the **test button on a real smoke detector** at home, 10 times, with the kitchen laptop at 2 m, then 5 m, then in the next room. Log caught/missed in `results/real_alarm_test.json`
  (`{n, caught, distance_m, notes}`). That turns "synthetic only" into a real-device number: big on testing/honesty and great on video.

### 3.6 Clean urgent UI checklist
- Kitchen device during an alert: full-screen red header "Urgent: smoke alarm heard", the time, "{Caregiver} has been told", big **I'm OK** and **I need help**, spoken aloud (it already uses `speak()`).
- Family: red banner on top of everything (`role="alert"`), red tick on the day bar, push notification, "Seen" button, state line (asking / no answer / OK / needs help).
- How sure: a short "Urgent alerts" table with caught / false alarms per day / data source / "synthetic" or "real" label for each alert type. Values from `results/safety.json` only.
- Put styles in a **new** `web/public/css/urgent.css` linked from family.html/kitchen HTML, so you don't collide with the UI agent. Follow Parth's UI rules: OKLCH colours, alpha borders, inner radius = outer radius − padding, no glow, no gradients, no pills.

---

## 4. P1: activity reliability, fewer and truer labels (target 7:30 to 8:15 PM, only if §3 is green)

Parth: "the classification should be limited... you just want to see what they have been doing and if everything seems okay."
Principle for judges and for him: **show a specific label only where we've measured that it's usually right. Everything else rolls up into an honest umbrella.**

### 4.1 Pre-register first (5 min)
Create `eval/PREREGISTER-DISPLAY.md` **before** any run: the new display map, the dev sets (SINS dev folds, Kitchen20 **tune** half, TUT-SED 2016 **dev** homes), the metric
(**wrong specific label shown**: share of windows showing a specific activity that the ground truth says is a different activity), and the gate:
**ship only if wrong-specific-label drops ≥ 30% relative and "kitchen activity caught" (any of cooking/washing/eating/kitchen) falls ≤ 3 points.**
Don't touch test halves tonight; they've been used 2-3 times already (disclosed in `results/kitchen_naming.json`).

### 4.2 The display map (all in `core.js`/`labels.py` display layer, model untouched)
Shown activities, at most 6, plus states:
- **Cooking**: only when cooking sounds win ≥ 10% of the stretch's windows (rule 2c already does this).
- **Washing up**: only when the stretch also has the **running water** sound name (head precision 95.7%) in ≥ 1 window; otherwise → Kitchen activity.
- **Eating**: **fold into Kitchen activity**. Cutlery clatter during cooking was Parth's live "eating" false reading, and we can't tell eating apart reliably.
- **Kitchen activity**: umbrella (already exists).
- **Talking / TV**: keep.
- **Some activity**: also used for **"Not sure" windows that are clearly above the room's quiet level** (`db ≥ floor + 3`). Honest, because something happened, and it shrinks the grey "Not sure" share (F11). "Typing" folds in here unless a family check uses it.
- States: Quiet, Not sure (only when level is ambiguous), Not listening, Paused, Private, **Urgent** (red).
- Keep the 8 shown sound names in the details card only (kettle, chopping, running water, cupboards/drawers, timer beep, talking/TV, typing, footsteps); they passed the precision ≥ 90% bar.

Mirror the same map in Python (`kettle/labels.py`, `kettle/timeline.py`, `kettle/view.py`) so parity tests stay green. Update `web/test/parity-web.mjs` expectations only through the fixture exporter.

### 4.3 Measure and report (15 min)
Write `eval/display.py` → `results/display.json`: per shown label, precision on each dev set before/after, the "Not sure" share before/after, and kitchen-activity recall before/after.
If the gate passes, ship and put one row on How sure ("We now show fewer labels: wrong specific labels X% → Y% on dev clips; N windows"). If it fails, **don't ship**, and report it anyway. "Measured, not shipped" is already our pattern and judges like it.

### 4.4 What NOT to do tonight
- Don't swap the encoder (F10 shows no gain). Don't train a new activity head on test data. Don't add sound classes (pets, doorbell, phone were cut on purpose).
- Don't rerun `eval.sound_head` or `eval.real_homes` "to improve" them: those test sets are spent.
- The single best accuracy evidence still missing is **one labelled real-kitchen recording** (protocol: `docs/REAL-KITCHEN-PROTOCOL.md`, scorer `eval/own_kitchen.py --timeline`). 20 minutes of cooking + washing up, with consent from everyone in the room, labelled by hand with start/end times. If a human can do it by 7:45 PM, it beats everything in §4.2 for points.

---

## 5. Write-up to one page (humans, 45 min, start now, parallel to §3)

The cold judge's top doubt. Rules from the brief: one page; problem, approach, how well it worked; cite every dataset/model/tool; list AI tools; "prototype, not medical advice"; report weak results too. Round 1 is blind: **no names, no school.**

Target about 550 words, using these headings (guide template):
1. **Problem and person** (2 sentences + the 28% statistic with source). Say the persona is illustrative, then name the real user group plainly: adult children of a parent living alone with early memory loss.
2. **What we built** (3 sentences): a spare phone/laptop names household sounds every 10 s on the device, keeps no audio, sends only labels; the family sees a calm day bar and checks ("kitchen activity by lunch"); **urgent sounds (smoke/CO alarm, a crash then a cry, screaming, gunshot) turn red and notify at once.**
3. **How it works**: CED-tiny (AudioSet-pretrained) on device via ONNX → frozen SINS-trained activity head → stretch naming rules → per-sound logistic heads (8 of 15 pass precision ≥ 90%) → safety detectors + sequence engine. One small diagram.
4. **Results** (table): held-out DCASE 2018 Task 5: 84.1 macro F1 [74.4, 86.7], n = 7,791 clips / 91 sessions, vs published baseline 85.0/83.1 (not directly comparable); Apple's classifier 31.8 on the same clips; kitchen-activity moments caught 87.8% raw; urgent-alert scenario rates from `results/safety.json` (scream 83.3%, smoke during cooking 68.3%, crash+groan 65.0%, **0 false urgent alerts in 12.3 h of ordinary home audio**). Update from new results files if §3/§4 changed them.
5. **Where it fails** (3 bullets with numbers): real-home TUT-SED: washing-up windows named as kitchen activity 53%, "Not sure" 42%; Parth's own kitchen test (metal pots read as eating → fixed with stretch naming, before/after counts from `results/kitchen_naming.json`); smoke alarms tested on synthetic tones only (or the real test-button number if §3.5 was done); no real fall recordings.
6. **Privacy and limits**: no audio stored (privacy check 0 files), parent consents and can pause/hide labels; not a replacement for detectors or 911; prototype, not medical advice.
7. **Credits + AI tools**: one line linking /credits. Claude Code (Anthropic), Aside, any others from `AI-USAGE-LOG.md`.

Move everything else (method detail, rule list, pre-registrations) into `docs/TECHNICAL.md` and link it. Export to PDF and **check it's one page.**

---

## 6. The 2-minute video (humans; record 8:00 to 8:45 PM, upload by 9:00 PM)

Script lives in `docs/VIDEO.md`; this replaces its order to lead with the strongest, most "only we can do this" moment.
A real teammate's voice, no AI voice, no faces, no names, **crop the address bar** (it shows "parth-dev"), or record on localhost.

| Time | Shot | Say (short, natural) |
|---|---|---|
| 0:00-0:08 | Kitchen. Press the real smoke detector's **test button**. Cut to the phone: red Kettle notification arrives. | "That's a smoke alarm in Mom's kitchen. Two seconds later her daughter's phone knows, from three hours away." (use the measured delay) |
| 0:08-0:20 | Family view: red banner, then calm day bar | "More than one in four Americans over 65 live alone. Kettle turns a spare phone or laptop into a calm timeline of their day, from sound alone, and it never records audio." |
| 0:20-0:32 | How sure top table | "On held-out recordings it had never heard, scored once: 84 macro F1. Apple's built-in sound classifier scores 32 on the same clips." |
| 0:32-0:55 | Split screen, live: stir a pan, run the tap → Cooking / Washing up appears on the phone; check turns Met | "Every ten seconds it names what it hears and forgets the sound. Only the label leaves the kitchen." |
| 0:55-1:10 | Kitchen: Pause, and "What can be seen" untick Talking/TV; phone shows it honestly | "The parent says yes first, can pause it, and decides what's shared." |
| 1:10-1:30 | Urgent alerts table on How sure; then a scream clip → kitchen "Are you OK? Asha has been told" → press I'm OK → phone banner turns amber | "Screaming, a crash then a cry, smoke or CO alarms, and gunshots go red at once. Ordinary days: zero false urgent alerts in twelve hours of real home audio." (only if still true in results) |
| 1:30-1:48 | How sure failure rows | "Where it fails: in a real home, 42% of the day is still 'not sure', and our alarm tests are mostly synthetic. We show that instead of hiding it." |
| 1:48-1:55 | Calm day bar, "Prototype, not medical advice" | "Kettle. Know the day went okay, without a camera." |

Rules: every spoken number must match a results file (`eval.check_metrics`). Use real sounds, not a phone speaker (speaker audio reads as TV and gets gated as media, including for gunshot/scream). **Do a rough full take first** as backup. Trim to ≤ 1:58. Upload **unlisted** to YouTube and open the link in a private window to check it plays.
If the live alert doesn't work by 8:15 PM, film the landing "Two screens" sample day instead and say "a sample day, real recordings through the same model". Don't fake a notification.

---

## 7. Deploy, check, submit (8:15 to 9:30 PM CT)

1. `git fetch && git rebase origin/main`; all four test commands green; `eval.check_metrics` 0 problems; grep the diff for secrets (`sk-`, `AIza`, `BEGIN PRIVATE`, `wrangler`).
2. Bump `CACHE` in sw.js. Push fast-forward to `main`.
3. Parth (or whoever has the wrangler login) deploys from a clean `git archive` export (§2). Then check `/`, `/family`, `/how-sure`, `/credits`, `/sw.js` return 200, and run the §3 success test once on the live site.
4. **Parth decides (needs his OK):** make the repo public (or give judges a public mirror/Colab), and genericize names in `docs/AI-USAGE-LOG.md` first.
5. Submission checklist, read aloud, one person submits: code link opens logged out · README has the one-line identity, how to run, results, limits, credits · write-up is one page (PDF) · video under 2:00, unlisted, plays logged out · AI tools listed on the form · "prototype, not medical advice" · confirmation screenshot + email saved.
6. **Resubmits:** per the earlier read of the rules, the latest version is judged and resubmits are allowed. **Submit a working version by 9:30 PM even if §4 isn't done**, then resubmit before 10:30 if something better lands. Re-check that rule in the organizer emails before relying on it.

---

## 8. Where we stand and what moves the needle (honest read)

Rubric (Round 1, 100): technical 30, originality 20, impact + track 20, testing + honesty 15, write-up + video 15. Finals = 70% of final rank, Round 1 = 30%.

| Line | Now (cold judge, Haiku, ~5:45 PM) | Main reason | Fastest lift |
|---|---:|---|---|
| Technical execution /30 | 22 | Runs in browser, but alerts don't notify, and no real-kitchen test | §3 working end to end + live alert in video |
| Originality /20 | 12 | Known technique; the angle (consent, labels only, remote family) is lightly argued | Say "why a chatbot can't do this": it can't hear the kitchen, and we never send audio |
| Impact + track /20 | 11 | Invented persona; "reports activity, not intent" reads weak for health | Lead with urgent alerts (smoke, fall, scream); real user group stated plainly |
| Testing + honesty /15 | 11 | Strong pre-registration and failure reporting; numbers not from a kitchen | Real smoke-detector test (§3.5) and/or 20-min real kitchen recording |
| Communication /15 | 6 | Write-up is ~6 pages; video not recorded | §5 and §6; probably the cheapest +7 on the board |
| **Total** | **≈ 62-64** | Earlier judge sims (Sat): ≈ 71-74 | Realistic tonight: **≈ 75-80** if §3, §5, §6 land |

My judgment, not data: as-is we're a mid-pack Round 1 entry, because the write-up and the missing video sink it. With §3 + §5 + §6 done well, a top-10 finals spot is plausible, roughly **40%** (unknown field size; this is a guess). Gold is a long shot tonight, maybe **10%**, and mostly decided in finals Q&A, where our pre-registration and "measured, not shipped" record is a real edge with research judges.
The single highest-value hour left is **communication (§5 + §6)**, not more model work.

Finals Q&A to drill (20 pts): How do you know the alarm detector works? (synthetic + real test-button numbers) · What makes it fail? (TV/speaker audio, far rooms, quiet falls) · Why not ChatGPT? (it can't listen 24/7 on device; we never send audio) · How did you split? (by session/home; test used once) · What's the harm if it's wrong? (false reds erode trust, which is why a thud alone isn't red; missed reds, which is why we say it doesn't replace a detector) · What did you build this weekend? (everything after kickoff; see CREDITS).

---

## 9. State at handoff

- `origin/main` = **45c3ec8** at ~6:00 PM CT (UI agent's latest push, also deployed live; sw.js CACHE is now `kettle-v31-5`). Fetch first anyway.
- The UI agent said its next edits stay in index.html, js/landing.js, css/polish.css, img/ and credits.html only.
- I wrote **no code changes**. Only this file was added (branch `handover-v3.5`, plus a copy in Parth's Downloads).
- A parallel agent is doing UI polish (fonts/animation) on Parth's machine. Its files are listed in §1.
- Open decisions for Parth: repo public; names in AI-USAGE-LOG; deploy go; thud design (§3.4); whether to turn on C6/C7/C9 notes.
