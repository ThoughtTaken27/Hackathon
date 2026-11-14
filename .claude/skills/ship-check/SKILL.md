---
description: Pre-submission audit (Sun 5–9 PM CT). Fresh-clone run with no keys, secret scan of all git history, numbers vs results/, README and write-up checks. Reports pass/fail with evidence; never submits.
disable-model-invocation: true
---

Run the AGENTS.md §11 ship checklist and prove each line. Report evidence for every item; the humans submit.

1. **Fresh clone, no keys.** In a temp directory: `git clone` the repo's origin URL, check out `main`, create a venv, `pip install -r requirements.txt`, then run exactly the commands the README gives, with every `*_API_KEY` / `*_TOKEN` env var unset. Time it (target: under ~5 minutes). It must work from the committed `demo_cache/` alone. Paste the commands and the decisive output lines.
2. **Smoke + eval.** `python smoke_test.py` and `python -m eval` in the fresh clone. Confirm `results/metrics.json` regenerates.
3. **Secrets in history.** Scan every commit, not just the current files:
   `git log -p --all | python -c "import sys; sys.path.insert(0, '.claude/hooks'); import guard; print(guard.find_secrets(sys.stdin.read()) or 'no secrets found')"`
   Also check notebook outputs (`*.ipynb`) for keys and personal data. Any hit means: rotate the key now and tell the human (history rewrite is a human decision).
4. **Numbers match.** Every number in `README.md`, `docs/WRITEUP.md` and the video script must equal a value in `results/` and carry its N. List each number with where it came from; flag any that don't match.
5. **Docs.** README top has: one-line what + who, screenshot/GIF, results table, how to run, limits, "prototype, not medical advice", credits. Write-up fits on one page (count words: roughly 500–650) and has problem + cited stat, persona, pipeline, baseline, slices, 3 failures, limits, credits including every AI tool. No names or school in the write-up or video (Round 1 is blind).
6. **Credits.** `docs/AI-USAGE-LOG.md` and `docs/DATA-SOURCES.md` cover every tool, dataset, API, library and pretrained model used. `docs/EXPLAIN.md` has an entry for every module.
7. **Access.** Remind the human to open the repo/Colab link in an incognito window and confirm the video is unlisted and under 2:00.

Output a checklist with ✅ / ❌ and one line of evidence each, then the fix list ranked by risk to the submission. Time left until the 9 PM target and the 10:59 PM hard close goes on the first line.
