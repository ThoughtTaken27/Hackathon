# PRD: Kettle

Status: draft v1 · written Sat Nov 14 2026, 09:31–10:45 AM CT (stage 2, unattended) · brief received Fri Nov 13, 10:47 PM CT · track: **AI + Health**
Every claim has a source link or says "assumption". Every number has its N or says "not measured yet". Numbers marked **probe** come from `docs/research/kettle/probes/` (tiny N, for decisions only); nothing here is a reported result.
Evidence keys used throughout: **P#** = pain theme # in `docs/research/kettle/pain-points.md` (count, severity) · **REA** = Evidence ID in `rea-evidence.md` · **Probe n** = `probes/0n-*.txt` · **Brief** = quoted from `docs/BRIEF.md` · **D** = a row in `docs/DECISIONS.md`.

---

## 0. The pitch

- **One sentence:** Kettle turns a laptop already in a parent's kitchen into a calm day timeline for the adult child who lives far away (cooking at 8:20, washing up at 8:45, TV from 9:10) from sound alone, with no camera, no recording and no words kept, and it publishes how often it misses an activity and how often it cries wolf.
- **The sentence a judge repeats to another judge:** "Of the nine 'is Mum OK' products they checked, it's the only one that says how often it's wrong: missed activities and false alarms, per 10-second window and per activity session, on a public week-long recording of someone living alone, against Apple's own sound classifier." (Absence claim from our Nov 2026 search of 9 products; say "that we found".)
- **Why this wins (three lines):**
  1. Health-track fit in the brief's own words: one named person, "manage an ongoing one better" (early memory loss, living alone), and **missed cases and false alarms reported separately** is literally our product's headline, not an afterthought (Brief §4.1).
  2. Real audio ML with a researcher-grade eval: frozen pretrained encoder + trained head, session-disjoint folds, the official DCASE 2018 eval set run once, unknown-microphone slice, Apple and zero-shot baselines, and our own kitchens as the honest worst slice.
  3. Built from 418 coded real reviews: people told us the parent feels watched (P1, 17 items) and alerts miss or cry wolf (P3 15, P5= 16). Kettle's design answers each one, and the incumbents publish **no accuracy at all** (`better-than.md`).

## 1. The brief and track fit

**Verbatim lines we answer** (Brief, AI + Health):

| Brief line | How Kettle answers it |
| --- | --- |
| "Build an AI tool that helps one specific person catch a health problem sooner, or **manage an ongoing one better**." | Meera manages her father's early memory loss from 300 miles away: Kettle shows whether today's ordinary rhythm (kitchen activity, meals, TV, an empty room) happened, so a change is noticed sooner and a normal day needs no anxious call. It is a daily-rhythm view, not a diagnostic. |
| "**Name your user** and explain how they'd use your tool." | §3: Meera (caregiver) and Ravi (the parent, who consents, sees the same screen and can pause it). Both invented personas, labelled so. |
| "Report **missed cases (false negatives) and false alarms (false positives) separately**, not just overall accuracy." | Every activity's missed count and false-alarm count with N on the "How sure is Kettle?" screen, in `results/metrics.json`, the write-up and the video (§13). |
| "This project is a prototype and is not medical advice." | On every screen footer, the write-up and the README (§12). |
| "Use public datasets only." | SINS / DCASE 2018 Task 5 dev (CC BY-NC 4.0) and eval (CC BY-NC-ND 4.0) on Zenodo. Own-kitchen recordings are our own consented data, no patient records (open question §20.2). |
| Judges: "how clearly you identify your user, how honestly you report missed cases and false alarms, and whether you checked that your model works equally well across groups" | Groups we can check: microphones (4 known + 3 unseen arrays), activities, homes (SINS vs our kitchens), one mic vs four. Groups we cannot: age, sex (SINS is one person). Said plainly (§13.6, §12). |
| "AI must be central … If you build a regular website … that doesn't count on its own." | The core job (sound → activity) is a trained model; without it there is no product (§6). |
| "Does it beat a simple baseline? … Report your baseline's score next to your model's score" | Majority, Apple SoundAnalysis zero-shot, AST/CED zero-shot, CLAP zero-shot, published DCASE baseline and winner (§13.3). |
| "Where does it fail? Show at least one example your model gets wrong and explain why" | ≥ 5 real failures (§13.8). |
| "Make sure all your results come from test data your model didn't see during training." | Session-disjoint folds re-verified in code; eval set run once, never tuned on (§13.2). |
| "Make it your own": "Your own user or setting … Your own data … Your own question." | Own setting (a parent living alone, caregiver view), own data (own-kitchen slice), own question ("can a laptop mic do what £419 sensor kits do, and how often is it wrong?"). |
| Hacker Guide common mistake: "Reusing a tutorial dataset without asking a new question of it" | SINS is a 2018 challenge set; our question (single consumer mic, unseen mic, product-level misses vs false alarms, against Apple's classifier) was not asked there. |

**Why Health over the other tracks.** The pre-kickoff triage (`docs/research/track-triage.md`) scored Finance 49, Health 41 (with HeatRx as the Health idea), Climate 37 out of 55. The wow-pitch round (`docs/research/wow-pitches.md`) then found Kettle, scoring it 50/60 (wow 8, depth 9, originality 8, impact 9, buildability 7, data 9), above every Finance and Climate pitch, because it fixes Health's two weak cells: "AI must be central" (Kettle's core is a model, not a lookup) and "strong incumbent to rebuild" (nine incumbents torn down in stage 1). Gold-sponsor fit is 5/5: Arecibo AI builds a companion app for older adults with cognitive impairment and their caregivers (`docs/RULES-AND-RUBRIC.md`).

## 2. Problem

- **One sentence:** An adult child who lives far from a parent with early memory loss cannot tell whether today was a normal day without calling to check up or putting cameras in the house; the sensor kits that answer this cost hundreds, make the parent feel watched, and say nothing about how often they are wrong.
- **Cited statistic (primary source opened Sat Nov 14 2026, ~10:00 CT):** "Of older adults 65 and older living in the community, 59% lived with their spouse/partner in 2023. **About 28% lived alone.**" US Administration for Community Living, *2023 Profile of Older Americans* announcement, https://acl.gov/news-and-events/announcements/acl-releases-2023-profile-older-americans . (This covers all community-dwelling adults 65+, not people with memory loss specifically; use it as context, not as the size of Meera's group. Counts such as "16.2 million" and dementia-specific living-alone shares were seen only in snippets and are **unverified; do not quote** until Lane B opens the PDF, §17.)
- **Voice of the user** (paraphrased; links in `pain-points.md`):
  1. A daughter put a camera in for her 80-year-old mum, who "hated it and said it felt like spying." (r/eldercare, P1)
  2. A self-described older adult: if their kids surveilled them like that, they'd "move and never tell them where I went." (r/AgingParents, P1)
  3. "Sensors fire on motion, but you need the opposite: an alert when there's NO motion for X hours." (r/smarthome, P10b)
  4. Alexa Emergency Assist smoke alerts came through about 2 of 15 tests. (Amazon forum, P3)
  5. "20 dollars a month for basic routine. What a joke." (Snug App Store review, P5=)

## 3. Who it's for

**Meera, 34** (invented persona), a nurse-scheduler in Chicago. Her father **Ravi, 79** (invented), lives alone 300 miles away in the family house in Columbus. He was diagnosed with early memory loss (mild cognitive impairment) last spring. He still cooks breakfast, watches cricket highlights and the news, and calls her on Sundays. He refused a pendant ("I'm not an invalid") and would never accept a camera.

- **The exact moment:** Tuesday, 11:05 AM, between meetings. Meera wonders "did Dad get up and have breakfast?" Calling now feels like checking up on him; texting gets no reply until afternoon. She opens Kettle on her phone: *Listening · last heard 40 s ago. So far today: cooking around 8:15–8:45, washing up around 8:45, TV from about 9:15.* Her rule "Kitchen activity by 10:00 AM" says *Met at 8:20 AM*. She closes the tab.
- **The day it matters:** Thursday the rule says *Not heard by 10:00 AM. Kettle was listening the whole time.* She calls. (Or it says *Can't tell: Kettle wasn't listening from 7:40 to 9:55 AM*, so she knows the silence means nothing.)
- **Ravi's side:** the laptop sits on the kitchen counter, plugged in. He agreed to it after reading three lines on the screen. When his friend visits, he presses **Pause for 1 hour**; Meera sees "Paused by Dad at 3:10 PM".
- **What they do today instead:** daily calls that both find awkward; a Snug-style check-in app he forgets to tap (P2, 25 items); or nothing until a crisis.

## 4. What already exists (teardown summary)

Full teardowns: `docs/research/kettle/teardown-*.md`; matrix: `feature-matrix.md`; REA ledger: `rea-evidence.md`.

| Product | Link | Why people use it | Price (latest public) | Biggest weakness | Evidence |
| --- | --- | --- | --- | --- | --- |
| Howz | https://www.howz.com/reassure | Easy sensor kit, routine alerts with plain names ("Late start", "Low day activity") | £149 kit + £9/mo (2020 consumer); £45–65/mo per user for councils (2026) | Raw sensor events ("Toilet opened 15:59"); hub drops and silence looks like a normal day; a demo sensor last seen 13 months earlier with no warning | `teardown-howz.md`; P4, P10a; REA `ev_19b89bee…` (static Astro site, app on separate origins) |
| Canary Care | https://www.canarycare.co.uk/families/ | "No cameras or microphones", calm, time-window rules | £419–539 + £29/mo | Leads with "9 alerts in the past 24 hours"; swim lanes of red; logs users out | `teardown-canarycare.md`; REA `ev_6b2506c1…` (Next.js + headless CMS) |
| havn (cortekAI) | https://www.havnwellness.com | Resident sees what family sees; sound + motion | Not published | Sends a **4-second audio clip** to caregivers on flagged events (FAQ) while its shipped How-It-Works copy says "motion and environment only"; live room location ("ACTIVE NOW · Living Room") | `teardown-havn.md`; REA `ev_e6dad2f5…`, string read of exported bundles |
| Assistiv Home Sensing | https://www.assistiv.services/home-sensing | Acoustic activity set (cooking, conversation, TV, silence) | Not published | Up to 11 devices; "validated proxy" with no number | `teardown-assistiv.md`; REA `ev_854f08ab…` |
| Apple Sound Recognition / SoundAnalysis | https://support.apple.com/guide/iphone/use-sound-recognition-iphf2dc33312/ios | Free, on-device, hedged copy ("may be from a kettle") | Free | Alerts only the phone's owner; 30 knock alerts an hour; 8–36% battery/day; no activities, no caregiver view | `teardown-apple-sound-recognition.md`; REA `ev_b1d3865a…` (19 sound-category strings); P4, P5= |
| Alexa Together → Emergency Assist | https://www.aboutamazon.com/news/devices/alexa-together-launches-to-help-customers-remotely-care-for-loved-ones | First-activity and no-activity alerts, "type not content" feed | Together $19.99/mo (ended Jun 25 2024); EA $5.99/mo | Discontinued under families; smoke alerts ~2 of 15; TV set off glass-break alerts | `teardown-alexa-together.md`; P3, P5=, P8 |
| StackCare | https://stackcare.com | "Up & About Check", "typical" range gauge, "system offline" notice | $95–119/mo, 90-day minimum | Intimate counts (bathroom 16 times); price | `teardown-stackcare.md` |
| Care Daily | https://caredaily.ai | Best status sentence ("Looking good · 10 seconds ago") | Quote only (B2B) | RCT on caregiver anxiety, not detection accuracy | `teardown-caredaily.md` |
| Snug (lighter) | https://apps.apple.com/us/app/snug-daily-safety-check-in/id1122758716 | One tap a day, 4.87★ (2,273 US ratings) | Up to ~$20/mo | The parent must act daily; missed taps send police | `teardown-snug.md`; P2 |

