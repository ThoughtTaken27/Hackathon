# Kettle, stage 2: probes, decisions and the PRD (target ~10:30 AM–12:00 PM CT Sat Nov 14)

Unattended on Parth's Mac; nobody answers questions. Decide, log the decision in `docs/DECISIONS.md`, move on.

**Read first:** `.overnight/kettle/STATE.md`, `AGENTS.md` (especially §0 stop-the-line rules, §5 coding practices, §9 model routing), `docs/RULES-AND-RUBRIC.md`, the Health section of `docs/BRIEF.md`, `docs/research/wow-pitches.md` (Pitch 1), **everything in `docs/research/kettle/`** (stage 1's teardowns, `pain-points.md`, `better-than.md`, `feature-matrix.md`, `ui-patterns.md`, `rea-evidence.md`), `.claude/skills/overnight/references/prd-template.md`, and the design skills in `.claude/skills/` (`ui-polish`, `apple-design`, `component-craft`, `emil-design-eng`, `frontend-design`).

Parth wants this "extremely detailed". Every PRD section must be specific enough that a build agent could implement it without guessing, and every product decision must point to evidence: a pain theme with its count, an REA Evidence ID, a probe result or a brief quote.

## Step 1. Probes before decisions (≤ 40 min, run in parallel where you can)
Each probe answers one question with a number, saved to `docs/research/kettle/probes/<name>.txt` (commands, versions, timings, results). Use a scratch venv outside the repo or `.venv-probe/` (gitignored).
1. **Data access.** Range-read ≥ 300 SINS dev clips (balanced across the 9 classes, several sessions, all 4 folds) from the Zenodo zips without downloading 46 GB, as the wow round did. Time it per clip and estimate the time for 6k and 12k clips. Repeat for ~100 eval-set clips (record 1291760; check the eval labels are really public and where they live).
2. **Encoders.** On the same 300 clips, time and run: AST (`MIT/ast-finetuned-audioset-10-10-0.4593`) embeddings; one smaller or faster encoder (e.g. PANNs CNN14, BEATs, or an EfficientAT/MobileNet AudioSet model; choose by licence and size); and **CLAP** (LAION or Microsoft, licence checked) for zero-shot "the sound of someone washing dishes" prompts. Report seconds per clip on CPU and on MPS, memory, and a 5-fold-free quick check (train on 2 sessions, test on another) of linear-probe macro F1 for each. This decides the encoder.
3. **Apple baseline.** Map Apple SoundAnalysis's 303 classes onto the 9 SINS activities with a written, frozen mapping (`apple_map.json`, decided before you look at the scores), and score it zero-shot on the 300 clips. It is the "what an iPhone already does" baseline.
4. **Live latency.** Browser mic → 16 kHz PCM over WebSocket → FastAPI → encoder → label. Measure end-to-end seconds from the sound to the label on screen, with a 10-s window and a hop of 2–5 s. Target ≤ 3 s perceived. Check that Chrome and Safari both allow mic on `http://localhost`.
5. **"Nothing saved" proof.** Design a check that proves no audio ever touches disk (e.g. run the server under `fs_usage`/`opensnoop`-style monitoring or audit every `open(..., 'w')` and temp file; pick what works on macOS without sudo, or document the sudo step for the lead). Prove it on the probe server.
6. **Own-kitchen domain shift.** Record nothing yourself (no mic access to Parth's home unattended). Instead, plan it for the team (stage 3 and §17).

## Step 2. Decide (≤ 15 min)
In `docs/DECISIONS.md` (new rows dated Sat Nov 14): encoder and head; window and hop; the activity set shown to users (the SINS 9, maybe merged into the ones a caregiver cares about, but measured on the official 9); how "usual vs today" works (a rule the caregiver sets: say plainly it is not learned); what the parent sees and controls; how speech is handled (no ASR anywhere; speech → "talking or TV", never words); the stack; what's cut. Each row: decision, evidence, rejected alternatives, how to reverse.

## Step 3. The PRD (≤ 60 min)
Replace `docs/PRD.md` with Kettle's PRD from the template, filling **every** section in depth (no placeholders). Specifics:
- **§0–3:** pitch, Health-track fit quoted from the brief ("catch a health problem sooner, or manage an ongoing one better"; report missed cases and false alarms separately; check across groups), the problem with a statistic opened at its primary source (or "unverified, find one" if you can't open it; never invent one), and the persona. Keep the invented-persona label.
- **§4–5 straight from stage 1:** a table of every product torn down, and for each top-10 pain theme from `pain-points.md` the Kettle feature or design choice that answers it and the test that proves it. This is the heart of the pitch: "people told us X N times; incumbents do Y; Kettle does Z, and here is the measurement."
- **§6:** which step is a real model task (sound → activity) and which are rules (alert thresholds, summaries), and the chatbot test: can a general LLM do this job? (It can't hear the kitchen, and that's the point, but say what an LLM *could* do and why we don't use one at runtime.)
- **§7–8 core flow and features, two sides:**
  - *Kitchen device* (laptop or old phone in a browser): a one-tap start, a big honest "Listening, nothing is recorded" state, a pause/privacy button the parent controls, and a live label with its evidence.
  - *Caregiver view*: today's timeline, "usual vs today" for the 2–3 moments the caregiver picks (e.g. "kitchen activity by 10 AM"), the device health heartbeat ("last heard 2 min ago", so "no news" never means "dead sensor"), and a calm daily summary line.
  - *Demo mode*: recorded SINS clips play through the real pipeline with no mic and no network (the judge's fallback), plus the live-mic mode.
  - *How we know*: the numbers panel with the baselines and failures.
  Every feature cites the pain theme or brief line it serves. Mark Must / Should / Could and a cut order.
- **§9 design spec, very detailed** (design skills plus `ui-patterns.md`): screen list; a state table for every state (idle, permission asked, mic denied, listening, low confidence "not sure", paused by the parent, offline/no heartbeat, demo mode, error) with **exact copy**; information hierarchy; type scale, spacing, colour tokens (light and dark), motion plan (one orchestrated moment when a new activity lands on the timeline; press feedback; reduced motion), accessibility for an older adult (large targets, contrast, plain words) and for the caregiver's phone at 393×852. Respect AGENTS.md design bans: no cream or black "old money" look, no big italic serif headlines, no purple gradients, no glow buttons, no side-stripe cards. Calm, warm and clearly not surveillance: say how, with specifics.
- **§10 architecture:** Python 3.11+, logic in small plain modules (`kettle/data.py`, `kettle/encoders.py`, `kettle/model.py`, `kettle/live.py`, `kettle/timeline.py`, `kettle/rules.py`, ...), FastAPI serving one static page (HTML + CSS + vanilla JS, no build step) with a WebSocket for live audio, an embedding cache on disk, committed small model weights and `demo_cache/`, `smoke_test.py`, `python -m eval`. One module diagram plus input → output contracts per module.
- **§11 data and licences:** SINS dev (CC BY-NC 4.0) and eval (CC BY-NC-ND 4.0); what we commit (labels, small processed features, a handful of demo clips with attribution) and what we never commit (the raw zips); model licences.
- **§12 safety and honesty:** prototype, not medical advice, on every screen; consent from the older adult first; no audio stored, no speech content; "unknown" is never "fine"; what the app must never claim.
- **§13 evaluation, the part MSR judges will attack:**
  - Folds: the official session-disjoint dev folds (verify this again).
  - **Headline test: the official DCASE 2018 Task 5 eval set**, run **once** with the frozen model and logged with the commit hash and time. We didn't make or label it, so it's an independent test. Report known-mic and unknown-mic slices separately, and compare against the published baseline (83.1 unknown-mic) and the best entry (88.4) with the caveat about subsampling.
  - Baselines: majority class; Apple SoundAnalysis zero-shot (frozen map); AST zero-shot (frozen map); CLAP zero-shot; and the published DCASE baseline numbers.
  - Metrics: macro F1 (the challenge metric), per-class precision/recall with missed vs false-alarm counts and N, confusion matrix, 95% CIs (bootstrap by session, not by clip), and latency.
  - Slices: per mic node (domain shift), per class, time-of-day if recoverable, and the team's own-kitchen set.
  - **Own-kitchen test set**, labelled by a teammate who didn't write the code (AGENTS.md §0.5): a Saturday-evening/Sunday-morning team task with a recording and labelling guide, consent, and no conversation recorded.
  - At least five real failures with an explanation each.
- **§14 rubric scorecard** with the expected points per line and the evidence a judge will see.
- **§15 premortem:** the five likeliest ways this loses, each with a mitigation.
- **§16 build plan** as stage 3 milestones with times (stage 3 starts as soon as this is done and must leave Sunday for the team: video, write-up, own-kitchen set).
- **§17 team lanes** for the two beginner teammates: copy-paste Claude Code prompts, allowed files and a done-check each (Lane A: own-kitchen recordings and labels; Lane B: write-up, video script and the statistic hunt). Parth is the lead and integrates.
- **§18–19:** a 2:00 video script with timestamps, and the 12 sharpest questions MSR researchers will ask, each with our answer.
- **§20–21:** ranked open questions with defaults, and credits linking every product and dataset.
Also write `docs/WRITEUP.md` (one page: problem, persona, approach, how well it works with placeholders only for numbers the build will fill, what we learned) and `docs/DATA-SOURCES.md` rows.

## Step 4. Red-team and fix (≤ 20 min)
Spawn two fresh subagents in parallel, each given only `docs/BRIEF.md`, `docs/RULES-AND-RUBRIC.md`, `docs/PRD.md` and `docs/research/kettle/better-than.md`:
1. A sceptical **Microsoft Research audio-ML researcher** acting as a judge: a score per rubric line, the five weakest technical points, leakage risks, anything unmeasurable, and any claim without evidence.
2. A **caregiver and older-adult UX critic**: does this feel like surveillance, is the copy calm and clear, does it answer the pain points, what would make a judge say "wow" in the first 10 seconds?
Fix the top issues in the PRD; log the rest in §20. Save both critiques to `docs/research/kettle/redteam-*.md`.

## Done
`git add docs && git commit` (local only, never push). Write `.overnight/kettle/PRD_DONE` with the one-sentence pitch and the chosen encoder. Update STATE: "Stage 2 complete; stage 3 builds from docs/PRD.md". Stop.
If it's past **12:30 PM CT**, finish §5–§13 and §16 first, mark the rest "to complete", and hand off.
