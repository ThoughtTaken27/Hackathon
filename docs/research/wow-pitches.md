# Wow round: three pitches (Sat Nov 14, 2026, ~8:00 AM CT)

For Parth to pick from. Nothing here is built. No PRD written. Candidates and kills are in `docs/research/wow-candidates.md`. Raw evidence is in `docs/research/samples/wow/`: `findings-*.md` (incumbents and Reddit, from read-only Aside research), `probe-*.txt` (models actually run on this laptop this morning), `clock-data-note.txt`, real data samples.

**Recommendation: Pitch 1, "Kettle" (household-sound day timeline for a parent who lives alone).** Why it beats the others is in the last section.

Rules I held to: every number below either came from a page Aside opened (marked with its source file) or from a probe I ran; anything not verified at the primary source says **unverified**. Statistics for the problem (how many people with dementia live alone, how many older adults fall) are **not yet verified**, so none are quoted; finding one is a P0 task for whichever pitch wins.

---

## Pitch 1 (recommended): **Kettle**, "know Dad's day went normally, from sound alone, without a camera"

**One sentence:** A laptop or old phone in the kitchen listens in 10-second windows, turns household sounds (dishes, cooking, vacuum, TV, an empty room) into a plain day timeline for an adult child, keeps no audio and no words, and we measure it on a public week-long recording of one person living alone, against the published challenge baseline.

**The person and the moment.** Meera, 34, lives 300 miles from her father, 79, who has early memory loss and lives alone (persona, invented). At 11 AM she wonders "did he eat breakfast?" Calling feels like checking up on him; cameras feel like spying. Kettle shows "dishes 8:05, cooking 8:20–8:40, TV 9:10–10:30". Arecibo AI, the Gold sponsor, builds a companion app for older adults with cognitive impairment and their caregivers, so this is squarely in its lane.

**The 10-second demo moment (what the judge sees).** The presenter clinks two plates and runs a tap next to the laptop. Within ~2 seconds a bar labelled "Dishwashing" appears on the live timeline, with the top sound evidence underneath ("Dishes, pots and pans 0.36 · Cutlery 0.19"). Then they switch on a vacuum or a TV clip and the timeline changes. A banner says "No audio saved. No words kept. Only these labels." In the finals the judge can make the sound themselves.

**Why it is not the obvious hackathon project.** It isn't in the brief's suggested projects or examples. Fall detection and pill reminders are the usual "aging parent" student builds; activity-from-sound needs real audio ML and a public long recording, and teams rarely know the SINS data exists.

