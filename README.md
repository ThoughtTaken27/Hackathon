# Veritas AI International High School Hackathon 2026

Team repo for the [Veritas AI International High School Hackathon](https://highschoolhackathon.org/) (Nov 14–15, 2026, virtual).

> **Status: pre-kickoff.** This repo holds planning docs only. Per the rules, **all project code must be written during the 48-hour window** (starts 12:00 AM ET Sat Nov 14 = 11:00 PM CT Fri Nov 13). Do not add code before then.

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

Full research doc (Claude Docs): [Veritas AI Hackathon — Health Idea Research & Game Plan](https://claude.ai/artifact/KxEQasfso3e2RMTBuqrS8v)

## Repo layout

```
AGENTS.md          Operating manual for every AI agent: rules, rubric, clock, practices
CLAUDE.md          Imports AGENTS.md so Claude Code loads it automatically
.claude/agents/    Haiku-pinned workers: scout (search), builder (routine code), runner (run + report)
docs/BRIEF.md      Paste the challenge brief here at kickoff
docs/DECISIONS.md  Locked idea, owners, interfaces (filled at kickoff)
docs/EXPLAIN.md    Plain-English explanation of every module (Q&A prep, filled as we build)
docs/              Planning docs (this is all that exists before kickoff)
```

The code layout gets decided at kickoff, once the idea is locked. See `docs/KICKOFF.md`.
