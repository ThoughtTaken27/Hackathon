# Kettle, stage 3: build it (from ~12:00 PM CT Sat Nov 14; hard stop Sun Nov 15 9:00 AM CT)

Unattended on Parth's Mac; nobody answers questions. Decide, log it in `docs/DECISIONS.md`, keep going. The team takes over Sunday morning for the video, the write-up and the own-kitchen test set; submission closes Sun 10:59 PM CT.

**Read first, every time you start:** `.overnight/kettle/STATE.md`, `docs/PRD.md`, `docs/DECISIONS.md`, `AGENTS.md`, `docs/research/kettle/better-than.md`, `docs/research/kettle/ui-patterns.md`, `docs/research/kettle/probes/`. On a restart, run `git status` and `git log --oneline | head -15`, then continue from the first unfinished milestone. Never redo finished work. Update STATE after every milestone.

**Context:** the last overnight build (Second Look) finished every milestone in 39 minutes and stopped, and Parth called the result basic. This time depth is the point. The quality bars below are the definition of done, not the clock. Use the time.

## Hard rules
- **Local only**, on branch `kettle`. Commit after every milestone. Never push, never open a PR.
- **AGENTS.md §0 holds:** no secrets in files, no real personal data, no fabricated or hand-typed numbers, unknown ≠ fine, "Prototype, not medical advice" on every screen.
- **Privacy is a feature we prove:** no audio is ever written to disk or sent anywhere except the local server; no speech recognition anywhere; only labels, scores and timestamps are kept.
- **Test hygiene:** tune only on dev folds. The official DCASE eval set is run **once**, at M6, with the frozen model; log the commit hash and time. Never create or label the team's own-kitchen test set (leave the guide and template).
- **Code a beginner can explain** (AGENTS.md §5): small pure functions, plain data, docstrings, pinned `requirements.txt`, no clever abstractions.
- **Delegation** (AGENTS.md §9): you plan, decide and review; hand routine typing to `builder` and test runs to `runner`.
- **20-minute rule:** stuck 20 minutes → stub, fall back or cut per PRD §16. Record the cut.
- Long jobs (embedding thousands of clips) run in the background with progress logged to `.overnight/kettle/jobs/`; build the UI while they run.
- If a guardrail hook blocks you, fix the cause. Never work around it.

## Milestones (commit + STATE after each)

**M1. Walking skeleton.** Layout from PRD §10. `python app.py` serves the page; a recorded clip → stub label → timeline, end to end. `smoke_test.py` passes in < 60 s. README "how to run".

**M2. Data and embeddings.** Range-fetch the training subset decided in stage 2 (balanced, all sessions, all folds; log counts per class/fold/node). Verify session-disjoint folds in code (a unit test). Background-embed into the on-disk cache with the chosen encoder(s). Commit only small artefacts (labels, splits, small features if < 50 MB in total, demo clips with attribution); never the raw zips.

**M3. Models and every baseline, honestly.** Train the head on dev folds (fold-wise cross-validation). Implement every baseline from PRD §13: majority, Apple SoundAnalysis zero-shot (a small Swift CLI under `tools/apple_baseline/` called from Python, frozen class map), AST zero-shot, CLAP zero-shot, plus published DCASE numbers quoted with a link. Ablations: encoder choice, window/hop, head type, with and without class balancing. Pick the final model from dev only and freeze it (`models/` + a hash in STATE).

**M4. Evaluation harness.** `python -m eval` → `results/metrics.json` + `results/metrics.md`: macro F1 with session-bootstrap 95% CIs, per-class precision/recall with missed vs false-alarm counts and N, confusion matrix image, per-node slices, latency, all labelled "dev folds, N=…". `results/failures.md`: ≥ 5 real failures with clips referenced and an explanation each. Unit tests check the metric code against a hand-computed tiny example. Leave `eval/OWN_KITCHEN_GUIDE.md` and a template for the teammate set.

