# Kickoff checklist (first hour)

Kickoff: **11:00 PM CT Fri Nov 13** (12:00 AM ET Sat Nov 14). The challenge briefs arrive **by email**. Goal: idea, track and roles locked by **12:00 AM CT**, and API calls returning real data by **2:00 AM CT**.

## Before 11:00 PM CT (allowed: no project code)

- [ ] All teammates confirmed on **one** registration (closes 10:59 PM CT). Max team size is 3.
- [ ] Everyone has the starter-kit email (sent Nov 13). Note any datasets or notebook templates it includes.
- [ ] Everyone can push to this GitHub repo and open it in Claude Code (see `TEAM-SETUP.md`).
- [ ] Everyone has a Google account for Colab, and one shared Drive folder exists.
- [ ] LLM/vision API key decided and working (see `TEAM-SETUP.md`). Keys stay out of git.
- [ ] Everyone has skimmed `IDEAS.md` and `RULES-AND-RUBRIC.md`.
- [ ] Group call/link ready for 10:55 PM CT.

## 11:00–11:20 PM CT: read the brief together

- [ ] Paste the full brief text into `docs/BRIEF.md` (verbatim, with the time received). Save attachments' names and links.
- [ ] Underline: the exact problem statement, the target user, any **named datasets**, any required deliverables or constraints.
- [ ] Match the brief to the decision table below.

## 11:20–11:45 PM CT: decide

Decision table (from the research doc). Use the brief's own words in our framing.

| If the health/climate brief is about… | Build | Lead with |
| --- | --- | --- |
| Climate impacts on health, extreme weather, vulnerable groups | **HeatRx** | Heat forecast + population map |
| Medication safety, chronic disease, older adults | **HeatRx** | Med-list parser + per-person plan |
| Aging, mobility, rehab, physical activity, computer vision | **ChairCheck** | Live demo + fairness table |
| Health literacy, patient communication, access | SafeSimplify | Omission rate + multilingual results |
| Healthcare operations, supply chain, cost | Shortage Radar | Prediction accuracy + alternatives |
| Social determinants, admin burden, benefits | CaseFill | Per-field accuracy + time saved |
| None of these fit | Reuse the HeatRx pattern | Public guideline + public data → personal plan + fairness test |

Rules of thumb:
- **If the brief names a dataset, use it**, even if that means changing idea. Track fit is worth 20 points.
- Pick the idea we can **finish and measure**. Technical execution (30) + testing/honesty (15) = 45 of 100.
- Avoid ideas on Veritas's own "common ideas" list (symptom checker, med-interaction checker, fall detection, skin classifier, heat-island map) unless we add a real twist.

## 11:45 PM–12:00 AM CT: lock it

Create `docs/DECISIONS.md` with:

- [ ] Track chosen
- [ ] Idea chosen, and one-sentence problem statement
- [ ] Specific target user (e.g. "a 72-year-old on a diuretic in Phoenix")
- [ ] MVP flow (5 steps max) and what is explicitly **out of scope**
- [ ] Module owners (who builds what), and the Evaluator (must not be the code author)
- [ ] Main evaluation metric + test-set plan
- [ ] Tech choices: Colab vs. repo, UI (Streamlit / Gradio / Colab widgets), LLM provider

## 12:00–2:00 AM CT: skeleton

- [ ] Code layout agreed and created (one folder per module, shared data formats written down in `DECISIONS.md`).
- [ ] Each external API returns real data once, and the response is cached to disk.
- [ ] Evaluator starts the test-set spec (inputs, labels, who labels).
- [ ] Then **sleep**. The Q&A is 20% of the finals, and everyone must be able to explain the code.
