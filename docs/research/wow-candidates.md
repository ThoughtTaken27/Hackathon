# Wow round: raw candidates and kills (Sat Nov 14, 7:50–8:05 AM CT)

Source of the task: `.claude/overnight/phase-wow.md`. Hard filters: (1) Health, Finance or Climate only; (2) not a suggested project or an "own idea" example from the brief (incl. sign-language webcam, mood journal, medicine-label reader, Climate TRACE emitter map, building energy forecast, meal-carbon photo, street flooding, teen budgeting, inflation tracker, bank-fee explainer), and no scam/spam detector of any kind; (3) strong incumbents are a plus; (4) AI is the main job; (5) buildable by Sun 6 PM CT on an 8 GB Apple-silicon laptop with no LLM key; (6) data exists today; (7) honestly measurable.

## Step 1: generate wide (one line each: who · 10-second moment · model task · data)

| # | Track | Candidate | Who | 10-second moment | Model task | Data |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Health | **Clock-drawing photo check** | Adult child of a parent with memory slips, before the doctor visit | Grandma draws a clock on paper, holds it to the webcam; in 2 s the screen marks "hands wrong, numbers crowded on the right" with a score on the standard scale | Image classification/regression of a hand-drawn clock (fine-tuned small CNN/ViT) + per-element checks | Public clock-drawing image sets (to verify); NHATS clock images |
| 2 | Health | **Sound of a day** (household-activity timeline from a laptop/phone mic, no speech kept) | Daughter 300 miles from a dad who lives alone with early memory loss | Judge runs a tap and clinks dishes; the timeline writes "dishwashing 8:02" live, and flags "no kitchen sounds by 11 AM, unusual for him" | Audio event/activity classification on pretrained audio embeddings (AST / PANNs / CLAP) + routine-deviation model | SINS / DCASE 2018 Task 5 (one person living alone, 200 h, 9 activities) — metadata saved |
| 3 | Health | **Webcam chair-stand check** (CDC STEADI 30-second chair stand + 4-stage balance) | Adult child checking a parent's fall risk monthly | Judge stands up and sits 30 s in front of the laptop; reps count live on a skeleton overlay; "11 stands: below the CDC norm for 75–79" | Pose estimation (MediaPipe/BlazePose) + rep-segmentation signal model | Our own consented recordings; Sit2Stand (Stanford) videos to check |
| 4 | Health | Webcam pulse + breathing (rPPG) for telehealth | Older adult on a video visit | Face on camera → live pulse waveform | rPPG (POS / pretrained PhysNet) | UBFC-rPPG / PURE (request form) |
| 5 | Health | Pill-from-photo check ("is this the pill on my list?") | Caregiver filling a weekly pillbox | Hold a pill to the webcam → "matches Metformin 500 mg on her list" or "not in our list" | Fine-grained image retrieval (CLIP/DINO embeddings) | NLM C3PI / Pill Image Recognition Challenge images (public domain, to verify) |
| 6 | Health | Spoken-picture-description cognitive screen (cookie-theft) | Older adult at home | Describe a picture aloud → linguistic markers | Whisper + classifier | DementiaBank / ADReSS (gated membership) |
| 7 | Health | Spiral/handwriting tremor screen for Parkinson's | Older adult | Draw a spiral → tremor score | CNN on spiral images | Kaggle Parkinson's spirals |
| 8 | Health | Video fall detection at home | Parent living alone | Person falls on camera → alert | Pose/action recognition | UR Fall, Le2i |
| 9 | Health | FAST stroke check (face droop + slurred speech) | Spouse at home | Smile + speak → stroke warning | Face landmarks + dysarthria classifier | TORGO (dysarthria, not stroke) |
| 10 | Finance | Medical-bill error finder from a photo | Older adult with a hospital bill | Photo of a bill → "this line is 3× the hospital's posted price" | OCR + price-transparency matching | Hospital machine-readable price files; no labelled errors |
| 11 | Finance | Voice-clone "grandparent call" detector | Older adult answering a call | Play a cloned voice → "synthetic" | Anti-spoofing audio classifier | ASVspoof 2019 LA |
| 12 | Finance/Climate | Appliance-level bill breakdown from one smart-meter (NILM) | Older adult on a fixed income | Upload a meter CSV → "your old freezer costs $14/month" | Energy disaggregation (seq2point CNN) | UK-DALE / REDD |
| 13 | Climate | **Wildfire smoke spotter on public fire cameras** | Volunteer fire lookout / county dispatcher in San Diego County backcountry | A 40-minute HPWREN timelapse plays; the model boxes a faint plume N minutes before the first 911 call time | Temporal image classification/detection of smoke (tiled CNN + frame differencing) | FIgLib (HPWREN Fire Ignition Library), sample saved |
| 14 | Climate | Rooftop-solar potential from aerial imagery for one neighbourhood | Homeowner/city | Map → panel-ready roofs | Segmentation | NAIP/ OpenStreetMap |
| 15 | Climate | Urban heat street map from Sentinel-2 + street view | City heat officer | Map hot blocks | Regression on imagery | Landsat LST |
| 16 | Health | Cough-sound triage | Clinic worker | Cough → condition | Audio classifier | COUGHVID / Coswara |

## Step 2: kill fast (keep 5)

**Kept:** #1 clock-drawing photo check · #2 Sound of a day · #3 webcam chair-stand check · #5 pill-from-photo check · #13 wildfire smoke spotter.

**Killed (one line each):**
- #4 rPPG: the strong datasets (UBFC-rPPG, PURE) need a request form, so the data won't be in hand today (filter 6). POS is also a signal-processing algorithm, not a learned model, so "AI is the main job" gets shaky (filter 4).
- #6 cookie-theft speech screen: DementiaBank/ADReSS need membership approval (filter 6), and it leans on language (filter 1 spirit).
- #7 Parkinson's spirals: one of the most common student ML projects; the Kaggle set is tiny (filter 2 spirit: every hackathon team builds it).
- #8 video fall detection: crowded student project, and the datasets are staged falls by young actors, so the honest number would be weak (filter 2 spirit, 7).
- #9 FAST stroke check: no public stroke-speech or stroke-face data; TORGO is cerebral palsy/ALS (filter 6, 7).
- #10 medical-bill error finder: no labelled set of billing errors, so we couldn't measure it honestly; the AI part is OCR + lookup (filters 4, 7).
- #11 voice-clone call detector: a scam detector (filter 2, explicit ban).
- #12 NILM bill breakdown: no live input to demo (a CSV upload), and close to the brief's "forecast a building's energy use" example (filter 2).
- #14 rooftop solar: Google Project Sunroof already does it at national scale, and the demo is a static map.
- #15 urban heat map: static map; weak "AI central" and no 10-second moment.
- #16 cough triage: COVID-era crowded project; the labels are self-reported (filter 7).
