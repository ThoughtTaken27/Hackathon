# Kettle v3.1 handover: what is built, what is left, and exactly how to finish it

Written Sun 15 Nov 2026, about 11:40 AM CT, at the moment the previous Claude session ran out of usage. `main` is at the
commit that adds this file. Everything listed under "Done" is committed, pushed and tested. Everything under "To do"
is not started unless it says "partly".

The source plan is the 23-page PDF "Kettle v3.1: Hard-Test Report and Build Plan for Claude" (the user uploaded it to
the previous session; ask the user to attach it again if you need the original). This handover restates every item of
that plan so you can work from this file alone. Plan item ids (E1, S3, C1, F5, M7, 3.2, ...) are kept so you can map
back to the PDF.

The user's instruction for the whole job: implement **every** item in the plan, plus quality-of-life improvements,
leaving nothing out. Also already done: the landing page's sample-day switch had an off-centre white hover pill.

---

## 0. Read first: the ground rules (breaking one can disqualify the team)

From `AGENTS.md` (read it in full; it is the team's operating manual) and `SETUP.md`:

1. **Never re-run the held-out test** (`python -m eval` on the eval split) and **never edit or retrain `models/head.json`**
   (frozen; sha256 `fa5de76a…`, theta 0.66, novelty threshold 28.15). The plan's S6 ("retrain the 9-activity head on more
   homes") conflicts with this rule. Do S6 as a **measurement only** (section 3, S6).
2. **Numbers only come from results files** written by scripts. Never type a number into the UI or docs by hand.
   `python -m eval.check_metrics` checks this and must report `0 problems`.
3. **No tuning on held-out data.** Pick thresholds on development splits and report once on held-out splits. If you look at
   held-out results and then change something, say so in the results file (see `process_note` in `results/safety.json`).
4. **No secrets in git.** No API keys are needed by judges. Web Push VAPID keys must be generated and stored by the server
   at runtime (Durable Object storage), never committed. Scan diffs before each commit:
   `git diff --cached | grep -E "sk-|AIza|BEGIN PRIVATE|ghp_|key="`.
5. **JS and Python must agree.** `web/public/js/core.js` is a line-for-line port of the Python `kettle/` timeline, rules and
   view. When you change a rule in one, change the other, then regenerate the fixtures and keep parity green.
6. Every screen says "Prototype, not medical advice". Safety screens also say "Not a replacement for 911 or a medical alert pendant."
7. **Audio never leaves the device.** Only labels, scores and alert types are sent.
8. Credit every dataset, model and AI tool: add rows to `docs/DATA-SOURCES.md` and `docs/AI-USAGE-LOG.md`. Add an
   explain-back to `docs/EXPLAIN.md` for each new module, and a row to `docs/DECISIONS.md` for each design choice.
9. Never force-push. Push to `main` only when the user asks (they asked for this push). Pull with `git pull --rebase origin main` first.
10. Times are Central (CT). Hard close is Sun 10:59 PM CT; the submit target is 9 PM CT. Freeze per `AGENTS.md` was 1 PM;
    the user explicitly asked for the full plan, so keep going, but keep `main` always green.
11. The Cloudflare deploy (`cd web && npx wrangler login && npx wrangler deploy`) needs a person to log in and Parth's OK.
    The live site https://kettle.parth-dev.workers.dev runs an older version until someone deploys.

Team: Shaurya (the user), Parth (repo owner and Kettle lead), plus one more. The cap is 3 registered members.

---

## 1. How to work (the process the previous session used)

### Environment
- Repo: `/home/user/Hackathon`. Use **`.venv/bin/python`**: the system python has no soundfile or onnxruntime.
- Web app: `web/`. Start the local server with `cd web && node dev.mjs` (http://localhost:8787). It has no dependencies,
  keeps households in memory and saves them to `web/.data/dev.json`.
- Playwright: Chromium is preinstalled.
  - Node: run scripts with `NODE_PATH=$(npm root -g) node script.js` and `require('playwright')`.
  - Python e2e: set `KETTLE_CHROME=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome`.
  - Never run `playwright install`.
- Local mic replay: on localhost, `?qamic=cooking` plays `web/public/_qa/cooking.flac` (git-ignored) in place of the
  microphone. See `listen.js` `qaClip()`. Put more test clips there (smoke alarm, crash, scream) for the live checks.
- Scratch files go to `/tmp/claude-0/-home-user-Hackathon/60d51b16-ed84-506e-b815-87c9e6d8b169/scratchpad/` or your own session's scratchpad.

### The test and check commands (run all before every commit)
```bash
cd /home/user/Hackathon && .venv/bin/python tools/export_web_fixtures.py      # regenerates web/test/fixtures.json + sample-days.json
.venv/bin/python tools/export_safety_fixtures.py                               # regenerates web/test/safety_fixtures.json
cd web && npm test                                                             # node --test on the explicit file list in package.json
cd .. && .venv/bin/python -m pytest -q                                         # 75 tests
.venv/bin/python smoke_test.py                                                 # < 60 s
.venv/bin/python -m eval.check_metrics                                         # 0 problems
.venv/bin/python web/test/e2e.py http://localhost:8787 <fake.wav> <outdir>     # full browser flow (needs dev server)
```
- `node --test test/` does **not** work on Node 22. List files explicitly in `web/package.json` "test".
- Last known state: 129 web tests pass, 4 skipped on purpose (see the lint PENDING list below), 75 Python tests pass,
  smoke test passes, numbers check reports 0 problems.

### Working style that worked
- Plan, then build in small steps. Run tests after each step, commit locally often, push when green.
- For independent chunks, the previous session used background sub-agents (Sonnet), each told exactly which files it
  owns and which it must not touch. Examples: data download and embedding, the Web Push crypto module, neutral names
  and setup. Always read and verify their output.
- Use `python3 - <<'EOF' ... EOF` scripts with `assert old in s` for exact multi-line edits to the big one-line-heavy JS
  files. `core.js` and `kitchen.js` have very long lines, so the Edit tool's exact matching is fiddly.
- Screens use `el()`, `$()`, `api()`, `toast()` and friends from `web/public/js/ui.js`. Read that file before UI work.
- Cache-busting: the HTML pages load assets with `?v=w4`. If you change CSS or JS that browsers may have cached, bump
  to `?v=w5` everywhere, **and** update `web/public/sw.js`'s precache list and its `CACHE` name.

---

## 2. Done (committed and pushed)

### 2.1 Landing page pill fix (the user's small request)
- `web/public/js/landing.js` `moveInd()` sizes the white sliding pill from the chosen button's own `offsetHeight`,
  `offsetLeft` and `offsetTop`, so it is centred at 44 px tall and on any wrapped row. A ResizeObserver also watches
  every button, plus a window resize listener.
- CSS: `web/public/css/landing2.css` `.lx-seg .ind` uses `top:0`, `height:44px` and transitions height.
  `web/public/css/landing.css` `.lx-seg button` uses `display:inline-flex; align-items:center`.
- Checked by screenshot at 1280 and 390 px wide.

### 2.2 Safety layer, Workstream E (detectors, alarm patterns, sequence engine)
- **`web/public/js/safety.js`** (browser, on the listening device only). Exports:
  - `prepareSafety(cfg)`
  - `detect(cfg, audiosetScores)` returns `{scores:{id:max}, hits:[ids ≥ tau], media:bool}`
  - `envelope(wave, sr=16000, frameS=0.05)` returns dB per 50 ms of the first-differenced signal (a cheap high-pass)
  - `alarmPattern(env)` returns `{t3, t4}`, the NFPA 72 cycle counts. Beeps must be steady in level (within 6 dB).
  - `newEngine()`
  - `step(st, w, {urgent, concern, paused, smokeWhilePaused})`, where `w = {t, hits, scores, media, pattern:{t3,t4}, db, floor, kinds, label}`
  - `timeouts(st, t)`, `answer(st, t, "ok"|"help")`, `help(st, t)` (button U6), `askStillness(st, t)` (U7)
  - `coughConcern(days[], today)` (C11)
  - `isActive`, `TEXT`, `CHECKIN_S`
  - Actions returned:
    - `{do:"alert", tier:"urgent"|"concern", type, at, since?, text, checkin?: "no_answer"|"ok"|"help", evidence:{scores}}`
    - `{do:"checkin", rule, type, at, deadline, text}`
  - Rules:
    - **U1 smoke**: a smoke-detector score in 2 of the last 3 windows, or T3 ≥ 2 in one window. Fires at once; works while paused if the person opted in.
    - **U2 CO**: T4 in 2 separate windows (10 s or more apart) within 40 s.
    - **U3 fall**: an impact or glass hit (no media), then within 60 s a distress voice or scream gives a 60-s check-in.
      Or 10 min of stillness (2 stray active windows allowed) after it, when active in the previous 30 min, gives a check-in.
      Kitchen sounds or cooking within 2 min cancel it (the dropped-pan case).
    - **U4 scream**: 2 separate scream windows in 2 min, or a scream plus distress, gives a 30-s check-in. With TV, radio or music in the last 3 windows it becomes a concern `scream_tv` instead.
    - **U5 distress**: 3 or more separate distress windows in 5 min with no cooking gives a 60-s check-in.
    - **U6**: `help()`.
    - **U7**: `askStillness()`, then a timeout gives Urgent `stillness`.
    - Check-in answers: "ok" gives a concern (C8, "said they were OK"); "help" gives Urgent help; a timeout gives Urgent with `checkin:"no_answer"`.
  - Device concerns:
    - **C6 stove**: cooking kinds (`frying`, `kettle`, `boiling`) at least every 3 min for 40 min, with no other kitchen kind or footsteps.
    - **C7 beep**: the beep detector or a `timer` kind repeating for 5 min.
    - **C9 water**: the `tap` kind in 80% of windows for 20 min.
  - Cooldown is 10 min per type. Smoke clears after 5 min without smoke.
- **`kettle/safety.py`**: the line-for-line Python twin (`detect`, `envelope`, `envelope_np` (numpy, for eval), `alarm_pattern`,
  `new_engine`, `step(st, w, urgent, concern, paused, smoke_while_paused)`, `timeouts`, `answer`, `help_button`,
  `ask_stillness`, `cough_concern`).
- **`tools/export_safety_fixtures.py`** writes `web/test/safety_fixtures.json`: 28 hand-made scenarios, each Urgent rule's positive case plus the plan's hard negatives:
  - TV drama scream
  - dropped pan then cooking
  - microwave beep
  - doorbell
  - paused
  - safety turned off
  - one scream in overlapping windows
  - crash with nobody active before

  It also writes 24 envelope pattern cases (t3, t4, timer, none), an envelope wave case, a detect case and cough cases.
  Run it after any change to `safety.py`, `safety.js` or `safety.json`.
- **`web/test/safety.test.mjs`**: the JS engine reproduces every Python answer exactly. 32 tests pass.
- **`web/public/model/safety.json`**: the detector thresholds the app uses, **written by `eval/safety.py`**. Do not hand-edit it.
  Detector ids: `smoke_alarm [399,400]`, `beep [481,398,395]`, `scream [14]`, `shout [8,11,13]`, `distress [38,25,22,24]`,
  `impact [460,466,469,358]`, `glass [443,470,441]`, `fire [298,299]`, `siren [396,397,322]`. Media is `[524,525,137,267,268,270]`.

### 2.3 Safety evaluation, E7/E9 (`eval/safety.py` writes `results/safety.json` and `web/public/data/safety.json`)
- **Data** (new caches committed; audio git-ignored under `data/clips/`):
  - `eval/esc50_all.py` → `results/cache/ced-tiny_esc50all.npz`: all 2,000 ESC-50 clips (50 categories × 40, folds 1–5).
  - `eval/nonspeech7k.py` → `results/cache/ced-tiny_nonspeech7k.npz`: Nonspeech7k **test split**, 725 clips. Classes:
    crying 205, breath 160, laugh 140, cough 70, screaming 70, yawm 50 (sic), sneeze 30. CC BY 4.0 per Zenodo.
  - `eval/synth_alarms.py` → `results/cache/ced-tiny_synth_alarms.npz`: 960 synthetic NFPA 72 alarms (t3, t4, timer, none
    × 60 seeds × SNR 20/10/0/−5 dB) over pink noise plus benign ESC-50 backgrounds, with echo on odd seeds. `synth(kind, seed, snr)` is deterministic.
  - Existing: SINS dev `results/cache/oof_dev.npz` (AudioSet scores of 8,920 clips with folds 1–4 and true activity labels).
  - Rows for these are in `docs/DATA-SOURCES.md`.
- **Splits**: development = SINS folds 1–2, ESC-50 folds 1–3, Nonspeech7k sha1(file) half 0, synthetic seeds 0–29.
  Held-out = the rest.
- **Threshold rule**: tau = max(floor, 99.5th percentile of development negatives). Floors: smoke 0.35, beep 0.2, scream 0.1,
  shout 0.3, distress 0.1, impact 0.1, glass 0.3, fire 0.3, siren 0.2. `process_note` in `results/safety.json`
  discloses that the floors for smoke, glass and fire were raised after a first held-out run. A development-split simulator
  run (`scenarios_dev`) is reported next to the held-out one.
- **Held-out results**: read them from `results/safety.json`. The last run's printout:
  - scream 29/32 caught; distress 71/102; glass 13/16; siren 16/16; fire 4/16; smoke detector score alone 10/240
    (the pattern detector does most of the work); impact and shout have no positives ("not measured").
  - On ordinary SINS home audio: false fires per hour ≤ 0.24 for all detectors except impact at 1.06 per hour.
    Impact never alerts alone.
  - T3 pattern found in 25–26 of 30 at 20 and 10 dB SNR, 1–2 of 30 at 0 and −5 dB. T4 found in 5–12 of 30.
    Timers never read as T3. On 2,000 real ESC-50 clips the pattern fired T3 on 2 clips and T4 on 20 clips (single
    windows; U2 needs 2 separate windows).
  - Scenario simulator, 60 timelines each, held-out clips, nobody answers:
    - Positives: crash then groan 39/60; crash then stillness 19/60; smoke alarm during cooking 41/60; screaming 50/60; repeated crying 43/60.
    - Hard negatives: TV drama with screaming, dropped pan then cooking, timer beeps, knocks/dogs/laughter and a busy kitchen all 0/60.
    - **12.3 h of ordinary held-out home audio: 0 Urgent, 0 check-ins, 0 concerns.**
  - Development-split simulator: similar; knocks/dogs/laughter 2/60.
  - Limits written into the results: no real falls (the crash is glass), synthetic alarms, no shout-for-help clips, no real kitchens.
- **Known weakness to improve (honestly, on development data only)**: smoke alarms at 0 dB SNR; crash then stillness at 19/60.

### 2.4 Concerns, Workstream C (partly: the JS logic is done; the Python twin and UI are not)
- `web/public/js/core.js`:
  - `MAX_RULES = 8`.
  - New rule type `{type:"concern", cid, ...params}`; `validateRules` calls `validConcern`; `activity_by` is an alias of `any_by`.
  - `any_by`'s title is now "Activity by …" (Python updated too).
  - `CONCERNS` defaults: too_quiet {hours 4, from 08:00, to 20:00, escalate 6}, no_meal {14:00}, tv_long {8}, tv_night {1},
    night {30 min}, stove, beep, water, device_off {2}, cough, unusual.
  - `DEVICE_CONCERNS = [stove, beep, water, cough]`. These show "watching" until an alert of that type arrives today, then "note".
  - `concernTitle(r)`, `concernOne(...)`. States: `ok | note | cant_tell | not_yet | watching`. A note can carry `escalate:true`
    (too_quiet past 6 h and still going: the kitchen should call `safety.askStillness`).
  - `statusStrip({alerts, rules, coverage, heartbeat, day0})` returns `{level: urgent|look|cant_tell|ok, text, n}`.
    Never green when coverage is under 75% or Kettle isn't listening.
  - `today()` now returns `out.alerts` (from `s.alerts`, with `at_text`) and `out.status`, and passes
    `ctx={alerts, days, hop}` to the rules.
  - **TV fix S7/F2** in `ruleTv` (JS **and** `kettle/rules.py`): when not_sure plus talk_or_tv time is over 25% of the listened time since 6 AM,
    the check says "Can't tell: Kettle couldn't name the sound for X of the Y it listened today." It no longer says "No TV heard today".
- `kettle/rules.py`: MAX_RULES 8; the concern type dispatches to **`kettle/concerns.py`, which does NOT exist yet**
  (imported lazily, so nothing breaks today). **Write it next** (section 3, C).

### 2.5 Web Push and PWA, Workstream N plus M1 (partly: modules done, not wired into the server or screens)
- `web/src/push.js` (Workers and Node, WebCrypto only):
  - `makeVapidKeys()` returns `{publicKey, privateJwk}`.
  - `vapidHeaders(endpoint, keys, subject, now)` builds an ES256 JWT.
  - `encryptPayload(sub, bytes)` uses RFC 8291 aes128gcm. **It matches the RFC's Appendix A vector byte for byte.**
  - `sendPush(sub, obj, keys, {ttl, urgency, fetchImpl})` returns `{ok, status, gone}` and never throws.
  - `validSubscription(sub)` allows only these push hosts: fcm.googleapis.com, mozilla, web.push.apple.com, notify.windows.com, push.apple.com.
  - Also exports `b64uEncode` and `b64uDecode`. Tests are in `web/test/push.test.mjs`.
- `web/public/sw.js`:
  - Offline shell precache with the `?v=w4` URLs; network-first HTML; cache-first `/model/` and `/vendor/ort/`; `/api/*` is never cached.
  - Push handler with `requireInteraction` and vibration for urgent; the action "I've got it" opens `data.url` with `?ack=<alertId>`.
  - `CACHE = "kettle-v31-1"`.
- `web/public/js/pushclient.js`: `pushSupport()` (detects iOS needing the Home Screen), `registerSW()`, `subscribe(vapidKey)`,
  `currentSubscription()`, `unsubscribe()`.
- `web/public/manifest.webmanifest`: dark theme, neutral description, a `/listen` shortcut.
- `docs/PUSH-INTEGRATION.md`: the server contract, written by the sub-agent. Read it.

### 2.6 Part 3, any person and any room (partly: helpers and setup done; screens and server not yet)
- `web/public/js/people.js` (pure):
  - Data: `RELATIONS`, `RELATION_LABELS`, `NAME_CHIPS`, `DEFAULT_NAMES`.
  - `ROOMS` (kitchen, living, bedroom, hallway, bathroom, home, other). Each has `name`, `label`, `showsActivities`, `showsSounds`,
    `sounds[]`, `defaultChecks[]`, `teach[{c,head,body,s}]`, `placement[4]`, `privacy`, and `measured` (true only for the kitchen).
  - `normaliseNames(n)`, `personName(names,{mid})`, `possessive(name)`, `roomName(room)`, `place(names, room, viewer, {mid})`,
    `caregiverName(names, viewer)`.
  - **Caution:**
    - `ROOMS[*].defaultChecks` use `{type:"concern", id:"no_meal"}`. `validConcern` accepts `r.cid || r.id`, so this works, but prefer `cid`.
    - `ROOMS[*].sounds` ids are plan names (doorbell, music, talking, alarm_clock, knock, keys); most don't exist yet in `kinds.json`. Align them when S1 lands.
- `web/public/js/start.js`:
  - Setup asks "Who is this for?" (6 chips), "What do you call them?" (empty input, name chips) and "Where will the device listen?" (rooms; Other asks for a custom name; Bathroom shows a safety-only notice).
  - "Myself" changes the caregiver question.
  - POST `/api/households` sends `{parent ("" when unnamed), relation, room:{type,name}, caregiver, tz, as}`.
    **The server ignores relation and room today** (see 3.P below). `saveHome` also stores relation and room.
- Landing hero:
  - The hero is "Know the day went okay, in any room. Without a camera."
  - Neutral copy; no gendered pronouns above the FAQ.
  - A persona switcher changes `#lp-title` via `place()`.
  - The sample-day tag reads "Invented example".
- Tests:
  - `web/test/people.test.mjs` covers every relationship × room × viewer.
  - `web/test/lint-words.test.mjs` is the plan 3.7 string lint for he/she/his/him/her, Dad and Mom.
    `PENDING = ["js/core.js","js/kitchen.js","js/family.js","index.html"]` are **skipped until you neutralise them: remove them from PENDING as you finish each.**

---

## 3. To do (in this order; it is the plan's own priority order)

Each item says the files, the exact behaviour and the done-check. "Twin" means: mirror it in Python and add a shared fixture.

### C. Finish the concern tier (P0)
1. **`kettle/concerns.py`**: a line-for-line port of the JS `CONCERNS`, `concernTitle` (as `title`), `validConcern` (as `validate`),
   `concernOne` (as `one(r, blocks, now, day0, tz, ctx)`) and `statusStrip`. Use `rules._one` and `rules._tv` for no_meal and tv_long,
   and the helpers `_clock`, `clock_range`, `_dur` and `unheard`.
   Watch the JS details: `clock(day0 + lo, 0)` (offset 0), the `usual` range regex that collapses "7:10 AM–8:20 AM" to "7:10–8:20 AM",
   `secOfDay`, `overlap()`, and the `heardBlock` definition (states activity (not absence), talk_or_tv, not_sure, private).
2. **Shared fixtures**: add a `concerns` section to `tools/export_safety_fixtures.py`, or a new `tools/export_concern_fixtures.py`.
   Build synthetic block lists for each C-rule (positive and negative): 9 h of TV; 14 h quiet after breakfast; activity at 2–3:30 AM;
   TV 1–3 AM; not listening 3 h at midday; a 7-day `days` history with breakfast 7:10–8:20 and today at 10:40; no meal by 2 PM;
   a TV-only day with 86% not-sure (must say Can't tell). Expect the Python output; test JS equality in a new
   `web/test/concerns.test.mjs`, added to package.json.
3. Python `view.today()` must also pass `ctx` and produce `alerts` and `status` like JS (parity fixtures only compare
   heartbeat, summary, blocks and rules; keep it that way or extend `strip()` consistently).
4. **`tallyDays`** (`web/src/household.js`): add a `night` count (windows with a heard activity whose local time is 00:00–05:00) and a `first`
   field (first heard activity of any kind). Keep `meal`. Raise the kept days from 9 to 15 (for the 2-week doctor summary, M9).
5. **Checks editor** (`family.js` `fields()`):
   - Replace the hard-coded `3` with `MAX_RULES` (it appears 3 times: `add-rule`, `disabled`, presets).
   - Add a "Worth a look" group with a toggle per concern and its number inputs (hours, time, minutes), using `CONCERNS` defaults.
   - Presets: "Too quiet for 4 h", "No meal by 2", "TV over 8 h", "Up at night", "Stove left on", "Water left running", "Device off 2 h", "Unusual day".
6. **New homes get room defaults**: in `household.create`, set `s.rules` from `ROOMS[room.type].defaultChecks`. Map `activity_by` to
   `kitchen_by` for kitchen rooms and `any_by` otherwise, and `{type:"concern", id}` to `{type:"concern", cid}`. Then validate.
   Old homes keep their rules.
- Done when: `npm test` and pytest are green, the new concern fixtures match, and the family UI can add, edit and remove concerns.

### E-UI. Kitchen (listening device) safety wiring (P0)
Files: `web/public/js/listen.js`, `kitchen.js`, `kitchen.html`, `app.css`.
1. **5-s hop (S4)**: `listen.js` `HOP_S` becomes 5 for detection.
   - Keep sending **one activity label per 10 s** to the server: in `kitchen.js` `onWindow`, queue only every second window
     (the same pattern teach-mode uses: `w.end - lastSent >= 10 - 0.5`).
   - Run `safety.step` on **every** window.
   - `staleS(hop)` uses the household `hop` (server state `hop: 10`); keep the server at 10.
2. **Detection in `listen.js classify()`**:
   - Also return `det = detect(safetyCfg, out.audioset.data)` and `pattern = alarmPattern(envelope(wave))`.
   - Load `/model/safety.json` in `loadModel` (add it to the `Promise.all` list) and `prepareSafety` it.
   - `envelope` on 160,000 samples is cheap. For speed, compute it in the worklet or just in JS.
3. **Engine in `kitchen.js`**:
   - `const eng = newEngine()`. On each window, `step(eng, {t:w.end, ...w.det, pattern:w.pattern, db:w.db, floor: enrolment?.floor ?? null, kinds:w.kinds, label:w.label}, {urgent: srv.safety?.urgent, concern: srv.safety?.concern, paused, smokeWhilePaused: srv.safety?.smoke_paused})`.
   - Call `timeouts(eng, now())` every second.
   - Handle the actions:
     - `checkin` → show the check-in overlay (E4).
     - `alert` → POST `/api/h/:id/alert` (queue and retry if offline; show "an Urgent alert can't be sent while offline").
4. **Check-in overlay (E4, M11)**:
   - Full screen, very large high-contrast text: "Kettle heard what might be a fall. Are you OK?" (wording per rule type).
   - Two huge buttons, at least 88 px tall: **I'm OK** and **I need help**.
   - A visible countdown "Telling {caregiverName} in 45 s".
   - A louder chime first (WebAudio beep), then a spoken prompt (the existing `speak()`), `navigator.vibrate`, a flashing border
     for deaf users, and an `aria-live="assertive"` announcement.
   - The answer calls `answer(eng, t, "ok"|"help")` and sends the alert.
   - "I'm OK" records a concern for the family, e.g. "said they were OK at 3:13 PM after a crash".
5. **Always-visible "I need help" button (U6)**:
   - Bottom of the screen, red outline, on every listening, paused and off screen (not before pairing).
   - It works while paused: the server must accept `type:"help"` even when paused or off (see N).
   - Confirm with one tap and a 3-s undo: "Telling your family… Cancel".
6. **Smoke alarm screen**: when U1 or U2 fires, show "Kettle hears a smoke alarm. If there's a fire, leave and call 911." (no check-in).
7. **Too quiet escalation (U7)**:
   - If the today() rule `too_quiet` has `escalate:true` on the kitchen device, call `askStillness(eng, now)` once and show the check-in.
   - The family gets Urgent `stillness` with no answer.
8. **Consent (E5)**:
   - Add a step after the existing "Is it OK for … to see this?" with three separate choices:
     - "Kettle can also watch for danger: a smoke alarm, glass breaking, a crash, screaming or calls for help. It still keeps no recordings and no words. If it hears danger it will ask you on this screen first, then tell {caregiver}." → **Safety alerts: Yes / No**
     - **Worth-a-look notes: Yes / No**
     - "Keep listening for smoke alarms while paused".
   - Store via a new action `{type:"safety", urgent, concern, smoke_paused}` → `s.safety = {...,at}`.
   - Also show these switches in the `sharePanel` so the person can change them any time.
   - Update the consent text and "Kettle never names voices" to say exactly: "Screams and groans are used only inside the safety check on this device. They never appear on the timeline."
9. **"Your family hasn't seen this yet"**: if an urgent alert is unacked 15 min after `at` (server state), show "Your family hasn't seen this yet. If you need help, call 911." with a `tel:911` link.
10. **C11 coughs (opt-in)**:
    - Count windows where cough index 47 ≥ 0.3 per local day in localStorage `kettle.cough.<id>`.
    - Use `coughConcern(last7, today)` and send only `{type:"cough", tier:"concern", ratio}`.
    - The opt-in switch lives in the share panel, off by default.
11. Room profile: use `people.ROOMS[room].teach` for teach steps (replace `TEACH`), `placement` for `placeScreen`, and the `privacy` line.
    - For bathroom: show no timeline and no sounds, safety only.
    - For bedroom and hallway: show an **activity level** (quiet / some movement / active, from dB above the floor plus footsteps, door and drawer kinds) instead of the 9 activity labels.
- Done when, with `?qamic=` clips (add `_qa/smoke.flac`, `_qa/crash_groan.flac`, `_qa/scream.flac`; synthesise the smoke one with `eval.synth_alarms.synth("t3", 0, 20)` and write a flac):
  - smoke gives a red banner on the family view within 30 s;
  - crash plus groan gives a kitchen check-in, and no answer gives Urgent;
  - "I'm OK" gives an amber note;
  - pause gives no alerts except opted-in smoke and help.
  - Take screenshots of both screens for each case.

### N. Server alerts, push, escalation (P0)
Files: `web/src/household.js`, `router.js`, `worker.js`, `web/dev.mjs`, `web/test/api.test.mjs`.
1. **State**:
   - `s.alerts = [{id, tier: urgent|concern|test, type, at, since, text, evidence:{scores only}, checkin, acks:[{who, at}], dismissed:[who], escalations:n}]`.
   - Keep 30 days; prune in the tick. They are deleted with the home (wipe already deletes everything).
   - Expose them in `/state` (publicState already includes the state).
2. **Routes** (all through `handle()`):
   - `POST alert` (kitchen role; also **family role for tier "test"**). Validate the type against `safety.TEXT` keys plus the concern ids,
     tier, and evidence numbers ≤ 12 keys in [0,1]. Accept even when paused or off for types help, smoke and co. Rate limit 30 per hour.
   - `POST alert/<aid>/ack` (family). Record `{who: viewer name, at}`; others then see "Meera is handling this".
     Note: the router regex `^/api/h/([a-z0-9]{6,24})(?:/([a-z]+))?$` must be extended for `alert/<aid>/ack` and `viewers/<vid>`.
   - `POST alert/<aid>/dismiss` (family, concerns).
   - `GET /api/push/key` returns `{publicKey}`. The VAPID keys are generated once by `makeVapidKeys()` and stored in the **Codes** Durable Object
     (`kv` table) and in `web/.data/dev.json` for dev. Never commit them, never use env.
   - `POST push` and `DELETE push` (family) `{subscription, name, quiet:{from,to}|null, digest:"19:00"|null, concernPush:bool}`: up to 10 subscriptions per home, checked with `validSubscription`.
3. **Sending**:
   - On a new urgent or test alert, `sendPush` to every subscription, with payload `{title:"Urgent: …", body, tag:"alert-"+id, url:"/family?h=<id>", tier, alertId, home}`.
     Concern notes are pushed only if the subscriber opted in (`concernPush`) and it's outside their quiet hours.
     Delete subscriptions that come back `gone`.
   - **Escalation**: re-push every 5 min until any ack. Track `escalations`.
     - Worker: use a Durable Object **alarm** (`ctx.storage.setAlarm`; implement `alarm()` in `Household` that calls a new exported `household.tick(store, now)`).
     - dev.mjs: a `setInterval` every 30 s over households.
   - **Daily digest (M4)** at each subscriber's `digest` time: compute `today()` server-side (core.js is importable in the worker) and push e.g. "Mom's day: activity from 7:40 AM, TV 3 h, no notes."
   - **Concern push**: in the tick, compute today's concerns; push a new `note` once per day per concern id, only to `concernPush` subscribers (C1/C2 "can push once when they happen").
4. **Fallbacks**:
   - The family page polls every 5 s already. On a new urgent alert, play a sound (WebAudio) and flash the title.
   - Email or SMS: not today; say so in the FAQ.
5. **M8 test alert**: a button in family Settings sends `tier:"test"` to every phone and asks each to acknowledge; show who did.
6. **M3 family roles**:
   - `s.viewers = [{id, name, keyHash, owner, created, notify settings}]`. The original family key is the owner.
   - `POST viewers {name}` (owner) returns a new link key. `DELETE viewers/<vid>` revokes it.
   - `handle()` role check: family if the hash matches `keys.family` or any viewer `keyHash`.
   - The kitchen screen shows "Who can see: Meera, Ravi".
7. **M12 pairing**:
   - Codes are single-use: `take()` deletes the code (Codes DO and dev).
   - "Add another room" codes are 8 characters.
   - The rate limit already exists (10 misses per 10 min per IP).
8. **M10 abuse safeguards**:
   - The server refuses events and alerts without a current consent record (already does for events).
   - Refuse when the weekly re-consent is overdue.
   - The listening screen always shows a visible indicator (it does).
   - No covert mode: state it in the FAQ.
- Done when: `api.test.mjs` covers alert create, ack, dismiss, test alert, viewer create and revoke, single-use codes, push subscription validation (mock `fetchImpl`), escalation via `tick` (call it with a fake now), and the help alert accepted while paused.

### F-UI. Family view (P0)
Files: `family.js`, `family.html`, `app.css`, `theme.css`.
1. **Status strip** at the very top, always visible: green "All OK so far today", amber "Worth a look: 2 notes", red "Urgent: tap to see", grey "Can't tell: …". Use `t.status` from `core.today()`.
2. **Alert cards**:
   - Red for urgent, amber for concern.
   - Each shows: what Kettle heard (`text`), when (`at_text`, `since_text`), how sure (evidence scores turned into words), the check-in result ("said they were OK at …" / "didn't answer").
   - Buttons: **Call** (`tel:` with the parent's phone number saved **only in this browser's localStorage**; prompt to add it), **I've handled it** (ack), **Dismiss** (concerns).
   - "Meera is handling this" when acked by someone else.
3. Alerts history (30 days) in a details section.
4. **Notification settings**: enable push (via `pushclient.js`; a tap triggers the permission request), quiet hours, digest time, concern pushes on or off. Add the iOS Add-to-Home-Screen guide ("Share → Add to Home Screen") when `pushSupport().why === "ios-needs-home-screen"`.
5. Read `?ack=<id>` on load (the service worker's "I've got it"), ack it, then strip it from the URL.
6. Register the service worker on every page (`registerSW()` from family, kitchen and landing).
7. **Neutral wording**:
   - Replace every "Dad's kitchen" and `${n.parent}'s kitchen` with `people.place(names, room, "family")`.
   - The title is `${place}, today`; "What {caregiverName} sees".
   - Footer: `${personName} sees the same day on their own screen`.
   - Then remove `js/family.js` from lint PENDING.
8. **M9 doctor-visit summary**: a printable 2-week page (activity times, TV hours, nights up, notes) from `s.days` (15 days) plus alerts, marked "not medical advice". A "Print 2-week summary" button.
9. **3.4 multiple rooms**:
   - A pragmatic version: "Add another room" creates a **new household** with the same names and relation, a chosen room and an 8-character kitchen code. The family browser stores both in `homes()`.
   - The family page shows a room switcher plus an "All rooms" status. C1 "too quiet in any room" is computed client-side across rooms.
   - Say in the FAQ and docs that server-side push for cross-room C1 is a next step.

### S. More sounds, more accurate (P0 for S1–S4, S7; P1 for S5; S6 measure-only; S8 needs people)
1. **S1, about 40 sounds**: extend `KINDS` in `eval/beyond.py` (or a new `eval/sounds.py` that becomes the writer of `kinds.json`) using the plan's Appendix A groups.
   Verified AudioSet indices:
   - frying 367, sizzle 490, boiling 456, steam 296, chopping 366, stir 455, microwave 368, blender 369, kettle whistle 402/403
   - dishes 364, cutlery 365, chink 442, cupboard 362, drawer 363, pour 449, fill 452, crunch 499
   - tap 370, sink 371, bathtub 372 (private), toilet flush 374 (private, veto), drip 448, trickle 450, splash 445, gush 451, water 288
   - vacuum 377, hair dryer 373, electric toothbrush 376 (private), shaver 382 (private), fan 412, air conditioning 413, sewing machine 411, printer 415, typing 384, computer keyboard 386
   - doorbell 355, ding-dong 356, knock 359, door 354, sliding door 357, slam 358 (an impact, not a door), footsteps 53, shuffle 52, keys 379, telephone 389, telephone bell 390, ringtone 391, alarm clock 395, beep 481, buzzer 398
   - TV 524, radio 525, music 137, speech 0, conversation 4 (activity only, never words)
   - dog 74, cat 81, bird 111, siren 396, emergency vehicle 322
   - Body (private, **never shown or sent**): cough 47, sneeze 49, throat clearing 48, snoring 43, breathing 41, sigh 26.

   Not in AudioSet: washing machine, dishwasher, fridge, toaster, coffee machine, pressure cooker. Train these in S5 with ESC-50 (washing_machine, can_opening, drinking_sipping) or leave them out and say so.
   - **Important:** the earlier team decision (`kettle/evidence_labels.json`, `SHOWN_SOUNDS`) excluded pets, phone and doorbell from the sound names. The v3.1 plan adds them back. Update `KIND_NAMES` in core.js (the family view and server allow-list use it), `kinds.json`, `sounds.js`/`evidence_labels.json` only if needed, and `kettle/kinds.py`. Record the change in DECISIONS.
2. **S2, calibration and the bar**:
   - Threshold = 99th percentile of development negatives (SINS folds 1–2, ESC-50 folds 1–3, Nonspeech7k half 0) with MIN_TAU 0.05.
   - **Pre-registered bar** (write it into `eval/PREREGISTER-SOUNDS.md` **before** running): precision ≥ 90% on held-out negatives and recall ≥ 40% on held-out positives.
   - Positives per sound: use the ESC-50 categories that match (vacuum_cleaner, keyboard_typing, door_wood_knock, pouring_water, water_drops, clock_alarm, glass_breaking, footsteps, dog, cat, door_wood_creaks, toilet_flush (private), crackling_fire, siren, clock_tick, washing_machine, can_opening, drinking_sipping, brushing_teeth (private)) and SINS activity labels for related sounds (cooking → frying/chopping, dishwashing → dishes/tap, watching_tv → tv, vacuum_cleaner → vacuum).
   - Write `results/sounds.json` (per sound: positives found, false names per 1,000 windows, N, 95% CI via `eval.beyond.rate`) and `web/public/data/sounds.json`.
   - **Sounds that fail the bar get `shown:false`**: never named on the timeline or used by checks; at most "possibly X" in block detail.
   - Extend the How sure table ("Everyday sounds Kettle can name").
   - Note that the existing 15 kinds currently ship from `eval/beyond.py`; keep `results/beyond.json` consistent or move the kinds part of beyond.py into sounds.py, and check `eval.check_metrics` still passes.
3. **S3, context rules** (in `sense.js kindsOf` + a twin in `kettle/kinds.py`, with tests):
   - kettle only when boiling, whistle or steam is top **and** tap/sink/dishes are below threshold **and** frying is below threshold, **and** it repeats in 2 or more windows;
   - split "alarm" into `smoke_alarm` (safety only) and `timer` ("Timer or appliance beep": beep, buzzer, microwave beep) and never merge them;
   - door needs the door or sliding-door class itself (slam is an impact);
   - microwave only with microwave ≥ 0.5, or followed by its beep; when vacuum, fan, engine or vehicle score above microwave, it's appliance hum (not shown);
   - cutlery or chink present with no tap/sink: the second opinion prefers eating over washing up (adjust `witness` family selection in `head.js` + `kettle/witness.py`; parity!);
   - a high-confidence doorbell, phone ring or knock overrides a novel activity guess as a **moment**, not a block.
4. **S4, overlap**: the 5-s hop (E-UI 1). Sustained sounds (TV, water, frying) need 2 of 3 windows; transient ones (doorbell, glass, scream, knock) need 1 window above a higher threshold. Implement as a per-kind `kind: "sustained"|"transient"` in kinds.json plus a `tau_once`.
5. **S5, trained multi-label head (if time)**: logistic per sound on 192-d CED embeddings (`emb` in the caches). Train on ESC-50 folds 1–3, test on folds 4–5 (split by fold = by source recording). Ship per sound whichever is better (zero-shot threshold vs trained). Write `models/sounds_head.json` (never touch `head.json`) and `results/sounds_head.json`. Add augmentation (room echo, band-pass 200 Hz–7 kHz, TV underneath at 0 to −18 dB) only if time.
6. **S6, measurement only** (the frozen-head rule): `eval/novelty_multihome.py` measures what a multi-home novelty threshold would do on other-homes data (`eval/other_homes.py` caches) next to the SINS numbers, **without changing `head.json` or the shipped theta or novelty values**. Report in How sure as "what we'd change with more homes". Explain in DECISIONS why it isn't shipped.
7. **S7**:
   - The TV check fix is done.
   - Still to do: make TV detectable. In `sense.js refine()`, if Television or Radio ≥ tau (or Music/Speech with a broadcast pattern: continuous for 3+ windows with no kitchen kinds), set `label: "watching_tv"` even when novel.
   - Mirror in Python (`kettle/kinds.py` or `witness.py`) and the timeline twin if `rawLabel` changes. Add a parity case.
8. **S8, real kitchens**: needs people. Update `eval/OWN_KITCHEN_GUIDE.md` and `docs/REAL-KITCHEN-PROTOCOL.md` with 5 minutes of **safe safety sounds** per kitchen (the smoke alarm test button, a recorded scream from a speaker, a dropped pot, a knock, the doorbell) and a scoring script `eval/own_kitchen_safety.py` that runs the safety engine over the labelled segments. Mark How sure "not measured yet" until recordings exist.

### F. Other fixes found in testing
- **F1 (P1)**:
  - Stop sending Speech, Conversation, Chatter, Hubbub and Crunch in the per-window `sounds` list. Check `kettle/evidence_labels.json` and `SHOWN_SOUNDS`: the tester saw "Speech" stored. Remove voice tags from the allow-list (regenerate `sounds.js` via `export_web_fixtures.py`).
  - Send only allow-listed named sounds.
  - Drop the full 9-class `probs` from uploads: send only the top 2 (and adapt `cleanEvent`, `makeBlock` guesses and `whyNotSure`, which use `probs`; set missing classes to 0 and keep parity by making Python accept the same reduced shape). Note the risk: it touches parity and why-not-sure; do it carefully or leave probs and document why.
- **F2**: done (S7).
- **F3**: S3 above.
- **F4 (P1)**: the landing hero sample must never show "Working (typing)" on a Silence window; use the same `rawLabel` rule as the day bar. Make "A TV-only afternoon" open on TV, not Conversation (check `landing.js` stage data and `demo_cache/scenarios.json`).
- **F5 (P0) new sample days** in `demo_cache/scenarios.json` and `tools/export_web_fixtures.py`:
  - "A smoke alarm" (Urgent sent, then acknowledged);
  - "A crash, then they said they're OK" (Concern);
  - "Too quiet after lunch" (Concern, then check-in);
  - "TV all day" (Concern).
  Sample days need an `alerts` array in sample-days.json; `landing.js` must draw the status strip and alert cards. **Lead the demo with one of these.** Use real clips (ESC-50 glass, Nonspeech7k screams, synthetic alarms) through `encoders.embed` the same way the existing days do.
- **F6 (P2)**: per-viewer links with names and one-tap revoke (M3 above).
- **F7 (P2)**: on delete, clear the kitchen browser's queue (`kettle.queue.<id>`), enrolment (`kettle.enrol.<id>`), setup and cough keys. The kitchen sees 404 in `poll()` → in `ui.gone`, remove those keys.
- **F8 (P2)**: the summary must not say "Nothing is known after…" while the heartbeat says Listening (the stale-window race). In `core.today()` only add that sentence when `hb.state` is not listening (it already checks; reproduce the race: a `last_window_t` update vs events merge in `kitchen.js`) and fix.
- **F9 (P1)**: teach-this-room gets an optional "everyday sounds" step (kettle, microwave, doorbell) and a safety test step ("press your smoke alarm's test button"; check that U1 or the T3 pattern fires and show "Kettle heard it"), stored on the device.
- **F10 (P0)**: home page and How sure:
  - Say "Kettle names N household sounds" only from `results/sounds.json` (N = sounds that passed S2).
  - Add "Safety alerts: what we measured" (from `web/public/data/safety.json`: detector table, pattern table, scenario table, false Urgent per 24 h, limits) and "What Kettle can't do" (it can't see a fall, will miss many falls, is not 911 or a pendant; unmeasured rooms).
  - Add to `web/public/js/howsure.js`, or a new `safetyreport.js` loaded by `how-sure.html`. `eval.check_metrics` may need to learn the new results files.

### Q. FAQ and judge Q&A (P0)
- Replace the landing FAQ ("Asked plainly", `index.html`) with the plan's 2g answers. Fill every X from results files at runtime (load `/data/safety.json` and `/data/results.json` in `landing.js`, like the hero numbers):
  - Does Kettle record?
  - Does it send alerts? (two levels: Urgent and Worth a look)
  - Can it detect a fall? ("not directly"; caught X of Y crash-then-groan sequences; misses many; doesn't replace a pendant)
  - Is it an emergency service? (no; call 911)
  - How often will it cry wolf? (X false Urgent in N hours of ordinary sound)
  - What sounds can it name? (N passed the bar)
  - Does it hear screams? (only inside the safety check, on the device)
  - TV all day?
  - Another room?
  - Visitors, carers and pets?
  - Night?
  - Power or Wi-Fi out? ("Can't reach the device since 3:10 PM", never "All OK"; urgent can't send offline)
  - Notifications on a phone? (iPhone: Add to Home Screen first)
  - Can the person turn it off or see what we see?
  - How accurate is it? (84.1 macro F1 benchmark from results; other homes X%; own kitchens; safety)
  - Can we delete everything? (labels after 8 days, alerts after 30)
  - Cost? (free prototype)
- Add the Part 3 FAQ items:
  - Does it have to go in the kitchen?
  - More than one device?
  - Only for parents?
  - A bathroom?
  - Why "Your parent's"?
- Then remove `index.html` from lint PENDING.
- Write `docs/JUDGE-QA.md` with the plan's judge Q&A table and answers filled from results:
  - How do you know emergency detection works? (simulator + dev/test)
  - Why not a wearable or radar?
  - What stops false alarms from TV? (media veto, check-in, repeated evidence; TV-drama negative 0/60)
  - Why is a scream detectable if you never name voices?
  - Why these concern thresholds?
  - How many sounds really?
  - What did you add beyond existing models?
  - The worst thing that can go wrong?
  - Medical device? (no)
  - Real kitchens?
  - Does the person really consent?

### Part 3. Remaining
- **3.2/3.6 wording everywhere**:
  - core.js:
    - `heartbeatLine`: "The kitchen phone is on battery" → `The phone in ${place} is on battery`.
    - "Kitchen activity by" stays only for kitchen rooms.
    - "No kitchen activity heard yet today" → `No activity heard yet today in ${roomName}` (needs the room in the today() opts: add `room` to the opts and pass `srv.room`).
    - Default names `{parent:"Dad", caregiver:"Meera"}` in `today()` are used by the parity fixtures. Keep the Python view's PARENT/CAREGIVER for parity, but the screens must pass real names (neutral when unnamed): `personName(names,{mid:true})` for "Paused by your parent".
  - kitchen.js:
    - "This laptop listens for kitchen sounds." → `This ${DEVICE} listens for sounds in your ${roomName}.`
    - "Listening for kitchen sounds" → `Listening in your ${roomName}`
    - "Teach Kettle this kitchen" → "Teach Kettle this room".
    - The person's own device speaks to them ("your bedroom").
    - `$("#who-tag")` uses `place(names, room, "person")`.
  - Then remove `js/core.js` and `js/kitchen.js` from lint PENDING.
- **Server**:
  - `household.create` must accept `relation`, `room {type, name ≤ 24}` and store `s.names.relation` and `s.room`. `parent` may be "" → null (not "Dad").
  - `cleanName` must allow null.
  - `POST names` also accepts relation and room.
  - Old homes (parent "Dad", no room) keep working.
- Route **`/listen`** as an alias of `/kitchen`: copy `kitchen.html` handling. In the worker, assets `html_handling` won't map it, so add `web/public/listen.html` (a copy of kitchen.html; scripts use `linkFromHash("kitchen")`; keep the key names) or a worker redirect. Update dev.mjs `file()` if needed.
- Room-specific checks, alerts and privacy defaults per the plan's 3.3 table (via `ROOMS.defaultChecks` and the E-UI room handling).
- 3.5 wider audience:
  - "Myself" relationship: alerts go to a chosen friend; only urgent and too-quiet, no timeline shared unless wanted.
  - A "short-term" mode with an end date (auto-off): add `s.ends_at` and auto `off` in `tick()`.
  - "Same home" carer mode (night alerts).
  - Large-text and screen-reader alerts.
  - State "not supported: covert listening" plainly in the FAQ.
- 3.7 tests:
  - Make the lint test pass with PENDING empty.
  - Add snapshot tests for every relationship (6) × room (7) × viewer (family, person) through `core.today()` titles, consent text, status, summary, checks and alerts (extend `people.test.mjs` or add `rooms.test.mjs`). Include unnamed, a name ending in s, and a non-English name.
  - Old homes show "Dad's kitchen".

### Part 4. Remaining items
- **M1 PWA**: modules done; register the service worker on every page and verify the offline shell with Playwright (go offline and reload /family).
- **M2 judge demo mode (P0)**: one button "Try a sample home" on the landing. The visitor picks a person and a room, then a scripted day plays: the timeline fills, a smoke alarm gives a red banner, and an "Are you OK?" check-in appears on a mock listening screen with working buttons. No microphone or pairing. Reuse the landing stage and the new F5 sample days.
- **M3 roles** → N.6. **M4 digest** → N.3.
- **M5 languages (P1)**: the listening device's consent, check-in, help button and "Read this to me" in Spanish and Hindi, chosen per device (localStorage `kettle.lang`; `speechSynthesis` lang `es-ES` or `hi-IN`). Mark them machine-written and needing native review.
- **M6 voice answer (P2, opt-in, off by default)**: during the 60-s check-in only, `SpeechRecognition` listens for "I'm OK", "okay", "help", "ayuda" or "मदद". **Privacy:** Chrome's recognizer sends audio to Google unless `processLocally` is supported. Disclose this plainly in the opt-in, prefer on-device, and never keep the words.
- **M7 device health (P0)**: warn the family before failure: battery under 20% (`batteryLine` already exists; add a threshold), slow labelling (`ms` > 8000), mic muted (exists), tab closed for 10 min (stale exists). Show these in the status strip as grey "Can't tell" with the reason. Overheating can't be read in browsers; say so.
- **M8 test alert** → N.5. **M9 doctor summary** → F-UI 8. **M10 safeguards** → N.8.
- **M11 accessibility**: check-in buttons at least 88 px, vibration, a flashing border, high-contrast red that also works in dark mode, screen-reader announcements; run the `web-quality-skills:accessibility` checks.
- **M12 pairing** → N.7.

### Docs, writing and shipping
- `CHANGELOG.md` (the plan asks for it): what changed and what was measured, per step.
- `docs/DECISIONS.md` rows:
  - safety thresholds and floors;
  - the 5-s hop;
  - device-side vs timeline concerns;
  - VAPID keys in the Durable Object;
  - S6 not shipped (frozen head);
  - pets, doorbell and phone now named (reverses the earlier allow-list choice);
  - neutral names;
  - rooms as separate households.
- `docs/EXPLAIN.md`: explain-backs for safety.js/safety.py, concerns, push.js, people.js and eval/safety.py.
- `docs/AI-USAGE-LOG.md`: rows for this session's work (safety, concerns, push, people, data scripts). Check which rows the sub-agents already added.
- `README.md`: the results table gets the safety rows (from the results files); a "What Kettle can't do" line.
- The write-up (`docs/WRITEUP.md`) and video are for humans; give them the new numbers.
- Before pushing:
  - run every check in section 1;
  - run the e2e (update `web/test/e2e.py` for the new setup questions: Who is this for, What do you call them, room, the safety consent step, and the help button);
  - take Playwright screenshots of `/`, `/start`, `/kitchen`, `/family` and `/how-sure` at 390 and 1280 px and look at them.

---

## 4. Data contracts (keep these exact)

- **Window event sent by the listening device** (`cleanEvent` in household.js):
  `{start, end, label, conf, probs{9}, novel, w:{k, family, v}?, sounds:[{name,score}]≤3 allow-listed, kinds:[ids], taught?}`,
  or a private event `{label:"private", private:true}`.
- **Alert sent by the listening device**: `{tier, type, at, since?, text, checkin?, evidence:{detector:score, t3?, t4?}}`. Never audio, never words.
- **Concern rule**: `{id:"r4", type:"concern", cid:"too_quiet", hours?, from?, to?, escalate?, time?, minutes?}`.
- **Household state additions** (planned): `names.relation`, `room:{type,name}`, `safety:{urgent,concern,smoke_paused,at}`,
  `alerts[]`, `viewers[]`, `push[]` (subscriptions with names and settings), `ends_at`.
- **`today()` output additions**: `alerts[]` (with `at_text`, `since_text`), `status {level,text,n}`, and rules with `concern` and `escalate`.

## 5. Files map (where things live)
- Python reference app: `kettle/` (labels, timeline, rules, view, live, heartbeat, witness, kinds, **safety**, concerns (to write)).
- Evaluation: `eval/` (`__main__` is the HELD-OUT test: don't run it). Also beyond, stress, stress_teach, other_homes, **safety**,
  esc50_all, nonspeech7k, synth_alarms, check_metrics.
- Web: `web/public/js/`:
  - core (shared logic), head (frozen head + second opinion), sense (kinds, enrolment), **safety**, listen (mic + ONNX), kitchen, family, start, landing, howsure, beyond, ui, **people**, **pushclient**, sounds (generated).
  - `web/public/sw.js`.
  - Server: `web/src/` (worker, router, household, **push**).
- Tests: `web/test/*.test.mjs` (core parity, api, fixes, sense, push, safety, people, lint-words), `web/test/e2e.py`, `tests/` (pytest).
- Generated files (never edit by hand):
  - `web/test/fixtures.json`, `web/public/data/sample-days.json`, `web/public/js/sounds.js`, `web/public/model/{head,evidence,witness}.json` (export_web_fixtures.py)
  - `web/public/model/{kinds,enrol}.json` (eval/beyond.py)
  - `web/public/model/safety.json` and `web/public/data/safety.json` (eval/safety.py)
  - `web/test/safety_fixtures.json` (export_safety_fixtures.py)

## 6. Known gotchas
- The two SINS caches list clips in different orders: always reindex by filename (see `eval/beyond.py load()`).
- `core.today()` has default names Dad/Meera, used by the parity fixtures; don't change the Python view's PARENT/CAREGIVER without regenerating.
- Python `round()` is banker's rounding; core.js has `pyRound`. In new twin code use JS `Math.round` semantics in Python as `math.floor(x+0.5)` (see `_r3` in kettle/safety.py), or avoid exact .5 cases in fixtures.
- Kitchen screen redraws every second; `extraKey` decides when `#extra` is rebuilt. Add new state to that key or checkboxes will reset.
- The kitchen `onWindow` handler ignores windows during the silent-mic run and while teaching. Keep the safety step running while teaching? No: teaching sets the hop to 2 s, so skip safety while teaching, or scale the engine timings.
- The service worker precaches `?v=w4` URLs: bump both together.
- The Durable Object `Household.call` rate limit is 300 per minute; alarms don't go through `call`.
- The sample-day switch pill: if you add sample days, the bar wraps on phones. The pill code already handles rows.

## 7. Suggested order for the next session (fits in about 8 hours)
1. C1–C6 (concerns twin, fixtures, editor, room defaults): 1 h.
2. N server alerts, push, escalation, viewers and codes, with api tests: 1.5 h.
3. E-UI kitchen: 5-s hop, engine wiring, check-in overlay, help button, consent, room wording: 1.5 h.
4. F-UI family: status strip, alert cards, notification settings, ack, neutral titles: 1 h.
5. F5 sample days, M2 demo mode, F4, F10 How sure safety section, Q FAQ, judge Q&A: 1.5 h.
6. S1–S4, S7 sounds expansion and calibration: 1.5 h. S5 and S6 if time.
7. M5, M6, M7, M9, M11, 3.4, 3.5: remaining time.
8. Docs, CHANGELOG, e2e, screenshots, push (ask the user first).
