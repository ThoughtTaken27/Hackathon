# Morning brief (read this first, Saturday 9 AM CT)

Written by the overnight build at <CT time>. Everything is on the local branch `overnight/build`. Nothing was pushed.

## 1. What exists now (two minutes)
- **The idea in one sentence:**
- **Track and why:**
- **Run it:** the exact commands, and what you should see. Screenshot: `docs/screenshots/…`
- **Status against the plan:** milestone table (M1–M7: done / partial / not started), honestly.
- **Numbers so far:** from `results/metrics.md`, each labelled "dev set, N=…". Not final.

## 2. What is not done or not right
Ranked by points at risk. For each: what, why, the fix, how long.

## 3. Decisions made overnight that a human should confirm
Each with the alternative that was rejected and how to reverse it. Start with the idea and track choice: if the team disagrees, Plan B is in `docs/PRD.md` §15.

## 4. First hour for the lead
1. Read `docs/PRD.md` §0, §5, §6 and `docs/EXPLAIN.md`.
2. Run the app and the smoke test yourself.
3. Review the diff: `git log --oneline main..overnight/build` and `git diff main..overnight/build --stat`.
4. If it's good: push the branch and open a PR to `main` (the team decides; the overnight run never pushes).
5. Add the LLM key to `.env` and re-record `demo_cache/` if the overnight run used the no-key fallback.

## 5. Team lanes (the two teammates are beginners; these are copy-paste ready)

### Lane A: Evaluator (must not edit the app code)
Goal: the frozen test set and the honest numbers (15 Round 1 points).
- Task 1: label the test set. What to open, the labelling guide path, how many items, how long.
  Paste into your Claude Code:
  > `<prompt>`
- Task 2 … (each: prompt, files you may touch, done-check command)

### Lane B: Storyteller
Goal: one-page write-up, 2-minute video, README top (15 points, plus the first impression for all the rest).
- Task 1 … (prompt, files, done-check)

### Lane C: Lead
Goal: review, integrate, fix the top failures, keep `main` running.
- Task 1 …

## 6. Explain it to a judge (everyone, 20 minutes)
Each person runs `/explain quiz <module>` for the modules listed here until they score 4/5:
- Module list with the one thing to know about each.

## 7. Today's clock
Check-ins 9 AM, 1 PM, 6 PM (GATE: full flow works), 10 PM (first test-set metrics). What must be true at each.

## 8. Credits and logs
Confirm `docs/AI-USAGE-LOG.md` and `docs/DATA-SOURCES.md` cover everything made overnight.
