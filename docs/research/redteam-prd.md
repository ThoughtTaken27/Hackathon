# Red team of PRD v1 (Fri Nov 13, ~11:56 PM CT)
A fresh Sonnet 5.5 subagent acting as a sceptical ML-researcher judge read only `docs/BRIEF.md`, `docs/PRD.md`, `docs/RULES-AND-RUBRIC.md` and AGENTS.md §0.

**Expected scores (v1 as written):** Round 1 ≈ 72 (technical 23, originality 12, impact 15, testing 11, comms 11). Finals: demo 24, depth 22, impact 14, Q&A 13.

**Top five weaknesses → what we changed in v2**
1. "Time split" only dates the scams; legit text is mostly 2012, so the model can learn era/source/masking style → synthetic modern legit in training; headline false alarms on modern look-alikes; style-only baseline; era controls (§13).
2. Recall counts "ask" as a catch but false alarms only count "scam" → headline "legit flagged" = scam **or** ask.
3. Look-alike test small and single-author → ~200 rows, two authors cross-checking; Wilson CI printed.
4. Sunday "fix the top failure" would tune on test → test-A (diagnostics) / test-B (run once, headline); fixes from dev only.
5. "Runs on her device / nothing leaves this computer" overstated → "makes no network calls"; prototype is a local web page.

**Other points taken:** near-duplicate (not just exact) de-dup; reply-bait safety floor so "No scam signs found" doesn't land on the worst slice; AI-written synthetic rows logged in AI-USAGE-LOG; chatbot baseline sees text only; IMC'25 tactic labels may be model-made (state provenance); the 12-text chatbot test is anecdote; prior-art search was limited (said so); self-scores lowered; persona frequency marked as assumption.

**Unresolved (see PRD §20):** no licensed post-2018 real legit SMS set found; beginners must explain TF-IDF, thresholds and de-dup (Sunday `/explain quiz`); the user test and video need humans.