**M5. The real product (the biggest milestone; take the time it needs).**
- *Live kitchen mode:* browser mic → WebSocket → 10-s windows with the stage-2 hop → label + top evidence + confidence → timeline. "Not sure" below the confidence threshold, never a guess presented as fact. Pause/privacy button the parent controls, with a visible state everywhere. Mic-denied and no-mic states designed.
- *Caregiver view:* today's timeline, the "usual vs today" checks the caregiver sets (a transparent rule, labelled as such), the device heartbeat ("last heard 2 min ago"; it turns to a clear warning when stale so "no news" never means "dead device"), the calm daily summary line, and the parent's pause shown as "paused by Dad at 3:10 PM", never hidden.
- *Demo mode:* a "Play a sample day" that streams real SINS clips through the same pipeline at speed, with no mic and no network. It's the judge's fallback and the video's spine.
- *How we know:* the numbers panel (ours vs Apple vs zero-shot vs DCASE published, with N and CIs, labelled dev until M6) and the failures.
- *Every top-10 pain theme in `better-than.md`* is visibly answered or explicitly cut; keep a checklist in `docs/research/kettle/better-than-checklist.md` with each theme → where in the app → screenshot.
- *The "nothing saved" proof* from stage 2's probe, wired into `python -m eval.privacy_check` (or the lead's sudo step documented if it truly needs sudo).
- Golden paths for the smoke test and screenshots: three sample-day scenarios (a usual morning; a quiet morning that trips the caregiver's check; a TV-only afternoon), one "not sure" input (an ambiguous clip), one garbage input (silence, white noise, a non-audio upload) → each a designed screen, never a stack trace.

**M6. Frozen test run.** With the M3 model frozen and tagged in STATE, run the official DCASE eval subset **once** (`python -m eval --split dcase-eval`), known-mic and unknown-mic separately, next to the published baseline and best entry with the subsampling caveat. Commit the result immediately with the commit hash. Don't retrain after seeing it; if it disappoints, that's the honest finding: write it up as one.

**M7. Design passes (at least 3 full rounds).** Follow `ui-polish` with `component-craft`, `apple-design`, `emil-design-eng`, `frontend-design` and PRD §9. AGENTS.md bans: no cream or black "old money" look, no big italic serif headlines, no purple gradients, no glow buttons, no side-stripe cards. Each round:
- Playwright screenshots of **every state** at 1440×900 and 393×852, light and dark (install Chromium if missing).
- **Open every image and critique it** in writing (`docs/screenshots/critique-round-<n>.md`): hierarchy, spacing, copy, contrast, calm vs surveillant feel, against the incumbent screens described in `ui-patterns.md`.
- Run the component-craft CSS audit; fix; repeat.
- Round 2 includes a fresh subagent design critic; round 3 includes a fresh "older adult and caregiver" usability walkthrough subagent reading the screenshots.
- Motion: one orchestrated moment (a new activity settling onto the timeline), press feedback, number transitions; `prefers-reduced-motion` honoured.
Click through like a judge: every golden path, the not-sure input, the garbage input, network off, mic denied.

**M8. Review and harden.** Review your own diff (bugs, dead code, secrets, anything a beginner can't explain); simplify. A fresh subagent code reviewer on the whole diff; fix what's real. Fresh-clone test: clone the local repo to a temp folder, new venv, follow the README exactly with no keys, time it, confirm the demo mode works.

**M9. Judge simulation and improvement (2 rounds).** Each round, a fresh subagent judge (sceptical MSR audio-ML researcher) gets only the README, `docs/WRITEUP.md`, `results/` and the screenshots, scores every Round 1 and finals rubric line, and names the three changes worth the most points. Make those changes if they fit the rules and time; log what you skipped and why.

**M10. Hand-off (never skip).**
- `docs/EXPLAIN.md`: every module (what, why this way, what was rejected, known limits, the likely judge question and our answer).
- `docs/AI-USAGE-LOG.md` rows; `docs/DATA-SOURCES.md` complete with licences and credits for every product torn down.
- `docs/MORNING-BRIEF.md` from `.claude/skills/overnight/references/morning-brief-template.md`: what exists, real numbers (dev and the one eval run), what's not done, decisions to confirm, the first hour for Parth, copy-paste lanes for the two beginners (own-kitchen set; video and write-up), and the video shot list.
- Update `docs/PRD.md` where reality differed, and `docs/WRITEUP.md` with real numbers.
- Final commit. Write `.overnight/kettle/BUILD_DONE` with a one-paragraph summary. If an Aside memory tool is available, save a short dated note.

## Order of cuts when behind
CLAP baseline → extra ablations → dark mode → extra slices → decorative motion. **Never cut:** live mode, demo mode, the caregiver view with the heartbeat, the parent's pause, the Apple baseline, the eval harness, the one frozen eval run, the privacy check, the smoke test, EXPLAIN.md, MORNING-BRIEF.md.

## Clock
Run `TZ=America/Chicago date` at the start and after each milestone. By **Sun 7:00 AM CT** go straight to M10 wherever you are; finish by 9:00 AM CT.
