# Real-kitchen test: pre-registered (plan A1, A3, A4, G3)

Written **before** any recording, so the metrics and pass bars can't be chosen after seeing results. The git commit
time of this file is the registration time. Report against these bars even if the results disappoint.

How to record and label: `eval/OWN_KITCHEN_GUIDE.md` (consent, labeller who didn't write the code, straddle rule).
Raw audio stays in `data/private/` and is never committed or published; only labels and metrics are.

## What to record (each kitchen, laptop where a parent would really put it)

| Part | Length | Purpose |
|---|---|---|
| Setup: quiet, washing up, cooking (Kettle's "Teach Kettle this kitchen" step) | ~3 min | enrolment (A3) |
| Later stretch: cooking, washing up, eating, quiet, TV, a conversation | 20–30 min | the test |
| Empty kitchen with appliances running: fridge, range hood, microwave, dishwasher/washing machine, vacuum | 5 min | false Cooking (A4) |
| Optional: cooking with the TV on; two people talking while cooking | 5 min each | A7/A14 slices |

At least 3 kitchens (different sizes, appliances, cooking styles: microwave-only, pressure cooker, frying). Record the
cooking style per kitchen for a per-style table (A10).

## Metrics (per kitchen, then pooled with a bootstrap over kitchens; call it a small pilot)

1. Kitchen activity noticed: share of labelled cooking/washing-up/eating windows shown as any of the three.
2. False kitchen blocks per hour of the appliances-only recording (target: close to 0).
3. Share of listened time shown as Not sure.
4. Macro F1 over the activities present.
5. Each of 1–4 **before and after** the 3-minute setup, scored only on the later stretch (never on setup windows).
6. Named sound types: for each labelled kettle boil, tap run, doorbell: was it named within ±30 s?

## Pass bars (fixed now)

| Metric | Bar |
|---|---|
| Kitchen activity noticed, after setup | ≥ 70% |
| False kitchen blocks, appliances-only | ≤ 1 per hour |
| Not sure share, after setup | ≤ 30% |
| After setup vs before | Not sure share lower, false kitchen not higher |

## Known gaps before running

- `eval/own_kitchen.py` scores the frozen model; scoring the after-setup condition needs the setup windows passed to
  `eval/beyond.py:adapt` (same rule as the browser). Not written yet.
- The browser computes everything from the live microphone; for scoring, replay the recordings through
  `web/test/e2e.py`-style fake-microphone runs or through the Python pipeline. Say which one was used.
