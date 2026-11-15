# Changelog

## Sun Nov 15, ~2:45–4:00 PM CT: trained sound head (v2), "Talking / TV", drag to read the day on phones
- Why: only 1 of 15 everyday sound names passed the pre-registered bar with hand-written rules (most were caught, but too
  often named on look-alikes); on a phone the day bar's thin stretches were too small to tap; "TV" was shown when people talked.
- Sound head: `eval/sound_head.py` (pre-registered in `eval/PREREGISTER-SOUNDS-V2.md` and committed before its one test run):
  one logistic regression per sound on the CED-tiny embedding (+ AudioSet log-odds where tune CV chose it), every choice from
  grouped 5-fold CV on the tune halves. **8 of 15 names now pass** (kettle, chopping, running water, cupboards/drawers, timer
  beep, talking/TV, typing, footsteps); frying, dishes, microwave, glass, vacuum and door stay hidden; blender failed on tune.
  `results/sound_head.json`; device file `web/public/model/sound_head.json`; `sense.js kindsOf()` / `kettle/kinds.py named()`
  use it when the embedding is there (same privacy veto). JS/Python parity: `web/test/sound_head.test.mjs`.
- "Talking / TV": the TV activity, the talk-or-TV state and the TV sound name all read "Talking / TV" (JS and Python twins).
- Family view: drag a finger (or the mouse) along the day bar; a line and a time + label bubble select the stretch under it and
  open its card. Taps, clicks and arrow keys still work; vertical swipes still scroll (`web/public/js/ui.js dayBar`).
- Not shipped: rule 2g (fill "Not sure" from the sound head) cut "Not sure" on Kitchen20 tune 80.9% → 75.0% but the gate
  written first asked for 10 points (`eval/sound_fill.py`, `results/sound_fill.json`).
- How sure, write-up, video and demo scripts updated from the results files. Checked: 140 web tests, 79 Python tests, smoke
  test, `eval.check_metrics` 0 problems, browser e2e errors [], phone drag test (iPhone 13 emulation).

## Sun Nov 15, ~12:10 PM CT: kitchen naming from evidence (rules 2c, 2d)
- Why: Parth ran Kettle in his own kitchen. Pots and cutlery while cooking showed as "washing up" and "eating".
- Changed: `kettle/witness.py` (evidence numbers cook/water/mouth, `name_kitchen`, `votes`), `kettle/timeline.py`
  (`name_stretches`, `_absorb`), `kettle/labels.py` ("kitchen" = "Kitchen activity"), `web/public/js/core.js` (twin),
  `web/public/js/head.js` (device sends the three numbers), `web/src/household.js` (server keeps them),
  `models/witness.json` (lists and thresholds), CSS `--act-kitchen`.
- Measured: `python -m eval.kitchen_naming` -> `results/kitchen_naming.json`. Thresholds picked on SINS dev and TUNE halves;
  TEST halves scored three times (process note in the file). Real-kitchen measurement still missing.
- Checked: 131 web tests, 77 Python tests, smoke test, `eval.check_metrics` 0 problems, browser e2e on a frying + cutlery clip
  (before: "cooking, washing up, cooking"; after: "kitchen activity and cooking").
- Also: `web/test/e2e.py` updated for the v3.1 setup questions.

## Sun Nov 15, ~1:10–1:45 PM CT: privacy (3.5) and named-sound misfires (3.1)
- Why: the server stored "Speech" per window while the family page says Kettle never names voices; Parth's live test showed
  "Kettle or a hot drink" and "Running water" on frying + cutlery with no kettle or tap.
- 3.5: voice tags (Speech, Conversation, Chatter, Hubbub, Narration) removed from `kettle/evidence_labels.json`; `sounds.js` and
  `evidence.json` regenerated. Tests on both sides.
- 3.1: context rules in `eval/beyond.py CONTEXT` → `kinds.json` (`beat`, `min`, `shown`), applied by `sense.js kindsOf()` and
  `kettle/kinds.py named()`: kettle = Boiling/Steam/Whistle only and louder than frying, tap, dishes, vacuum and fan; tap = tap/sink
  only and louder than frying; microwave ≥ 0.5 and louder than vacuum, fan, air conditioning, engine; "An alarm or beeping" is
  now "Timer or appliance beep" (Beep, Buzzer, Alarm clock; never smoke or fire alarm classes).
