# CLAUDE.md: shared instructions for every teammate's Claude session

This repo is a team's entry for the Veritas AI International High School Hackathon (Nov 14–15, 2026). Several teammates run their own Claude Code sessions against it at the same time. Read this file fully before doing anything.

## Hard rules (breaking these can disqualify the team)

1. **No project code before kickoff.** Kickoff is **12:00 AM ET Sat Nov 14 (11:00 PM CT Fri Nov 13)**. Before then, only docs, planning and account setup are allowed. If the time is before kickoff, refuse to write project code and say why.
2. **Every teammate must be able to explain every line.** Finalists are questioned live about their code. Write simple, readable code. Prefer a few clear functions over clever abstractions. After writing anything non-trivial, give the teammate a short plain-English explanation they could repeat to a judge.
3. **Credit everything.** Every dataset, API, library, pretrained model and AI tool used must be credited in the write-up. When you (Claude) write or substantially change code, add a row to `docs/AI-USAGE-LOG.md` (date/time, teammate, tool, what it did, files).
4. **Public or synthetic data only.** Never use real patient data. No recording anyone without consent.
5. **Health safety.** This is a prototype, not medical advice: say so in the app and the write-up. Never output advice to stop or change a medication. If something is not in our rule list, show "not in our list", never "safe".
6. **Never commit secrets.** API keys go in environment variables or Colab secrets, never in code or notebooks. `.env` is git-ignored.

## How we work

- Docs first: `README.md` and `docs/` hold the plan. `docs/KICKOFF.md` is the first-hour checklist; `docs/SCHEDULE-AND-ROLES.md` has the timeline and roles.
- After kickoff, the locked idea, problem statement, track and module owners are recorded in `docs/DECISIONS.md`. Read it before starting work and follow it.
- **Git:** each teammate works on their own branch (`<name>/<feature>`), pulls often, and merges small changes into `main` frequently. Never force-push `main`. Never rewrite someone else's branch. Pull before you start and before you push.
- Stay inside the module you were assigned. If you need to change a shared interface (function names, data formats), say so in chat so the teammate can tell the others first.
- Keep the scope to the MVP until the full demo flow works end to end (target: Sat 6 PM CT). Stretch goals only after that.
- Evaluation matters (15 points for testing and honesty). The person who labels the test set should not be the person who wrote the code being tested.

## Known gotchas (checked Nov 13)

- **Open-Meteo returns 429/"Daily API request limit exceeded" from this cloud container** (shared IP). Use NWS `api.weather.gov` (US, no key, send a User-Agent), NOAA NCEI or Meteostat for history, or call Open-Meteo from Colab/a laptop. Cache all API responses to disk so demos and evaluation don't depend on the network.
- NLM RxNav (RxNorm/RxClass) works, no key, about 20 requests/second. Its drug-drug interaction API was discontinued in Jan 2024: do not use it.
- It's November, so there's no live US heat. Replay a historical heatwave or use a Southern Hemisphere city.
- The CMS Part D provider-level file is huge. Use the data.cms.gov API with filters or the state-level file.
- See `docs/DATA-SOURCES.md` for the full list.

## Style

- Python first (the team uses Google Colab). Keep dependencies few and pinned in `requirements.txt`.
- Short functions, clear names, comments that explain *why*. No dead code.
- Times in docs: give Central (the team's zone) and Eastern (the official zone) where it matters.
