---
description: Finish a task the team way. Verify, write the explain-back and AI-usage row, commit, rebase on main, push, open a PR and update the issue. Use when a task is done or before ending a session.
argument-hint: "[issue number, optional]"
disable-model-invocation: true
---

Close out the current task so a teammate can pick it up and a judge can trust it (AGENTS.md §5, §8).

1. **Verify.** Run the task's done-check, then `python smoke_test.py` if it exists. Paste each command and its real output. If anything fails, stop: report it and fix or stub. Never merge red.
2. **Review the diff.** `git diff main...HEAD --stat` and read the diff. Remove dead code, commented-out blocks, TODO stubs and debug prints. Check every number in code or docs came from a script run, not typed by hand.
3. **Explain-back.** Append to `docs/EXPLAIN.md` under the module name: what it does, why this way and what we rejected, known limit, one likely judge question and our answer (3 sentences + Q&A). Add a decision-log row to `docs/DECISIONS.md` if a choice was made.
4. **Credit.** Add a row to `docs/AI-USAGE-LOG.md` (teammate role, tool, what it did, files, who reviewed it). Add any new dataset, API, library or model to `docs/DATA-SOURCES.md`.
5. **Commit and sync.** Small commit(s) with clear messages (the commit hook scans for secrets). `git pull --rebase origin main`, resolve conflicts carefully (ask if unsure whose change wins), rerun the smoke test, then `git push -u origin HEAD`.
6. **PR.** If `gh` works: `gh pr create --fill` and fill the PR template; put `Closes #<issue>` in the body if there is one (`$ARGUMENTS`). Otherwise print the GitHub compare URL. Ask a teammate to review: the reviewer must be able to explain the change. If nobody can review within ~15 minutes and the smoke test passes, the human may merge it themselves.
7. **Report** in the AGENTS.md §8 format: result · files changed · how to verify (one command) · explain-back · next best step ranked by points.

If the session is ending mid-task: commit work-in-progress to the branch (never to main), push it, and comment on the issue what's done, what's next and what's blocked.
