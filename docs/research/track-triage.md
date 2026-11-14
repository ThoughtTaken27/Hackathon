# Track triage v2 (Fri Nov 13, 11:50 PM CT; restart)

**Parth's override (11:50 PM CT): AI + Languages is out.** "We will most definitely not be doing AI + Language. Anything but that." The earlier pick (Samjha) is archived at `docs/research/killed-samjha-prd.md`. This triage covers Health, Finance and Climate only.

Source: `docs/BRIEF.md` (Veritas Project Briefs PDF, received 10:47 PM CT). Scores 1–5. Measurable, demo-able and fresh angle count double ("easiest to win" ≠ "easiest to build"). Team: one strong lead plus two beginners, Claude Code, an 8 GB Apple-silicon laptop, **no LLM API key** in the environment (checked 11:22 PM CT), so the core model must run locally on CPU or from a committed cache.

The brief's hard rule that shapes every row: **"AI must be central. Your project needs to use AI or machine learning to do its main job."**

| | Health | Finance | Climate |
| --- | --- | --- | --- |
| **What the brief literally asks** | "helps one specific person catch a health problem sooner, or manage an ongoing one better"; report missed cases and false alarms separately; check across age/sex | "helps a person or a small business make a safer or fairer money decision, and show that it beats a simple rule"; precision/recall for rare events; "If your data has dates, train on earlier data and test on later data"; "whether a real person could trust your tool enough to act on it" | "helps a community, a city or an energy system measure, predict or reduce its climate impact"; one place; persistence baseline; "Explain what decision your prediction supports and who makes it" |
| **Named datasets** | PneumoniaMNIST, Kaggle Chest X-Ray, UCI Heart Disease, WHO GHO, OWID | **SMS Spam Collection**, Kaggle card fraud, German Credit, Combined_News_DJIA, yfinance, FRED | NASA POWER, Open-Meteo, OpenAQ, EuroSAT, GFW, Climate TRACE |
| **Obvious crowded project** | Pneumonia CNN (beginner); heart-disease logistic regression | Scam text filter (beginner); the brief lists its three "own" twists, so many teams will hand in the same three | Solar MAE vs persistence (beginner) |
| **Fresh angle available** | HeatRx (med list + heat forecast for an older adult). But its main job is a lookup + rules, which fails "AI must be central" unless the model part is real | The brief's scam filter, but done as a researcher would: a **dated** test (2012 → 2022 → 2023–25 scam sets), the **lookalike-legit** question nobody asks (does it bury the real bank-fraud alert, pharmacy refill or USPS text an older adult needs?), and tactic-level "why" an older adult can learn from | Smoke/heat day warning for one senior centre; but our model would compete with the official NWS/AirNow forecast and lose |
| **Best candidate for us** | HeatRx | **"Second look": a scam-text check for an older adult and the family member they forward texts to** | Next-day PM2.5 / heat warning for one city's senior centre |
| Fits brief's words | 3 ("AI must be central" is shaky) | 5 | 4 |
| Measurable in 48 h (×2) | 3 (needs a hand-labelled med-list set; no public ground truth for "plan correctness") | 5 (labelled public sets with dates exist; precision/recall with N) | 5 |
| Demo-able in 60 s (×2) | 4 | 5 (paste a real text; the judge pastes their own) | 3 (a number for tomorrow) |
| Buildable (lead + 2 beginners) | 4 | 5 (TF-IDF + logistic regression and a small local sentence-embedding model on CPU) | 4 |
| Public data ready tonight | 4 (RxNav, CDC table, NWS) | 4 (UCI SMS on HF; Mendeley 2022 CC BY 4.0; newer sets pending scout) | 4 (Open-Meteo 429s from cloud; NWS OK) |
| Strong incumbent to rebuild and beat | 2 (none consumer-facing; NWS HeatRisk is general) | 3 (Google Messages, Truecaller, Scamio: free, no published accuracy) | 3 (AirNow, NWS) |
| Gold sponsor fit (older adults, caregivers) | 5 | 5 (older adults are the target of the losses; the caregiver is the person they forward texts to) | 2 |
| Fresh angle (×2) | 4 | 3 (crowded topic, but our question and test data are not the brief's) | 2 |
| **Weighted total (max 55)** | 41 | **49** | 37 |

## Finalists
1. **Finance: "Second look", a scam-text check for an older adult, measured on dated modern scams and on lookalike legit texts.** Highest on measurable + demo-able; labelled data with dates exists, which lets us obey "train on earlier data and test on later data" literally; the brief's judging hint "whether a real person could trust your tool enough to act on it" is exactly the false-alarm question. Risk: crowded, so our additions must be visible and measured.
2. **Health: HeatRx**, medication list + heat forecast → a hot-day plan for an older adult. Best sponsor fit and a real gap (CDC asks clinicians for a "medication plan for hot days"; no consumer tool). Risk: the main job is lookup + rules, so "AI must be central" is in doubt, and there's no public ground truth.

## Why Climate lost
Weakest sponsor fit and weakest demo (a number for tomorrow). The persistence baseline is hard to beat and the official NWS/AirNow forecasts are better than anything we can train in 48 hours, so our headline would be modest and the "who decides" link weak.
