---
description: Team check-in summary (Sat 9 AM, 1 PM, 6 PM, 10 PM; Sun 9 AM, 1 PM, 5 PM). Done / next / blocked per person, status against the clock, top risk and the cut to make if behind.
model: claude-haiku-5-5
disable-model-invocation: true
---

Build a 10-line check-in from evidence, not guesses (`docs/SCHEDULE-AND-ROLES.md`).

1. Run `TZ=America/Chicago date`; name the phase and the next gate (AGENTS.md §3).
2. `git fetch origin` then `git log origin/main --since="4 hours ago" --format="%h %an %ar %s"` and `git branch -r --sort=-committerdate | head -10`.
3. If `gh` works: `gh pr list --state open` and `gh issue list --state open` (with assignees).
4. Check whether `python smoke_test.py` exists and passes, and whether `results/metrics.json` exists and when it was last updated.

Report, ten lines max:
- **Clock:** phase, time to next gate, on track / behind (one line).
- **Per teammate** (by git author / assignee): done · next · blocked. Write "unknown" rather than inventing.
- **Main runs?** smoke test result.
- **Numbers:** does a metrics table exist yet (required by Sat 10 PM)?
- **Top risk** and, if behind schedule, **the one cut** to make now (AGENTS.md: cut scope, don't add hours).

Read-only: change no files and post nothing unless the human asks.