**Existing products (from `findings-sound.md`; ratings not checked on store pages):**
| Product | What it does | What we take | Gap we measure |
| --- | --- | --- | --- |
| Howz (https://www.howz.com/reassure) | Plug-in and motion sensors learn a routine; family app | Routine-first family view, "usual vs today" | Needs hardware installed; we need only a laptop/phone mic |
| Canary Care (https://www.canarycare.co.uk/families/) | Motion, door, smart-plug kettle sensors; "no cameras or microphones" | Calm, non-alarming copy; privacy promise up front | Coarse (a plug knows the kettle, not cooking vs dishes) |
| Assistiv Home Sensing (https://www.assistiv.services/home-sensing) and havn by cortekAI (launched Oct 26, 2026, https://www.prnewswire.com/news-releases/cortekai-launches-havn-a-home-wellness-service-that-helps-older-adults-live-independently-302915601.html) | Acoustic AI that "doesn't record speech" | Proof the market wants sound-based sensing | No published accuracy we could find; ours publishes per-activity F1 with N and the failures |
| Apple Sound Recognition (https://support.apple.com/guide/iphone/use-sound-recognition-iphf2dc33312/ios) | On-device kettle, water, door, smoke-alarm alerts | On-device, no upload | Alerts only the phone's owner; no timeline for a remote caregiver |

Head-to-head we can actually show: none of these publish accuracy, so the comparison judges see is **ours vs the published DCASE 2018 Task 5 systems on the same public test**, plus a feature table (hardware needed, what leaves the home, activities covered).

**Voice of the user (Reddit, snippets only, from `findings-sound.md`):** r/eldercare "How do I check on dad without him feeling like I'm hovering?" https://www.reddit.com/r/eldercare/comments/1vs1py9/ · r/AgingParents "My dad is 85 and lives alone" https://www.reddit.com/r/AgingParents/comments/1rquxw3/ · r/CaregiverSupport "check in on aging parents that doesn't feel like micromanaging" https://www.reddit.com/r/CaregiverSupport/comments/1kwze56/ · r/TechForAgingParents "quietly check in on aging parents without cameras" https://www.reddit.com/r/TechForAgingParents/comments/1q0f2nx/

**Model task and exact model.** 10-second audio clip → one of 9 activities (absence, cooking, dishwashing, eating, social activity, vacuum cleaning, watching TV, working, other). Frozen pretrained audio encoder **MIT/ast-finetuned-audioset-10-10-0.4593** (Audio Spectrogram Transformer, 86.6 M params, licence BSD-3-Clause per the Hugging Face API, checked 7:59 AM CT), using its embedding + a logistic-regression head trained on SINS. Ablation: AST's own AudioSet labels zero-shot (no training), and a smaller encoder if speed needs it.

**Probe result (ran it, `probe-sound-ast.txt`):** loads in 9.6 s, **0.9 s per 10-s clip on CPU** (fast enough for live use). Zero-shot on one real SINS clip per class: dishwashing → "Dishes, pots, and pans", vacuum → "Vacuum cleaner", TV → "Speech/Music/Television", empty room → "Static/Hum"; **cooking missed** ("Inside, small room"). N=5, an anecdote, but it says the encoder hears the right things and that a trained head is needed.

**Data.** SINS / DCASE 2018 Task 5: "continuous recording of one person living in a vacation home over a period of one week", 4 mic arrays, ~200 h, 72,984 ten-second clips (`meta.txt`, counted). Dev set https://doi.org/10.5281/zenodo.1247102, **CC BY-NC 4.0** (Zenodo API), 46 GB in 23 zips; eval set https://zenodo.org/records/1291760, **CC BY-NC-ND 4.0**, 45 GB, labels released. We don't need the 46 GB: I pulled individual clips out of the remote zips with HTTP range reads (`samples/wow/sins/audio/`, 6 real clips), so we fetch only the subset we use. Class counts are skewed (absence 18,860 / TV 18,648 / working 18,644 vs vacuum 972, dishwashing 1,424).

**Test set, baseline, honest metric.**
- Metric: macro F1 over the 9 activities (the challenge's own metric), plus per-activity missed-vs-false-alarm counts (the Health brief asks for them separately), each with N.
- Leakage check done this morning: the official 4 dev folds are **session-disjoint** (0 shared sessions in all 4 folds; all 4 microphones of one moment stay in the same fold).
- Headline test: the official eval set, "unknown mic" slice (microphones in positions never seen in training). Published numbers on that slice (https://dcase.community/challenge2018/task-monitoring-domestic-activities-results, parsed today): **official CNN baseline 83.1 macro F1** (85.0 on known mics, 84.5 on dev); **best entry, Inoue/IBM, 88.4** (90.4, 90.0). Its worst class is "Other" (baseline 35.0).
- Baselines: majority class; AST zero-shot label mapping (no training); the published DCASE baseline.
- Real-world slice: 10–20 minutes recorded by the team in our own kitchens (consented, no conversation), labelled by a teammate who didn't write the code. It shows the drop from a lab home to a laptop mic, which will be our honest worst slice.
- Caveat to state: if we evaluate on a subsample of the eval set (speed), our number is not strictly comparable to the leaderboard. Say so.

**What a sharp MSR judge attacks, and our answer.**
1. *"One home, one person: you've learned that house."* Yes. That's why the headline is the unknown-mic slice and our own-kitchen slice, and why we lead with the drop.
2. *"An always-on mic in an old man's home is surveillance."* Audio never leaves the device and is never written to disk; only the label and timestamp are kept; speech is reduced to "social activity" with no words; the older adult sees the same timeline and can pause it. Consent comes from him, not the caregiver.
3. *"Why not smart plugs?"* A plug on the kettle is more reliable for the kettle. Sound covers cooking, dishes, vacuuming, TV and an empty house with one device and no install. We show both columns honestly.
4. *"Frozen embeddings + logistic regression is shallow."* Ablation: zero-shot vs linear head vs the published CNN. If a frozen 2022 transformer plus a linear head lands near a 2018 tuned CNN, that's the finding, with the compute cost next to it.
5. *"How does 'unusual day' work?"* SINS dev clips lost their clock times, so we can't measure a learned routine model. "No kitchen sounds by 11 AM" is a transparent rule the caregiver sets (rules decide, the model only labels). We say this plainly.

**Build plan to Sun 6 PM CT (lead + 2 beginners).**
- Sat 9–10 AM, **riskiest assumption first:** frozen AST embeddings + logistic regression reach ≥ 80 macro F1 on one session-disjoint fold. Test: range-fetch ~3,000 balanced clips, embed (~45 min CPU in background), train, score. If it fails: switch to the published-baseline-style log-mel CNN, or report the honest lower number.
- Sat 10 AM–2 PM: embedding cache for ~8–10k clips (background); eval script `python -m eval` with folds, the unknown-mic slice, CIs, per-class missed/false-alarm counts. Beginner 1: record and label our own-kitchen clips. Beginner 2: write-up + video script.
- Sat 2–6 PM (gate): live page — browser mic → 10-s windows → local model → timeline with evidence labels; demo_cache of recorded clips for a no-mic "Run all".
- Sun AM: failure gallery (cooking vs eating, "other"), real-world slice, ablation; the "nothing saved" check (grep the run for written audio).
- Risks: CPU embedding time (mitigate: subsample, cache, MPS); range-fetch speed from Zenodo; mic domain shift (that's the honest finding, not a blocker).

**Scores (out of 10):** wow 8 · depth 9 · originality 8 · impact 9 · buildability 7 · data readiness 9 → **50/60**.

---

## Pitch 2: **Ten Past Eleven**, a paper clock-drawing check from a photo

**One sentence:** Grandma draws a clock showing "ten past eleven" on paper, the caregiver holds it to a webcam, and an image model scores it on the clinical Shulman 0–5 scale and points at what went wrong, as a "mention this to the doctor" prompt, never a diagnosis.

**The person and the moment.** A caregiver who saw Mom's clock at the annual physical and didn't know it was a test (r/AgingParents snippet, `findings-clock.md`), or one checking month to month. Strongest possible Arecibo AI fit (cognitive impairment).

**The 10-second demo moment.** A judge draws a clock on a napkin, holds it up, and in under 2 s sees "Score 3/5: hands don't point to 11 and 2" with the hands outlined. Then they draw a bad clock on purpose and watch the score drop.

**Why it is not the obvious project, and the existing products (`findings-clock.md`):**
| Product | What it does | Take | Gap |
| --- | --- | --- | --- |
| Linus Health DCTclock (https://linushealth.com/our-assessments) | iPad digital-pen clock, AI scoring of drawing + process; sold to clinics | The clinical credibility bar | Clinic-only, needs a stylus; nothing for paper at home |
| CDT Open / BrainScanology (https://www.brainscanology.com/clockdraw) | Free at-home clock app; says it doesn't diagnose | Consumer framing and the disclaimer | App Store listing reportedly removed May 27, 2025 (AppBrain, unverified); no published accuracy |
| Memory Sketch (https://memorysketch.co/) | Stylus clock test, Shulman/Sunderland scores, $15/month, "in clinical validation" | Multi-scale scoring | Paid, stylus |
| NIH-CARD clock_collector (https://github.com/NIH-CARD/clock_collector) | Photo of a paper clock read by a vision LLM, scored on 5 scales; alpha | Photo-of-paper input | Needs a cloud LLM; no accuracy reported |

Head-to-head: our trained small model vs a no-training rule baseline, plus (if Parth adds a free Gemini key) vs a vision-LLM prompt like clock_collector's, on the same held-out clocks.

**Model, probe.** Fine-tune a small ImageNet CNN (e.g. EfficientNet-B0 / MobileNetV3, ~5 M params) on MPS; ordinal regression on Shulman 0–5. **Not probed beyond the data** this morning (a forward pass of a 5 M-param CNN on a laptop is routine; training time on 3k images is the real unknown, estimated under 30 min).

**Data (the weak spot).** cccnlab CDT-API-Network `clock_shulman.zip` (https://github.com/cccnlab/CDT-API-Network): 3,114 images, Shulman labels by majority of three clinicians (per the paper). **No licence in the repo** (GitHub API: null), so it's "all rights reserved" until the authors say otherwise. Counted today: only **89 images at Shulman ≤ 2** and 442 at ≤ 3, so the impaired end is tiny. Images are cropped near-binary scans (365×329), not webcam photos. Not copied into our repo (`clock-data-note.txt`). NHATS (>47k images) needs registration and its terms reportedly ban uploading to AI platforms (unverified at source).

**Test set and metric.** Stratified held-out split; quadratic-weighted kappa vs the clinician label and recall on Shulman ≤ 3 (missed vs false alarm separately); a second test of 40–60 clocks hand-drawn by people who didn't write the code and photographed on a phone (the domain-shift slice).

**What a judge attacks.** (1) "Clock drawing alone misses a lot of mild impairment; you'll scare or falsely reassure people." Answer: it's one Mini-Cog element; the output is "worth mentioning to the doctor", never a diagnosis. (2) "Your data has no licence." We'd need the authors' permission before using it. (3) "89 impaired examples, from one hospital in Bangkok." Wide CIs, a stated limit.

**Build plan.** Hour 1: email the authors (a human, not an agent) and in parallel test the riskiest assumption: does a model trained on scans hold up on 20 phone photos of hand-drawn clocks? Then fine-tune, build the webcam page, run eval. Risk: the licence answer may not arrive this weekend.

**Scores:** wow 9 · depth 7 · originality 6 · impact 9 · buildability 7 · data readiness 4 → **42/60**.

---

## Pitch 3: **First Wisp**, a wildfire-smoke spotter for one county's public fire cameras (Climate)

**One sentence:** For a dispatcher watching San Diego County's public HPWREN mountaintop cameras, a small on-laptop model flags a new smoke plume minutes after ignition and, unlike the off-the-shelf detector, doesn't cry wolf at haze on the horizon. We measure minutes-to-detect and false alarms per camera-day on fires it never saw.

**The person and the moment.** A county emergency-communications dispatcher or volunteer lookout who can't watch 20 camera feeds at once. The brief itself names "forest rangers decide where to patrol". The Climate brief asks for one place, a test period the model never saw, and a decision someone makes; here that's "send an engine to look".

**The 10-second demo moment.** A 40-minute timelapse from a real 2016 fire plays. At minute 4 a box appears on a faint grey wisp at the horizon, with "smoke, 4 min after ignition". A side panel shows the off-the-shelf model lighting up three empty haze tiles that ours stays quiet on.

**Existing products (`findings-smoke.md`):**
| Product | What it does | Take | Gap |
| --- | --- | --- | --- |
| Pano AI (https://www.pano.ai/) | Cameras + cloud AI + human analysts; **$35,000 per camera per year** (Rancho Palos Verdes staff report) | Human-in-the-loop confirmation | Price shuts out small rural districts; false alarms (snow blowers in Aspen, ag burns) |
| ALERTCalifornia (https://alertcalifornia.org/) | 1,200+ public PTZ cameras, AI alerts confirmed by watchstanders | Public cameras we can use | State-scale; CAL FIRE says >50% of 2025 alerts came before a 911 call, but another source gives 38%: numbers disagree |
| FireScout (Alchera X) | SaaS on existing feeds; "91% accuracy" vendor claim | Runs on existing cameras | Vendor numbers only |
| Pyronear (https://github.com/pyronear/vision-rd, Apache-2.0) | Open source YOLO + temporal model on Raspberry Pi | **Its pretrained model is our baseline** | — |

No independent head-to-head of the commercial systems exists (`findings-smoke.md`). Ours is measured on FIgLib against Pyronear's open model and against the published SmokeyNet numbers.

**Model, probe (`probe-smoke-pyronear.txt`).** Baseline: `pyronear/rexnet1_0x` (Apache-2.0, ONNX), **0.06 s per crop on CPU**. On a real FIgLib frame 240 s after ignition: full frame **missed** (p≈0.26); tiled, the plume tile scored **0.98** but three smoke-free horizon tiles scored **0.88–0.92**. That's the false-alarm problem in one frame. Ours: tile classifier + a temporal input (current frame minus the frame a few minutes earlier) fine-tuned on FIgLib, like SmokeyNet's idea at a fraction of the size.

**Data.** FIgLib (HPWREN Fire Ignition images Library, https://hpwren.ucsd.edu/FIgLib): per the SmokeyNet paper, nearly 25,000 labelled images from fixed Southern California cameras; best published model 83.49% accuracy, 89.84% precision, 76.45% recall, 3.12 min mean time-to-detect (https://www.mdpi.com/2072-4292/14/4/1007); a later model 2.26 min. One real frame saved. **Risk:** the FIgLib server didn't answer from this laptop at ~7:56 AM (it redirected to `legacy-www.hpwren.ucsd.edu` and then timed out); the earlier run fetched a frame at 7:47. Licence **unverified**.

**Test, baseline, metric.** Split by fire and by date (train on earlier fires, test on later), never by frame. Metrics: recall on smoke sequences, minutes-to-detect, false alarms per camera-day; baselines Pyronear off-the-shelf and frame differencing; slices: by camera, time of day, haze/fog days.

**What a judge attacks.** (1) "SmokeyNet already did this." Yes; our addition is a laptop-sized model, an honest false-alarm number per camera-day, and a rural-district framing. (2) "Who acts on it?" The dispatcher. A human confirms every alert, as with ALERTCalifornia. (3) A r/Wildfire commenter says the bottleneck is "funding, management of resources", not detection. That's a fair hit on impact.

**Build plan.** Hour 1: confirm FIgLib downloads (riskiest assumption) and fetch 30 fires; if it stays down, fall back to Pyronear's openfire set on Hugging Face (different, no sequences). Then cache Pyronear baseline scores, train the temporal tile model on MPS, build the timelapse player.

**Scores:** wow 8 · depth 8 · originality 6 · impact 7 · buildability 6 · data readiness 5 → **40/60**.

---

## Ranking and the call

| | Wow | Depth | Originality | Impact | Buildability | Data | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **1. Kettle** (sound timeline) | 8 | 9 | 8 | 9 | 7 | 9 | **50** |
| 2. Ten Past Eleven (clock photo) | 9 | 7 | 6 | 9 | 7 | 4 | 42 |
| 3. First Wisp (smoke cameras) | 8 | 8 | 6 | 7 | 6 | 5 | 40 |

**Pick Kettle.** It's the only one of the three where everything is true today:
- **Data:** real, licensed (CC BY-NC) and in hand, already fetched clip by clip.
- **Model:** already probed on this laptop and correct on 3 of 4 non-empty clips with zero training.
- **Leakage:** checked; the official folds don't leak.
- **Benchmark:** a public leaderboard (baseline 83.1, best 88.4 on unseen mics) to stand next to, which is the comparison MSR researchers trust most.

The live moment is physical and works for any judge with a plate and a tap. The person (an adult child of a parent living alone with memory loss) is Arecibo AI's own user.

The clock check is the bigger "wow" and the better sponsor story, but it rests on an unlicensed dataset with only 89 clearly impaired examples. That's a stop-the-line risk we can't fix by Sunday without the authors' reply. The smoke spotter has the cleanest Climate fit, but its data server didn't answer this morning, its incumbent research already did the core idea (SmokeyNet), and the person is further from our judges' sponsor.

**What Parth should check before saying yes:** (1) Is a microphone-in-the-home idea "mind-blowing" enough for him? The wow comes from the live sound demo plus "no audio leaves". If he wants the bigger gasp, Pitch 2 is the higher-ceiling, higher-risk choice. (2) A verified statistic on older adults with dementia living alone has to be found and opened at the source before it goes in any write-up.
