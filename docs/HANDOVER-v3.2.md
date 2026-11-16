# Kettle v3.2 handover: detection accuracy comes first

> **Superseded for current status by `docs/HANDOVER-v3.3.md`** (Sun 15 Nov ~1:25 PM CT). §0–9 here still hold for ground rules and Parth's Mac setup.

Written Sun 15 Nov 2026, about 12:15 PM CT, by Parth's Aside session (Claude) when his usage ran low.
It picks up from `docs/HANDOVER-v3.1.md` (Shaurya's handover, commit `b4e1f93`). **Read both.** v3.1 has the ground rules,
data contracts, file map and the full feature backlog. This file says what changed since then and what matters most now.
Where they disagree, this file wins.

`main` is at the commit that adds this file. Everything under "Done" is committed, pushed and tested.

---

## 0. THE PRIORITY (Parth's words, Sun Nov 15 ~12:10 PM CT)

Parth tested Kettle himself, live in his own kitchen. His verdict: **"very subpar in terms of functionality and performance."**
What he saw:
- **Washing up when nobody washed anything.** No tap ran, and Kettle said "washing up".
- **Metal cooking sounds read as eating.** His mom was cooking with metal pots and utensils, and Kettle said "eating".
- "Small things like these", meaning many more misfires of the same kind.

His instruction for the next agent, in his words: **focus most on improving the accuracy and quality of the detectors.**
Work on it a lot and in depth. Give it a lot of time and focus. That means how accurately Kettle detects things, what it detects
falsely, and every bug like these. Fix them **extremely carefully.**

What that means for you:
1. **Accuracy is the main job for the rest of the hackathon.** The UI and front end are already good, so new screens,
   features or polish come **after** detection quality. Parth said it plainly: "We have a nice UI and a front end... we need
   to focus on the main functionality."
2. **The v3.1 backlog is now secondary**: rooms, push notifications, viewers, languages, doctor summary, multiple
   devices and so on. Section 6 sorts it into keep, cut and later.
3. **Every accuracy claim needs a measured number**, chosen on development data and reported on held-out data
   (AGENTS.md rules). "Looks better" doesn't count. Parth personally hit wrong labels, so judges will too.
4. **The single most valuable artifact is a labelled recording of a real kitchen** (section 4). Every public-data proxy we
   have only partly reproduces Parth's failures. Get one as early as possible.

Deadlines (CT): video uploaded unlisted by **7:00 PM**, submit target **9:00 PM**, hard close **10:59 PM**. Parth presses
Submit. You fill the form and stop. Leave enough time for the video (section 7).

---

## 1. Environment on Parth's Mac (different from Shaurya's cloud box)

- Repo: **`<repo>`** (not `/home/user/Hackathon`).
- Python: **`.venv-probe/bin/python`** has torch, soundfile, librosa, transformers, sklearn and playwright. `.venv/bin/python`
  **lacks soundfile**, so `tools/export_web_fixtures.py` fails there. Use `.venv-probe` for everything.
- Prefix git, wrangler and Python with **`HOME=~`**. The agent shell's HOME is a sandbox without the git
  credential helper or the wrangler login. For git also set `GIT_TERMINAL_PROMPT=0`.
- Playwright: `PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/ms-playwright`. Don't run `playwright install`.
- Dev server: `cd web && PORT=8799 node dev.mjs`. Use a port other than 8787 (another agent has used 8787). It writes
  `web/.data/dev.json` (git-ignored).
- Hugging Face models already cached: `mispeech/ced-tiny`, `mispeech/ced-small`, `MIT/ast-finetuned-audioset-10-10-0.4593`,
  `laion/clap-htsat-unfused`.
- Data on disk (git-ignored): `data/raw/{sins,desed,kitchen20,esc50_house,audioset}`, `data/clips/{dev,eval,...}` (6.9 GB),
  embeddings in `data/emb/ced-tiny/{kitchen20,desed,esc50_house,dev,eval}/` (npz with `emb` [N,192] and `audioset` [N,527]),
  SINS dev caches `results/cache/oof_dev.npz` (out-of-fold head probabilities `P0`, labels `y`, `session`, `fold`) and
  `results/cache/ced-tiny_dev.npz` (`scores` [8920,1,527], `emb`). The two SINS caches list clips in **different orders**:
  always reindex by filename (see `eval/kitchen_naming.py sets()`).
- **pytest:** run `pytest -q tests`, not bare `pytest`. Bare pytest collects `data/raw/kitchen20/tests` and errors out.

### Commands to run before every commit
```bash
cd <repo>
HOME=~ .venv-probe/bin/python tools/export_web_fixtures.py      # sample days + parity fixtures + web/public/model/witness.json
HOME=~ .venv-probe/bin/python tools/export_safety_fixtures.py
cd web && npm test && cd ..                                                 # expect: 131 pass, 0 fail, 4 skipped (lint PENDING)
HOME=~ .venv-probe/bin/python -m pytest -q tests                 # expect: 77 passed
HOME=~ .venv-probe/bin/python smoke_test.py                      # PASS, < 60 s
.venv-probe/bin/python -m eval.check_metrics                                # 0 problems
HOME=~ .venv-probe/bin/python -m eval.kitchen_naming --dev       # dev-only accuracy table (never touches TEST)
git diff --cached | grep -E "sk-|AIza|BEGIN PRIVATE|ghp_|key="              # 'key=lambda' in Python is a known false hit
```
Full browser flow (works again, see 2.4):
```bash
cd web && (PORT=8799 node dev.mjs &) ; cd ..
HOME=~ PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/ms-playwright KETTLE_E2E_LISTEN_MS=170000 \
  .venv-probe/bin/python web/test/e2e.py http://localhost:8799 <clip.wav 16 kHz mono> <out_dir>
```
It takes about 3.5 minutes with a 170 s listen, so run it with `nohup ... &` and poll the log. Screenshots go to `<out_dir>/e2e-*.png`.
The family summary line printed in the log is the quickest accuracy check.

---

## 2. Done this session (commit `cdd3671`, pushed with this file)

### 2.1 Root cause of Parth's two failures (diagnosed in code, then reproduced)
Kettle labels each 10-s window in two ways:
- **The head**: the frozen 9-class logistic model in `models/head.json`, trained in ONE research home (SINS). If it is
  confident (≥ theta 0.66) and the sound is not "novel", its label is shown.
- **The second opinion** (`kettle/witness.py`, `models/witness.json`): when the head has no answer (novel or unsure), the
  general AudioSet tags can "rescue" the window. **The bug:** the rescue picked the activity from the single loudest kitchen tag
  in that one window: `"Dishes, pots, and pans"` → **washing up**, `"Cutlery, silverware"` → **eating**, frying and similar → cooking.
  A pot clanking while someone cooks hits "Dishes, pots, and pans", so it showed washing up. A spoon or ladle hits "Cutlery", so it
  showed eating. That is exactly what Parth saw.
- **A second path found by the browser e2e:** the head itself said **washing up at 93% confidence**, not novel, on plate and
  cutlery clatter between frying, with **zero running-water evidence** (tap/sink tag 0.001). So confident head labels misfire
  too, outside the research home.

### 2.2 Experiments run (results feed the decisions; scripts were scratch, numbers below)
| Idea | Result | Verdict |
|---|---|---|
| Hard gate "no running water heard = no washing up" (per window, ±20 s) | SINS dev dishwashing F1 **88.6 → 41**. The tags miss a distant tap: even in true SINS dishwashing only 14% of windows have tap/sink ≥ 0.05, 47% within ±30 s, 86% within ±3 min | **Rejected.** Water evidence has to come from minutes of windows, not seconds |
| Bigger "ear": CED-small (22M) and AST (87M) instead of CED-tiny, same tag rules | Kitchen20 TEST, 3-way cooking/washing/eating balanced accuracy: tiny 73.5, small 66.7, AST 73.7 | **No gain.** The ear is not the bottleneck |
| CLAP zero-shot (`laion/clap-htsat-unfused`, text prompts) | 74.9 on the same set | **No gain** |
| Trained "judge": logistic regression on the 527 log-tags, trained on Kitchen20 + DESED + ESC-50 + SINS (tune halves) | Single-split peek: ~95 balanced accuracy, but with ambiguous classes folded in. Proper group-CV on tune with an "other" class: K20 right 46 → 75%, but **non-meal sounds called meal 5.5 → 10%**, and real-room DESED frying wrong-activity 11 → 16% | **Not shipped yet. The most promising lever for the next agent** (see 3.2) |
| Name each kitchen **stretch** from evidence across all its windows (rules 2c, 2d) | No loss anywhere. Details in 2.3 | **Shipped** |

Takeaway: **the ear (CED-tiny's 527 tags) hears the right things. The judgment that turns tags into activities is weak**, because it
looks at single 10-s windows and was hand-mapped from one home. Better judgment over time is where accuracy comes from.

### 2.3 Shipped: timeline rules 2c and 2d (JS and Python twins, parity green)
- **Evidence numbers on each window.** `w` grows from `{k, family, v}` to `{k, family, v, cook, water, mouth}`:
  - `cook` = max(Frying (food), Sizzle, Boiling, Chopping (food), Stir)
  - `water` = max(Water tap, faucet; Sink (filling or washing))
  - `mouth` = max(Chewing, mastication; Biting; Crunch)

  Computed on the device in `web/public/js/head.js opinion()` and `kettle/witness.py opinion()`. Lists and thresholds live in
  `models/witness.json` (`evidence`, `tau_cook` 0.05, `tau_water` 0.05, `tau_mouth` 0.1, `cook_share` 0.1); the web copy is
  generated as indices. The server keeps the three numbers (`web/src/household.js cleanEvent`).
- **Rule 2c** (`kettle/timeline.py name_stretches`, `kettle/witness.py name_kitchen`; JS `nameStretches`, `nameKitchen` in core.js):
  - A rescued window now says only **"kitchen"**.
  - After smoothing and bridging, each run of "kitchen" windows is named once, from the whole stretch. Each window votes for the
    louder of cook and water.
    - **cooking** if cook votes ≥ max(1, 10% of windows) and ≥ water votes;
    - else **washing up** if any water vote;
    - else **eating** if any chewing;
    - else stays **"Kitchen activity"** (new display label, colour `--act-kitchen`, counts as MEAL and ACTIVE, so
      "kitchen activity by 10" checks still work).
  - Old events without evidence numbers keep the old family (backward compatible).
- **Rule 2d** (`_absorb` / `absorb`): a washing-up, eating or kitchen stretch with **no evidence of its own** (no water vote,
  no chewing), **≤ 3 windows long**, **next to cooking**, becomes cooking. This catches the head's confident 93% "washing up" flip.
  A wider version (also renaming long unsupported washing-up stretches) cost 3 of 132 SINS sessions on dev and was dropped.
- **The chip** ("Sounds like ...") applies 2c to its single window.
- **Measured** by `eval/kitchen_naming.py` → `results/kitchen_naming.json`. It runs the app's own `timeline.blocks()` with and
  without the evidence numbers, so "before" is exactly the old shipped behaviour:

  | Set | Before | After |
  |---|---|---|
  | SINS dev, 132 meal sessions | 130 right, 2 wrong | **132 right, 0 wrong** |
  | Kitchen20 TEST, 222 meal clips | 130 right, 9 wrong activity | **130 right, 7 wrong** |
  | DESED TEST frying, 25 | 24 right | 24 right |
  | DESED TEST dish clatter called washing up or eating | 6 of 15 | **1 of 15** (now cooking 6, kitchen activity 3) |
  | False "kitchen" on non-meal sounds | unchanged on every set | |

  **Honesty note (kept in the file's `process` field):**
  - TEST halves were scored three times today: the first rule version, the fix after seeing it, and rule 2d.
  - Kitchen20 TEST was also looked at once in the exploratory model comparison.
  - The first run (cooking checked before water) made Kitchen20 worse (right 130 → 123). It is saved under `first_test_run`.
  - **These public TEST numbers are not pristine. The clean measurement must be a real kitchen recording.**
- **Browser e2e** on a 230-s clip (Kitchen20 frying-pan alternating with cutlery and plates, no tap):
  - before: "cooking, **washing up**, cooking";
  - after: "**kitchen activity** around 12:05 PM and **cooking** around 12:05 PM".

  Screenshot checked: "Kitchen activity" legend swatch renders, layout fine at 393 px.
- Tests added: `web/test/fixes.test.mjs` (opinion numbers, threshold match with witness.json, the six 2c/2d cases including
  "real washing up between frying stays washing up"); `tests/test_timeline.py` (2c and 2d twins); `tests/test_witness.py` updated.
- Docs: `docs/DECISIONS.md` row (Sun Nov 15 12:10), `CHANGELOG.md` (new file, the plan asked for one).

### 2.4 Also fixed
- `web/test/e2e.py` works with the v3.1 setup again ("My parent", name "Papa" in `#p`, room "Kitchen", caregiver in `#c`).
  It also accepts `KETTLE_E2E_LISTEN_MS` for long listens.

---

## 3. THE ACCURACY WORK (do this first, in this order)

For every item:
1. Reproduce it with a clip or fixture.
2. Fix it in **both** twins (JS `web/public/js/*.js` and Python `kettle/*.py`).
3. Add a test on each side.
4. Measure on dev with a script that writes `results/*.json`.
5. Report on held-out once.
6. Add a DECISIONS row and a CHANGELOG line.

Rerun the browser e2e on a relevant clip after each one. If a fix looks great on public clips, be suspicious: those clips are
close-mic sound effects, not a laptop across a room.

### 3.1 P0: named-sound misfires (seen live in this session's e2e screenshot, and in the PDF's T7)
On the frying + cutlery clip (no kettle, no tap), "Sounds Kettle named today" showed **"Kettle or a hot drink (6x)"** and
**"Running water (2x)"**. Families read this list. Fix in `web/public/js/sense.js kindsOf()` and its twin
`kettle/kinds.py named()` (same order, same output).

Current kinds (`web/public/model/kinds.json`, written by `eval/beyond.py`):

| id | AudioSet indices | tau |
|---|---|---|
| kettle | 456 Boiling, 296 Steam, 403 Steam whistle, 402 Whistle, 449 Pour, 452 Fill | 0.071 |
| frying | 367, 490 | 0.05 |
| chopping | 366, 438 | |
| blender | 369 | |
| microwave | 368 | 0.05 |
| dishes | 364, 365, 442, 489 | 0.077 |
| tap | 370, 371, **288 Water (generic)** | 0.05 |
| cupboard | 362, 363 | |
| door | 354, 357 | |
| alarm | 399, 400, 388, 395, 481 | |
| tv | 524, 525 | |
| vacuum | 377 | |
| typing | 384, 386 | |
| footsteps | 53 | |
| glass | 443, 470 | |

Context rules to implement (from PDF S3, plus what was seen today):
- **kettle**:
  - drop Pour and Fill from its indices (pouring isn't a kettle);
  - name it only when max(Boiling, Steam, Whistle, Steam whistle) ≥ tau **and** beats frying/sizzle, tap/sink and dishes in the
    same window;
  - in the timeline, require it in **2 or more windows within 3 minutes** before a "kettle by 9" check can be met.
    `kind_by` in core.js `ruleKindBy`, plus the Python rules twin.
- **tap**:
  - drop generic `Water` (288), which fires on frying;
  - require tap/sink to beat frying/sizzle in the same window.
- **alarm**: split into a smoke/fire alarm (safety only, never in this list) and "Timer or appliance beep" (Beep, bleep 481;
  Buzzer 398; Alarm clock 395). Never merge them.
- **door**: needs the Door or Sliding door class itself. Slam (358) is an impact, not a door.
- **microwave**: score ≥ 0.5, **and** above Vacuum, Mechanical fan, Air conditioning and Engine. Otherwise call it appliance hum
  and don't name it.
- **dishes vs washing**: "Dishes and cutlery" is fine as a sound name. It must never feed "washing up" (rule 2c already ensures
  this for activities).

Measure the false names per 1,000 windows on negatives (ESC-50 all 2,000 clips in `results/cache/ced-tiny_esc50all.npz`, SINS
dev, Kitchen20 non-matching categories) and recall on positives (Kitchen20 `boiling-water` for kettle-ish, `water-flowing` and
`clean-dishes` for tap, `microwave`, ESC-50 `pouring_water` etc.) before and after. Write `results/sounds.json`, as v3.1's
S2 describes. Pre-register the bar in `eval/PREREGISTER-SOUNDS.md` **before** scoring held-out: precision ≥ 90%, recall ≥ 40%.
Sounds that fail are hidden (`shown:false`). `kinds.json` is generated by `eval/beyond.py`: change the generator, not the JSON.

### 3.2 P0/P1: a trained, multi-home "judge" for which kitchen activity it is (the biggest real lever)
Rules 2c and 2d are careful patches. The real upgrade is learned judgment on the 527 tags (or the 192-d embedding) over **time**,
trained across many homes. Parth asked directly for "a smarter AI model for this judgment". The honest answer from 2.2: a bigger
or different audio model doesn't help, but **a trained judge does**, if its false meal calls are controlled.

Plan:
1. Data, by group (uploader or session) into tune and test with `eval/other_homes.py half()`:
   - Kitchen20: cooking = frying-pan, boiling-water, chopping, stove-burner, peel; washing = clean-dishes, water-flowing;
     eating = eat; other = book, cupboard, drawer, fridge, microwave, sweep, stove-fan, dishwasher, juicer, blender;
     leave cutlery and plates out (ambiguous).
   - DESED: Frying-main kitchen clips = cooking; vacuum, shaver, pets_alarms, speech = other; dish clips ambiguous.
   - ESC-50 household = other.
   - SINS dev all folds, cooking/dishwashing/eating/other. Down-weight it (0.15 per window) so one home doesn't dominate.
   - **Add the team's own kitchen recordings (section 4) as soon as they exist. That is the data that matters most.**
2. Features: `log(tags + 1e-4)`, standardised. Try the 192-d embedding and the concatenation too. Optionally mean and max over
   the last 3 windows (30 s context).
3. Model: multinomial logistic (sklearn), C chosen by GroupKFold on tune only. Prototype numbers at C=0.03: K20 group-CV
   balanced accuracy ~83%, meal 3-way ~82%.
4. Integration to test (mode A was better than B on dev):
   - **mode A**: head confident and non-meal → keep the head; head not_sure → the judge names the meal if p ≥ tau (0.7–0.8) and
     beats "other", else not_sure;
   - **mode B**: the judge also overrides the head's meal labels. That cost SINS too much (right 86 → 71 at tau 0.7).
   - Feed the judge's window outputs into rule 2c's stretch naming instead of the hand votes. Keep rule 2d.
5. **Gate before shipping:** on dev, false meal calls on non-meal sounds must not rise above the shipped rule's (K20 tune 16/290,
   DESED tune 0/179, SINS sessions 13/895), and wrong-activity must fall. If it can't meet that, don't ship. Say so in How sure.
6. Ship as `models/judge.json` (never touch `models/head.json`). Load it in `head.js` and `kettle/witness.py`. Parity tests and
   a `results/judge.json` with n and bootstrap CIs.

The prototype code isn't in the repo. Rebuild it from this description. `eval/kitchen_naming.py` is the harness to extend: add a
third "judge" column next to before and after.

### 3.3 P0: too much "Not sure" and confetti
The e2e showed a single cooking session split into 6–10 blocks with "Not sure" between them (window 5-s offsets give
`cooking 2, not_sure 1, cooking 4, not_sure 1, kitchen 1, ...`). The PDF measured 86% Not sure on public clips. Ideas, each
measured on SINS dev and tune:
- **Bridge across novel not_sure windows** inside a kitchen stretch when the not_sure window has kitchen tags (k ≥ TAU_K). Today
  novel windows are never bridged (`bridge()` in timeline).
- **Longer smoothing for meal labels** (5-window majority instead of 2-of-3).
- **A 5-s hop** (v3.1 S4): more windows means better smoothing. The device labels a window in ~0.2 s. Send only every second
  window to the server so storage doesn't double.
- **TV detection** (v3.1 S7, still to do): if Television or Radio ≥ tau (or continuous music/speech for 3+ windows with no
  kitchen kinds), label watching_tv even when novel.

### 3.4 P0: the real-kitchen measurement
See section 4. Without it, the How sure page still says "Our own kitchens: not measured yet". Judges will ask "did you test it in
a real kitchen?" and Parth already has, informally, with bad results. Turn that into a measured before/after.

### 3.5 P1: privacy-vs-data bug (v3.1 F1)
The server stores per-window "Speech", "Conversation" and similar tags while the family page says "Kettle never names voices".
Remove voice tags from the allow-list (`kettle/evidence_labels.json` → regenerate `web/public/js/sounds.js`). A judge spotting
this would hurt the honesty score.

### 3.6 P1: safety detectors: wire the strongest only
Shaurya's safety engine (`web/public/js/safety.js`, `kettle/safety.py`, `results/safety.json`) is done, tested and well measured
(scream 29/32, glass 13/16, 0 false Urgent in 12.3 h of ordinary home audio). It **is not wired into the kitchen screen, server
or family view.** Only after 3.1–3.4: wire the smoke alarm (U1), scream (U4) and crash+groan (U3) with the on-screen
"Are you OK?" check-in, plus an in-app red banner on the family view. Skip Web Push (v3.1 N) unless everything else is done.
The banner plus polling is enough for the demo.

---

## 4. Real-kitchen recording (needs a human; ask Parth at once)

At ~11:10 AM Parth was sent a notification asking him to record his mom cooking lunch, with her OK. He hadn't answered by
12:15 PM. Ask him whether a recording exists in `~/Downloads/`, or ask him to make one:
- Laptop on the counter, 1–2 m from the stove, QuickTime → New Audio Recording, 20–30 min.
- A **written log of clock times**: cooking, washing up (tap running), eating, quiet. A second short session on another meal
  becomes the held-out test.
- Consent from everyone audible (`eval/own_kitchen/CONSENT.md`, initials only).
- Audio stays local in `data/private/own_kitchen/` (git-ignored). **Never send it to any cloud model.** Parth's rule:
  no family audio to third parties without his OK.
- Labels go in `eval/own_kitchen/labels.csv` (`file,start_s,end_s,activity,session,notes`).
- The guide says the labeller shouldn't be the code author. Parth didn't write the code, and live notes taken while it happens
  are fine. Record who labelled in NOTES.md.
- Scoring: `eval/own_kitchen.py` exists for the 9 classes. Extend it to also run the full timeline (`timeline.blocks`, so 2c and
  2d apply) and report activity-level right, wrong and kitchen-activity, the way `eval/kitchen_naming.py` does. Score the old rule
  vs the new rule. **First session = dev (tune on it), second session = test (score once).**
- Also add 5 min of safe safety sounds if wiring 3.6: smoke alarm test button, a scream played from a speaker, a dropped pot.

---

## 5. Gotchas found this session
- The JS core `TAU_*` constants are hard-coded and **tested against `models/witness.json`** (`fixes.test.mjs`). Change both.
- `tools/export_web_fixtures.py` regenerates `web/public/model/witness.json` (as indices) and the sample days. The sample days
  now contain evidence numbers, so they use rules 2c and 2d.
- The parity fixtures (36 cases) don't specifically exercise 2c and 2d. The twin unit tests do. If you change those rules, update
  **both** test files.
- `MEAL` and `ACTIVE` now include `"kitchen"` in both twins. `CLASSES` (the head's 9) does not. The device never *sends*
  "kitchen" as a label: it is derived on screen.
- The window alignment in the browser is arbitrary. Offline checks should try several offsets (0, 2.5, 5, 7.5 s) like this
  session did. One offset can hide a flip that the browser shows.
- The Kitchen20 and DESED TEST halves have been looked at several times today. For any new rule, choose on `--dev` and use
  the real-kitchen session as the clean test.
- The e2e listens on Chromium's fake mic with `--use-file-for-fake-audio-capture`. Make clips 16 kHz mono WAV.

---

## 6. Triage of Shaurya's v3.1 backlog (after accuracy)
- **Keep, after section 3:**
  - safety wiring, minimal (3.6);
  - F4 landing hero bug ("Typing" on a Silence window; the TV sample opens on Conversation);
  - F5 sample days led by a real failure-and-fix story;
  - F10 How sure gets a "Kitchen naming" table from `results/kitchen_naming.json` and "What Kettle can't do";
  - FAQ answers for what changed (Q, only for features that exist);
  - finish neutral wording where cheap (core.js, kitchen.js, family.js in lint PENDING); the server storing `relation` and `room`.
- **Cut for today and list as next steps in the write-up:** Web Push with VAPID and escalation, viewer roles (M3), digest (M4),
  languages (M5), voice answer (M6), doctor summary (M9), multiple devices (3.4), wider audiences (3.5), PWA polish.
  Shaurya's push module and service worker stay in the repo, unwired.
- **Don't** retrain or edit `models/head.json` and **don't** rerun `python -m eval` (the held-out SINS test).

## 7. Packaging (humans; don't let accuracy work eat it)
- Write-up and video need the **before/after accuracy story**. The strongest beat: "In my own kitchen, Kettle called my mom's
  cooking 'eating'. We found why (one tag per 10 s), measured it, fixed it with stretch-level evidence, and here's the
  real-kitchen number." Every number comes from `results/*.json`.
- A rough video cut must exist by ~5 PM. Upload unlisted by 7 PM.
- Deploy to Cloudflare only with Parth's OK. Steps are in `docs/HANDOVER-v3.1.md` §0.11 and memory: `HOME=~`,
  deploy from a clean `git archive` of `web/` at the pushed commit, wrangler 4.x.
  **The live site still runs the OLD version without rules 2c and 2d**, so anyone testing live will still see the old misfires.
  Deploying is the next step once Parth says go.

## 8. Suggested order for the next session
1. Ask Parth for the kitchen recording (section 4). Score old vs new on it (dev session).
2. 3.1 named-sound misfires (kettle, tap, alarm split, microwave, door): ~1–1.5 h with measurement.
3. 3.3 confetti and Not sure (novel-window bridging, 5-window meal smoothing, TV detection): ~1.5 h.
4. 3.2 trained judge, only if the dev gate passes: ~1.5–2 h.
5. Score the held-out kitchen session once. Update How sure and FAQ from the results files.
6. 3.5 privacy fix: 20 min.
7. Deploy (with Parth's OK), private-window check, then the 3.6 safety wiring if time remains.
8. Hand the numbers to the write-up and video by 5 PM.

## 9. State at handover
- Branch `main` = this commit, on top of `cdd3671` (rules 2c, 2d) and `b4e1f93` (Shaurya's handover).
- All checks green at `cdd3671`:
  - npm test: 131 pass / 0 fail / 4 skipped;
  - pytest: 77 passed;
  - smoke test PASS;
  - check_metrics: 0 problems;
  - e2e: no errors.
- Not deployed. No background processes left running.

---

## 10. Merged in after this handover: the usability and detection round (branch `claude/dreamy-fermi-m2iux4`, Sun 15 Nov ~12:45 PM CT)

Merged on top of `05bf6ea`; every check above is still green after the merge (npm test 132 pass / 0 fail / 4 skipped, pytest 77,
smoke PASS, check_metrics 0 problems, e2e no errors). Web only (the Python twins are unchanged; the parity fixtures don't cover these).

- **Two on-device detection rules** (`web/public/js/sense.js roomRules`, after teach-this-kitchen, before rules 2c/2d see the window):
  - **Quiet:** a window at or below the kitchen's taught quiet level (`enrolment.floor`, which was computed but unused after the
    earlier merge) or −55 dBFS before setup is **Quiet**, whatever the head said. Room hum on a real laptop read as "Some
    activity" or "Not sure".
  - **Voices:** a window the head could NOT name whose loudest AudioSet speech class (0, 4, 5, 70) is ≥ 0.5 and above every
    body/bathroom class becomes **Conversation**. Indices are fixed in `listen.js`, so it survives removing voice names from the
    allow-list (3.5).
  - Measured with `web/test/sound_check.cjs` (real `/kitchen` page, Chromium fake mic) → `results/sound_check_web.json`
    (`round2`): room tone at −63 dBFS Quiet 3/3, three close voices Conversation 9/9, cooking/TV/washing up/conversation unchanged,
    dog/alarm/cough still Not sure; re-run after this merge with the same results. Limit: −55 dBFS is a guess; teaching sets the real floor.
- **Kitchen screen:** setup has 4 steps, the 4th is "Teach Kettle this kitchen"; until taught, a "First, teach Kettle" card sits on
  top of the listening screen; each teaching step waits for "I'm ready. Start step N". Condensed type and spacing.
- **Background listening:** worker clock (`js/tick.js`), one listening tab per home (BroadcastChannel), "Keep it in a small window"
  next to Pause, "● Listening" in the tab title, a warning before closing, microphone restart if windows stop, audio-context resume,
  a note on return ("N moments noted while out of sight"). Muted mic: "Kettle hears nothing at all"; exact silence is never sent.
- **Landing:** neutral names (Parth's switcher kept), hero list slides (FLIP) and shows allow-listed sound names, blocks glide.
  Sample days now use clips the frozen model labels as their recorded activity (DECISIONS row; `demo_cache/scenarios.json _about`),
  so the "Typing on Silence" hero bug (F4) is gone; "A usual morning" opens with one quiet clip.
- Details and judge Q&A: `docs/EXPLAIN.md` → "Usability round" and "Second pass after a hands-on test".

## 11. Handover v3.2 worked through (same branch, Sun 15 Nov ~1:05–3:15 PM CT)

| Item | Outcome | Evidence |
|---|---|---|
| 3.5 voice tags | **Done.** Off the allow-list; tests on both sides | `kettle/evidence_labels.json`, `web/test/fixes.test.mjs`, `tests/test_privacy_grep.py` |
| 3.1 named sounds | **Done.** Context rules (kettle, tap, microwave, timer split); pre-registered bar; only "TV or radio" passes, 14 names hidden (device-only); checks on hidden sounds say Can't tell; kettle check needs 2 windows | `eval/PREREGISTER-SOUNDS.md`, `eval/sounds.py` → `results/sounds.json` (kettle precision 16 → 44%, tap 48 → 67%, microwave 12 → 55% on test halves) |
| 3.3 confetti / TV | **Measured, not shipped** (no dev gain). Real cause: Kitchen20 is 80.9% Not sure because whole sessions are novel | `eval/confetti.py` → `results/confetti.json` |
| 3.2 trained judge | **Measured, not shipped**: fails the gate written before the run (0.9: wrong 4 → 0, false meal 41 → 30, right 218 → 212). `models/judge.json` not written; K20 TEST untouched | `eval/judge.py` → `results/judge.json` |
| 3.4 real kitchen | **Scorer ready** (`python -m eval.own_kitchen --timeline --session <name>`, old vs new rule); **recording still needed from a person** | `eval/OWN_KITCHEN_GUIDE.md` |
| 3.6 safety | **Wired, minimal**: smoke alarm, crash then cry/stillness, screaming, "I need help"; "Are you OK?" on the kitchen; red banner on the family view; no push | browser run: synthetic smoke alarm → banner in 12 s; 17 ordinary sounds → no alert |
| §6 keep | How sure section from `results/*.json` (`tools/export_accuracy.py`); FAQ/README alert wording; F4 gone with the new sample days. F5 (a failure-and-fix sample day) not done | `web/public/js/beyond.js` |

Kitchen20 was cloned and embedded on this machine (`data/raw/kitchen20`, `data/emb/ced-tiny/kitchen20/all.npz`, both git-ignored).
DESED is not here, so `eval/kitchen_naming.py` can't be re-run on this machine (its committed results are unchanged).
Checks at the last commit: npm 137 pass / 0 fail; pytest 79; smoke PASS; check_metrics 0 problems; e2e no errors.
Not deployed (needs Parth's OK and his Cloudflare login).
