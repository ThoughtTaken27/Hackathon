---
name: overnight
description: "The kickoff-night autopilot: read the brief, triage all four tracks, research existing products, tear them down, write the full PRD, then build the product overnight with every design skill, tests and a morning hand-off. Run by the repo owner on their own computer. Use only when asked to run or resume the overnight kickoff."
argument-hint: "[research | build | status]"
disable-model-invocation: true
---

# Overnight kickoff

Two phases, each with its own playbook. Both are written for an unattended run; when a human is present, the same playbooks apply but you may ask them things.

| Phase | Playbook | Ends when | Output |
| --- | --- | --- | --- |
| A. Research → PRD | `.claude/overnight/phase-a.md` | `.overnight/PRD_DONE` exists | `docs/BRIEF.md`, `docs/research/*`, `docs/DECISIONS.md`, `docs/PRD.md` |
| B. Build | `.claude/overnight/phase-b.md` (run under `/goal` with `.claude/overnight/goal.txt`) | `.overnight/BUILD_DONE` exists | the working product, `results/`, `docs/screenshots/`, `docs/EXPLAIN.md`, `docs/MORNING-BRIEF.md` |

## How it is normally started (unattended)

In a terminal on the owner's computer, before 11 PM CT:

```bash
bash .claude/overnight/run.sh check
```

```bash
bash .claude/overnight/run.sh
```

The script keeps the computer awake, waits for kickoff, takes the brief (pasted, or found in Gmail), runs Phase A, then starts Phase B in a **new session** on Opus at high effort under `/goal`, and restarts it after a usage-limit pause until the build is done or it is 8:30 AM CT. Progress: `bash .claude/overnight/run.sh status`.

## When invoked by hand (`/overnight …`)

- `research` (or no argument): read and carry out `.claude/overnight/phase-a.md`.
- `build`: read `.claude/overnight/phase-b.md`, then work until every condition in `.claude/overnight/goal.txt` holds. Tell the human they can instead run `/goal` with that text to keep it going unprompted.
- `status`: summarise `.overnight/STATE.md`, which done-files exist, the last commits, and what remains.

## Rules that hold in every mode

- `AGENTS.md` §0 stop-the-line rules apply overnight exactly as in the day. No project code before Fri Nov 13, 11 PM CT (a hook enforces it).
- **Local only: never push, never open a PR.** A human reviews the branch in the morning.
- The brief comes first; prepared ideas in `docs/IDEAS.md` are a starting point, not a commitment.
- Rebuild from scratch and credit the original. Public surface only when studying existing products (`product-teardown` skill; REA's `reverse-engineer-anything` skill and tools where installed and where we are allowed to examine the target). Never copy code, assets or paid content.
- The frozen test set is labelled by a teammate, not by the build session. Overnight numbers are dev-set numbers.
- Leave the team able to explain everything: `docs/EXPLAIN.md` and `docs/MORNING-BRIEF.md` are part of "done".