- **What we rebuild from:** Howz/Canary's *job* (a family app that says whether the day was normal, with plain rules like "Late start") and Assistiv/havn's *sensor* (sound), with Care Daily's status sentence and Alexa Together's "type, not content" grain. Those four cover the value; the parts we refuse are their hardware, their cloud and their silence about accuracy.
- **Past hackathon projects:** WellNest (Devpost, https://devpost.com/software/wellnest-rplons) flags missed kitchen visits with LLM summaries, but runs on a custom event **simulator** with no accuracy claims. No GitHub repo found that does household-sound activity monitoring with a caregiver view and publishes accuracy (`raw/scout-opensource.md`).
- **Research prior art:** DCASE 2018 Task 5 (https://dcase.community/challenge2018/task-monitoring-domestic-activities): official CNN baseline 83.1 macro F1 on unknown mics, best entry (Inoue, IBM) 88.4. No published frozen pretrained-encoder (AST/CED/CLAP) result on SINS was found (search not exhaustive; re-check before claiming, §20).

## 5. What we build differently

### 5.1 Pain → Kettle → proof (the heart of the pitch)

"People told us X N times; incumbents do Y; Kettle does Z; here is the measurement." Top-10 themes by count × severity from `pain-points.md` (418 items, 153 stating a pain; one coder, counts ±20%).

| # | People told us (count, severity) | Incumbents do | Kettle does (feature, §8 id) | The test that proves it |
| --- | --- | --- | --- | --- |
| P1 | **The parent feels watched** (17, sev 3) | Kits promise "no cameras"; havn sends 4-s audio clips; Apple alerts only its owner | Audio only in a RAM ring buffer, never written or sent (F10); speech becomes "Conversation", never words (F11); the parent sees the same day bar and has Pause (F5, F6); copy says "Dad's kitchen today", never "monitoring" (§9) | `python -m eval.privacy_check` → `results/privacy_check.json`: 0 audio-like files, 0 write-opens, lsof clean, over a 60-s live run (probe 5 passed on the prototype); code-grep test for audio writes and for any ASR import; demo moment: presenter speaks, timeline shows "Conversation", no words anywhere |
| P2 | **Burden on the older adult** (25, sev 2) | Snug/Alexa need daily taps or talking; watches need charging | The parent does nothing after "Yes, start"; laptop stays plugged in; Pause is optional (F4) | Sample day plays with zero parent input; README counts setup steps (target: parent does 1 thing, once) |
| P3 | **Missed a real problem** (15, sev 3) | No incumbent publishes a detection or miss rate | Per-activity **missed count, recall, N, 95% CI** on SINS dev folds, the DCASE eval set (unknown mics) and our kitchens, on screen (F9); scope stated: "not an emergency device" | `results/metrics.json` per-class FN with N and session-bootstrap CI; failure gallery ≥ 5 (§13.8) |
| P4 | **Hub / Wi-Fi / battery** (19, sev 2); Apple SR 8–36% battery/day | Hubs + batteries; phone battery | A laptop on its charger; no hub; inference 24–35 ms per window (probe 4); fully offline | `results/runtime.json`: CPU seconds per window and mean CPU% over a 30-min live run on the 8 GB laptop |
| P5= | **Subscription price** (16, sev 2) | £419 + £29/mo; $95–119/mo; $20/mo | Free, open source, no hardware to buy, no account | Feature matrix cost column; fresh-clone install timed (M8) |
| P5= | **False alarms** (16, sev 2); TV → glass-break; 30 knocks/hour | Per-sound toggles, no confidence, no rates | Per-activity **false-alarm counts** and precision with N, TV row called out (F9); "Not sure" hatching below θ (F3); 2-of-3 smoothing; **no push alerts** (F7 rules only show state) | Confusion matrix + FP counts; ablation: false activity segments per hour with smoothing on/off on dev sample days; θ chosen on dev only |
| P7 | **Consent overridden** (8, sev 3) | No product makes consent a step | Listening starts only after the parent presses "Yes, start" on the kitchen device; the caregiver can't start or resume it remotely (F4) | Unit test: the live loop refuses audio until the consent flag is set from `/kitchen`; caregiver API has no start endpoint |
| P8 | **Discontinued under you** (11, sev 2) | Cloud services that stop | Local-first, open source; weights committed | `smoke_test.py` passes with the network off |
| P9 | **App bugs, logouts** (21, sev 1) | Accounts everywhere | No accounts, no login | Playwright sweep of every state: zero sign-in screens |
| P10a | **"No news" is ambiguous** (6, sev 3) | Last-event time only; dead sensors look alive (Howz) | Heartbeat is the first line: "Listening · last heard 40 s ago" / "Not listening since 10:42 AM…"; "Quiet" (heard, nothing happening) is drawn differently from "Not listening" (F2) | Test: feeding silence → "Quiet"; stopping input → "Not listening since…" within 2 heartbeats; the two never render the same |
| P10b | **Wants "no activity by X"** (9, sev 2) | Alexa Together had it (ended); kits have it behind hardware | Up to 3 caregiver-set rules with Met / Not yet / Missed / Can't tell, labelled "a rule you set" (F7) | `tests/test_rules.py`: normal day, late start, not listening (must give Can't tell, never Missed) |

Lower themes (P12 cancel/support, P13 raw data, P14 install, P15 sharing, P16 cold start) are answered as side effects: no account to cancel; activity blocks instead of raw events; nothing to install but placing the laptop; the caregiver page opens on any device on the home network; no cold start (labels from the first window).

### 5.2 Keep · Cut · Add
- **Keep:** a family view that says whether the day looked normal; plain rule names ("Kitchen activity by 10:00 AM", after Howz "Late start", Caregiver Aware "Rise and Shine"); a status sentence with when it last checked (Care Daily); "type, not content" (Alexa Together); the resident sees what the family sees (havn).
- **Cut:** hardware kits, hubs, cloud, accounts, push alerts per event, raw sensor events, bathroom/intimate counts, live location, audio clips, cold-start routine learning.
- **Add (nobody has these):** published per-activity missed and false-alarm rates with N; the evidence under every block ("Sounds Kettle heard: dishes, pots and pans 0.36 · water tap 0.21"); a "Not sure" state; a heartbeat that makes silence unambiguous; the parent's consent and pause as first-class states; a comparison against Apple's own built-in classifier.

### 5.3 Why would anyone use ours instead? (for Meera, no "AI")
Meera can see at 11 AM that her father cooked and washed up, from a laptop he already owns, without a camera he'd hate or a kit that costs as much as a flight home. He agreed to it himself, he can switch it off when his friend visits, and when the page says "not heard by 10", it also tells her whether it was actually listening. And unlike every kit she looked at, it tells her up front which things it often gets wrong.

### 5.4 Who will care
- **Meera / caregivers:** fewer anxious calls on normal days; a reason to call on abnormal ones.
- **Ravi / older adults:** no device to wear or tap; consent and pause are his.
- **Clinicians, memory clinics, Arecibo AI:** changes in daily rhythm (meals, activity) are what families report at appointments; a labelled, privacy-preserving day log is a conversation starter, not a diagnosis.
- **Judges (MSR audio-ML researchers):** an honest frozen-encoder study on SINS with an unseen-mic slice, a consumer-mic slice, a calibration-based abstain rule and Apple as a baseline.

### 5.5 What is free in ours and why we can offer it
Everything: hardware (a laptop the family owns), software (open source), the model (Apache-2.0 CED-tiny, 21 MB, committed), the data (public SINS), no server to pay for (local-only). **How Meera sees it from Chicago without a server of ours:** the caregiver page needs no microphone, so the kitchen laptop and Meera's phone join a free private network (Tailscale personal plan or any WireGuard VPN), set up once by Meera; she opens `http://<laptop-name>:8000/`. This is a documented setup step in the README, not code we write, and it is how the demo phone connects too (or the same Wi-Fi). A relay or hosted sync stays out of scope (§8 Won't).

## 6. Does this need AI?

| Step | Lookup / rules / model | Why |
| --- | --- | --- |
| Mic → 16 kHz PCM → 10-s window | Plumbing | — |
| **Window → activity probabilities (9)** | **Model**: frozen CED-tiny encoder (192-d) + trained logistic-regression head | Hearing "washing up" vs "cooking" vs "TV" is a perception task with no rule-based solution; zero-shot maps score 40–49 macro F1 vs ~82 for a trained head (probe 2) |
| Window → "sounds Kettle heard" evidence | **Model**: CED-tiny's own AudioSet head (527 labels), top 3 among a fixed kitchen-relevant list | Shows the judge and Meera what the encoder heard, independent of the activity head |
| "Not sure" | **Rule** on model output: top probability < θ (θ picked on dev folds) | Transparent abstain |
| Windows → blocks | **Rule**: 2-of-3 smoothing, merge consecutive same-activity windows | Auditable; ablated |
| Heartbeat | **Rule**: last window time vs now (stale after 2 × hop + 30 s) | Must never be learned |
| Caregiver rules ("by 10:00 AM") | **Rules** set by Meera | SINS has no clock times, so a learned routine can't be validated; "LLMs format, rules decide" (AGENTS.md §5) |
| Day summary sentence | **Template** from blocks | Deterministic, no hallucination |

- **The model component judges will see:** a classifier (sound → one of 9 activities), CED-tiny chosen because it equals the best probe score at 1/40th of AST's CPU time (probe 2, D); AST, CED-small and CLAP are ablations.
- **No-AI baseline:** majority class (always "Quiet") and a loudness rule (RMS above a threshold → "something happening"). **Zero-shot baselines:** Apple SoundAnalysis (what an iPhone/Mac already ships), AST/CED AudioSet maps, CLAP prompts (probe 3: 40.0, 45.4/42.1, 48.8 on 304 clips).
- **Chatbot test:** a general LLM can't do this job at runtime because it can't hear the kitchen: a text chatbot gets no audio, and an audio-capable LLM would need the audio sent to a cloud, which breaks the privacy promise (P1) and the offline promise (P4, P8). What an LLM *could* do: write a warmer daily summary from the block list. We don't, because a template is deterministic, testable and never invents an activity ("Dad had lunch") the model didn't detect; the summary's facts must equal the blocks exactly (a unit test checks it). Measurable difference: Kettle's macro F1 vs zero-shot models on the same clips, and a 0-byte network footprint during live use.
- **LLMs format, rules decide:** there is no LLM in the product. The only model decisions are the activity label and the evidence sounds; every user-facing decision (not sure, rule state, heartbeat) is a rule on top, unit-tested.

## 7. The core flow (5 steps, each visible in the demo)

1. **Ravi says yes.** On the kitchen laptop, `/kitchen` shows three plain lines and "Yes, start". The browser asks for the mic; he allows it.
2. **Kettle listens.** The kitchen screen shows "Listening for kitchen sounds", a "Sounds like washing up" chip that updates every 2 s, and "Nothing is recorded."
3. **Activities land on the day bar.** Every 10-s window is labelled; after 2 of 3 agree, a block settles onto the bar with its evidence ("Washing up · dishes, pots and pans 0.36 · water tap 0.21 · how sure: high").
4. **Meera checks.** On her phone, `/` shows the heartbeat, the one-line summary, the day bar and her rule "Kitchen activity by 10:00 AM: Met at 8:20 AM".
5. **She can see how sure it is.** "How sure is Kettle?" shows, per activity, how often it was missed and how often it was a false alarm, with N, from `results/metrics.json`.

**The 60-second test (script of what happens on screen):** (0–10 s) Kitchen screen, "Yes, start", mic allowed. (10–25 s) Presenter clinks two plates under a running tap; the chip says "Sounds like washing up" within ~2–3 s (probe 4: 2.6 s for a loud onset); a Washing up block settles on the bar ~10–20 s later. (25–35 s) Presenter speaks a sentence; the chip says "Conversation"; no words appear anywhere. (35–45 s) Presenter presses Pause; the caregiver phone shows "Paused by Dad at 11:42 AM". (45–60 s) Caregiver view: rule Met, summary sentence, tap a block for its evidence, "How sure is Kettle?".

**The one interactive moment:** the judge makes a sound themselves (finals, live mic), or in Round 1 drops any audio file on **"Try your own sound"** (demo page) and watches it go through the same pipeline, including the designed "Not sure" and "That isn't audio Kettle can read" outcomes.

**Three golden-path demo inputs** (real SINS dev clips stitched in session order; the clock times are staged and labelled so, because SINS dev clips carry no clock times):
1. **"A usual morning"**: Quiet 6:00–7:40 → Cooking 8:20–8:40 → Washing up 8:45 → Eating → TV 9:10–10:30 → rule Met at 8:20.
2. **"A quiet morning"**: Quiet until 10:00 → rule Missed at 10:00 ("Kettle was listening the whole time") → Cooking at 10:35 (late start).
3. **"A TV-only afternoon"**: TV 13:00–17:30 with a 40-min gap where the laptop slept → the TV rule (> 4 h) fires; the gap shows "Not listening 14:10–14:50", and the rule says Can't tell for that stretch.
Plus one **ambiguous** input (a cooking/eating edge clip that the model is unsure of → hatched "Not sure") and one **garbage** input (white noise / a non-audio file → "Not sure" or a designed error, never a confident activity).

## 8. Features

Ids are used in §5 and §9. Cut order: highest number in "Cut order" goes first.