- Measured: `python -m eval.sounds` → `results/sounds.json`, pre-registered in `eval/PREREGISTER-SOUNDS.md` before the test halves
  were scored (once). Test halves (Kitchen20 by uploader, ESC-50 by source, SINS dev folds 3-4, synthetic alarms, Nonspeech7k):
  kettle precision 16.0 → 44.0% (false names per 1,000 windows 17.06 → 3.02), running water 47.8 → 67.1% (15.69 → 5.97),
  microwave 11.9 → 54.5% (18.55 → 0.74). Bar (precision ≥ 90%, recall ≥ 40%): **only "TV or radio" passes** (97.8%, recall 79.2%);
  every other name is now hidden (computed on the device for the privacy veto and safety concerns, never sent or listed).
  A check on a hidden sound says "Can't tell"; a kettle check needs 2 windows of one block. The family's check editor offers
  only shown sounds. Kitchen20 was embedded on this machine with the app's encoder (`data/emb/ced-tiny/kitchen20/all.npz`).
- Also: `eval/beyond.py` crashed on the new "kitchen" meal label; fixed (thresholds, enrolment and novelty numbers unchanged).

## Sun Nov 15, ~1:45–2:20 PM CT: 3.3 and 3.2 measured, not shipped; 3.4 scorer ready
- 3.3 (`eval/confetti.py` → `results/confetti.json`): rule 2e (bridge novel kitchen-tagged gaps) and 2f (TV named → TV) on SINS dev
  stitched and on Kitchen20 TUNE stitched into 6-clip sessions. 2e: no change on either set; 2f: SINS pieces per session
  2.58 → 2.56, false blocks per hour 1.78 → 1.82, nothing on Kitchen20. **Neither ships.** The real finding: on Kitchen20, 80.9%
  of the time is "Not sure" because whole sessions are "unlike anything it learned", not short gaps.
- 3.2 (`eval/judge.py` → `results/judge.json`): logistic judge on 527 log-tags, trained on Kitchen20 TUNE, ESC-50 TUNE and SINS dev
  (weight 0.15), group-CV out-of-fold. Best trade: cutoff 0.9 cuts wrong activity 4 → 0 and false meal calls 41 → 30, but names
  6 fewer real meals (218 → 212); cutoff 0.8 names 18 more but adds one false call on Kitchen20. **Fails the gate written before
  the run** (it passes the handover's narrower gate at 0.9 only). Not shipped; `models/judge.json` not written; Kitchen20 TEST not
  touched. DESED is not on this machine.
- 3.4: `python -m eval.own_kitchen --timeline --session <name>` scores a labelled recording old rule vs new rule; dry-run checked.

## Sun Nov 15, ~2:20–2:50 PM CT: safety wired, minimal (3.6)
- The kitchen device runs Shaurya's safety engine (`web/public/js/safety.js`) on every window: detector scores and the alarm-pattern
  count come from `listen.js` (device only, never sent). Wired: smoke or fire alarm (U1), a crash then a cry or stillness (U3),
  screaming (U4), and "I need help" from the check-in. A crash or screaming first asks "Are you OK?" on the kitchen screen (read
  aloud) with "I'm OK" / "I need help"; no answer in time, or "I need help", sends an Urgent alert. Not wired: CO alarm, repeated
  distress (U5), Worth-a-look notes, Web Push.
- Server (`web/src/household.js`): kitchen action `alert` stores only kind, time and how the check-in ended (last 20); family route
  `seen` marks one seen. Family view: a red "Urgent" banner per unseen alert from the last 12 hours, "Call <parent> now. Kettle
  can't call for help itself." Consent screen says so.
- Checked: API test (roles, consent gate, stored fields); browser run with a synthetic T3 smoke-alarm pattern through Chromium's
  fake microphone: alert stored after 12 s, kitchen says "Kettle told Asha", family banner shown, cleared by "I've seen this";
  17 ordinary and confusing sounds (cooking, TV, voices, cough, crying, laughing, glass breaking, siren, dog, alarm clock, knock),
  about 4 windows each: no alert.

## Sun Nov 15, ~2:50–3:10 PM CT: How sure, FAQ, a family-page fix (handover §6)
- How sure: new section "Kitchen naming after a live test in a real kitchen" (rules 2c/2d before → after per set), the named-sound
  table (precision, recall, false names, shown/hidden) and "Tried and not shipped" (judge, 2e/2f), all from
  `web/public/data/accuracy.json` written by `tools/export_accuracy.py` from `results/*.json`.
- FAQ, family footer, README: the "no alerts" wording was out of date after 3.6; now says which urgent notes exist and that
  Kettle can't call for help.
- `/family` opened without a link threw an error (listeners on elements that aren't there); guarded.
- F4 (hero "Typing" on a Silence window, TV sample opening on Conversation): gone with the sample days rebuilt this morning.
