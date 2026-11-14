---
description: Start a work session the team way. Sync with main, read the decisions, claim one task, make a branch, and state the plan, rubric line and model tier. Use at the start of every session.
argument-hint: "[issue number or short task name]"
disable-model-invocation: true
---

Run the AGENTS.md session-start ritual. Be quick: this should take under two minutes.

1. **Clock.** Use the hackathon briefing from the SessionStart hook if it is in context; otherwise run `TZ=America/Chicago date` and name the phase from AGENTS.md §3. Before kickoff, only docs/setup work is allowed: say so if the task is code.
2. **Sync.** `git status`. If there are uncommitted changes, ask before touching them. Then `git switch main && git pull --rebase origin main`.
3. **Read** `docs/DECISIONS.md` (idea, owners, contracts) and `docs/BRIEF.md`. Skim `docs/EXPLAIN.md` for the module you'll touch.
4. **Pick one task.** Task = `$ARGUMENTS` if given. If `gh` works: `gh issue list --state open` and `gh issue list --assignee @me`; if `$ARGUMENTS` is an issue number, `gh issue view` it, then claim it with `gh issue edit <n> --add-assignee @me` and a one-line comment. Without `gh`, ask the human which task. If the task is in another teammate's module (per `docs/DECISIONS.md`), say so and ask before going on.
5. **Branch.** `git switch -c <handle>/<short-task>`, where handle is the first word of `git config user.name` in lowercase. If you're already on a task branch, rebase it on main instead.
6. **State the plan in one reply:** task · rubric line and points (AGENTS.md §1) · model tier and why (AGENTS.md §9; suggest `/model` if the session is on the wrong tier) · the done-check command · 3–5 step plan. Then wait for "go" unless the human already said go.

Rules while working: one task per session, small diffs, run it before claiming it works, 20-minute rule when stuck. Finish with `/done`.
