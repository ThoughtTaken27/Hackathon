# Explain-back notes

One entry per module. Every teammate should be able to say these out loud to a judge. Format: what it does · why this way (and what we rejected) · known limit · the likely judge question and our answer.

## The whole thing in 30 seconds
A laptop in the kitchen hears 10-second windows of sound. A frozen pretrained audio model (CED-tiny) turns each window into 192 numbers; a small logistic-regression head we trained turns those into probabilities for 9 household activities. Transparent rules then decide what the screen says: "Not sure" when it isn't confident or the sound is unlike anything it learned, blocks only when 2 of 3 windows agree, "Can't tell" when it wasn't listening. Audio only ever lives in a 10-second RAM buffer. The caregiver sees a day bar, a heartbeat and checks she set herself; the parent sees the same day and can pause it.

---

## Product (runs on the kitchen laptop)

### `kettle/labels.py`
- **What it does:** the 9 SINS activity names in the official order, the plain words the screens use ("absence" → "Quiet", "other" → "Moving about"), their colour tokens, and two groups: "kitchen activity" (cooking, washing up, eating) and "any activity".
- **Why this way:** one place for every name, so renaming on screen never touches the model. We kept the official 9 classes for every number (so we're comparable to DCASE) and only rename for display.
- **Known limit:** "Moving about" is SINS's catch-all "other" class; it's vague and it's our weakest class.
- **Judge question:** *Why not merge cooking, eating and washing up, since they're confused?* We measure the official 9 so numbers are honest and comparable; the caregiver check uses the merged "kitchen activity" group, which is what Meera actually needs.

### `kettle/audio.py`
- **What it does:** decodes an uploaded file from bytes in memory (WAV, FLAC, OGG, MP3 via libsndfile; M4A via PyAV), converts to 16 kHz mono and cuts 10-second windows. Raises a reason ("unreadable", "too short") the UI turns into a designed message.
- **Why this way:** nothing touches disk; the upload endpoint reads the raw request body, because multipart uploads over 1 MB get spooled to a temp file by the web framework.
- **Known limit:** reads only the first 60 seconds (decoding itself stops there, so a tiny file holding hours of silence can't exhaust memory: a review finding, tested); a clip under 10 seconds can't be scored.
- **Judge question:** *What if I upload a photo?* You get "That isn't audio Kettle can read", not a crash; the smoke test sends a JPEG and a text file.

### `kettle/encoders.py` (+ `kettle/vendor/ced/`)
- **What it does:** loads CED-tiny (5.5 M parameters, Apache-2.0) from the committed weights and returns, for each 10-s window, a 192-number embedding (mean of its output tokens) and CED's own scores for 527 AudioSet sounds.
- **Why this way:** CED-tiny matched bigger models on our session-disjoint check while running ~40× faster than AST on a laptop CPU (probe 2), which matters for something that listens all day on an old laptop. Its code is vendored (copied with its licence) so nothing runs remote code or needs the network. We never train it: frozen first, as AGENTS.md says.
- **Known limit:** trained on AudioSet (YouTube audio); a laptop mic in a real kitchen is a different domain.
- **Judge question:** *Why not fine-tune?* No time to do it honestly (session-grouped early stopping) in 48 hours; the encoder ablation shows how much the encoder matters vs the head.

### `kettle/evidence.py` (+ `kettle/evidence_labels.json`)
- **What it does:** from CED's 527 AudioSet scores, picks the top 3 among a fixed list of 88 kitchen and living-room sounds ("Dishes, pots, and pans 0.36 · Water tap, faucet 0.21"). Blocks show these as "Sounds Kettle heard".
- **Why this way:** it's an independent view of the audio (not the head we trained), so a judge or Meera can check *why* a block says "Washing up". Body sounds, bathroom sounds and speaker details (male/female/child, shouting, whispering) are deliberately excluded.
- **Known limit:** the scores come from a model trained on YouTube; they're evidence, not proof.
- **Judge question:** *Isn't showing "Speech" a privacy leak?* It's the type, never the words or who; the label list is in a file anyone can read.

### `kettle/model.py`
- **What it does:** the trained head: standardise the 192 numbers, logistic regression (9 classes, class-balanced), divide by a temperature, softmax. Saved as plain JSON with a sha256. Also the novelty score: Mahalanobis distance from the embedding to the nearest activity's mean (shared covariance with Ledoit-Wolf shrinkage).
- **Why this way:** a linear head is the simplest thing that works (probe 2: every trained head ~76–82, every zero-shot map 40–49) and a beginner can explain it; JSON means no pickle and nothing executes on load. Temperature makes "how sure" honest (calibration is measured). The novelty score exists because max-probability alone gave confident labels to most off-list sounds (dogs, sirens, noise).
- **Known limit:** the novelty threshold comes from SINS's one home; a new kitchen might look "unlike anything" more often (we measure the leave-one-microphone-out version of this and report it).
- **Judge question:** *Why logistic regression and not an MLP?* The MLP ablation is in `results/metrics.md`; we keep the simpler model unless the bigger one wins clearly on dev folds.

### `kettle/live.py`
- **What it does:** the kitchen state (consent, pause, off, weekly check) and the live listening loop: 16-bit audio chunks from the browser go into a NumPy ring buffer of at most 10 s; every 2 s it labels the last 5 s (the "Sounds like…" chip) and the last 10 s (the timeline window). Audio is refused (and the buffer emptied) unless the parent said yes and Kettle isn't paused or off.
- **Why this way:** the gate is in the server, not just the page, and only the kitchen laptop itself can open the gate (127.0.0.1). 10-s windows every 2 s keep the label fresh (2.6 s for a loud new sound in probe 4) while every number is measured on the same 10-s unit SINS is labelled in.
- **Known limit:** when one activity changes to another, the old sound still fills the window, so the new label takes ~6–8 s.
- **Judge question:** *Could a caregiver turn it on remotely?* No: consent, pause, resume, sample days and audio are only accepted from the kitchen laptop's own browser (`app._is_kitchen`: a local connection, a local Host name and, if sent, a local Origin, so another web page or DNS rebinding can't press the parent's buttons either); `tests/test_heartbeat_consent.py` and `tests/test_app.py` check it.

### `kettle/timeline.py`
- **What it does:** turns window events into day-bar blocks with these rules: below θ or novel → "Not sure"; TV and Conversation within 0.15 → "Talking or TV"; 2-of-3 smoothing; a "Not sure" gap of ≤ 30 s between two windows of the same activity is bridged (rule 2b); merge equal neighbours; gaps over 34 s → "Not listening"; pauses drawn as "Paused by Dad". Also writes the one-line summary from the blocks only.
- **Why this way:** every rule is transparent and unit-tested; smoothing cut false-alarm blocks per hour several-fold on dev sessions (number in `results/metrics.md`). The summary is a template, so it can never invent "Dad had lunch".
- **Bridging (rule 2b, added after the frozen held-out run, addendum item 10):** on dev, 18 of 33 kitchen sessions were split into 3–12 pieces by short "Not sure" stretches even though the right activity covered 64–94% of them, so Meera saw confetti instead of "cooking 8:10–8:35". Bridging gaps up to 30 s (chosen from dev gap lengths; θ and the model unchanged; novel sounds never bridged) took strict kitchen sessions from 15 to 26 of 33 and false kitchen blocks from 3.87 to 3.23 per day. `results/metrics.md` shows every number with and without it.
- **Known limit:** smoothing delays a new block by one window and can swallow a very short real activity; bridging can paint up to 30 s of an unclear sound as the surrounding activity (the block's "how sure" still averages those windows).
- **Judge question:** *You changed post-processing after the test run. Isn't that tuning on the test set?* No. It was diagnosed and chosen on dev folds only; the held-out numbers are window-level and don't use the timeline; we report before and after, and `bridge_s=0` reproduces the old behaviour.
- **Judge question:** *Isn't "Not sure" just hiding errors?* We report what it costs (coverage) and what it buys (precision of shown labels, off-list confident-wrong rate), both on dev, and the numbers without it.

### `kettle/heartbeat.py`
- **What it does:** says whether Kettle is hearing the kitchen right now: never started, off, paused, mic blocked, no mic, starting, listening, or stale ("Not listening since 10:42 AM").
- **Why this way:** "no news" must never look like a normal day (pain theme 10a); a quiet kitchen still produces "Quiet" windows every 2 s, so silence is "listening", while no windows for 34 s is "stale". It's a rule, never learned.
- **Known limit:** it knows the laptop stopped sending, not why (asleep, closed, crashed).
- **Judge question:** *How do you tell an empty kitchen from a dead laptop?* An empty kitchen still sends windows (labelled Quiet); a dead laptop sends none. `tests/test_heartbeat_consent.py::test_silence_is_listening_but_no_input_is_stale`.

### `kettle/rules.py`
- **What it does:** up to 3 checks Meera sets ("Kitchen activity by 10:00 AM", "Some sound of activity by …", "TV on for more than N hours"), each Met / Not yet / Missed / Can't tell (or over/under for TV), with the exact sentence shown.
- **Why this way:** rules decide, the model only labels (AGENTS.md §5). A learned "unusual day" model can't be validated on SINS (no clock times). The safety rule: if Kettle didn't hear more than 25% of the check's window, the answer is "Can't tell", never "Missed" and never "Met"; "Not sure" blocks never satisfy a check.
- **Known limit:** "Met" means kitchen sounds were heard, not that Dad ate; the copy says "kitchen activity", never "Dad ate", and Met always says how sure ("Met at 8:05 AM (cooking, how sure: medium)").
- **Details added after review:** only blocks inside the check's window (from 6 AM) count, so a 1 AM snack can't satisfy "by 10:00 AM" (a reviewer found that bug; `tests/test_app.py`). If Kettle heard sounds it couldn't name before the deadline, Missed says so ("No clear kitchen activity by 10:00 AM. Kettle heard sounds it couldn't name for 30 min before then.") instead of "Not heard". If Kettle only started after the check's time: "Can't tell: Kettle started at 12:30 PM, after this check's time."
- **Judge question:** *Why no alert when a check is missed?* Alerts are the false-alarm pain, and sending one needs a cloud relay; Meera sees the state when she looks. With another week: an opt-in browser notification.

### `kettle/view.py`
- **What it does:** builds everything both screens show from the state: the heartbeat sentence, the blocks with their evidence-card text, the summary and the checks, in the kitchen laptop's time zone ("Dad's local time").
- **Why this way:** all caregiver copy in one testable place (`tests/test_view.py` bans words like "safe", "fine", "normal day", "!"). When Kettle is paused, asleep or off, the summary adds "Nothing is known after {time}." so a gap never reads as a settled day (usability walkthrough finding).
- **Judge question:** *What does Meera see if the laptop died at midnight?* "Not listening since 11:59 PM… Nothing is known after that", and the new day's bar is cross-hatched, not blank (a test covers it).

### `kettle/demo.py` (+ `demo_cache/`)
- **What it does:** "Play a sample day": 90 real SINS clips from 9 sessions held out of training, pushed through the same encoder and head; each clip's window gets a staged clock time so a morning plays in ~15 s. Three days: a usual morning, a quiet morning (check missed), a TV-only afternoon (laptop asleep → Can't tell).
- **Why this way:** Round 1 judges have no mic; this needs no mic, no network and no keys, and the labels are real model output (if it's wrong on a clip, the sample day shows that).
- **Known limit:** the clock times are staged (SINS has none), and the screens say "Sample day".
- **Judge question:** *Did you cherry-pick clips?* The sessions were chosen at random (seed 0) before any model existed, and the first 10 segments of each are used in order.

### `kettle/data.py`
- **What it does:** reads the SINS labels and official folds, picks the training subset (≤ 1,000 clips per activity, round-robin over sessions, all 4 mic nodes and folds, demo sessions excluded) and fetches each clip with one HTTP range request into the Zenodo zips, at ≤ 2 requests a second.
- **Why this way:** the dataset is 46 GB; range reads got us 8,920 balanced clips in ~75 minutes. The app never imports it (a test checks that).
- **Judge question:** *Why not all the data?* 10 hours of downloading at Zenodo's rate limit; we say our head trains on ≤ 1,000 clips per class, and published systems used everything.

### `app.py`
- **What it does:** one FastAPI process: the three pages, `/api/today` (polled once a second), the parent's controls (kitchen laptop only), checks, "Try your own sound", sample days and the mic WebSocket. Writes only `data/timeline/<date>.jsonl` (labels and times, never audio).
- **Why this way:** boring, explainable stack; polling instead of a second WebSocket; no accounts or database.
- **Judge question:** *What's in the file it writes?* Window labels, the 9 probabilities, the novelty flag, the top 3 evidence sounds, times, and consent/pause events. The privacy check lists the exact fields. After a restart the day is rebuilt from this file (a reviewer found windows were being saved under the wrong `kind` and lost on restart; fixed and tested).

### `static/` (the three pages)
- **What it does:** plain HTML, CSS and JavaScript, no build step. `common.js` draws the day bar (existing blocks are never removed and re-added; only new ones animate in) and the evidence card; `caregiver.js`, `kitchen.js`, `howsure.js` drive each page; `worklet.js` passes mic samples from the browser's audio thread.
- **Why this way:** design tokens from PRD §9.5; activity colours from a palette validated for colour-blind readers on the pairs that actually sit next to each other; every block also has a text label.
- **Judge question:** *Does the browser record audio?* No `MediaRecorder`, no Blob, no storage: `tests/test_privacy_grep.py`.

---

## Evaluation (how every number is made)

### `eval/dev.py` (+ `python -m eval`)
- **What it does:** the whole development-fold study. Uses the official 4 SINS folds (session-disjoint): train the head on 3 folds (all 4 microphone channels as examples), predict the 4th, rotate. C is chosen inside each training set by leave-one-fold-out (nested), so the test fold never picks C. Then: temperature and θ from out-of-fold logits; every baseline on the same clips and folds; ablations (channel-0-only training, no class balancing, MLP head, 5-s chip window, leave-one-mic-node-out); the session-level score through the real timeline rules; the "kitchen activity" metric; calibration; the θ trade-off; per-node slices.
- **Why this way:** the folds are the dataset authors' (we re-verified they're session-disjoint in `tests/test_folds.py`); nested C avoids tuning on the scored fold; everything else that was chosen on dev is labelled "dev folds (also used for selection)" because it's optimistic.
- **Known limit:** dev numbers are optimistic (selection uses the same folds); the frozen eval run is the unbiased number.
- **Judge question (Prasad): why macro F1?** It's the DCASE 2018 metric, so we're comparable to published systems, and it weights rare activities (vacuuming, washing up) like common ones; accuracy would reward always saying "Quiet". For Meera we also report the metric that matches her question: "any kitchen activity" caught vs false alarms.

### `eval/metrics.py`
- **What it does:** confusion matrix; per-activity recall ("caught"), precision ("right when it says so"), F1, missed (FN) and false-alarm (FP) counts; macro F1; prevalence reweighting; the session bootstrap; Wilson intervals.
- **Why this way:** we score a class-balanced subset, which inflates precision on rare classes, so each confusion row is reweighted to the class's true frequency (cap 50); recall doesn't change. Clips in one session are correlated, so CIs resample whole sessions (1,000 draws). Checked against a hand-computed example in `tests/test_metrics.py`.
- **Judge question:** *Why not a normal bootstrap over clips?* It would treat 30 clips of one cooking session as 30 independent cooks and give intervals that are far too narrow.

### `eval/sample.py`, `eval/PREREGISTER.md`, `eval/dcase.py`, `eval/guard.py`
- **What they do:** the one frozen run on the official DCASE 2018 Task 5 evaluation set. The sample (1,000 random moments + top-up to ≥ 50 per activity, all 7 microphone copies = 7,791 clips, seed 20261114), the scoring and the mic-fingerprint rule were committed (commit `0119c57`) before any eval audio was fetched. `guard.py` refuses to open eval embeddings unless it's the sanctioned run with a frozen head. `run_once()` refuses a second run once predictions exist; `rehearse()` runs the same scoring on a dev stand-in with a random head first.
- **Why this way:** a held-out set is only held out if nothing can peek at it. Pre-registering the recipe means we couldn't pick a flattering sample after the fact.
- **Known limit:** a seeded subsample of the eval set, reweighted to its true class counts, not all 72,972 clips: close to, not exactly, a leaderboard number.
- **Judge question (Kerimov): does it hold up on microphones it never heard?** The unknown-mic slice is exactly that; which nodes are "unknown" was decided from unlabelled spectra (`eval/fingerprint.py`), never from labels or predictions.

### `eval/fingerprint.py`
- **What it does:** decides which eval sensor nodes are the 3 microphones the dev set never had, using only each node's average log-mel spectrum (no labels, no predictions): an eval node is "known" if it's nearest one dev node and within that node's own fold-to-fold spread, one-to-one.
- **Judge question:** *What if it can't tell?* Then we report per-node numbers only and never call a slice "unknown-mic".

### `eval/offlist.py`
- **What it does:** 200 ESC-50 clips from 20 non-household categories (dog, siren, rain, alarm clock…) plus 60 generated noise and silence clips: sounds that are none of the 9 activities. Every confident label on them is wrong by construction.
- **Why this way:** "Not sure" only matters if it catches the sounds Kettle wasn't trained on; this measures it, with and without the novelty gate.
- **Judge question (Batool): where is it confidently wrong?** On these off-list sounds with θ alone, and on TV vs conversation in the dev confusions; the page shows both.

### `eval/privacy_check.py`
- **What it does:** runs the real app under a Python audit hook while headless Chromium plays a sample day into the kitchen page as a fake microphone; samples `lsof`; diffs the repo, temp folders and caches for new audio files or audio magic bytes; uploads 5 MB to "Try your own sound". Writes `results/privacy_check.json` and fails on any audio write.
- **Known limit:** not a kernel trace (the optional `sudo fs_usage` step is in the docstring); OS swap is outside our control.
- **Judge question:** *How do you prove nothing is recorded?* Four independent checks against the running app, plus a code grep test, plus a stated threat model.

### `eval/own_kitchen.py`, `eval/OWN_KITCHEN_GUIDE.md`, `eval/own_kitchen/`
- **What it does:** the team's own kitchens as the honest worst slice: a teammate who didn't write the code records with consent and labels while recording; a format checker (`python -m eval.own_kitchen_check`) that never changes a label; one scoring run with the frozen head, with Wilson intervals.
- **Judge question:** *Who labelled it and why them?* A teammate who didn't write the code, so the labels can't drift toward what the model says.

### `eval/cache.py` + `notebooks/kettle_reproduce.ipynb`
- **What it does:** a small committed cache (dev embeddings in float16, log-mel features, baseline predictions, Apple's per-activity scores) so the notebook can retrain the head and rebuild every table and plot in minutes, without the 76-minute download. The eval set's embeddings are not committed (its licence forbids derivatives); its saved predictions are.
- **Judge question:** *Can I check your numbers myself?* Open the notebook and run it: its last cell compares every number with `results/metrics.json`.

### `tools/apple_baseline/`
- **What it does:** a Swift command-line tool that runs Apple's built-in SoundAnalysis classifier (303 sound classes, the one a Mac ships) on channel 0 of each clip; `run.py` maps classes to our 9 activities with a map frozen before any score was computed.
- **Judge question (Batool): what did you add beyond the pretrained encoder?** A trained head, calibration, an abstain rule measured on off-list sounds, a session-level pipeline, and the comparison with what a Mac already does out of the box.

## Evaluation helpers and training (added in M10 so every module is covered)

### `eval/__main__.py` (`python -m eval`)
- **What it does:** the one command that regenerates every number: the dev-fold study (`eval/dev.py`), the off-list test, the plots (confusion, reliability, θ trade-off), `results/metrics.json`, `results/metrics.md` and `results/failures.md`. `--split dcase-eval` was the one frozen held-out run; `--rehearse` tested that code path on a dev stand-in first; `--render` rebuilds the markdown and plots from the saved JSON without recomputing.
- **Why this way:** one command, one output file, and the write-up copies from that file (`tools/writeup_numbers.py`), so no number is ever typed by hand.
- **Known limit:** the dev study takes several minutes on a laptop CPU because the session bootstrap resamples many times; the notebook reuses a committed cache to stay under 5 minutes.
- **Judge question:** *How do I know the write-up numbers aren't edited?* Delete `results/`, run `python -m eval` and `python tools/writeup_numbers.py`, and diff: the markers in README/WRITEUP are rewritten from `metrics.json`.

### `eval/check_metrics.py`
- **What it does:** walks `results/metrics.json` and fails if any metric lacks its split, N or CI (or if a bare score appears).
- **Why this way:** AGENTS.md §6 says no bare percentages; a 50-line checker enforces it on every run instead of trusting us to remember.
- **Judge question:** *Does every number have an N?* `python -m eval.check_metrics` prints "0 problems".

### `eval/common.py`
- **What it does:** lines cached embeddings up with labels, folds, sessions and microphone nodes; maps AudioSet or Apple classes to our 9 activities for the zero-shot baselines; `num()` wraps every number with its split, N and CI.
- **Known limit:** the zero-shot class maps were written by hand once, before any score was computed, and frozen; a different map would give a different zero-shot number (we say so).

### `eval/embed.py` + `eval/encoders_extra.py`
- **What they do:** run each encoder once over the fetched clips and cache the embeddings on disk (git-ignored; only the small committed cache in `results/cache` ships). `encoders_extra.py` holds the encoders used only for baselines and ablations: AST, CED-small, CLAP, log-mel statistics.
- **Why this way:** embedding is the slow step (minutes to hours); caching it means every head, threshold and ablation reruns in seconds and the same numbers feed every table.
- **Judge question:** *Why CED-tiny over AST?* On dev, AST + the same head scored 83.0 vs Kettle 85.5 on the same 2,700 clips, at 16× the size; CED-small scored 85.9 vs Kettle 85.1 on all 8,920 dev clips (inside the CI), at 4× the size. We picked the small one for live latency on a laptop.

### `eval/train.py`
- **What it does:** fits the shipped head (`models/head.json`) on every dev training clip with C, temperature and θ chosen only from dev folds; `--freeze` writes the SHA-256 to `models/FROZEN`, and retraining is refused after the held-out run.
- **Judge question:** *Could you have retrained after seeing the test score?* The code refuses (`held_out_run_done`), and `results/eval_run.json` logs the frozen head hash, the commit and one attempt.

### `eval/own_kitchen_check.py`
- **What it does:** format checks on the teammates' `labels.csv` (activity names, stretches under 10 s, missing audio files, overlaps); it never changes a label.

### `smoke_test.py`
- **What it does:** runs the real app in-process with no network, microphone or keys: pages load, the consent gate, a sample day through the real model, heartbeat, checks, pause, "Try your own sound" on a real, unclear, silent, white-noise and non-audio input, and live audio refused before consent. Exit 0 = pass, in well under 60 s.
- **Judge question:** *Does it run for a stranger?* The fresh-clone test (M8) followed the README on a new venv with no keys and ran this.

### `tools/` (build helpers, never used by the app)
- `screenshots.py`: Playwright captures every designed state at 1440×900 and 393×852, light and dark, with a fake microphone playing held-out SINS clips; it also fails if any screen shows an uncaught page error, a server traceback or broken text ("undefined", "NaN").
- `contact_sheets.py`: tiles a round's screenshots so a reviewer can open them all at a glance.
- `stability_check.py`: while a sample day plays, counts day-bar blocks that get re-created instead of extended (they should not jump).
- `make_notebook.py`: builds `notebooks/kettle_reproduce.ipynb`, then nbconvert executes it with outputs saved.
- `writeup_numbers.py`: fills the number blocks in README and WRITEUP from `results/metrics.json`.

### Research scripts (`docs/research/kettle/probes/`, `docs/research/kettle/raw/`)
Stage-2 probes (encoder speed, Apple's classifier, live latency) and the pain-point coding scripts. They produced the decisions in `docs/DECISIONS.md`; no reported number comes from them except where labelled "probe".

## Improvement round (Sat Nov 14, evening)

### `web/public/js/sense.js` (on-device layers after the frozen head)
- **What:** teach-this-kitchen (nearest setup windows vote, only when the head is unsure) and 15 named household sounds with a privacy veto. (Appliance hum and silence are handled by the second opinion and the silent-mic rule.)
- **Why this way:** the head is frozen and pre-registered, so fixes go after it, each measured in `eval/beyond.py` with thresholds picked on folds 1–2 and reported on folds 3–4 / ESC-50.
- **Known limit:** no real-kitchen data yet; gains are small (Not sure 10.6% → 7.6% after 1 minute of setup in simulation); a toilet flush is still named "running water" 31% of the time.
- **Judge question:** "Isn't kNN on 20 setup windows overfitting?" It only acts on windows the head couldn't name and only within 1.5× the setup spread; the always-on version was measured worse and dropped.

### `eval/beyond.py` and `eval/stress_teach.py`
- **What:** beyond.py measures every new layer on the committed dev caches + ESC-50 (`results/beyond.json`); stress_teach.py replays the 90 demo clips quieter, with TV underneath, with echo and a laptop-mic band (`results/stress_teach.json`).
- **Why:** "where it fails" curves for the honesty line; nothing re-reads the held-out audio.
- **Known limit:** N = 90 clips (18–30 per slice); read slopes, not decimals.
- **Judge question:** "What breaks it worst?" A TV left on: kitchen activity noticed falls from 73% to 27% at 10 dB and to 0% at 0 dB.

### `web/src/household.js` (server changes)
- **What:** `cleanEvent` keeps only the 9 activity names and the 15 allowed sound-type ids (plan D1); `tallyDays` keeps a tiny per-day count for the week view; `privacy` and guest `pause` actions. `router.js` limits wrong pairing codes to 10 per address per 10 minutes.
- **Known limit:** one family link per home; per-person links and revocation aren't built.

### `kettle/kinds.py`
- **What:** the Python copy of the sound-type rule and the appliance hold, used to give sample days the same fields a kitchen laptop sends.