| Id | Feature | Must / Should / Could / Won't | Serves (evidence) | Rubric line it moves | Done-check | Cut order |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | **Live kitchen mode**: browser mic → WebSocket → 10-s windows every 2 s → label + confidence + top sounds; "Sounds like…" chip from the last 5 s | Must | Brief "real input producing a result"; probe 4 | Technical 30, Demo 30 | Playwright fake-mic run shows ≥ 5 labels; onset→label median logged in `results/runtime.json` | never |
| F2 | **Heartbeat** line (listening / not listening since / paused / never started) | Must | P10a (6, sev 3); Howz dead-sensor anti-pattern | Impact 20, Testing 15 | `tests/test_heartbeat.py`: silence ≠ no input | never |
| F3 | **Day bar + blocks + evidence card + "Not sure" hatching** | Must | P5= (16), ui-patterns 2/5/6, better-than "evidence under every bar" | Communication 15, Demo 30 | Screenshot of every block state; evidence matches the window events | never |
| F4 | **Consent first-run on the kitchen device** ("Yes, start" / "Not now", read aloud) | Must | P7 (8, sev 3), P2 | Impact 20 | `tests/test_consent.py`: audio refused before consent | never |
| F5 | **Pause / Resume / Turn it off** (15 min, 1 hour, until tomorrow morning; weekly "Keep it on?" that pauses if unanswered; consent teach-back step), visible to the caregiver as "Paused by Dad at 3:10 PM" | Must | P1 (17, sev 3), P7 | Impact 20, Demo 30 | Pause on `/kitchen` → `/` shows paused within 1 s (WebSocket push) | never |
| F6 | **Caregiver view** `/`: heartbeat, summary sentence, day bar, rules, footer | Must | Persona §3; ui-patterns "Kettle's main screens" | Demo 30, Impact 20 | Renders at 393×852 and 1440×900 without scrolling to the bar | never |
| F7 | **Caregiver rules** (≤ 3): kitchen activity by HH:MM; any activity by HH:MM; TV more than N h. States Met / Not yet / Missed / Can't tell | Must | P10b (9) | Impact 20 | `tests/test_rules.py` 3 scripted days + edge cases | never (TV rule is cut order 6) |
| F8 | **Demo mode**: "Play a sample day" (3 scenarios) streaming real SINS clips through the same pipeline at 20× speed; no mic, no network | Must | Round 1 judges have no mic; AGENTS.md §4 no-key mode | Technical 30 | `smoke_test.py` plays scenario 1 end to end in < 60 s offline | never |
| F9 | **"How sure is Kettle?"** `/how-sure`: per-activity missed / false alarms / N / CI, baselines, the worst slice, 5 failures; read from `results/metrics.json` | Must | P3, P5=; Brief "report missed cases and false alarms separately" | Testing 15, Communication 15 | Page numbers == `results/metrics.json` (test) | never |
| F10 | **Nothing-saved guarantee + `python -m eval.privacy_check`** | Must | P1; probe 5 | Testing 15, Q&A 20 | Exit 0; `results/privacy_check.json` | never |
| F11 | **Speech as a type only** ("Conversation", "Talking or TV") | Must | P1; Alexa "type not content" | Impact 20 | Grep test: no `whisper`, `speech_recognition`, `asr`, `transcri` in `kettle/` | never |
| F12 | **"Try your own sound"** file drop (WAV/MP3/M4A/OGG ≤ 60 s, in-memory decode) → windows → labels | Should | Brief "real input"; the one interactive moment | Demo 30, Technical 30 | Golden + not-sure + garbage files each give a designed screen | 5 |
| F13 | **Day summary sentence** (template) | Should | Care Daily status sentence | Communication 15 | `tests/test_summary.py`: facts == blocks | 7 |
| F14 | **Dark mode** | Should | Caregiver phone at night | Communication 15 | Screens in both themes | 3 |
| F15 | **Read-aloud consent** (Web Speech synthesis, local) | Should | Older-adult accessibility | Impact 20 | Button speaks the 3 lines | 4 |
| F19 | **Remote caregiver access** via a private VPN (Tailscale/WireGuard) documented in the README; laptop "stay awake" setup (`caffeinate -s` / Energy settings) and a printable counter card ("This laptop listens for kitchen sounds. Nothing is recorded.") | Must (docs only) | §3 persona is remote; UX red-team: lid-close is the new dead sensor; visitors | Impact 20 | README section followed on a second device | never |
| F16 | **Phone as kitchen mic** via self-signed HTTPS | Could | Old phone on a stand (better-than #4) | Impact 20 | Phone Safari shows listening | 1 |
| F17 | **"Usual" faint band** on the day bar from the caregiver's own rule times | Could | StackCare typical gauge | Communication | Screenshot | 2 |
| F18 | Weekly view (7 day bars) | Could | Caregiver trend | — | — | 1 |
| — | Fall / emergency detection, smoke/CO/glass, any ASR or voice features, accounts, cloud sync, push notifications, learned routines, native apps, medication features, multi-home dashboards | **Won't** | `better-than.md` won't-build table; P3 (unvalidatable safety-critical), P1, P8, P9 | — | — | — |

## 9. Design and UX spec

Inputs: `ui-patterns.md` (measured incumbent screens), `.claude/skills/component-craft` (measured system, ten laws), `apple-design`, `emil-design-eng`, `ui-polish`, `frontend-design`. AGENTS.md / ui-polish bans hold: **no cream or black "old money" canvas, no big italic serif headlines, no purple gradients, no glow buttons, no side-stripe (`border-left`) cards.**

### 9.1 How it stays calm, warm and clearly not surveillance (specifics)
1. **Past tense, minutes late, never "now".** The caregiver view shows what *happened in the kitchen* as settled blocks; no live location, no "ACTIVE NOW" (havn anti-pattern). The only live element on the caregiver view is the heartbeat.
2. **Words before colours.** Every state has a sentence; colour only reinforces it. **Red is reserved for "Kettle itself is broken"** and never used for an ordinary activity or a rule (Canary anti-pattern).
3. **Lead with the day, not the alerts.** There is no alert count anywhere (Canary "9 alerts" anti-pattern). Rules sit below the bar and read as checks, not alarms.
4. **The parent's agency is visible.** "Paused by Dad at 3:10 PM" is styled like any other fact, never as a warning; the Pause button is the largest control on the kitchen screen.
5. **Privacy is said where the data is.** Under the bar: "No audio saved. No words kept. Only these labels." with a link to the privacy check result.
6. **Hedged evidence.** "Sounds like washing up", "how sure: high", "Not sure" (Apple's "may be from" pattern), never "Dad washed up" or "Dad ate".
7. **Warm, not cute.** Plain sans, generous spacing, a soft neutral canvas, activity colours at medium saturation; no illustrations of old people, no hearts, no stock photos, no exclamation marks, no "Nothing to worry about!" (ui-polish ban; unsafe in health).
8. **No intimate categories.** Kitchen and living-room activities only; no bathroom, sleep or body sounds as categories (StackCare/havn anti-pattern).

### 9.2 Screens
| Screen | URL | Device | Purpose |
| --- | --- | --- | --- |
| S1 Caregiver: "Dad's kitchen today" | `/` | Meera's phone 393×852 (primary), laptop 1440×900 | Is today normal? |
| S2 Kitchen device | `/kitchen` | The kitchen laptop 1440×900 (and 1280×800), read from 1–2 m away | Consent, listening state, pause |
| S3 "How sure is Kettle?" | `/how-sure` | Both | Measured misses and false alarms, baselines, failures |
| S4 Demo controls | panel on S1 and S2 (`?demo=1` opens it) | Both | Play a sample day; try your own sound |
| S5 Rule editor | sheet on S1 | Phone | Set up to 3 rules |

### 9.3 Information hierarchy
**S1 (phone, top to bottom, no scrolling needed to see the bar):** (1) title row "Dad's kitchen today" + date (left), "How sure?" link (right) · (2) **heartbeat line** · (3) **summary sentence** · (4) **day bar** 6 AM → midnight with inline labels, hour ticks every 3 h, a "now" tick · (5) rule cards (≤ 3) · (6) footer: privacy line, "Prototype, not medical advice.", demo badge when in demo. Tapping a block opens the evidence card under the bar (inline, pushes the rules down; not a modal).
**S2 (laptop at 1–2 m):** (1) one huge status sentence · (2) the permanent re-explainer "Listening since {Monday}. Meera sees the kinds of sounds, not recordings or words." (so a parent who forgot agreeing is told again every time he looks) · (3) every check Meera set, listed ("Meera's check: kitchen activity by 10:00 AM") · (4) the same day bar, taller, fewer labels · (5) Pause button (largest target) and "Turn it off" · (6) small "Sounds like…" chip behind "What does it hear?" (56 px only in demo/presenter mode) · (7) footer "Nothing is recorded. Only the kind of sound is noted. Prototype, not medical advice."
**S3:** (1) the one-line verdict ("Kettle catches TV and vacuuming almost always. It often mixes up cooking and eating. 'Moving about' is its weakest.") · (2) table: activity | caught (recall) | missed | false alarms | N | 95% CI · (3) baselines row group · (4) "Where it does worst" (worst slice first) · (5) 5 failures with the clip id and cause · (6) data line "Measured on … N = …, run on <date>, commit <hash>".

### 9.4 State table (exact copy). `{}` = filled from data; times in the viewer's locale, 12-hour.

**Heartbeat line (S1, first line; S2 status)**
| State | Trigger | Glyph | S1 copy (caregiver) | S2 copy (kitchen) |
| --- | --- | --- | --- | --- |
| Never started today | no consent yet / no window today | hollow grey dot | "Kettle isn't on yet. It starts when Dad chooses to turn it on." | (consent screen) |
| Turned off by parent | "Turn it off" pressed | hollow grey dot | "Turned off by Dad on {Tuesday at 6:05 PM}." | "Kettle is off." |
| Starting | consent given, < 10 s of audio | grey dot, slow pulse | "Starting… the first label appears in about 10 seconds." | "Listening… the first sound label appears in about 10 seconds." |
| Listening | last window ≤ 2 × hop + 30 s ago | green dot | "Listening · last heard {40 s} ago" | "Listening for kitchen sounds" |
| Not listening (stale) | no window for > 2 × hop + 30 s, not paused | grey dot, no pulse, grey hatch on the bar from that time | "Not listening since {10:42 AM} (laptop asleep, closed or off). Nothing is known after that." | (the kitchen page is closed, so nothing shows) |
| Mic blocked | browser denied mic | grey dot | "Not listening: the microphone is blocked on the kitchen laptop." | see S2 states |
| Paused by parent | Pause pressed | slate-blue pause glyph | "Paused by Dad at {3:10 PM} · resumes at {4:10 PM}" / "Paused by Dad at {3:10 PM} · until tomorrow at {8 AM} at the latest" | "Paused. Kettle isn't listening." |
| Demo | demo playing | outlined "Sample day" tag | "Sample day · recorded sounds from a public research home, not Dad" | same |
| Server error | WebSocket closed and HTTP fails | red dot (the only red) | "Kettle stopped working on the kitchen laptop at {10:42 AM}." | "Kettle stopped working. Labels so far are kept. Restart Kettle on this laptop." |

**Summary sentence (S1)** — templates in `kettle/timeline.py`:
- Some activity: "So far today: {cooking around 8:15–8:45}, {washing up around 8:45}, {TV from about 9:15}." (max 3 items, most recent last; times **rounded to 15 minutes** in the summary so it reads as a day, not a log; exact times only in the evidence card; "and 2 more" link scrolls the bar)
- Nothing yet, listening: "No kitchen activity heard yet today. Kettle has been listening since {7:02 AM}."
- Mostly not sure: "Kettle wasn't sure about {40 minutes} of sound this morning."
- Not started: (hidden)
- End of day (after 9 PM): "Today: {cooking twice}, {washing up}, {TV for 3 h 10 min}."

**Day bar block states (S1, S2)**
| State | Drawing | Label | Evidence card copy |
| --- | --- | --- | --- |
| Activity (high conf ≥ 0.8) | solid fill, activity colour | "Cooking" | "Cooking · {8:20–8:40 AM} · {12} windows · how sure: high" / "Sounds Kettle heard: mostly {frying}, some {dishes} and {running water}" (scores behind "Details": {Frying 0.31 · Dishes, pots and pans 0.22 · Water tap 0.12}) / "Kettle labels 10-second stretches of sound. It keeps no recording." |
| Activity (θ ≤ conf < 0.8) | same fill at 70% opacity | "Cooking" | "… how sure: medium" |
| Not sure (conf < θ) | diagonal hatch in muted ink, no fill colour | "Not sure" | "Not sure · {8:41–8:43 AM} · Kettle heard something but couldn't tell what. Closest guesses: {Eating 0.38 · Cooking 0.31}." |
| Talking or TV | split hatch of the two colours | "Talking or TV" | "Talking or TV · Kettle heard voices and can't tell talking from the TV here. It never keeps words." |
| Quiet (SINS "absence") | 2 px neutral line on the bar baseline | none (tooltip "Quiet") | "Quiet · {6:00–7:40 AM} · Kettle was listening; the kitchen was quiet." |
| Not listening | gap with light grey cross-hatch | "Not listening" | "Not listening · {14:10–14:50} · Kettle can't say what happened here." |
| Paused | dotted slate-blue band | "Paused by Dad" | "Paused by Dad · {3:10–4:10 PM}" |
| Future | blank, faint ticks | — | — |

**Rule cards (S1)**
| State | Copy |
| --- | --- |
| Met | "Kitchen activity by 10:00 AM" · "Met at {8:20 AM} ({cooking})" |
| Not yet | "Kitchen activity by 10:00 AM" · "Not yet · checks in {47 min}" |
| Missed | "Kitchen activity by 10:00 AM" · "Not heard by 10:00 AM. Kettle was listening the whole time." · secondary text "You might call to say hello." |
| Can't tell | "Kitchen activity by 10:00 AM" · "Can't tell: Kettle wasn't listening from {7:40} to {9:55 AM}." |
| TV long (rule 3) | "TV on for more than 4 hours" · "TV for {4 h 20 min} today (from {1:05 PM})" / "Not today" |
| No rules | "Add a check, like 'kitchen activity by 10:00 AM'. Kettle only checks rules you set." · button "Add a check" |
| Footer under cards | "Rules you set. Kettle doesn't learn Dad's routine and doesn't send alerts." |

**Kitchen device (S2)**
| State | Headline (40 px) | Body (24 px) | Controls |
| --- | --- | --- | --- |
| First run (consent, step 1) | "This laptop listens for kitchen sounds." | "The program is called Kettle. It only notes the kind of sound, like 'dishes' or 'TV'." · "It keeps no recordings and no words." · "Meera sees a day timeline like this one. You can pause it or turn it off any time." | "Next" (primary, 64 px) · "Not now" · "Read this to me" |
| First run (consent, step 2: teach-back) | "Is it OK for Meera to see this?" | "She will see the kinds of sound and when they happened. Nothing else." | "Yes, Meera can see this" (primary) · "No, not now" |
| Not now / turned off | "Kettle is off." | "This laptop isn't listening. Press Start when you want it on." | "Start" |
| Weekly check (7 days after consent) | "Kettle has been on for a week. Keep it on?" | "Meera sees the kinds of sounds, not recordings or words." | "Keep it on" · "Turn it off". **No answer within 24 h → Kettle pauses** (never keeps listening by default) |
| Permission asked | "A box will pop up about the microphone." | "Press Allow. Only this laptop uses it." | — |
| Mic denied | "Kettle can't hear the kitchen." | "Ask Meera or a helper to turn the microphone on." (fold "Steps for a helper": Chrome: the icon left of the address → Microphone → Allow → Try again; Safari: Settings for this website → Microphone → Allow) | "Try again" · "Play a sample day instead" |
| No mic found | "No microphone found." | "Plug one in, or use a laptop with a built-in microphone." | "Try again" · "Play a sample day instead" |
| Starting | "Listening…" | "The first sound label appears in about 10 seconds." | Pause |
| Listening | "Listening for kitchen sounds" | "Listening since {Monday}. Meera sees the kinds of sounds, not recordings or words." · "Meera's check: kitchen activity by 10:00 AM." (every caregiver rule listed here, so nothing is hidden from him) · small chip (24 px) "Sounds like {washing up}" behind a "What does it hear?" toggle, on by default for the first day, then off; the 56 px chip is shown only in demo/presenter mode | **Pause** (opens: "Pause for 15 minutes" · "Pause for 1 hour" · "Pause until tomorrow morning", capped at 8 AM next day) · "Turn it off" (secondary) |
| Listening, not sure | same | chip "Not sure what that is" | Pause |
| Listening, quiet | same | chip "Quiet" | Pause |
| Paused | "Paused. Kettle isn't listening." | "Meera sees: Paused by you at {3:10 PM}." · "Starts listening again at {4:10 PM}." | **Resume listening** |
| Just resumed (10 s) | "Kettle is listening again." | "Paused from {3:10} to {4:10 PM}." | Pause |
| Error | "Kettle has stopped." | "Press Try again, or ask Meera for help." (fold for a helper: technical detail; "today's timeline is kept") | "Try again" |
| Demo | "Sample day: {A usual morning}" | "Recorded sounds from a public research home, played fast. Not Dad." | "Stop sample" |

**Try your own sound (S4)**
| State | Copy |
| --- | --- |
| Idle | "Try your own sound. Drop an audio file (up to 60 seconds). It's read in memory and never saved." |
| Reading | "Listening to {kitchen.m4a}… {3 of 6} windows" (shimmer on the label) |
| Result | the windows as a mini bar + "Kettle heard: {Washing up 0:00–0:20 · Not sure 0:20–0:30}" |
| All not sure | "Kettle wasn't sure about any of this. It knows 9 household activities; this may be something else." |
| Too short | "That clip is {3} seconds. Kettle needs at least 10 seconds." |
| Not audio / unreadable | "That isn't audio Kettle can read. Try a WAV, MP3, M4A or OGG file." |
| Too long | "Kettle reads the first 60 seconds only." (then proceeds) |

**S3 "How sure is Kettle?"**: Loading "Reading the latest test results…"; no results file → "No test results yet. Run `python -m eval` to make them."; results → the table, every number with N; dev-only results carry the tag "Development folds" until the eval run exists, then "Held-out test, run once on {Nov 14, 11:20 PM}".

**Narrow (393 px):** the bar spans 6 AM–midnight in 353 px; labels shed in order: hour ticks to every 6 h → block labels inside blocks narrower than 44 px move to the evidence card only → summary wraps to 3 lines max. Touch targets ≥ 44 px; the bar's hit area is 56 px tall even though the bar is 28 px.

### 9.5 Tokens
**Type** (system sans: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`; `font-variant-numeric: tabular-nums` on all times, durations and numbers; weights 400/500/600 only; letter-spacing -0.01em on ≥ 20 px). Eight sizes, shared by both screens:
| Token | px / line-height | Use |
| --- | --- | --- |
| `--fs-micro` | 13 / 18 | hour ticks, tags, CI brackets |
| `--fs-meta` | 15 / 22 | heartbeat time, card meta, footer |
| `--fs-body` | 17 / 26 | caregiver body, rule text, evidence card |
| `--fs-lead` | 20 / 28 | caregiver summary sentence, kitchen meta |
| `--fs-kbody` | 24 / 34 | kitchen body text (older adult at 1–2 m) |
| `--fs-title` | 28 / 34 | caregiver page title |
| `--fs-khead` | 40 / 48 | kitchen headline |
| `--fs-chip` | 56 / 64 | kitchen "Sounds like…" chip |
(Larger than component-craft's 13–14 px body on purpose: caregivers read on phones, older adults read from across a kitchen. Kitchen body never below 24 px.)

**Spacing:** 4 px base; scale 4, 8, 12, 16, 24, 32, 48, 64. Page gutters 16 px (phone), 32 px (laptop). Card padding 16 (phone) / 24 (laptop).
**Radii:** tray 20 · card 16 · row/area 12 · button 12 (md) / 16 (kitchen lg) · chip 8 · tag 6 · pill/dot 999. Day-bar blocks 4 px radius (inner), the bar 8 px.
**Controls:** caregiver buttons 44 px tall (15 px text); kitchen buttons 64 px tall, ≥ 240 px wide (24 px text); Pause button 96 px tall, full width up to 520 px.

**Colour (light).** Canvas is a cool near-white, not cream.
| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--canvas` | #F4F5F7 | #111214 | page |
| `--card` | #FFFFFF | #1A1C1F | cards, bar track |
| `--line` | #E3E6EA | #2C2F34 | hairlines, ticks |
| `--ink` | #15181C | #EEF0F2 | headlines |
| `--text` | #3A4048 | #C9CED4 | body |
| `--muted` | #626A73 | #99A1AA | meta (≥ 4.5:1 on card in both) |
| `--ok` | #1E7F4A | #4CC386 | listening dot only |
| `--paused` | #4B6584 | #8FA9C9 | pause glyph, paused band |
| `--stale` | #8A6100 | #D7A640 | "not listening" text accent |
| `--danger` | #C62828 | #FF6B6B | server error only |
| `--act-cooking` | #D47A1F | #F0A050 | amber |
| `--act-washing` | #2B83C6 | #5FAEEA | blue |
| `--act-eating` | #C04F75 | #E7809F | rose |
| `--act-vacuum` | #2F9A8A | #5CC9B8 | teal |
| `--act-tv` | #5462C9 | #8C97EC | indigo (solid only; no gradients) |
| `--act-talk` | #3A9A55 | #6CCB86 | green |
| `--act-working` | #6E7B88 | #9AA6B2 | slate |
| `--act-moving` | #9AA2AB | #737C86 | light slate |
| `--act-empty` | #C5CAD0 | #3E434A | 2 px baseline line |
| `--hatch` | #626A73 @ 35% | #99A1AA @ 35% | not sure / not listening hatch |
Block labels sit **outside** the fill when the block is narrower than its label; inside labels use `--ink` on fills lightened to ≥ 4.5:1 (checked in M7 with a contrast script). Activity colours are never the only cue: every block has a text label or an evidence card.
**Surfaces:** card edge `0 0 0 1px var(--line), 0 1px 2px rgba(0,0,0,.04)`; no large drop shadows; no gradients anywhere.

### 9.6 Motion
Easings (4 only): out `cubic-bezier(0.22,1,0.36,1)`; out-soft `cubic-bezier(0.25,1,0.5,1)`; drawer `cubic-bezier(0.32,0.72,0.24,1)`; linear (shimmer, pulse).
- **The one orchestrated moment: a new activity settles onto the day bar.** t=0: the block grows from its left edge (`transform: scaleX(0→1)`, origin left, 380 ms, out). t=+120 ms: its label fades in (opacity 0→1, translateY 4→0 px, blur 3→0 px, 300 ms, out). t=+160 ms: the summary sentence crossfades (old text out 200 ms upward with blur 3 px, new text in 260 ms out-soft). t=+200 ms: the heartbeat "last heard" number rolls (digit roll, 260 ms). Nothing else moves; existing blocks are never removed and re-added (component-craft law 5; MutationObserver check in M7).
- **Kitchen chip change:** blur crossfade 260 ms; width reserved for the longest label ("Sounds like vacuuming") so nothing shifts.
- **Press feedback:** every button `:active { transform: scale(.97) }`, 160 ms; hover colour 150 ms.
- **Pause sheet:** slides up 320 ms drawer; closes 200 ms.
- **Evidence card:** unfolds with `grid-template-rows: 0fr → 1fr`, 300 ms out-soft.
- **Heartbeat dot:** listening = 2.4 s linear opacity pulse 1 → .55; stale = no pulse.
- **Reduced motion** (`prefers-reduced-motion: reduce`): no scale, translate or blur; state changes are a 120 ms opacity fade; the dot doesn't pulse; the digit roll becomes an instant swap.

### 9.7 Accessibility
- **Older adult (S2):** body ≥ 24 px, headline 40 px; targets ≥ 64 px; contrast ≥ 7:1 for headline and body (`--ink`/`--text` on `--card` both pass); plain words, no jargon ("microphone", not "input device"); one decision per screen; consent can be read aloud; the Pause button names its effect.
- **Caregiver phone (393×852):** heartbeat, summary and bar visible without scrolling; targets ≥ 44 px; body 17 px; supports text zoom to 200% without horizontal scroll (the bar becomes a vertical list of blocks below 320 px of available width).
- One polite `aria-live` region per screen announces new blocks ("Washing up, 8:45 AM, how sure: high") and heartbeat changes; the bar has a text alternative (an ordered list of blocks, visually hidden); focus-visible rings `2px solid rgba(21,24,28,.22)`, offset 2 px; colours are never the only signal.

### 9.8 Trust display and disclaimers
- Every block → its evidence card (activity, time range, windows, how sure, top sounds from the encoder's AudioSet head, and "Kettle labels 10-second stretches of sound. It keeps no recording.").
- "How sure is Kettle?" link on S1 and S2, numbers read from `results/metrics.json` (never typed), with N, CI, split name and date.
- **"Prototype, not medical advice."** in the footer of S1, S2, S3, S4, in the README top, the write-up and the video end card. Also on S1: "Kettle is not an emergency device. It can't detect falls or call for help."

## 10. Architecture

### 10.1 Stack and why
Python 3.11 · FastAPI + uvicorn (one process serves the pages, a JSON API and one WebSocket) · static HTML + CSS + vanilla JS, no build step · numpy, soundfile, torch (CPU; MPS optional for batch embedding), transformers (CED-tiny; modeling code vendored under `kettle/vendor/ced/` with its Apache-2.0 notice so nothing runs `trust_remote_code`), scikit-learn · Playwright (screenshots, privacy check, fake-mic tests) · a 40-line Swift CLI for the Apple baseline (macOS only; its outputs are cached in `results/` so nobody else needs a Mac). Every piece ran end to end in probe 4 on the 8 GB laptop. Judges run `pip install -r requirements.txt && python app.py` with **no keys and no network** (weights and demo clips are committed).

### 10.2 Repo layout
```
app.py                    # FastAPI: pages, /api/*, /ws/audio, /ws/state; demo player
kettle/
  labels.py               # the 9 SINS classes, display names, colours, "meal activity" group
  data.py                 # SINS meta, folds, zip index, rate-limited range fetch (stage 3 M2)
  audio.py                # decode in memory (WAV/MP3/M4A/OGG via soundfile/av), resample to 16 kHz, 10-s windows
  encoders.py             # CED-tiny (+ AST/CED-small/CLAP for ablation): wave -> embedding, AudioSet scores
  model.py                # head: fit / predict_proba / save JSON / load JSON; temperature for calibration
  evidence.py             # AudioSet scores -> top-3 kitchen-relevant sounds
  live.py                 # ring buffer, hop scheduler, consent + pause gate, window events
  timeline.py             # window events -> blocks (smoothing, not-sure, merge) + summary sentence
  rules.py                # caregiver rules -> Met / Not yet / Missed / Can't tell
  heartbeat.py            # listening / stale / paused / never-started
  vendor/ced/             # vendored modeling_ced.py + feature_extraction_ced.py + LICENSE (Apache-2.0)
static/                   # index.html (caregiver), kitchen.html, how-sure.html, app.css, app.js, kitchen.js, worklet.js
models/ced-tiny/          # config.json + model.safetensors (21 MB, Apache-2.0) ; models/head.json (+ head.sha256)
demo_cache/               # 3 sample days: clip list + ~90 SINS dev clips (FLAC, mono, CC BY-NC 4.0, ATTRIBUTION.md)
data/                     # git-ignored: raw zips index, fetched clips, embeddings cache (data/emb/<encoder>/<file>.npy)
eval/                     # __main__.py (python -m eval), metrics.py, bootstrap.py, baselines.py, privacy_check.py, own_kitchen/
tools/apple_baseline/     # apple_classify.swift + build.sh + README
results/                  # metrics.json, metrics.md, confusion_*.png, failures.md, runtime.json, privacy_check.json, eval_run.json
tests/                    # test_folds, test_metrics, test_rules, test_heartbeat, test_timeline, test_consent, test_privacy_grep, test_summary
smoke_test.py             # golden path offline in < 60 s
```

### 10.3 Module contracts (inputs → outputs, field names and types)
| Module | Function(s) | Input → output | Done-check |
| --- | --- | --- | --- |
| `kettle/labels.py` | `CLASSES`, `DISPLAY`, `MEAL` | — → `CLASSES: list[str]` (9, SINS order), `DISPLAY: dict[str, str]`, `COLOUR_TOKEN: dict[str,str]` | imported by every module |
| `kettle/data.py` | `load_meta(split)`, `folds()`, `build_index(split)`, `fetch(names, out_dir)` | split ∈ {dev, eval} → `list[{"file": str, "label": str, "session": str, "node": str, "fold": int\|None}]`; `fetch` writes `data/clips/<file>.flac` (4-ch) and returns counts | `tests/test_folds.py`: 0 shared sessions per fold; eval sessions disjoint by label check |
| `kettle/audio.py` | `decode(bytes) -> (np.float32[ch, n], sr)`; `to_16k_mono(x, sr, channel=0)`; `windows(x, win_s=10, hop_s=10)` | raw bytes → float32 arrays; raises `AudioError("unreadable" \| "too_short")` | unit tests with a WAV, an MP3, silence, a JPEG |
| `kettle/encoders.py` | `load(name="ced-tiny")`, `embed(batch: float32[B,160000]) -> (emb float32[B,192], audioset float32[B,527])` | 16 kHz 10-s windows → embeddings + AudioSet probabilities; cached on disk by `(encoder, file, channel)` | reproduces probe 2 numbers on the probe clips |
| `kettle/model.py` | `fit(X, y, C) -> Head`; `predict_proba(head, X) -> float32[B,9]`; `save(head, path)`; `load(path)` | `Head = {"classes", "mean", "std", "coef" [9×D], "intercept" [9], "temperature", "theta", "encoder", "trained_on", "sha256"}` as JSON | round-trip test; sha256 printed by `python -m eval` |
| `kettle/evidence.py` | `top_sounds(audioset[527], k=3)` | → `list[{"name": str, "score": float}]` from a fixed list of ~60 household AudioSet labels | test: dishes clip → "Dishes, pots, and pans" first |
| `kettle/live.py` | `Session` dict + `feed(session, pcm_int16) -> list[WindowEvent]` | `WindowEvent = {"t": float (unix s), "start": float, "end": float, "label": str, "conf": float, "probs": dict[str,float], "sounds": list, "kind": "window10"\|"chip5"}`; refuses audio unless `session["consent"] is True and not paused` | `tests/test_consent.py`; fake-mic Playwright test |
| `kettle/timeline.py` | `blocks(events, theta) -> list[Block]`; `summary(blocks, now) -> str` | `Block = {"start", "end", "activity": str\|None, "state": "activity"\|"not_sure"\|"talk_or_tv"\|"empty"\|"not_listening"\|"paused", "conf": float, "n_windows": int, "sounds": list}` | `tests/test_timeline.py` (smoothing, merge, gaps) ; `tests/test_summary.py` (facts == blocks) |
| `kettle/heartbeat.py` | `status(last_window_t, paused, consent, now, hop_s) -> dict` | → `{"state": "never"\|"starting"\|"listening"\|"stale"\|"paused"\|"mic_blocked"\|"error", "since": float, "until": float\|None}` | `tests/test_heartbeat.py` |
| `kettle/rules.py` | `evaluate(rules, blocks, heartbeat_log, now) -> list[RuleState]` | `Rule = {"id", "type": "kitchen_by"\|"any_by"\|"tv_over", "time": "10:00", "hours": float}` → `RuleState = {"id", "state": "met"\|"not_yet"\|"missed"\|"cant_tell"\|"off", "at": float\|None, "detail": str}` | `tests/test_rules.py`: 3 scripted days + boundary cases |
| `app.py` | routes | `GET /`, `/kitchen`, `/how-sure`; `GET /api/today` → `{"heartbeat", "blocks", "summary", "rules", "demo"}`; `POST /api/consent`, `/api/pause {"minutes": 15\|60\|null}`, `/api/resume` (accepted only from `/kitchen`'s session token); `POST /api/rules`; `POST /api/try` (multipart audio → windows, in memory); `POST /api/demo/{scenario}`; `WS /ws/audio` (Int16 PCM in, window events out); `WS /ws/state` (pushes `/api/today` diffs to every open page) | `smoke_test.py` |
| `eval/__main__.py` | `python -m eval [--split dev\|dcase-eval\|own-kitchen] [--encoder ced-tiny]` | cached embeddings + frozen head → `results/metrics.json`, `results/metrics.md`, `results/confusion_<split>.png`, `results/failures.md` | `tests/test_metrics.py` hand-computed example |
| `eval/privacy_check.py` | `python -m eval.privacy_check [--seconds 60]` | runs `app.py` with a fake mic → `results/privacy_check.json` (+ exit code) | exit 0 |

**Persistence (labels only):** `data/timeline/<YYYY-MM-DD>.jsonl` holds window events and pause/consent events (no audio, no probabilities beyond the 9 numbers and top sounds). This is the only file the server writes during live use; the privacy check whitelists exactly it and the server log.

### 10.4 Data flow (text diagram)
```
Kitchen laptop browser (/kitchen)                              Kettle server (python app.py, localhost:8000)
 getUserMedia ─► AudioWorklet (16 kHz) ─► Int16 chunks 0.1 s ─WS /ws/audio─► live.feed: consent+pause gate
                                                                             │ RAM ring buffer (10 s; overwritten)
                                                                             ├─ every 2 s: last 5 s ─► encoder ─► head ─► chip event ─┐
                                                                             └─ every 10 s: last 10 s ─► encoder ─► head + AudioSet top sounds ─► window event
                                                                                                    │
                                                                   timeline.blocks (2-of-3, θ, merge) ─► rules.evaluate ─► heartbeat.status
                                                                                                    │                        (labels → data/timeline/*.jsonl)
Caregiver phone (/ on the home Wi-Fi) ◄──────────── WS /ws/state (today's blocks, rules, heartbeat) ◄┘
Demo player: demo_cache/<scenario>/*.flac ─► same live.feed path at 20× (no mic, no network)
Try your own sound: POST /api/try (bytes in memory) ─► audio.decode ─► windows ─► encoder ─► head ─► JSON (not stored)
```

### 10.5 Caching, offline, timeouts
- No external call at runtime. The only network use anywhere is `kettle/data.py` fetching SINS clips (stage 3, eval only): 0.5 s request spacing (Zenodo's 133/min cap), 120 s timeout, 5 retries with back-off, resumable (skips clips already on disk), progress logged to `.overnight/kettle/jobs/fetch.log`.
- Embeddings cached per `(encoder, file, channel)` in `data/emb/`; `python -m eval` never re-embeds unless `--recompute`.
- Apple baseline results cached in `results/baselines/apple_<split>.jsonl` (so non-Mac users get the numbers).
- WebSocket drops: the kitchen page reconnects with back-off (1, 2, 4, 8 s) and shows "Reconnecting…" in the heartbeat slot; the caregiver page falls back to polling `/api/today` every 10 s.

## 11. Data, models, licences

| Source | Use | Licence | Key? | Hit once and cached? |
| --- | --- | --- | --- | --- |
| SINS / DCASE 2018 Task 5 **development** set, Zenodo https://doi.org/10.5281/zenodo.1247102 (72,984 10-s clips, 4 nodes × 4 mics, one person, one home, one week) | Train head, dev folds, demo clips | **CC BY-NC 4.0** (attribution, non-commercial) | No | Yes: meta + zip index committed (small); ≤ ~9k clips fetched to `data/` (git-ignored) |
| SINS / DCASE 2018 Task 5 **evaluation** set, audio https://zenodo.org/records/1291760 (v1.0.0), labels https://zenodo.org/records/1964758 (v2.0.0) | One frozen test run | **CC BY-NC-ND 4.0** (no derivatives) | No | Yes; audio never committed, labels file committed unmodified with attribution (≈1 MB) |
| DCASE 2018 Task 5 results and baseline, https://dcase.community/challenge2018/task-monitoring-domestic-activities-results · https://github.com/DCASE-REPO/dcase2018_baseline (MIT) | Published comparison numbers | Page; MIT | No | Numbers quoted with link |
| CED-tiny, https://huggingface.co/mispeech/ced-tiny (revision `ace276d29dd0bb3f3517b0fa8cf300738c409019`) | Encoder + AudioSet evidence | **Apache-2.0** | No | Weights committed (21 MB) |
| AST, https://huggingface.co/MIT/ast-finetuned-audioset-10-10-0.4593 | Ablation + zero-shot baseline | **BSD-3-Clause** | No | HF cache, not committed |
| CED-small, https://huggingface.co/mispeech/ced-small | Ablation | Apache-2.0 | No | HF cache |
| LAION CLAP, https://huggingface.co/laion/clap-htsat-unfused | Zero-shot baseline + ablation | Apache-2.0 | No | HF cache |
| Apple SoundAnalysis `SNClassifySoundRequest(.version1)` (macOS 27.2.1) | Zero-shot baseline | Apple SDK (used on our own Mac; no redistribution) | No | Outputs cached |
| AudioSet ontology label names (via the model configs) | Evidence names | CC BY 4.0 (Google) | No | In model config |
| ACL 2023 Profile of Older Americans, https://acl.gov/news-and-events/announcements/acl-releases-2023-profile-older-americans | Problem statistic | US government work | No | Quoted |
| Own-kitchen recordings (Lane A) | Worst-slice test | Ours; consent forms; publish only with every audible person's agreement (§20) | — | Local `data/private/` |

**Commit:** labels and meta (dev meta.txt, folds, eval labels/map), the zip index (≈ 6 MB JSON; or regenerate in 35 s), ≤ 90 demo clips as mono FLAC (dev only, ~8 MB total, `demo_cache/ATTRIBUTION.md` naming the dataset, authors, DOI and licence), CED-tiny weights, `models/head.json`, `results/`. **Never commit:** the raw zips, any eval-set audio (ND licence), fetched training clips, embeddings caches, own-kitchen audio, anything in `data/`.

## 12. Safety and honesty rules
1. **"This project is a prototype and is not medical advice."** on every screen, the README, the write-up and the video.
2. **Not an emergency device.** Kettle never claims to detect falls, illness, wandering, smoke or distress. S1 says: "Kettle is not an emergency device. It can't detect falls or call for help."
3. **Unknown is never "fine".** Not listening → "Kettle can't tell you anything about the time since then"; rule → Can't tell, never Met or Missed; Not sure is drawn as not sure. There is no green "all good" state for the day; the heartbeat dot is green only for "Kettle is listening".
4. **Consent from the older adult first,** on his device; the caregiver can't start, resume or hide a pause. Copy names who sees the page.
5. **No audio stored or sent; no speech content.** RAM only; no ASR; speech becomes a type. Proven by `python -m eval.privacy_check` and a grep test; limits of that proof are stated (§13.9).
6. **Hedged language:** "sounds like", "how sure", "kitchen activity". Never "Dad ate", "Dad is fine", "normal day", "safe".
7. **Never claim** that Kettle diagnoses, monitors health, detects decline, or replaces visits or calls; never claim accuracy on homes or people we didn't test; never quote a number not in `results/`.
8. **Data:** public SINS only for training and testing; own-kitchen recordings by consenting teammates with no conversation; no patient data; no real names in fixtures (Meera and Ravi are labelled invented).
9. **Known limits stated openly:** one home and one person in all of SINS (it can't show fairness across age, sex or households; our kitchens are the only other homes); eating is hard to hear; "Other/Moving about" is the weakest class in every DCASE system; TV vs conversation; laptop mic vs SINS's array mics; the eval subsample isn't strictly leaderboard-comparable; staged clock times in demo days.

## 13. Evaluation plan (what MSR judges will attack)

### 13.1 Primary metric and why
**Macro F1 over the 9 SINS activities** on 10-s segments: it is the DCASE 2018 Task 5 metric ("the mean of the class-wise F1-scores", Dekkers et al. 2018), so our numbers sit next to the published systems, and it weights rare activities (vacuum, washing up) equally with the common ones. **For Meera, the per-activity split matters more than the average:** a **missed** cooking (FN) can make a normal morning look like a "not heard by 10:00"; a **false alarm** cooking (FP) can hide a skipped breakfast. So every activity reports caught (recall), missed (FN count), false alarms (FP count), precision, N, and a 95% CI. **Two levels, both reported:** (a) **per 10-s window** (the DCASE unit, comparable to published systems); (b) **per activity session, through the shipped pipeline** (θ, 2-of-3 smoothing, merge) on contiguous held-out dev-fold sessions stitched in segment order: a true activity session is **caught** if a predicted block of the same activity overlaps ≥ 50% of it; a predicted block with no ≥ 50% match is a **false alarm**; reported as caught / missed sessions with N and false-alarm blocks per hour of audio (and per 16-h "day"). The eval set can only be scored at level (a), because its sample is non-contiguous; we say so. Secondary: the caregiver-level "meal activity" (cooking ∪ washing up ∪ eating) recall and false-alarm rate; calibration (ECE, reliability plot) because "Not sure" relies on it; coverage vs precision at θ; latency (onset→label, s); CPU per window.

### 13.2 Splits and leakage controls
- **Dev:** the official 4 folds, session-disjoint. Re-verified in code (probe 1): 0 shared sessions train/test in every fold, no session in two test folds, all node copies of a moment in one fold. Stage 3 keeps this as `tests/test_folds.py`.
- **Model selection** (encoder, C, head type, θ, smoothing, window) uses **dev folds only**, by fold-wise CV (train 3 folds, test the 4th, rotate); C by inner session-grouped CV inside the training folds.
- **Headline test: the official DCASE 2018 Task 5 eval set, run once.** We didn't record or label it (KU Leuven ADVISE did), so it's an independent test. Recipe (fixed now, before any eval audio is fetched): 1,000 moments (session + segment) drawn uniformly at random with seed 20261114, topped up to ≥ 50 moments per class, all 7 node copies of each (~9,100 clips). The frozen model (`models/head.json`, sha256 in STATE) runs once via `python -m eval --split dcase-eval`; `results/eval_run.json` records commit hash, head sha256, start/end time and N; it's committed immediately. No retraining afterwards; a disappointing number is the finding.
- **Pre-registration (before any eval audio is fetched):** a commit `eval: pre-register` containing the eval sampling script with its seed, the recipe above, the reweighting and bootstrap code, and the mic-fingerprint rule below. Its hash goes in STATE and `results/eval_run.json`.
- **Rehearsal and rerun rule:** the exact `--split dcase-eval` code path is first run end to end on a stand-in (dev fold 4 relabelled as "eval", with a dummy head) so the harness is tested before the one real run. A real rerun is allowed only if the run crashed before writing predictions; both attempts are logged. Once predictions exist they are final.
- **Mic-fingerprint rule (written now, before looking):** for each node, the mean log-mel spectrum (64 bands, channel 0) over its fetched clips, **unlabelled**; known/unknown is decided by cosine distance to the 4 dev-node centroids: an EvalNode is "matched to DevNode k" if its nearest dev centroid is k and that distance is below the largest distance between the same dev node's fold-wise centroids; nodes matched one-to-one to DevNode1–4 are "known", the rest "unknown". The test never touches eval labels or predictions; if fewer than 4 nodes match one-to-one, the slice is reported per node only.
- **Dev numbers are optimistic:** encoder, head, C, θ, temperature and smoothing are all chosen on the same 4-fold CV we report, so every dev number is labelled "dev folds (also used for selection)". The frozen eval run is the only unbiased number.
- **Demo sessions held out:** 3 whole dev sessions per demo scenario activity are removed from the training subset before the final head is fit (listed in `demo_cache/sessions.txt`), so demo days and "Try your own sound" golden clips are out-of-sample for the shipped head.
- **Dev vs eval independence:** eval session ids are numbered separately (35 label matches of 129 shared ids vs ~33 by chance, probe 1); both partitions come from the same home and week, so "same home" is a known optimism we state.
- **Slices on the eval run:** known mics vs unknown mics (EvalNode 5–7 assumed, **must be confirmed** by the mic-fingerprint test in M2 before the slice is labelled "unknown-mic"; otherwise per-node only), node-averaged vs single-channel.
- **Comparability caveat** (say it in the write-up): we score a seeded subsample of the eval set and reweight to its true class counts; published systems scored all 72,972 segments, so our number is close to, but not strictly, a leaderboard number. Our head trains on ≤ 9k dev clips, not all 72,984.
- **Leakage checks before believing any number:** duplicate audio across splits (hash every fetched clip; 0 duplicates allowed); a "too good" fold (> 95) triggers a manual look; the head never sees eval embeddings before the frozen run (the eval cache lives in a separate folder that `eval/__main__.py` refuses to open unless `--split dcase-eval` and a frozen head hash are given).

### 13.3 Baselines (all frozen before scoring; maps in `docs/research/kettle/probes/maps/`)
| Baseline | What it is | Probe result (304 balanced dev clips) |
| --- | --- | --- |
| Majority | Always "Quiet" (SINS absence, the most common dev class) | 2.2 |
| Loudness rule | RMS > dev-chosen threshold → "Moving about", else "Quiet" (no-AI floor) | not measured yet |
| **Log-mel statistics + logistic regression** (trained, no deep model) | mean and std of 64 log-mel bands + RMS, same training subset, folds and balancing | not measured yet |
| **AST linear probe** (trained) | frozen AST embeddings + the same head | 75.8 (quick check) |
| Apple SoundAnalysis zero-shot, mapped | 303 classes → 9 via `apple_map.json`; a *reference* for "what a Mac already ships", not a competitor (the map was written after the wow round saw 6 Apple outputs, disclosed) | 40.0 |
| AST zero-shot | AudioSet 527 → 9 via `audioset_map.json` | 45.4 |
| CED-tiny zero-shot | same map | 42.1 |
| CLAP zero-shot | 9 fixed prompts, `clap_prompts.json` | 48.8 |
| DCASE 2018 official baseline (published) | log-mel CNN, 4-mic posterior averaging | 84.5 dev · 85.0 known-mic eval · **83.1 unknown-mic eval** |
| DCASE 2018 best entry (published) | Inoue et al. (IBM), CNN ensemble + augmentation | 90.0 dev · 90.4 · **88.4** |
Published numbers are quoted from https://dcase.community/challenge2018/task-monitoring-domestic-activities-results with the caveat that they used all eval segments and full training data.

### 13.4 Ablations (dev folds; cheap)
**Leave-one-node-out (mic-shift proxy, no eval data needed):** train on 3 dev nodes, test on the 4th, still respecting session folds (train folds × 3 nodes → test fold × held-out node), 4 × 4 runs; reported as the in-home microphone-shift number. If time: EQ and noise augmentation chosen on this result only.
Encoder (CED-tiny / CED-small / AST / CLAP embeddings, same head) · head (logistic regression / 1-hidden-layer MLP) · class balancing on/off · channels (train ch0 only vs all 4) · test-time node averaging vs single channel · window 10 s vs 5 s (the chip) · smoothing on/off (false activity segments per hour on dev sample days) · θ sweep (coverage vs precision curve).

### 13.5 Metrics detail
- Confusion matrices (counts, row-normalised) per split, saved as PNG and in JSON.
- **95% CIs by session bootstrap** (resample sessions with replacement, 1,000 draws, seed 0; percentile interval), because clips within a session are correlated; per-class and macro.
- **Prevalence reweighting** for capped dev subsets and the eval sample: confusion rows × (true class count ÷ sampled count) before computing precision/F1; raw and reweighted both reported.
- **Bootstrap with reweighting:** each draw resamples sessions with replacement within the scored set, rebuilds the confusion matrix, applies the **fixed** weights (true class count in the full split ÷ sampled count, computed once from the full label file, capped at 50), then computes per-class P/R/F1 and macro F1; 1,000 draws, percentile 95% interval.
- **θ and temperature recipe:** out-of-fold dev logits (each clip scored by the model that didn't train on its fold); temperature fitted on them by NLL; θ = the lowest threshold whose prevalence-reweighted shown-label precision, macro-averaged over the 9 classes, is ≥ 0.9; coverage at θ reported.
- Latency: onset→label for every activity change in the 3 sample days and a 20-transition set (median, p90, N); each transition joins two held-out dev clips of different activities from the same node, played through Chromium's fake mic at real time in a quiet room (no added noise), onset = the joint; CPU s/window and CPU% (30-min live run).
- Every number in `results/metrics.json` carries `{"split", "n_clips", "n_sessions", "value", "ci95"}`.

### 13.6 Slices (lead with the expected worst)
1. **Own kitchens** (laptop mic, new homes, new people) — expected worst.
2. **Unknown-mic nodes** on the eval run (if confirmed).
3. **Single channel** (one laptop-like mic) vs 4-channel node average.
4. **Per class:** "Moving about"/Other (weakest in every DCASE system: baseline 35.0 unknown-mic) and eating vs cooking.
5. **Per mic node** on dev (1–4) and eval (1–7).
6. **Off-list inputs (out-of-distribution, ~200 clips):** ESC-50 categories outside the 9 activities (e.g. dog, rain, siren, crying baby, clock alarm; https://github.com/karolpiczak/ESC-50, CC BY-NC 3.0, 5 s clips padded to 10 s) plus generated white/pink noise and silence (N = 20 each): the confident-wrong rate at θ and a **risk-coverage curve** (in-distribution dev vs off-list), so "Not sure" is tested where it matters.
7. **Time of day: not recoverable.** SINS dev clips have no clock times; we say so rather than invent a slice.
8. **Groups the brief names (age, sex):** not checkable on SINS (one person). Stated as a limit with the validation plan (another week: 5 consenting households of different ages, §19 Q12).

### 13.7 Own-kitchen test set (Lane A; frozen-model test only)
Recorded and labelled by a teammate who did not write the code (AGENTS.md §0.5), with consent from every audible person, no conversation, no names. Recipe in `docs/research/kettle/probes/06-own-kitchen-plan.txt` and `eval/OWN_KITCHEN_GUIDE.md` (written in M4): the Kettle laptop on the counter 1–2 m from the sink and hob, 8 activities × ≥ 5 sessions × ~1 min on ≥ 2 days (ideally 2 kitchens), labels written during recording (start, end, activity), straddling windows dropped by a rule fixed before scoring. Scored once with `python -m eval --split own-kitchen`, through the full pipeline (window level, session level and the 5-s chip). Labelled **exploratory**: ~240 windows from ≤ 2 kitchens, sounds staged and labelled by the same teammate (so label noise may correlate with difficulty); reported with session-level Wilson intervals, never as a "home fairness" result.

### 13.8 Failure gallery (≥ 5 real failures, each: clip id, true, predicted with probabilities, top sounds, cause)
Expected categories (to be filled from real outputs, never invented): cooking ↔ eating (shared cutlery and plate sounds; SINS README says eating is hard); "Moving about" ↔ Quiet (quiet movement); TV ↔ Conversation (speech on TV; Apple called TV conversation 25/34); washing up ↔ cooking (taps run in both); a domain-shift miss in our kitchens (laptop fan, different room); an edge window straddling two activities (probe 4 showed these at every transition).

### 13.9 Privacy proof (`python -m eval.privacy_check`)
Runs the real app for 60 s with a sample day as Chromium's fake mic and asserts: 0 Python write-opens outside the whitelist (`data/timeline/*.jsonl`, the log), 0 lsof regular files open for write outside it, 0 new/changed audio-extension or RIFF/fLaC/OggS files in the repo, `$TMPDIR`, `/tmp`, `~/Library/Caches`; plus a grep test (no `sf.write`, `wave.open`, `np.save`, `MediaRecorder`, `IndexedDB` on audio paths; no ASR imports). `/api/try` reads the raw request body (`await request.body()`, capped at 10 MB, `Content-Type: audio/*`) instead of `UploadFile`, because Starlette spools multipart uploads over 1 MB to a temp file; a test uploads 5 MB and asserts nothing new in `$TMPDIR`. The fake-mic input (`demo_cache/…flac`, pre-existing, unchanged) is whitelisted by exact path. **Threat model (one sentence):** we prove that Kettle's own code never writes audio to disk or sends it off the machine; we do not protect against a compromised OS, browser extensions or crash dumps, or someone with access to the unlocked laptop. Output `results/privacy_check.json` + `.txt`. Limits: not a kernel trace (optional sudo `fs_usage` step documented for the lead), OS swap is out of our control.

### 13.10 The one command
`python -m eval` → `results/metrics.json` + `results/metrics.md` (+ PNGs, `failures.md`) from cached embeddings in < 2 min. `--split dcase-eval` only with a frozen head hash. The write-up and `/how-sure` read from `results/metrics.json`.

## 14. Rubric scorecard

| Line | Pts | What the judge will see from us | Self-score now (plan) | Biggest risk | Fix |
| --- | --- | --- | --- | --- | --- |
| R1 Technical execution | 30 | `python app.py` runs offline, demo mode with real SINS audio through the real model, live mic in Chrome, clean small modules, tests, smoke test | 24 | Live mic or install breaks on a judge's machine | Demo mode needs no mic; fresh-clone test (M8); pinned requirements; weights committed |
| R1 Originality | 20 | Sound-only daily rhythm for a distant caregiver; first published per-activity misses/false alarms in this product category; Apple baseline; consent + pause as product states | 16 | "Activity recognition is a known task" | Lead with the product question and the 9-incumbent teardown, not the task |
| R1 Impact + track fit | 20 | Named persona; brief's words; missed vs false alarms separately; ACL statistic; P1–P10 answered | 16 | Health link feels indirect ("is this health?") | Frame as "manage an ongoing condition better" for MCI caregiving; Arecibo fit; no overclaiming |
| R1 Testing + honesty | 15 | Session-disjoint folds, frozen eval run with commit hash, unknown-mic slice, CIs, 5 baselines, ≥ 5 failures, own-kitchen worst slice, privacy check | 13 | Unknown-mic mapping unverified; subsample caveat | Mic-fingerprint test; say the caveat in the first table |
| R1 Communication | 15 | One page, numbers in the top third, 2:00 video with the live clink moment and the misses/false-alarms table | 12 | Too much to say | §18 script; one sentence to protect (§0) |
| **R1 total** | 100 | | **81** (red-team MSR judge scored the pre-fix plan ~72) | | |
| Finals Demo + clarity | 30 | Live: judge clinks a plate → "Sounds like washing up" in ~2–3 s; pause shows on the phone | 24 | Room noise, mic permission | Demo mode fallback; recorded backup video; second laptop |
| Finals Technical depth | 30 | Frozen encoder vs zero-shot vs DCASE, calibration-based abstain, channel and mic slices, ablations | 24 | "Why not fine-tune?" | Ablation table + compute budget answer (§19) |
| Finals Impact | 20 | P-theme table; consent; cost; offline | 15 | Single-home data | Own-kitchen slice + validation plan |
| Finals Q&A | 20 | §19 rehearsed by all three | 15 | Beginners can't explain the model | `/explain quiz` drills; EXPLAIN.md |
| **Finals total** | 100 | | **78** (red-team: ~72 pre-fix) | | |

Red-team critiques: `docs/research/kettle/redteam-msr-judge.md`, `docs/research/kettle/redteam-caregiver-ux.md`. Fixed in this version: session-level metric through the shipped pipeline; trained cheap baselines (log-mel + LR, AST probe); leave-one-node-out mic shift; off-list risk-coverage set; upload spooling hole and threat model; pre-registration, rehearsal and rerun rule; fingerprint rule without labels; held-out demo sessions; reweighted bootstrap and θ recipes; remote access path; absence-claim wording; consent teach-back, Turn it off, weekly re-consent, rules shown to the parent, demoted chip, plain-language copy, rounded summary times, "Quiet" instead of "Quiet". The rest is logged in §20.9–11.

## 15. Risks and premortem ("It's Sunday 9 PM and we lost. Why?")
| # | Cause | Likelihood | If-then plan | Cut |
| --- | --- | --- | --- | --- |
| 1 | **Zenodo fetch stalls** (rate limit, slow bandwidth) and we have too few training clips or no eval run | Medium | Fetch starts first in stage 3 (M2) in the background, resumable; if < 50% done by Sat 3 PM, cap at 600 per class; eval fetch runs overnight; if eval fetch fails, report dev folds only and say why | Eval sample down to 500 moments |
| 2 | **Live demo fails** in front of judges (mic permission, room noise, laptop) | Medium | Demo mode with real SINS audio is the video's spine and the Round 1 path; recorded backup video; Safari checked by hand; second laptop | Live mode becomes finals-only |
| 3 | **The number disappoints** (e.g. 70 on unknown mics, 40 in our kitchens) | High for own-kitchen | That's the honest finding: lead with it, explain domain shift, show the drop is measured; the brief rewards "an honest, modest result" | none |
| 4 | **Judge says "this is surveillance"** | Medium | Show consent, pause, privacy check output, "type not content", RAM-only design in the first 30 s of the video | none |
| 5 | **Scope eats the design passes** (UI looks basic, Parth's main complaint last time) | Medium | UI built in parallel with the fetch (M5 starts during M2); 3 screenshot critique rounds are milestone M7, not optional | Weekly view, phone-mic HTTPS, dark mode (in that order) |
**Plan B:** Pitch 2 "Ten Past Eleven" (clock-drawing check, `wow-pitches.md`). Switch gate: Sat 3:00 PM CT, only if no SINS clips can be fetched at all *and* the probe clips can't support a head; otherwise never switch (Kettle's probes already work end to end).

## 16. Build plan (stage 3: from ~10:45 AM Sat; hard stop Sun 9:00 AM CT; Sunday daytime belongs to the team)
| Milestone | CT window | Output | Gate / done-check |
| --- | --- | --- | --- |
| M1 Walking skeleton | Sat 10:45–12:00 | Layout §10.2; `python app.py` serves `/`, `/kitchen`; a probe clip → stub label → block on the bar; `smoke_test.py` < 60 s; README "how to run" | smoke passes |
| M2 Data + embeddings | Sat 11:30 start (background) → ~14:30 | Dev subset fetch (~8,970 clips, ~76 min; demo sessions excluded from training) then embeddings (all 4 ch, CED-tiny; AST + log-mel stats on ch0 for baselines); fold test; **`eval: pre-register` commit** (sampling script, seed, reweighting/bootstrap code, fingerprint rule) **before** the eval fetch; eval sample fetched (~77 min, may run overnight) with only **unlabelled** per-node spectra computed for the fingerprint rule; ESC-50 off-list set (~200 clips) | counts per class/fold/node logged; `tests/test_folds.py`; pre-register hash in STATE |
| M5a Product UI (parallel with M2) | Sat 12:00–15:30 | S1/S2 with real live path on the probe head; consent, pause, heartbeat, rules; demo player skeleton | Playwright fake-mic run |
| M3 Models + baselines | Sat 15:00–17:00 | Head by fold-wise CV; θ and smoothing on dev; all baselines incl. Apple on dev; ablations; final head frozen (hash in STATE) | dev table complete |
| **GATE** | **Sat 18:00** | Full demo flow works in demo mode and live | If not, cut F12, F14, F17, F18 now |
| M4 Eval harness | Sat 17:00–19:00 | `python -m eval`: window- and session-level metrics, reweighted bootstrap CIs, leave-one-node-out, off-list risk-coverage, failures, unit tests, `eval/OWN_KITCHEN_GUIDE.md` + template | test_metrics passes on a hand-computed example (incl. a session-level match case) |
| M5b Product complete | Sat 19:00–23:00 | Demo scenarios, try-your-own-sound, how-sure page, privacy check wired, better-than checklist | every golden path + not-sure + garbage screen designed |
| M6 Frozen eval run | Sat ~23:00 rehearsal, ~23:30 real (once) | Rehearse the exact path on the dev-fold-4 stand-in with a dummy head; then `python -m eval --split dcase-eval`; `results/eval_run.json` with commit hash, head sha256, pre-register hash | committed immediately; rerun only after a crash before predictions, both logged |
| M7 Design passes ×3 | Sun 00:00–04:00 | Screenshots of every state, 2 sizes × 2 themes; written critiques; CSS audit; subagent critics | critique files exist; FIX items 0 |
| M8 Review + harden | Sun 04:00–05:30 | Self + subagent code review; fresh-clone timed install | fresh clone works offline |
| M9 Judge simulation ×2 | Sun 05:30–07:00 | Subagent judge scores; top-3 changes made | logged |
| M10 Hand-off | Sun 07:00–09:00 | EXPLAIN.md, AI log, DATA-SOURCES, MORNING-BRIEF, PRD/WRITEUP with real numbers, BUILD_DONE | never skipped |
| Team (Sunday) | Sun 9:00 AM–9:00 PM | Own-kitchen set (Lane A, 9 AM–1 PM, scored once by 2 PM); video recorded 1–4 PM; write-up final 4–6 PM; fresh-clone rehearsal 6–8 PM; **submit by 9 PM** | AGENTS.md §11 checklist |
**Cut list (in order):** CLAP ablation → extra ablations → F18 weekly view → F16 phone HTTPS → F17 usual band → F14 dark mode → extra slices → F15 read-aloud → decorative motion. **Never cut:** live mode, demo mode, caregiver view with heartbeat, the parent's pause, the Apple baseline, the eval harness, the one frozen eval run, the privacy check, the smoke test, EXPLAIN.md, MORNING-BRIEF.md.

## 17. Team lanes (Parth is the lead and integrates; two beginner teammates)
Each lane works on its own branch, touches only its files, and finishes with `/done`. Every prompt starts a fresh Claude Code session on **Sonnet 5.5 or Haiku 5.5** (`/model sonnet`), never Opus.

**Lane A: own-kitchen test set (Sunday 9 AM–1 PM).** Allowed files: `eval/own_kitchen/labels.csv`, `eval/own_kitchen/CONSENT.md`, `eval/own_kitchen/NOTES.md`; audio stays in `data/private/own_kitchen/` (git-ignored). Must explain to a judge: how the labels were made, why the code author didn't label, what was dropped and why.
1. Prompt: *"Read AGENTS.md §0 and eval/OWN_KITCHEN_GUIDE.md. Walk me through the consent form and the recording checklist one step at a time. Don't write any code. Ask me to confirm each step before the next."* Done-check: `eval/own_kitchen/CONSENT.md` signed (initials only) by every audible person.
2. Prompt: *"I'm recording kitchen sounds for Kettle's own-kitchen test set following eval/OWN_KITCHEN_GUIDE.md. Help me fill eval/own_kitchen/labels.csv as I go: columns file,start_s,end_s,activity,session,notes, activity from the 9 names in the guide. After each session, check my rows for overlaps or gaps and tell me, but never change an activity label yourself."* Done-check: ≥ 40 sessions-minutes of rows, no overlaps.
3. Prompt: *"Run `python -m eval.own_kitchen_check` and explain any errors in plain words. Don't edit labels.csv to make it pass; tell me what's wrong and I'll fix it."* Done-check: the check prints "ready to score".
4. Parth runs `python -m eval --split own-kitchen` once. Lane A reads `results/metrics.md` and writes three sentences in `eval/own_kitchen/NOTES.md`: what got worse vs SINS and the likely cause.

**Lane B: write-up, video script and the statistic hunt (Saturday afternoon onward; final Sunday 4–6 PM).** Allowed files: `docs/WRITEUP.md`, `docs/DATA-SOURCES.md` (new rows only), `docs/video/SHOTLIST.md`. Must explain: the persona, why the numbers matter for Meera, the worst slice and why.
1. Prompt: *"Read docs/PRD.md §0–§3 and docs/WRITEUP.md. Rewrite the Problem and Who it's for paragraphs in plain words for a judge skimming in 30 seconds. Keep every number exactly as written and keep 'This project is a prototype and is not medical advice.' Show me a diff."* Done-check: ≤ 120 words for both paragraphs.
2. Prompt: *"Find one more statistic for this problem, opened at the primary source: the share of family caregivers who live an hour or more from the person they care for (AARP/National Alliance for Caregiving 'Caregiving in the U.S.'), or the share of people with dementia who live alone (Alzheimer's Association Facts and Figures). Open the PDF yourself. Give me the exact quoted sentence, page number and URL, or tell me you couldn't open it. Don't round or guess."* Done-check: a new row in `docs/DATA-SOURCES.md` with a quote, or "not found".
3. Prompt: *"Using docs/PRD.md §18, turn the video script into a shot list in docs/video/SHOTLIST.md: for each line, what's on screen, who records it, which app state to set up first. Leave every number as {from results/metrics.json} until Parth fills them."* Done-check: every 15-s beat has a shot.
4. Sunday: Prompt: *"Fill docs/WRITEUP.md's Results table and the three failures from results/metrics.json and results/failures.md. Copy numbers exactly, with N and CI. Then check the write-up fits one page (about 550 words) and list anything over."* Done-check: every number in WRITEUP.md matches `results/metrics.json` (Parth spot-checks 5).

**Lead (Parth):** integrates, runs every eval, records the live demo, reviews every diff, answers technical Q&A. First hour Sunday: read `docs/MORNING-BRIEF.md`, confirm the decisions in `docs/DECISIONS.md`, rerun `smoke_test.py` and `python -m eval`, then unblock Lane A.

## 18. Demo and video script (2:00)
| Time | Says | Shows |
| --- | --- | --- |
| 0:00–0:15 | "About 28% of Americans 65 and over who live at home live alone. Meera's dad is one of them, 300 miles away, with early memory loss. Calling to check feels like checking up on him. Cameras feel like spying. And the sensor kits for this publish no accuracy at all." | Kitchen laptop on a counter; caregiver phone; one line of the incumbent comparison (price, cameras, accuracy: "none published") |
| 0:15–0:35 | "Kettle runs on a laptop already in the kitchen. Dad says yes on the screen. It listens in 10-second windows and keeps no recording and no words." | S2 consent → "Yes, start" → Listening |
| 0:35–1:05 | "Watch: plates under a tap…" (clink) "…it says washing up, and here's what it heard. Now I talk: it says conversation, and no words appear anywhere. Dad can pause it; Meera sees that he did." | Live: chip "Sounds like washing up" → block settles on the bar → evidence card; speaking → "Conversation"; Pause → phone shows "Paused by Dad at …" |
| 1:05–1:20 | "Meera's view at 11 AM: listening 40 seconds ago, cooking at 8:20, her own rule 'kitchen activity by 10' met. If the laptop dies, it says so: silence never looks like a normal day." | S1 on phone; then a sample day with a "Not listening since…" gap and a Can't tell rule |
| 1:20–1:45 | "How sure is it? On the official DCASE 2018 test, run once with a frozen model: {macro F1 + CI} on microphones it never heard, versus Apple's built-in classifier at {x} and the 2018 challenge baseline at 83.1. Per activity, here are the misses and the false alarms." | S3 table with N and CIs; the missed/false-alarm columns highlighted |
| 1:45–1:55 | "Where it fails: in our own kitchens it drops to {y}; it confuses cooking with eating, and TV with conversation. We show those on the screen instead of hiding them." | Failure card; own-kitchen row |
| 1:55–2:00 | "Kettle. Know Dad's day went normally, without watching him. Prototype, not medical advice." | End card with repo link and the disclaimer |
Numbers in `{}` are filled only from `results/metrics.json`. Real voices, real screen, no names or school (Round 1 is blind).

## 19. Finals Q&A prep (12 sharpest questions from MSR researchers)
1. **Why CED-tiny and not AST or a fine-tuned model?** Same or better on our session-disjoint check at 1/40th of AST's CPU time (probe 2: 0.014 vs 0.52 s per window), which matters for always-on use on an old laptop; the ablation table shows the full-dev comparison. Fine-tuning: frozen embeddings + a linear head were the 48-hour budget; with a week we'd fine-tune the top blocks with session-grouped early stopping.
2. **One home, one person: haven't you just learned that house?** Yes, and we separate three shifts: **microphone shift in the same home** (leave-one-node-out on dev, and the unseen eval arrays), **time shift in the same home** (the eval set is a different stretch of the same week), and **home + person + mic shift** (our own kitchens, exploratory, ~240 windows). Only the last one tests a new home, it is small, and we lead with its drop. SINS can't show fairness across people; we say so.
3. **How do you know the eval set didn't leak?** We never trained or tuned on it; it was fetched into a separate cache the training code refuses to read; the model hash and commit were logged before the single run; eval sessions are numbered independently of dev (label agreement at chance level).
4. **Your eval is a subsample. Is it comparable to the leaderboard?** Not strictly: seeded sample of ~9k of 72,972 segments, reweighted to true class counts, with session-bootstrap CIs. We report it as "close to" with that caveat in the first table.
5. **Which nodes are "unknown mic"?** The files don't name them; we tested it with a mic-fingerprint classifier (mean log-mel spectrum per node) — result in `results/`. If it's unconfirmed we only report per-node numbers.
6. **Why macro F1 and not accuracy?** Classes are very skewed (absence 18,860 vs vacuum 972); accuracy would reward always predicting "Quiet". Macro F1 is the challenge metric. For Meera we split it into misses and false alarms per activity, as the brief asks.
7. **How is "Not sure" chosen? Isn't that just hiding errors?** Temperature-scaled max probability on out-of-fold dev logits; θ = the lowest threshold keeping prevalence-reweighted shown-label precision ≥ 0.9. We report the coverage it costs, the precision with and without it, and a risk-coverage curve on ~200 off-list clips (ESC-50 sounds, noise, silence), because max-softmax is known to be overconfident out of distribution: the confident-wrong rate there is the honest limit.
8. **Why not just use Apple's Sound Recognition?** It alerts the phone's owner per sound, has no activities and no caregiver view. As a reference we mapped Apple's 303-class classifier to the 9 activities with a map frozen before scoring: {x} vs our {y} on the same clips (results file). On the 304-clip probe its confusions were cooking and washing up heard as doors/drawers and TV heard as speech (it has no TV class); the full-dev confusion matrix shows whether that holds. It's a zero-shot reference, not a fair fight, and we say so; the fair trained baselines are log-mel + LR and AST linear probe.
9. **Why not an LLM?** It can't hear the kitchen without sending audio to a cloud, which breaks the privacy promise. The summary is a template so it never invents an activity.
10. **How do you prove nothing is recorded?** Threat model first: we prove Kettle's own code never writes audio to disk or sends it anywhere; we don't defend against a compromised OS or someone at the unlocked laptop. Evidence: RAM ring buffer; uploads read as a raw body (not spooled to temp files, tested with 5 MB); a privacy check that runs the real app under a Python audit hook, samples lsof, and diffs repo, $TMPDIR, /tmp and caches for audio extensions and audio magic bytes; a code grep; the only network listener is localhost/the private VPN; and a documented `fs_usage` kernel-level check for the sudo-capable. Limits: OS swap (encrypted), Chromium internals.
11. **What happens off-list (a dog, a blender, a fall)?** The model only knows 9 activities; an unknown sound either falls below θ ("Not sure") or is mislabelled; we measure the confident-wrong rate on noise, music and silence. Kettle is not an emergency device and says so on screen.
12. **How would you validate with real users, and what would you change with another week?** Five consenting households (different ages, kitchens, mics) for two weeks: measure misses and false alarms against a diary, and ask caregivers whether "Missed" and "Can't tell" changed what they did. Technically: fine-tune with mic augmentation for domain shift, a phone-mic HTTPS path, and a relay for outside-the-house access with end-to-end encryption.

## 20. Open questions for the humans (ranked; our default if nobody answers)
1. **Unknown-mic node ids** (EvalNode 5–7?). Default: run the mic-fingerprint test in M2; until confirmed, per-node numbers only and no "unknown-mic" label.
2. **"Use public datasets only" vs our own-kitchen recordings.** Default: keep them as our own consented test data with no patient information, publish labels and predictions; publish the audio too (CC BY 4.0) only if every audible person agrees, which also makes it public.
3. **Novelty claim** ("no published frozen-encoder result on SINS"). Default: don't claim it; say "we found none" with the search date until Lane B re-checks Google Scholar.
4. **Persona names.** Default: Meera and Ravi, labelled invented; Parth may rename.
5. **Safari mic on localhost.** Default: assume it works; a teammate checks by hand on Saturday evening; if it fails, the README says "use Chrome".
6. **Demo clip licence.** Default: CC BY-NC 4.0 allows non-commercial redistribution with attribution; we commit ≤ 90 dev clips with `ATTRIBUTION.md`; no eval audio (ND).
7. **Training subset size** (≤ 1,000 per class). Default as decided; grow only if the fetch is fast.
8. **Arecibo framing** in the write-up. Default: one line on fit (older adults with cognitive impairment and their caregivers), no claim of partnership.
9. **Red-team items not adopted (logged):** (a) UX critic: show Meera a neutral "Paused 3:10–4:10 PM" without "by Dad". Kept "Paused by Dad at 3:10 PM" because the stage-3 spec requires it and it frames the pause as his act, not a fault; his pause sheet tells him Meera sees it. Reverse if Parth prefers. (b) "A late morning is common." under Missed: rejected as reassurance in a health product (unknown ≠ fine). (c) A push alert when a rule is Missed (users asked for an *alert*, P10b): out of scope (no relay; false-alarm pain P5=); a Could: a browser notification on Meera's open tab. (d) Nested CV for selection: too slow for the weekend; dev numbers are labelled optimistic instead. (e) Augmentation for domain shift: only if leave-one-node-out shows a large drop and time allows. (f) The UX critic's example "Apple 41, Kettle 82" cold open uses invented numbers: never use; the cold open waits for `results/`.
10. **Laptop sleep / lid close** is the new "dead sensor" (UX critic). Default: README setup says plugged in, sleep off (`caffeinate -s` on macOS or Energy settings), lid open; the heartbeat makes any lapse visible. A Could: Screen Wake Lock API on the kitchen page.
11. **Printed counter card for visitors** (UX critic). Default: a one-page printable card in `docs/COUNTER-CARD.md`, zero code.

## 21. Credits
- **Data:** SINS / DCASE 2018 Task 5 dev and eval (Dekkers, Karsmakers et al., KU Leuven ADVISE; CC BY-NC 4.0 / CC BY-NC-ND 4.0; https://doi.org/10.5281/zenodo.1247102, https://zenodo.org/records/1291760, https://zenodo.org/records/1964758). DCASE 2018 Task 5 results and baseline (https://dcase.community/challenge2018/task-monitoring-domestic-activities-results, https://github.com/DCASE-REPO/dcase2018_baseline, MIT).
- **Models:** CED-tiny / CED-small (Xiaomi, Apache-2.0, https://huggingface.co/mispeech/ced-tiny); AST (MIT CSAIL, BSD-3-Clause, https://huggingface.co/MIT/ast-finetuned-audioset-10-10-0.4593); LAION CLAP (Apache-2.0, https://huggingface.co/laion/clap-htsat-unfused); Apple SoundAnalysis (built into macOS, used as a baseline); AudioSet ontology (Google, CC BY 4.0).
- **Libraries:** PyTorch, Hugging Face transformers, scikit-learn, numpy, soundfile/libsndfile, librosa, FastAPI, uvicorn, Playwright.
- **Products studied (patterns only, no code or assets):** Howz, Canary Care, havn (cortekAI), Assistiv Home Sensing, Apple Sound Recognition, Alexa Together / Emergency Assist, StackCare, Care Daily, Snug, Caregiver Aware; WellNest (Devpost). Links in §4 and `docs/DATA-SOURCES.md`.
- **Statistic:** US Administration for Community Living, 2023 Profile of Older Americans.
- **AI tools:** Claude Code (Claude Opus 5.5 for planning and review; Sonnet 5.5 / Haiku 5.5 workers) wrote research summaries, probes and code; REA (morluto/rea, MIT) for public-surface teardowns; Aside (repo owner's agent) for read-only web research. Every use logged in `docs/AI-USAGE-LOG.md`.

## 22. What changed during the build (stage 3, Sat Nov 14; details and evidence in `docs/DECISIONS.md`)
Where this section and an earlier one disagree, this section describes what was actually built.
- **Demo hold-out:** 1 whole session per activity (9 sessions, 90 clips, DevNode1 channel 0), not 3 (§13.2): rare activities have only 9–10 sessions.
- **Pages poll** `/api/today` once a second; there is no `/ws/state` socket (§10.3). The only WebSocket carries the kitchen mic.
- **Kitchen-only controls** are enforced by request origin: consent, pause, resume, off and mic audio are accepted only from the kitchen laptop itself (127.0.0.1); no session token.
- **"Not sure" has two triggers:** top probability below θ, *or* a sound unlike every activity Kettle learned (Mahalanobis distance above the 99th percentile of out-of-fold dev windows). Added after the off-list test showed θ alone let most non-household sounds through (§13.6).
- **Day bar range:** 6 AM to a little after now (≥ 6 h; the whole day once it's late), not a fixed 6 AM–midnight (§9.3), so blocks stay tappable on a phone.
- **Activity colours:** the dataviz reference palette's validated hues, assigned so real neighbours pass colour-blind checks (§9.5's hand-picked palette failed the validator); red kept for "Kettle stopped working" only.
- **Evidence list:** 79 kitchen/living-room AudioSet labels; body sounds, bathroom sounds, speaker attributes (male/female/child, shouting, whispering) and room tone (hum, static, white/pink noise) removed.
- **Baselines:** CLAP cut on the full dev subset (time; its stage-2 probe number is quoted as a probe). AST zero-shot and AST linear probe scored on a seeded 2,700-clip subset, beside Kettle on the same clips. Apple scored on every dev clip.
- **Off-list set:** ESC-50 clips repeated to 10 s, not zero-padded.
- **Added from Parth's addendum:** reliability plot + ECE with CI (temperature cross-fitted across folds), the θ trade-off for the caregiver check, slices per mic node / activity / home, the "kitchen activity" metric in the headline, the measured gap on "How sure" (reframed after judge round 2, see below), `notebooks/kettle_reproduce.ipynb` from a committed cache, per-judge Q&A (§19), `docs/SUBMISSION-DRAFT.md`.
- **Cut from the addendum:** both unverified pitch quotes (not found as worded; see DECISIONS).
- **Kitchen sessions, two definitions (addendum item 9):** the θ table counts a kitchen session as noticed if any cooking / washing-up / eating block overlaps it (33 of 33 on dev); the strict rule (the right activity as one block covering half the session) catches 15 of 33. Both are reported; the write-up leads with the strict one.
- **After judge round 2:** the lead no longer says "level with the baseline" or leads with Apple. It says "close to, not directly comparable", calls Apple context only (zero-shot, a different label set) and says "not yet a real kitchen". Added a held-out microphone × activity slice (post-hoc, saved predictions) and measured live latency (median 7.1 s from an activity change to the timeline, 8 changes, fake-mic run). No log-mel on held-out (a post-hoc second look at the test set).

## 23. Per-judge Q&A prep (Parth's addendum item 7; every number from `results/metrics.json`, Sat Nov 14 run)
Judge names come from Parth's research; the questions are what each has argued for, not quotes.

**Prasad — "the metric should come from the clinical problem, not the ML default."**
- *Why macro F1?* It's the DCASE 2018 Task 5 metric (comparability) and it weights rare activities equally; accuracy would reward always saying "Quiet" (always-Quiet scores 5.0 macro F1 on the held-out test). But we lead with the metric Meera's check actually uses: **any kitchen activity** (cooking, washing up or eating). Held-out, one mic: caught 89.3% [85.3, 94.1] of 1,183 kitchen windows (144 missed), false alarms on 0.5% [0.2, 1.1] of 6,608 other windows (41). That metric was computed after the run from the frozen predictions; it was declared in DECISIONS but not in the pre-registration, and we say so.
- *Which activity is worst-served?* "Moving about" (SINS "other"): held-out recall 55.4%, F1 41.4, 156 missed and 248 false alarms; then washing up (recall 72.6%, 96 missed). Cooking is caught 86.1% with 94.5% precision. Moving about was also the weakest class for every DCASE 2018 system (baseline 35.0 on unseen mics). It matters little for Meera's check because it isn't a kitchen activity.

**Batool — "where is it confidently wrong, and what did you add beyond the pretrained encoder?"**
- *Confidently wrong:* TV vs conversation is the clearest case: on the held-out test 27 TV clips were called conversation (conversation has 81 false alarms in total); the most confident dev example is `DevNode4_ex229_102` (Conversation 0.88; the encoder heard "Speech 0.87"). Off-list sounds are the other: with the confidence threshold alone, 56.2% [50.1, 62.1] of 260 dogs/sirens/alarms/noise clips got a confident label; with the novelty check, 0.4% [0.1, 2.1]. Cooking heard as washing up (27 held-out clips; 63 dev clips) is the main kitchen confusion; it doesn't change Meera's check because both are kitchen activity.
- *What we added:* a trained head (85.1 vs 37.5 macro F1 for the same encoder with a zero-shot label map, dev); calibration measured with CIs; an abstain rule tested on off-list sounds; a session-level score through the real timeline (smoothing cuts false-alarm blocks from 11.1 to 3.2 per hour on dev); and the product rules (heartbeat, consent, Can't tell) that turn labels into something a caregiver can act on.

**Kerimov — "uncertainty, and homes it hasn't heard."**
- *Uncertainty:* the reliability plot (`results/reliability_dev.png`): expected calibration error 1.6 points [0.9, 2.6] before temperature scaling and 1.5 [0.8, 2.6] after (dev, cross-fitted temperature), i.e. the head is already close to calibrated. "Not sure" below θ = 0.66 leaves 85% of dev windows labelled with 90% shown-label precision; 14.2% of held-out windows came out "Not sure".
- *Homes and microphones it hasn't heard:* leaving one dev microphone position out of training costs about 2.5 points (82.7 vs 85.2 macro F1, mean of 4), and the novelty check flags only 0.7–1.9% of that unseen microphone's windows. On the held-out test, per-node single-mic scores range 79.9 (EvalNode3) to 85.6; our pre-registered fingerprint rule could not identify which nodes are the three unseen microphones, so we don't claim an unseen-mic number. A different home is the open question: the own-kitchen set (Sunday) is the only test of that, and we expect a drop.
