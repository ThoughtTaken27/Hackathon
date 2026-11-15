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
