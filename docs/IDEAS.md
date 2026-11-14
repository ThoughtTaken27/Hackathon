# Ideas (pre-researched, not built)

Summary of the research doc: [Veritas AI Hackathon — Health Idea Research & Game Plan](https://claude.ai/artifact/KxEQasfso3e2RMTBuqrS8v). The final pick happens at kickoff with the decision table in `KICKOFF.md`. Nothing here is code; it's a plan to adapt to the brief.

## Strategy: rebuild and surpass a weak incumbent (Nov 13, evening)

Take a tool that already exists and has real users but is retired, clunky, stale or unsafe. Rebuild it **from scratch** in the 48 hours and add the one capability it lacks. Then **measure ours against it**: the incumbent is our baseline.

Rules for doing this cleanly:
- Never fork or copy their code. Take the problem, public data and lessons only. All our code is written after kickoff.
- Credit the original in the write-up: "X exists (link); here's what it gets wrong for [persona]; here's what we add, measured." The rubric rewards exactly that (originality: "prior-art check; state our twist; cite what exists").
- Prefer **government, retired or abandoned tools**. Their data is public, there's no brand or IP problem, and the story is strong ("NIH shut it down; nothing replaced it").
- Better UI alone scores little in Round 1. The twist must be a measurable capability. Polish pays off in the video and the finals demo.
- **The brief comes first.** Briefs drop at 11 PM CT; match a candidate below to the brief, or adapt the pattern to whatever the brief asks.

Research caveat: this session's network blocked most outside sites, so most facts below come from search results. Open the primary page before quoting any number in the write-up.

### What we know about kickoff (verified from the organizer emails)
- At 11:00 PM CT, the exact project brief for each of the four tracks arrives by email, together with the submission form.
- "You don't need to pick a track until then." The FAQ also says code, writeup and video are required, and teams may use public data, open-source libraries and pretrained models with credit.
- The About page says projects are "applied to a real problem in the track you choose". Whether a brief fixes one problem or sets a theme is unknown until 11 PM.
- Submissions close Sun 11:59 PM ET (10:59 PM CT). Top 10 finalists are named Nov 18. Finals are Nov 21.

### Shortlist (ranked for our rubric)

**1. Pill identifier with a safety net (Health; strongest).** Incumbent: NIH's Pillbox, retired Jan 28, 2021.
- **Why now:**
  - NLM says it has no plans to replace Pillbox. It also says its final static files "should not be used for pill identification".
  - What's left are ad-heavy or third-party sites (Drugs.com, Medscape, PillID). PillID's image archive covers only 8,693 photos.
  - Chatbots get about 88% (22/25) on clear photos. Their errors are misread imprints, e.g. "NF 06" read as "NF 05" turned nifedipine into metformin (Renal Failure, Dec 2024).
- **Rebuild:** photo → vision model reads the imprint, colour and shape → match against an authoritative table (DailyMed product characteristics). Show the top 3 candidates with the evidence for each. **Abstain** ("not sure, ask your pharmacist") when the imprint is uncertain.
- **Measure:** top-1 and top-3 accuracy, plus the wrong answers avoided by abstaining. Baselines: chatbot alone, and imprint-text search. Slices: lighting, pill shape, worn imprints.
- **User:** a caregiver sorting a parent's loose pills. This fits Arecibo (older adults, caregivers).
- **Risks:**
  - We need a vision API key and a cached demo.
  - A wrong ID is dangerous, so abstention and the "not medical advice" line are core.
  - Verify the Pillbox archive and DailyMed imprint fields at kickoff.
- Sources: [NLM retirement notice](https://www.nlm.nih.gov/pubs/techbull/ja20/ja20_pillbox_discontinue.html), [data.gov archive](https://catalog.data.gov/dataset/pillbox-retired-january-28-2021), [PillID](https://pillid.pages.dev/about.html), [Mayo ChatGPT pill study](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11391868/), [one pill, three chatbots](https://dhinsights.org/news/one-pill-three-chatbots-four-answers-why-ai-models-get-simple-healthcare-questions-wrong).

**2. Discharge or medication instructions translated with a safety check (Languages, crosses into Health).** Incumbent: Google Translate, as used in ERs.
- **Why:**
  - Khoong et al. (JAMA Intern Med, 2019) found 92% accuracy for Spanish and 81% for Chinese, with 2% and 8% potentially harmful errors. "Hold the kidney medicine" became "keep taking" it.
  - A 2021 study ranged from 55% (Armenian) to 94% by language.
  - NYC law requires translated pharmacy labels in seven languages.
- **Rebuild:** translate + back-translate. Rules then check that doses, numbers, negations and hold/stop/continue verbs survived. Flag risky lines and show the English beside them for a bilingual family member.
- **Measure:** harmful-error detection recall vs plain machine translation; per-language slice table.
- **Warning:** a workshop mentor called translation ideas saturated. Our twist is the safety check, not the translation.
- Sources: [UCSF summary](https://www.ucsf.edu/news/2019/02/413376/google-translates-doctors-orders-spanish-and-chinese-few-significant-errors), [ScienceDaily](https://www.sciencedaily.com/releases/2019/02/190225123451.htm).

**3. Personal smoke and heat alerts for sensitive people (Climate).** Incumbents: the EPA AirNow app, CDC Heat & Health Tracker, and EJScreen.
- **Why:**
  - AirNow is about 3.6★ from 818 Google Play ratings (third-party aggregator). Complaints: no alerts, slow updates, low resolution, readings that don't match the website.
  - EPA removed EJScreen in Feb 2025, and the CDC heat tracker's daily data was paused in 2025 (both from search results).
- **Rebuild:** one person (asthma, or an older adult on heat-sensitive medication), their places → next-day AQI and heat risk → a plain action plan.
- **Measure:** next-day forecast error vs a persistence baseline and vs the official forecast.
- **Prior art:** Leeward, 2nd place at the Health in Climate AI Hackathon NYC 2026 (heat and smoke risk for veterans), and AirCast (NASA Space Apps 2025 nominee, heuristic forecast with no backtest). This overlaps HeatRx.
- Sources: [AirNow app](https://apps.apple.com/us/app/epa-airnow/id467653238), [android-stats](https://android-stats.com/d/com.saic.airnow), [Leeward repo](https://github.com/harshini2212/Climate-Health-Cornell-Hackathon), [AirCast repo](https://github.com/allenvarghese05/aircast-nasa-hackathon).

**4. Finance (only if the finance brief fits; weakest evidence).**
- **Medicare Plan Finder:** in 2019 it ranked plans by premium instead of total cost. One example was about $5,800/year apart. Current state unchecked.
- **IRS Free File:** about 68% of eligible taxpayers didn't use it (2019 Taxpayer Advocate). Direct File won't run in 2026 (Nextgov, Nov 2025).
- **CFPB college-cost tool:** no four-year debt estimate (2012 critique).
- **Impact statistic:** NCOA BenefitsCheckUp: 36% of older adults applied and 20% enrolled within 8–10 weeks.
- Sources: [Nextgov](https://www.nextgov.com/digital-government/2025/11/direct-file-wont-happen-2026-irs-tells-states/409309), [Becker's on Plan Finder](https://www.beckershospitalreview.com/payer-issues/cms-spent-11m-on-a-new-medicare-cost-tool-consumers-say-it-doesn-t-work.html), [NCOA study](https://ncoa.org/article/new-study-finds-benefitscheckup-effective-for-helping-older-adults-access-federal-and-state-programs).

### Past hackathon projects worth learning from (inspiration only; never copy code)
The pattern across all of them: a good idea, synthetic data, and **no measured evaluation against a baseline**. Measurement is our edge.
- [still-kicking](https://github.com/CarolinaBosch/still-kicking): voice check-in for older adults with caregiver summaries. Synthetic patients; the microphone path is untested.
- [MedLingo](https://github.com/MdBilalNad/MedLingo): explains lab reports in the user's language. Its eval folder has no results.
- [medclear-ai](https://github.com/Vallejo1921/medclear-ai): clinical notes in plain language. One test, no metrics, unsourced claims.
- [AirCast](https://github.com/allenvarghese05/aircast-nasa-hackathon) and [Leeward](https://github.com/harshini2212/Climate-Health-Cornell-Hackathon): see candidate 3.

## Idea filter (latest, Nov 12–13)

From later research rounds, after several picks were rejected. Run every candidate through it at kickoff:

1. **Real pull:** people already show the problem through painful workarounds or explicit "I wish" posts.
2. **Chatbot test:** a 2026 frontier chatbot can't simply do it. Paste a real input into ChatGPT/Gemini/Claude and save the transcript. If the chatbot nails it, the idea is dead unless we can measure specific cases where it fails, with the chatbot as our baseline. Don't underestimate current models.
3. **Not already solved** for *this specific user, in this specific way*. Almost every category has companies in 2026. Winners pick a narrow user and moment, an insider fact, a product that acts instead of just answering, or a trust layer.
4. **Buildable and measurable in 48 hours,** with public or synthetic data.

Pattern seen in 2026 searches: "AI decodes a confusing document" ideas are saturated. Obvious wish-tools (pharmacy stock finders, AI that calls offices for you, check-in calls for aging parents, photo calorie counters) all exist already.

## Newer candidate: OneCabinet (not yet confirmed by the team)

**Pitch:** one medicine list for a family that mixes Indian and US medicines. A grandchild photographs a grandparent's medicine strips and bottles. A vision model reads brand, composition and strength. The result is matched against a public Indian-medicine dataset (`junioralive` on GitHub, ~254k rows, MIT licence; recheck before use) and NIH RxNorm. Then **plain rules** flag:

- same-ingredient duplicates (Crocin = Tylenol: paracetamol = acetaminophen)
- same-class duplicates (telmisartan + losartan)
- hidden combination duplicates (Telma-AM + US amlodipine)
- daily maximum doses exceeded
- drugs not approved in the US

**Output:** an English sheet for the US doctor, a Hindi/Gujarati daily schedule built from fixed phrase templates, and questions to ask. It never says "stop" a medicine.

**Evidence:** an FDA study (BMJ Qual Saf 2020) found 27 US brand names that match foreign brands with *different* drugs, plus 74 near matches. Reopen the paper before citing it.

**Competitors:** ScanMyPills (US data only), travel name-translators (e.g. MediHelp), Indian apps like 1mg. **Gate before committing:** run the chatbot test on 8–10 real-looking strips (synthetic or public images, no real patient data).

## Killed ideas, with reasons (saves time at kickoff)

| Idea | Why killed |
| --- | --- |
| Camera-checked home blood-pressure technique | A general AI could do most of it, the pitch was unclear, and nobody asked for it |
| Snore-clip analysis | A voice recorder plus a chatbot already covers it |
| Employer health-plan picker | Benefits Decoder, Healthee, Nayya, ALEX already do it |
| Financial-aid letter decoder | Niche, College Raptor, TuitionFit, plus 6+ Devpost clones |
| Medicaid work-requirement navigator | Free calculators; well-funded startups |
| ER-or-wait triage interviewer | Ada, nurse lines, chatbot health modes |
| Phone-video fall-risk test | CDC STEADI checklist and OneStep exist. ChairCheck below needs its fairness/abstention twist to survive |

## Ranking (first research round)

Scores are estimates out of 5 against the rubric.

| # | Idea | One-liner | Original | Testable | Demo | Doable in 48h | Data |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **HeatRx** (main) | Med list + heat forecast → personal hot-day plan for older adults | 5 | 5 | 4 | 4 | CDC drug table, RxNorm/RxClass, weather API, CMS Part D |
| 2 | **ChairCheck** (backup) | Phone camera scores the CDC 30-second chair-stand fall-risk test, with a fairness audit | 3 | 5 | 5 | 4 | MediaPipe Pose + consented clips |
| 3 | SafeSimplify | Medical-document simplifier with a "safety diff" that catches dropped doses/dates | 3 | 4 | 4 | 5 | Synthetic discharge notes, MedlinePlus |
| 4 | Shortage Radar | Predict drug shortages, suggest same-class alternatives | 4 | 4 | 3 | 3 | openFDA shortages + NDC, RxClass |
| 5 | CaseFill | Pre-fill benefit forms from case notes, citing the source sentence of every field | 3 | 4 | 3 | 4 | Synthetic case notes |

## 1. HeatRx

**Pitch:** "Your grandma's water pill makes a 95°F day dangerous, and no weather app knows that. HeatRx reads her medication list and gives her a plan for the hot days ahead."

**Why it's real:** The [CDC](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html) lists drug classes that raise heat-illness risk (diuretics, anticholinergics, some psychiatric drugs; ACE inhibitor/ARB + diuretic is especially risky) and drugs damaged by heat (insulin, inhalers, EpiPens). It asks clinicians to make a "medication plan for hot days". No consumer tool does that. [Layton et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7728169/) found the risk applies all summer, with no extra heatwave effect, so advise for the whole summer, not just heatwaves.

**Planned pipeline (build after kickoff):**
1. Input: typed list, photo of a med list, or pill-bottle photo → drug names (vision model/OCR).
2. Normalize: RxNorm approximate match (misspellings, brands, abbreviations) → RxClass drug class.
3. Risk engine: **transparent rules** encoded from the CDC table: class → mechanism (dehydration/electrolytes, less sweating, central thermoregulation, toxicity from reduced clearance such as lithium, photosensitivity, heat-damaged storage) + combination rules.
4. Heat forecast: 7-day temp + humidity → heat index → risk level per day.
5. Output: plain-language one-page plan. The LLM **only rewrites rule outputs**; it never decides risk. Never advises stopping a medication.

**Evaluation:** ~150 synthetic med lists (generic, brand, misspellings, abbreviations like HCTZ, Spanish/Hindi/Telugu, handwritten and pill-bottle photos), labeled blind by a teammate who didn't write the code. Metrics: recall of risky drugs (primary), precision, plan correctness on 20 hand-checked cases. Baseline (RxNorm only) vs. system (LLM + RxNorm). Fairness table by input type.

**Stretch:** CMS Part D heat-sensitizing prescriptions by state/ZIP + CDC Social Vulnerability Index map. Only if the MVP is done by Saturday night.

**Risks:** No US heat in November (replay a past heatwave). CDC list is incomplete (say "not in our list", never "safe").

## 2. ChairCheck

**Pitch:** "A doctor's fall-risk test, scored by your phone in 30 seconds, and honest about when it can't see you well enough."

**Planned pipeline:** MediaPipe Pose (pretrained, credited) tracks hips/knees/shoulders → hip/knee angles drive a sit↔stand state machine with a buffer zone (one wobble ≠ two reps) → rep count in 30 s vs. CDC STEADI norms by age/sex. **Twist:** a "can't see you" abstention from landmark-visibility scores: refuse to score rather than guess.

**Evaluation:** ~40 consented clips, reps counted by hand by two people. Mean rep error, % exact, fairness table by lighting, camera angle, clothing (incl. sarees/long skirts), skin tone, body size, age; abstention rate and whether abstaining prevented wrong counts.

**Originality, honestly:** phone scoring of this test exists ([PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7650655/), [Springer](https://link.springer.com/chapter/10.1007/978-3-031-59091-7_18)); cite them. Ours adds the fairness audit, the abstention, and an older-adult home flow. Pose datasets underrepresent older adults and darker skin ([Sony AI](https://ai.sony/blog/blog-029/)).

**Privacy:** written consent from everyone recorded; don't store raw clips.

## 3–5 in one line each

- **SafeSimplify:** extract every med, dose, frequency, date and warning before/after simplification; flag and fix omissions. Evidence: in [Zaretsky et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC10928500) 18 of 100 physician reviews flagged safety concerns in LLM-simplified discharge summaries.
- **Shortage Radar:** classifier on [openFDA shortages](https://open.fda.gov/apis/drug/drugshortages/how-to-use-the-endpoint/) + NDC features (manufacturer count, dosage form, route). Only ~1,700 imbalanced records. Best for a supply-chain/cost brief.
- **CaseFill:** LLM extraction into a form, each field linked to its source sentence with confidence; low confidence → human. Measure per-field accuracy and fairness across name origins / non-native writing.

## Dropped ideas (and why)

- Pharmacy robo-caller: stock data isn't public; calling pharmacies without consent breaks data rules.
- Doctor-informed Q&A bot: crowded, hard to test honestly.
- PT companion for loneliness: sensitive with older users, hard to evaluate.
- Elderly daily-routine anomaly tracker: needs months of sensor data → became ChairCheck.
