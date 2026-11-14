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
- **Known limit:** reads only the first 60 seconds; a clip under 10 seconds can't be scored.
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
- **Judge question:** *Could a caregiver turn it on remotely?* No: consent, pause, resume and audio are only accepted from the kitchen laptop; `tests/test_heartbeat_consent.py` checks the gate.

### `kettle/timeline.py`
- **What it does:** turns window events into day-bar blocks with these rules: below θ or novel → "Not sure"; TV and Conversation within 0.15 → "Talking or TV"; 2-of-3 smoothing; merge equal neighbours; gaps over 34 s → "Not listening"; pauses drawn as "Paused by Dad". Also writes the one-line summary from the blocks only.
- **Why this way:** every rule is transparent and unit-tested; smoothing cut false-alarm blocks per hour several-fold on dev sessions (number in `results/metrics.md`). The summary is a template, so it can never invent "Dad had lunch".
- **Known limit:** smoothing delays a new block by one window and can swallow a very short real activity.
- **Judge question:** *Isn't "Not sure" just hiding errors?* We report what it costs (coverage) and what it buys (precision of shown labels, off-list confident-wrong rate), both on dev, and the numbers without it.

### `kettle/heartbeat.py`
- **What it does:** says whether Kettle is hearing the kitchen right now: never started, off, paused, mic blocked, no mic, starting, listening, or stale ("Not listening since 10:42 AM").
- **Why this way:** "no news" must never look like a normal day (pain theme 10a); a quiet kitchen still produces "Quiet" windows every 2 s, so silence is "listening", while no windows for 34 s is "stale". It's a rule, never learned.
- **Known limit:** it knows the laptop stopped sending, not why (asleep, closed, crashed).
- **Judge question:** *How do you tell an empty kitchen from a dead laptop?* An empty kitchen still sends windows (labelled Quiet); a dead laptop sends none. `tests/test_heartbeat_consent.py::test_silence_is_listening_but_no_input_is_stale`.

### `kettle/rules.py`
- **What it does:** up to 3 checks Meera sets ("Kitchen activity by 10:00 AM", "Some sound of activity by …", "TV on for more than N hours"), each Met / Not yet / Missed / Can't tell (or over/under for TV), with the exact sentence shown.
- **Why this way:** rules decide, the model only labels (AGENTS.md §5). A learned "unusual day" model can't be validated on SINS (no clock times). The safety rule: if Kettle didn't hear more than 25% of the check's window, the answer is "Can't tell", never "Missed" and never "Met"; "Not sure" blocks never satisfy a check.
- **Known limit:** "Met" means kitchen sounds were heard, not that Dad ate; the copy says "kitchen activity", never "Dad ate".
- **Judge question:** *Why no alert when a check is missed?* Alerts are the false-alarm pain, and sending one needs a cloud relay; Meera sees the state when she looks. With another week: an opt-in browser notification.

### `kettle/view.py`
- **What it does:** builds everything both screens show from the state: the heartbeat sentence, the blocks with their evidence-card text, the summary and the checks, in the kitchen laptop's time zone ("Dad's local time").
- **Why this way:** all caregiver copy in one testable place (`tests/test_view.py` bans words like "safe", "fine", "normal day", "!").
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
- **Judge question:** *What's in the file it writes?* Window labels, the 9 probabilities, the top 3 evidence sounds, times, and consent/pause events. The privacy check lists the exact fields.

### `static/` (the three pages)
- **What it does:** plain HTML, CSS and JavaScript, no build step. `common.js` draws the day bar (existing blocks are never removed and re-added; only new ones animate in) and the evidence card; `caregiver.js`, `kitchen.js`, `howsure.js` drive each page; `worklet.js` passes mic samples from the browser's audio thread.
- **Why this way:** design tokens from PRD §9.5; activity colours from a palette validated for colour-blind readers on the pairs that actually sit next to each other; every block also has a text label.
- **Judge question:** *Does the browser record audio?* No `MediaRecorder`, no Blob, no storage: `tests/test_privacy_grep.py`.
