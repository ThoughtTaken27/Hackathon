# Overnight Phase B: build the product in docs/PRD.md

You are running unattended on the repo owner's own computer, overnight. Nobody will answer questions: never wait for a human. Decide, record the decision in `docs/DECISIONS.md`, and move on. The team wakes up at 9 AM CT and must be able to run, understand and explain everything you made.

**Read first, every time you start:** `.overnight/STATE.md`, `docs/PRD.md`, `docs/DECISIONS.md`, `AGENTS.md`. If STATE says work is in progress, you are a restart (the session may have hit a usage limit): run `git status` and `git log --oneline | head`, then continue from the first unfinished milestone. Never redo finished work. Update STATE after every milestone (done, next, problems).

## Hard rules
- **Local only.** Work on the current local branch. Commit after every milestone. **Never push, never open a PR.**
- **AGENTS.md §0 holds overnight**: no secrets in files (keys come from the environment; you cannot read `.env`, and must not try), no real personal data, no fabricated or hand-typed numbers, unknown ≠ safe, "prototype, not medical advice" on every screen.
- **No test-set contamination.** You may build the eval code and a **dev** set. Do not create or label the frozen test set: leave `eval/test_set_TEMPLATE` and instructions for a teammate. Every number you report is labelled "dev set, N=…".
- **Code a beginner can explain** (AGENTS.md §5): small pure functions, plain data, clear names, docstrings, few dependencies pinned in `requirements.txt`. No clever abstractions.
- **Usage budget:** you plan, decide and review; hand routine typing to the `builder` worker and test runs to the `runner` worker (AGENTS.md §9). Don't re-read large files needlessly.
- **20-minute rule:** stuck on one thing for 20 minutes → stub it, fall back, or cut it per the PRD cut list. Record the cut. Never burn an hour.
- If a guardrail hook blocks you, fix the cause. Never work around it.
- If no LLM key is in the environment (check with a one-line Python `bool(os.environ.get(...))`, never print it), build the LLM step behind one function with a template fallback and a recorded `demo_cache/`, and list "add key and re-record cache" as the first morning task.

## Milestones (commit and update STATE after each)
**M1. Walking skeleton (target 45 min).** Repo layout from the PRD. Input → process → output end to end with stubs. `python app.py` serves the page; `python smoke_test.py` passes in under 60 s. `README.md` "how to run" updated.

**M2. Core flow real (target 2 h).** Replace stubs one at a time, smoke test after each. Each external API/dataset called for real once and cached to disk; timeout, one retry, graceful fallback on every call. `demo_cache/` makes the three golden-path inputs work with no keys and no network. Unknown input shows "not in our list". The judge's own-input moment works.

**M3. Tests where silence hurts (target 30 min).** Unit tests for rules, parsers and metric code; metric code checked against a tiny hand-computed example.

**M4. Evaluation harness (target 1 h).** `python -m eval` → `results/metrics.json` + `results/metrics.md`: primary metric, trivial baseline, simple baseline (and the incumbent/chatbot baseline if the PRD defines one), N with every number, slices, three real failures from the dev set. Leave the test-set template and a labelling guide for the teammate.

**M5. Design pass (target 2 h).** Follow the `ui-polish` loop with `component-craft`, `frontend-design`, `emil-design-eng`, `apple-design` and the PRD §9 spec. One screen, result and its "why" visible without scrolling. Every state designed with real copy (idle, loading, result, not-in-list, error, empty, narrow). Motion: one orchestrated moment, press feedback, text and number transitions where they explain a change, all honouring `prefers-reduced-motion`. Reference libraries for patterns (never copy source): useplanes.com/components, uiarc.dev/components, aisdkagents.com/ai-components, affectui.com/components.
- **Look at it.** Take real screenshots with Playwright (install Chromium if missing) at 1440×900 and 393×852 for every state; open the images and critique them; run the component-craft CSS audit; fix; repeat. At least two full rounds. Save final shots to `docs/screenshots/`.
- Click through the whole flow in the browser like a judge would: three golden inputs, one unknown input, one garbage input, network off. No stack trace may ever reach the screen.

**M6. Review and harden (target 45 min).** Review your own diff for bugs, dead code, secrets and anything a beginner couldn't explain; simplify. Run a fresh subagent as a code reviewer on the whole diff and fix what's real. Fresh-clone test: clone the local repo to a temp folder, new venv, follow the README exactly with no keys set, confirm it runs. Record the time it took.

**M7. Hand-off (target 30 min, do not skip).**
- `docs/EXPLAIN.md`: an entry for every module (what, why this way and what was rejected, known limit, likely judge question + answer).
- `docs/AI-USAGE-LOG.md` rows for tonight's work; `docs/DATA-SOURCES.md` complete with licences.
- `docs/MORNING-BRIEF.md` from `.claude/skills/overnight/references/morning-brief-template.md`.
- Update `docs/PRD.md` where reality differed, and `docs/WRITEUP.md` with real dev numbers from `results/`.
- Final commit. Write `.overnight/BUILD_DONE` with a one-paragraph summary. If an Aside memory tool is available, save a short dated note of what was built and what's open.

## Order of cuts when behind
Stretch features → secondary inputs (e.g. photo upload) → extra slices → decorative motion. **Never cut:** the core flow, the no-key demo mode, the smoke test, the eval harness, EXPLAIN.md, MORNING-BRIEF.md.

## Clock
Run `TZ=America/Chicago date` at the start and after each milestone. At 7:30 AM CT, stop building wherever you are and go straight to M7. Finish by 8:30 AM CT.
