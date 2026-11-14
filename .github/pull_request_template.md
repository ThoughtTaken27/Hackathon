## What and why

<!-- One or two sentences. Which rubric line does this move (AGENTS.md §1)? -->

Closes #

## How to verify

```bash
python smoke_test.py
```

<!-- Paste the real output, or the done-check command and its output. -->

## Checklist

- [ ] Smoke test passes on this branch after `git pull --rebase origin main`
- [ ] No keys, tokens or personal data in the diff (the commit hook also checks)
- [ ] No dead code, commented-out blocks or TODO stubs
- [ ] Numbers in code/docs come from a script run, not typed by hand
- [ ] `docs/EXPLAIN.md` entry added/updated (what · why · limit · judge Q&A)
- [ ] `docs/AI-USAGE-LOG.md` row added; new data/libraries credited in `docs/DATA-SOURCES.md`
- [ ] Reviewer can explain this change out loud
