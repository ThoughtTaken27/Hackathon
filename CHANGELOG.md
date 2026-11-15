# Changelog

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
