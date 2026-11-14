# Veritas AI International High School Hackathon 2026

Team repo for the [Veritas AI International High School Hackathon](https://highschoolhackathon.org/) (Nov 14–15, 2026, virtual).

> **Status: pre-kickoff.** This repo holds planning docs and team tooling only (Claude Code config, hooks, templates; no project logic). Per the rules, **all project code must be written during the 48-hour window** (starts 12:00 AM ET Sat Nov 14 = 11:00 PM CT Fri Nov 13). Do not add code before then.

## Key times

| Event | Eastern (official) | Central |
| --- | --- | --- |
| Registration closes | Fri Nov 13, 11:59 PM | Fri Nov 13, 10:59 PM |
| **Kickoff: briefs emailed, 48h starts** | **Sat Nov 14, 12:00 AM** | **Fri Nov 13, 11:00 PM** |
| Code-complete target (full demo flow) | Sat Nov 14, 7:00 PM | Sat Nov 14, 6:00 PM |
| Our submit target | Sun Nov 15, 10:00 PM | Sun Nov 15, 9:00 PM |
| **Submissions close (no late entries)** | **Sun Nov 15, 11:59 PM** | **Sun Nov 15, 10:59 PM** |
| Finalists announced | Wed Nov 18 | Wed Nov 18 |
| Live finals (5-min demo + Q&A) | Sat Nov 21 | Sat Nov 21 |

## New teammate? 15 minutes

1. Follow [`docs/TEAM-SETUP.md`](docs/TEAM-SETUP.md) §2: install Git, Python and Claude Code, clone, run `claude`, **trust the folder**.
2. The first reply should show the **hackathon briefing** (CT time, phase, next deadline). That means the team hooks are working.
3. Type `/start`. When a task is finished, type `/done`.

| Command | When |
| --- | --- |
| `/kickoff` | Fri 11 PM CT, once, whole team |
| `/start [issue#]` · `/done [issue#]` | Every session / every task |
| `/explain <module>` · `/explain quiz <module>` | After each change · Q&A drills |
| `/checkin` | Team check-ins |
| `/ship-check` | Sun 5 PM CT, before submitting |

## Start here

0. [`AGENTS.md`](AGENTS.md): the operating manual every AI agent (and teammate) follows. Read it once.
1. [`docs/KICKOFF.md`](docs/KICKOFF.md): what to do in the first hour after the brief drops.
2. [`docs/RULES-AND-RUBRIC.md`](docs/RULES-AND-RUBRIC.md): rules, scoring, what we submit.
3. [`docs/IDEAS.md`](docs/IDEAS.md): our pre-researched ideas (HeatRx main, ChairCheck backup) and the decision table.
4. [`docs/SCHEDULE-AND-ROLES.md`](docs/SCHEDULE-AND-ROLES.md): the 48-hour plan and who does what.
5. [`docs/DATA-SOURCES.md`](docs/DATA-SOURCES.md): APIs and datasets, checked on Nov 13, with gotchas.
6. [`docs/TEAM-SETUP.md`](docs/TEAM-SETUP.md): accounts, keys, Claude Code, git workflow.
7. [`docs/SUBMISSION.md`](docs/SUBMISSION.md): write-up template, video script, Q&A prep, final checklist.
8. [`docs/AI-USAGE-LOG.md`](docs/AI-USAGE-LOG.md): log every AI tool use here (we must credit them).

Full research doc (Claude Docs, ask the repo owner to share it): [Veritas AI Hackathon — Health Idea Research & Game Plan](https://claude.ai/artifact/KxEQasfso3e2RMTBuqrS8v)

## Repo layout

```
AGENTS.md          Operating manual for every AI agent: rules, rubric, clock, practices
CLAUDE.md          Imports AGENTS.md so Claude Code loads it automatically
.claude/settings.json  Shared Claude Code config: default model, safe-command allowlist, hooks
.claude/hooks/     Session briefing (clock + git state) and guardrails (secrets, pre-kickoff code, force-push)
.claude/skills/    Team slash commands: /kickoff /start /done /explain /checkin /ship-check,
                   plus build/design skills /agentic-build /ui-polish /component-craft
                   /frontend-design /emil-design-eng /apple-design
.claude/agents/    Haiku-pinned workers: scout (search), builder (routine code), runner (run + report)
.github/           Issue + PR templates (done-check, explain-back, AI-usage row)
.env.example       Key names only; copy to .env (git-ignored)
docs/WRITEUP.md    Living one-page write-up + 2-minute video script
docs/BRIEF.md      Paste the challenge brief here at kickoff
docs/DECISIONS.md  Locked idea, owners, interfaces (filled at kickoff)
docs/EXPLAIN.md    Plain-English explanation of every module (Q&A prep, filled as we build)
docs/              Planning docs (this is all that exists before kickoff)
```

The code layout gets decided at kickoff, once the idea is locked. See `docs/KICKOFF.md`.
