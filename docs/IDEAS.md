# Ideas (pre-researched, not built)

Summary of the research doc: [Veritas AI Hackathon — Health Idea Research & Game Plan](https://claude.ai/artifact/KxEQasfso3e2RMTBuqrS8v). The final pick happens at kickoff with the decision table in `KICKOFF.md`. Nothing here is code; it's a plan to adapt to the brief.

## Ranking

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
