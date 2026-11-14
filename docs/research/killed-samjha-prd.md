# PRD: Samjha (समझा, "understood?")

Status: draft v2 (red-team fixes applied) · written Fri Nov 13, 11:25 PM–12:15 AM CT by the overnight agent (all after kickoff at 11:00 PM CT) · brief received 10:47 PM CT · track: **AI + Languages**
Every claim has a source link or says "assumption". Every number has its N or says "not measured yet". Research behind this document: `docs/research/` (triage, five teardowns, chatbot test, probe output).

## 0. The pitch
- **One sentence:** Samjha checks a translated medicine label line by line for a family translating into Marathi or Hindi. It shows which lines kept the dose, timing and "do not", and which line not to rely on, with the evidence in English.
- **The sentence a judge repeats to another judge:** "They measured how often a free translator breaks the dose or the 'do not' in Marathi, Hindi and Spanish medicine directions, then built a checker that tells a grandchild *which* line of grandma's label not to trust." (Until `results/metrics.json` says so, we do **not** claim Marathi is worse. That is the question we measure. Martos 2025 covers other languages and Azure, not NLLB.)
- **Why this wins (three lines):**
  1. It answers the Languages brief word for word: "medicine instructions … decide whether people could safely rely on it", NLLB-200 + FLORES, per-language results, side-by-side examples, and "checks by a real speaker" (our lead reads Marathi and Hindi).
  2. It's a measured contribution, not a wrapper. We report (a) how often a free model breaks critical facts per language, and (b) how many of those breaks our checker catches vs a generic back-translation score, with misses and false alarms reported separately.
  3. Older adults and the grandchildren who care for them are exactly the Gold sponsor's users.

## 1. The brief and track fit
Verbatim lines from `docs/BRIEF.md` we answer:
| Brief says | How we answer |
| --- | --- |
| "help people understand each other … especially in a language that technology serves poorly" | Marathi (served poorly; absent even from California's official translated-label list and from MedlinePlus) and Hindi, with Spanish as the well-served control |
| 4.4.2: "Measure how well a free translation model handles a less widely served language compared with a widely spoken one, then find and explain where it struggles" | chrF of NLLB-200-distilled-600M on FLORES-200 per language, plus critical-fact error rate on medicine directions per language |
| 4.4.2 make-it-your-own: "Translate text from a real setting, such as school notices or medicine instructions, and decide whether people could safely rely on it" | This is the whole product |
| 4.4.2 make-it-your-own: "Use a language your team speaks, and check whether your own ratings agree with chrF" | Native-speaker labels vs chrF, and the checker vs a chrF threshold |
| "Report results separately for each language" · "Show real examples: your model's output next to the correct output" | Per-language tables; failure gallery shows English, translation, back-translation and the human-corrected line |
| "checks by a real speaker of the language" | Test labels by fluent Marathi/Hindi readers, two raters, agreement reported |
| "If you build on a large language model API, judges will focus on what you add around it" | No LLM API. We add our own data, our own question and a measured checker |
| §3 "Does it beat a simple baseline?" / "Where does it fail?" | Baselines: trust every line, flag every line, back-translation chrF threshold. Three failures in a gallery |

Why Languages over the other three: `docs/research/track-triage.md` (weighted: Languages 50/55, Finance 45, Health 40, Climate 38). Finance (scam filter) is Plan B: measurable, but it's the brief's own beginner project with its three twists already listed, against a free built-in incumbent (Google Messages + Gemini).

## 2. Problem
- **One sentence + statistic:** families and clinicians lean on machine translation for medicine directions, and its clinically important errors concentrate in poorly served languages. In Martos et al. (JAMA Netw Open 2025;8(9):e2532312, https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2839035, opened Nov 13 2026), neural MT (Azure AI Translator) made clinically impactful errors in **7% of Spanish sections vs 41% Vietnamese, 52% Chinese and 92% Somali** (148 sections from 34 pediatric discharge instructions), while professional translators were at 7–20%.
- Supporting: Google Translate on 100 ED discharge instructions was 92% correct in Spanish and 81% in Chinese. Errors with potential for clinically significant harm were 2% and 8% (Khoong et al., JAMA Intern Med 2019; UCSF summary opened: https://www.ucsf.edu/news/2019/02/413376/google-translates-doctors-orders-spanish-and-chinese-few-significant-errors).
- The gap for our languages: California's official translated directions exist only in Chinese, Farsi, Korean, Russian, Spanish and Vietnamese (https://www.pharmacy.ca.gov/publications/translations.shtml, opened). No Hindi or Marathi. MedlinePlus has Hindi but no Marathi (scout, Nov 13).
- And 91.8% of 169 surveyed prescribers didn't tell patients they could ask for a non-English label (Annals of Family Medicine survey via US Pharmacist, opened by scout: https://www.uspharmacist.com/article/survey-finds-gaps-in-nonenglish-medication-instructions). Families are left to translate themselves.
- **Voice of the user:** we could not open a single Reddit or forum thread on this from tonight's network (the Reddit JSON is blocked; searches returned studies, not posts). We won't invent quotes. Saturday task for Teammate B: find 2–3 real posts (r/ABCDesis, r/AskDocs, r/pharmacy, caregiver forums), paste them into `docs/research/voice.md` paraphrased and anonymised. Default if none are found: lead with the studies and the persona.

## 3. Who it's for
- **Persona (illustrative, assumption):** Riya, 16, lives in Edison, New Jersey with her parents and her grandmother, Aaji (76). Aaji moved from Pune two years ago. She reads Marathi well and Hindi slowly, and reads no English. After a hospital stay she has three new prescriptions, one of them insulin.
- **The moment:** Sunday night, kitchen table. Riya fills Aaji's weekly pill organiser and writes each label's directions out in Marathi on a sticky note. She speaks Marathi fluently but reads Devanagari haltingly, so **she can't verify the translation she pastes from her phone.** Her parents get home late.
- **What she does today:** types the label into a phone translator, copies the Devanagari onto the sticky note and hopes. Or she waits for a parent and the note doesn't get written.
- Secondary users: a pharmacy tech printing a "courtesy translation"; a clinic nurse checking a discharge sheet before handing it over.

## 4. What already exists (teardown summary)
| Product | Link | Why people use it | Price | Biggest weakness | Evidence |
| --- | --- | --- | --- | --- | --- |
| Google Translate | translate.google.com | Free, instant, 240+ languages; 4.29★ from 84,157 iOS ratings | free | No per-line signal of which line is wrong; quality falls in poorly served languages | `docs/research/teardown-google-translate.md` |
| Frontier chatbot (Claude/ChatGPT/Gemini) | — | Fluent, explains risk | free tier | Translates well (8/8 in our test) but can't audit the translation the family *already has*, and gives no measured error rate | `docs/research/chatbot-test-translation.md` |
| RxTran (Language Scientific) | rxtran.com | Pharmacies buy it to meet translated-label laws | paid, B2B, unpublished | Human-reviewed but reaches only pharmacies that pay; no published accuracy | `docs/research/teardown-rxtran.md` |
| CA Board of Pharmacy translated directions | pharmacy.ca.gov | Vetted, free, legally backed | free | 15 simple phrases, 6 languages, no South Asian languages | `docs/research/teardown-ca-board-translations.md` |
| Mehandru et al., EMNLP 2023 (research) | arxiv.org/abs/2310.16924 | Showed back-translation helps *physicians* catch clinically harmful MT errors | — | Shows the back-translation to a human expert; no automated fact comparison; not Hindi/Marathi | `docs/research/research-languages.md` |

- **We rebuild from** Google Translate (the tool families actually use; it becomes "trust every line", our status-quo baseline) and Mehandru et al.'s back-translation idea (it becomes our "simple reasonable" baseline: a back-translation similarity score with a threshold).
- **Past hackathon projects:** GitHub search returned zero repos for "medication instructions translation", "prescription label translation" or "medical translation back-translation". The only one is a 0-star discharge simplifier with Tamil (https://github.com/kkeerthigasri73-dot/discharge-ai-tool). Devpost page 1 had no medication-translation project. Neighbours (MedLingo, medclear-ai) translate or simplify with no measured evaluation (`docs/IDEAS.md`).

## 5. What we build differently
- **Keep:** translate one line at a time (from the translators). Show the back-translation (from Mehandru et al.).
- **Cut:** camera/OCR, conversation, 200 languages, accounts, history, any advice about the medicine itself.
- **Add (measurable):**
  1. **Fact extraction** from the English line. **v1 (Must, overnight): 7 kinds + 1 structural check**: count+unit (incl. every number, which also covers numbers inside limits and conditions), frequency/interval, time of day, food, "do not", route, **"hold"** (must read as "skip/don't take this dose", not "stop" or "keep"; the probe broke it in all three languages), plus **sentence count** (source sentences vs translation sentences; the probe dropped whole second sentences). **v2 (Should, Sunday AM, only if v1 is green):** duration, days, other conditions ("if", "as needed"), maximum as a structured fact. Until v2, any line containing a v2 kind is checked on its numbers and v1 facts, and shows "Couldn't check: this line has a condition/limit Samjha v1 doesn't read" for the rest. Narrow and correct beats broad and brittle.
  2. **Two checks per fact:** (a) is it present in the translation itself (language lexicons written and checked by a native speaker, with Devanagari digits normalised)? (b) does it survive back-translation to English **by a different model** (OPUS-MT mr→en / hi→en / es→en, Apache-2.0), so the translator can't quietly repair its own error on the way back? Same-model (NLLB) back-translation is kept only as an ablation.
  3. **A per-line verdict** with the evidence in English. A grandchild who can't read Devanagari can still see "English says 2 capsules; the translation says १ (1)".
  4. **Works on any translation:** paste what the phone gave you, or let Samjha translate with NLLB-200.
- **Why would anyone use ours instead of the original?** Riya already has a translator. What she doesn't have is a way to know whether the Marathi she copied still says *two* capsules, *at bedtime*, and *don't* take it with alcohol. Samjha tells her in English which lines kept every number and warning and which one she should ask the pharmacist to confirm. She gets that from her laptop, for free, without sending Aaji's medicines to anyone.
- **Why it matters and who will care:** Riya and Aaji (the right dose); the pharmacist (fewer callbacks, a concrete line to confirm); clinics serving South Asian families; judges (an honest per-language measurement on a language almost nobody tests).
- **Free here, paid elsewhere:** human-verified label translation (RxTran, interpreter services) is paid and B2B. We can offer a check for free because it runs on an open model (NLLB-200), public data (FLORES-200, CA Board phrases) and plain rules, with no proprietary dependency.

## 6. Does this need AI?
| Step | Lookup / rules / model | Why |
| --- | --- | --- |
| Translate English → Marathi/Hindi/Spanish | **Model** (NLLB-200-distilled-600M) | Real generation task; the brief's named model |
| Back-translate → English | **Model** (OPUS-MT, a *different* model from the translator, so the check is independent; NLLB reverse as an ablation) | Lets English-only rules read the meaning back without the translator repairing its own error |
| Extract facts from English (source and back-translation) | Rules (regex + small vocab) | Must be auditable; label English is formulaic |
| Find facts in the translation | Rules + native-speaker lexicons | Auditable; a speaker can read and fix every entry |
| Verdict | Rules over the two checks | Safety decisions must be explainable ("LLMs format, rules decide") |

- **The model component judges see:** NLLB-200 generates the translation and the back-translation. Without it there's nothing to check and no back-translation evidence. It's the cheapest model that covers all four languages both ways, runs on a laptop CPU, and is the one the brief names. A bigger model (NLLB-1.3B, 3.3B) is a stretch ablation, not the default.
- **No-AI baseline:** "trust every line" (recall 0 by definition). A digits-only rule (do the source numbers appear in the translation?) is the cheap rule baseline.
- **Simple-reasonable baseline:** back-translation chrF with a threshold tuned on dev (automating what Mehandru et al. showed to physicians).
- **Chatbot baseline:** a frontier chatbot's translations of the test directions (run once; transcript saved) are an audited row: how many critical errors it makes, and our false-alarm rate on good translations. Chatbot test transcript: `docs/research/chatbot-test-translation.md` (8/8 correct).
- **What ours does that they can't, measurably:** catch lines whose critical facts changed (recall on unsafe lines, per language) at a stated false-alarm rate, beating the back-translation chrF threshold at the same false-alarm rate.
- **Validation of model output:** NLLB output is never trusted directly. Every translated line goes through the fact checks. Empty, repeated or wrong-script output (e.g. Latin letters when Devanagari was expected) → "Couldn't check".

## 7. The core flow (max 5 steps, each visible in the demo)
1. Paste the label's English directions, or tap one of three example labels.
2. Pick the language: मराठी Marathi · हिन्दी Hindi · Español.
3. Click **Check translation**. Samjha translates with NLLB-200, or uses the translation you pasted under "I already have a translation".
4. Each line appears as a card: the English line, the translation, and fact chips (e.g. `2 capsules ✓` `at bedtime ✓` `by mouth ✓`) ticked or flagged.
5. A verdict on each card (green never means "correct" or "safe"; the footer says so beside it): **Key facts found** / **Don't rely on this line: ask the pharmacist** / **Couldn't check this line**, with the reason in one English sentence and the back-translation under "Why?".

- **60-second script:** "Riya pastes Aaji's three label lines (5 s) → picks Marathi (2 s) → clicks Check (translation ~10–20 s on CPU, or instant from cache) → sees two green cards and one amber: 'English says *before breakfast*; the translation and its back-translation say *after*' (15 s) → opens Why? to see the back-translation (5 s) → pastes her phone's translation of the same line instead, and it turns green (15 s)."
- **Interactive moment:** a judge types any English direction, or pastes a translation from their own phone, and watches the chips tick live.
- **Three golden-path demo inputs** (final picks come from the probe run, `docs/research/samples/nllb-probe-12-directions.json`; see §13 "Probe"):
  - **G1 Marathi, "Aaji's new medicines":** "Take 10 units under the skin before breakfast." (probe: ok) · "Take 2 capsules by mouth at bedtime." (ok) · "Hold this medicine if your blood pressure is below 100." (probe: NLLB wrote "stop this medicine", थांबा → expected amber). Paste-mode follow-up: paste the chatbot's line 6 ("…त्या वेळी घेऊ नका", from `docs/research/chatbot-test-translation.md`) → expected green.
  - **G2 Hindi, "Blood-thinner and pain tablets":** "Take 1 tablet by mouth twice daily with food." (ok) · "Take half (1/2) tablet every morning. Do not crush or chew." (probe: 2nd sentence dropped → expected amber via sentence count + missing "do not") · "Take 1 tablet on Monday, Wednesday and Friday only." (ok).
  - **G3 Spanish control, CA-style:** "Take 2 capsules by mouth at bedtime." · "Take 3 pills in the morning and 3 pills at bedtime." · "Take 1 tablet every 8 hours for 7 days." (probe: all ok → expected all green).
  - Probe outputs are the agent's reading, not labels. Phase B re-runs them through the real pipeline (NLLB + OPUS-MT back) and caches them in `demo_cache/`. If a verdict differs from the expectation, keep the real verdict and pick a different golden line. **Never edit outputs to fit the story.**

## 8. Features
| Feature | Must / Should / Won't | Rubric line it moves | Done-check |
| --- | --- | --- | --- |
| English fact extraction (v1: 6 kinds; v2 kinds Should) | Must | Technical, Testing | `pytest tests/test_facts.py` passes on 30 hand-written cases |
| Marathi/Hindi/Spanish lexicons + Devanagari digit normalisation | Must | Technical, Creativity | `pytest tests/test_lexicon.py` |
| NLLB forward + OPUS-MT back translation with disk cache | Must | Technical | `python -c "from samjha.translate import translate; print(translate(['Take 1 tablet daily'],'eng_Latn','mar_Deva'))"` returns cached text in < 1 s on the second call |
| Per-line verdict with evidence | Must | Technical, Impact | `pytest tests/test_check.py` |
| One-screen UI with all states in §9 | Must | Clarity | screenshots in `docs/screenshots/` at 1440×900 and 393×852 |
| "I already have a translation" paste mode | Must | Impact, Creativity | golden G1 with pasted text flips verdict |
| No-key / no-download demo mode from `demo_cache/` | Must | Technical | fresh clone, no model download, the 3 golden inputs render |
| `python -m eval` → `results/metrics.json` (dev now, test Saturday) | Must | Testing | file exists with N + baseline for every number |
| `smoke_test.py` < 60 s | Must | Technical | exits 0 |
| FLORES-200 chrF per language (200 devtest sentences) | Should | Testing, track fit | row in metrics.json |
| Second translator (OPUS-MT en-mr/en-hi/en-es) as an audited system (more natural errors → more positives) | **Must** | Testing | rows in metrics.json |
| v2 fact kinds (duration, days, conditions, maximum) | Should (Sun AM) | Technical | tests |
| NLLB-1.3B ablation | Won't (unless all green Sun AM) | Testing | — |
| Camera/OCR, speech, more languages, drug info | Won't | — | — |

Out of scope, explicitly: any statement about whether a medicine is right, safe or interacting; stopping or changing doses; storing anyone's medicine list; accounts; deployment.

## 9. Design and UX spec
**Direction:** "a careful pharmacist's counter". Warm paper background, ink-dark text, large type. Status colour only where it carries meaning. Calm, never alarming: the amber state says "ask the pharmacist", not "danger". Designed for a 16-year-old on a laptop and readable over a grandparent's shoulder. Process: `ui-polish` workflow in Phase B (reference sites → sourced values → screenshots → two critique rounds). Component rules from `component-craft` and `emil-design-eng`; restraint and spatial consistency from `apple-design`.

**Screen list:** one screen. Desktop: two columns (input 5/12, results 7/12). Phone (393 px): stacked, input first, results below; the Check button stays reachable.

**Components and state tables (exact copy):**

*Header*: wordmark "Samjha" + "समझा" in Devanagari at 60% opacity. Subtitle: "Check a translated medicine label, line by line." Right side, a permanent pill: "Prototype · not medical advice".

*Input card*
| State | What shows (exact copy) |
| --- | --- |
| Idle | Label: "English directions from the label". Placeholder: "Take 1 tablet by mouth twice daily with food." Helper: "One direction per line." Example chips: "Aaji's insulin (Marathi)" · "Blood pressure (Hindi)" · "California label (Spanish)". Language segmented control: "मराठी Marathi" · "हिन्दी Hindi" · "Español". Disclosure: "I already have a translation". Button: "Check translation" |
| Paste mode open | Second textarea, label "Your translation (one line per English line)", helper "Paste exactly what your translation app gave you." |
| Line-count mismatch in paste mode | Inline under the textarea: "You have 3 English lines and 2 translated lines. Put each translation on its own line." Button disabled |
| Empty submit | Button disabled; helper turns ink: "Add at least one direction to check." |
| Too long (> 12 lines or > 300 chars per line) | "Samjha checks up to 12 short lines at a time." |

*Results column*
| State | What shows (exact copy) |
| --- | --- |
| Empty (before first check) | Muted illustration-free panel: "Your lines will appear here. Each one gets a verdict: Key facts found, Don't rely on this line, or Couldn't check." |
| Loading (live translation) | One skeleton card per line with the English text already filled in; status line "Translating with NLLB-200 on this computer… line 2 of 3". If > 8 s: "First run loads the translation model (about 30 s)." |
| Loading (cache) | No skeleton; results cascade in |
| Result: match | Green tick badge, "Key facts found". Reason: "Every number, time and warning we look for is in the translation." Chips all ticked |
| Result: mismatch | Amber badge, "Don't rely on this line". Reason, one sentence, generated from the failed fact by template: "English says **2 capsules**; the translation says **१ (1)**." / "English says **do not**; we can't find a 'do not' in the translation." / "English says **before breakfast**; the back-translation says **after breakfast**." Action line: "Ask the pharmacist to confirm this line." |
| Result: couldn't check | Slate badge, "Couldn't check this line". Reason: "We didn't find a dose, time or warning we know how to check, so we can't vouch for it." Never green |
| Unknown input (no facts, e.g. "Apply a thin layer to the affected area") | Couldn't-check card as above |
| Garbage input (e.g. "asdf jkl") | Single panel: "We couldn't find medicine directions here. Try a line like 'Take 1 tablet by mouth twice daily.'" |
| Model unavailable (no download, not in cache) | Banner: "The translator isn't installed on this computer, so Samjha can only check translations you paste. To install it: `python app.py --download-model` (about 2.5 GB)." Paste mode auto-opens |
| Server error | Banner: "Something went wrong on our side. Your text is still here; try again." No stack trace ever |
| Narrow | Cards full width; chips wrap; "Why?" disclosure collapsed by default |

*Line card anatomy* (top to bottom): line number + verdict badge (right) → English line (17 px, ink 70%) → translation (24 px Devanagari, `lang="mr"`/`"hi"`/`"es"`, ink 100%) → chip row (each chip: fact text + ✓ / ✗ / ?) → reason sentence (16 px) → "Why?" disclosure: back-translation in quotes + "Checked two ways: in the translation itself, and by translating it back to English."

*Summary strip* above the cards after a check: "3 lines · 2 key facts found · 1 don't rely" + "Translated by NLLB-200 (Meta, open model) on this computer" or "Your pasted translation".

**Token plan:**
- Colour (light): `--paper #FBF8F3`, `--card #FFFFFF`, `--ink #1C1B19`, `--ink-2 #5B5750`, `--line #E7E1D8`, `--match #1F7A4D` on `--match-bg #E8F3EC`, `--warn #9A4D00` on `--warn-bg #FDF0E1`, `--unk #55606E` on `--unk-bg #EEF1F4`, `--focus #2F5BD3`. Dark mode: `--paper #151412`, `--card #1E1C1A`, `--ink #F2EEE8`, status colours lifted for contrast. All text pairs ≥ 4.5:1 (check in Phase B).
- Type: UI "Inter" (or the system UI stack). Devanagari "Noto Sans Devanagari" (OFL; vendored woff2 in `static/fonts/` so the demo works offline; credited). Scale 14 / 16 / 17 / 20 / 24 / 32; body 17 px / 1.5; Devanagari lines 24 px / 1.6 (Devanagari needs more leading for matras).
- Spacing unit 4 px; card padding 20 px (16 on phone); gap between cards 12 px; column gutter 32 px; page max-width 1200 px; 16 px side gutter on phone.
- Radii: cards 14 px, chips 999 px, inputs 10 px, buttons 10 px.
- Elevation: cards 1 px `--line` border + `0 1px 2px rgba(0,0,0,.04)`; no heavy shadows.

**Reference patterns** (pattern and measurement only; never copied source, never paid source): status/approval rows and step progress from aisdkagents.com/ai-components and affectui.com/components (badge + one-line reason anatomy, staggered list reveal); segmented controls and disclosure rows from useplanes.com/components and uiarc.dev/components. Phase B records the specific measured values it adopts in `docs/design-notes.md`. Assumption: the sites are reachable.

**Motion plan:**
- The one orchestrated moment: results cascade, each card fading in with `opacity 0→1` and `translateY(6px→0)` over 200 ms `cubic-bezier(0.2, 0, 0, 1)`, staggered 60 ms. Then each card's chips tick in order (scale 0.9→1, 120 ms, 30 ms stagger). The verdict badge settles last. A mismatch badge does one gentle 2 px nudge, never a shake.
- Press feedback: buttons `scale(0.98)` over 100 ms ease-out; focus ring 2 px `--focus`, offset 2 px.
- "Why?" disclosure: height + opacity over 180 ms ease-out.
- `prefers-reduced-motion: reduce`: no transforms, opacity only at 120 ms, no stagger.

**Trust display:** every verdict names its evidence (which fact, what the English says, what the translation or back-translation says). The summary strip names the translator. The footer links "How Samjha checks" to a short README section and the metrics table: "On our test set (N = …) Samjha flagged X of Y Marathi lines with a changed fact …". N is always shown beside the number. Numbers come from `results/metrics.json` only, and nothing appears on screen before the test run exists.

**Disclaimer placement:** header pill on every screen; footer sentence "Samjha is a prototype and is not medical advice. It checks whether a translation kept the words on the label. It does not check whether a medicine or dose is right for anyone. Always confirm with your pharmacist."; also in README and write-up.

## 10. Architecture
- **Stack:** Python 3.11, plain modules in `samjha/`, FastAPI + uvicorn serving `static/index.html` (HTML + CSS + vanilla JS, no build step), `transformers` + `torch` + `sentencepiece` for NLLB, `sacrebleu` for chrF, `pytest`. A judge runs `pip install -r requirements.txt && python app.py` and gets a working demo **without downloading the model** (cached golden inputs + paste mode). `python app.py --download-model` enables live translation. Why: boring, local, no keys, and a polished single page.
- **Module table:**
| Module | Owner | Inputs → outputs | Done-check |
| --- | --- | --- | --- |
| `samjha/facts.py` | Lead | `extract_facts(text_en: str) -> list[Fact]`, `Fact = {"kind": str, "value": str, "span": str}`; values normalised (`"count:2"`, `"unit:capsule"`, `"frequency:2/day"`, `"interval:8h"`, `"time:bedtime"`, `"food:with"`, `"negation"`, `"route:oral"`, `"condition:hold_if"`, `"day:mon"`, `"duration:7d"`, `"max:8/24h"`) | `pytest tests/test_facts.py` |
| `samjha/lexicon.py` + `samjha/lexicons/{mar,hin,spa}.json` | Lead (mr/hi), Teammate A (es) | `find_in_target(fact, text, lang) -> bool \| None`; `normalise_digits(text) -> str` | `pytest tests/test_lexicon.py` |
| `samjha/translate.py` | Lead | `translate(lines: list[str], src: str, tgt: str) -> list[str]`; `available() -> bool`; disk cache `demo_cache/translations.json` keyed by sha256(model\|src\|tgt\|line); 60 s timeout per batch, one retry, then `TranslatorUnavailable` | second call < 1 s |
| `samjha/check.py` | Lead | `check_line(en, tr, lang, back_en) -> Verdict`; `check_label(lines, lang, translation=None) -> dict` | `pytest tests/test_check.py` |
| `app.py` | Lead | `GET /` → page; `POST /api/check` `{"lines": [str], "lang": "mar_Deva"\|"hin_Deva"\|"spa_Latn", "translation": [str]\|null}` → `{"results": [Verdict], "translator": "nllb-200-distilled-600M"\|"pasted", "cached": bool, "summary": {...}}`; `GET /api/examples` | `smoke_test.py` |
| `eval/__main__.py`, `eval/metrics.py`, `eval/baselines.py` | Lead | `data/{dev,test}/items.jsonl` (`{"id","en","lang","system","translation","back","label_ok": bool,"bad_kinds":[...],"labeller"}`) → `results/metrics.json`, `results/metrics.md` | `python -m eval` |
| `data/` | Teammate A (test), agent (dev) | JSONL as above; `data/test/FROZEN.sha256` | hash matches |
- **Data flow:** `English lines + lang (+ optional pasted translation)` → `facts.extract_facts(en)` → (if no pasted translation) `translate(en→tgt)` with NLLB → `back_translate(tgt→en)` with OPUS-MT = back → for each fact: `lexicon.find_in_target(fact, tr)` and `fact ∈ facts.extract_facts(back)` → `check.verdict` → JSON → UI cards.
- **Verdict rule (v1, tuned on dev only):** per fact, `in_translation ∈ {True, False, None}`, `in_back ∈ {True, False}`. A fact **fails** if `in_translation is False`, or if `in_translation is None and in_back is False`. Extra numbers in the translation that aren't in the source also fail ("translation adds a 3"). Line = `mismatch` if any fact fails; `unchecked` if no facts were extracted, or any fact has `in_translation None` and no back-translation; else `match`.
- **Caching / no-key mode:** `demo_cache/translations.json` committed (golden inputs, dev set, test set translations). Tests and eval run fully from the cache. There are no API keys at all. The only external fetch is the one-time model download (`huggingface_hub`, 2.5 GB), wrapped with a timeout and a designed fallback (paste mode).

## 11. Data, models, licences
| Source | Use | Licence | Key? | Hit once and cached? |
| --- | --- | --- | --- | --- |
| facebook/nllb-200-distilled-600M https://huggingface.co/facebook/nllb-200-distilled-600M | translate + back-translate | CC-BY-NC 4.0 (non-commercial; hackathon OK, credited) | no | yes: probe Nov 13 (`docs/research/samples/nllb-probe-12-directions.json`) |
| FLORES-200 https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz | chrF per language (brief's 4.4.2 baseline) | CC-BY-SA 4.0 | no | yes: downloaded Nov 13, 1,012 devtest lines each for eng/spa/hin/mar (`samples/flores200-devtest-head.txt`) |
| CA Board of Pharmacy translated directions https://www.pharmacy.ca.gov/publications/translations.shtml | 15 professional Spanish references; Spanish anchor slice | © State of California; reuse terms unclear → we store the 15 short phrase pairs with attribution as research/eval data and don't redistribute the PDFs (open question §20) | no | yes: Spanish PDF |
| Our directions corpus (dev: agent-written; test: Teammate A) | eval | ours, CC-BY 4.0 | — | Saturday |
| Native-speaker labels | eval ground truth | ours | — | Saturday |
| Frontier-chatbot translations (Claude, run once) | audited comparison row | output used under Anthropic terms, credited | n/a (run once via a Claude Code subagent; the transcript and translations are saved to `data/test/chatbot_translations.jsonl`, so `python -m eval` reads them from file with no key. Generating them isn't part of the no-key pipeline) | Saturday |
| Noto Sans Devanagari https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari | UI font (vendored) | OFL 1.1 | no | Phase B |
| Libraries: transformers, torch, sentencepiece, sacrebleu, fastapi, uvicorn, pytest | | Apache-2.0 / BSD / MIT | | |
| Helsinki-NLP/opus-mt-{mr,hi,es}-en and opus-mt-en-{mr,hi,es} https://huggingface.co/Helsinki-NLP | independent back-translator; second audited translator | Apache-2.0, not gated (all six checked via HF API Nov 13 23:30 CT) | no | metadata yes; **first Phase B task: load and run once** |

## 12. Safety and honesty rules
- **Unknown ≠ safe.** The top verdict is "Key facts found", never "safe" or "correct". Lines we can't parse are "Couldn't check", never green.
- Samjha never comments on the medicine, the dose's appropriateness, interactions, or whether to take, stop or change anything. Every amber action says "Ask the pharmacist to confirm this line."
- No personal or patient data. Directions are synthetic or from public phrase lists. No real labels photographed. The persona is illustrative. Labellers are volunteers who consent to have their *labels* used, and nothing about them is stored except an initial.
- Everything runs locally. Nothing typed leaves the computer (the model is local).
- **Known limits we state openly:** checks only the facts in our 12 kinds (not nuance, tone or idiom); lexicons cover three languages and were written by one native speaker; back-translation can "repair" an error and hide it (we reduce this by back-translating with a different model, but OPUS-MT can make its own errors); a dev set written by the builder; small test N with wide CIs; Hindi/Marathi labels come from family members, not professional translators.

## 13. Evaluation plan
**Question 1 (brief 4.4.2, the baseline project):** how well does NLLB-600M translate each language? → chrF on 200 FLORES-200 devtest sentences per language (eng→spa, eng→hin, eng→mar). Expectation (assumption): Spanish > Hindi > Marathi.

**Question 2 (our own question):** how often does NLLB-600M break a critical fact in medicine directions, per language? → % of translated directions with ≥ 1 critical-fact error, from native-speaker labels on the frozen test set. Wilson 95% CI, N per language.

**Question 3 (our system):** can a cheap, auditable checker tell which lines not to rely on?
- **Primary metric:** recall on unsafe lines (label `ok=false`) per language, i.e. the share of broken lines we flag. **Reported with the false-alarm rate** (share of correct lines flagged amber) separately, plus "couldn't check" rate. Wilson CIs. Why it matters for Riya: a missed broken line is the harm; false alarms cost a pharmacist call.
- **Baselines:** (B0) trust every line, which is what a translator user does today: recall 0, false alarms 0. (B1) flag every line: recall 1, false alarms 1. (B2) digits-only rule (source digits must appear in the normalised translation). (B3) back-translation chrF < τ, τ chosen on dev to match our dev false-alarm rate (the automated Mehandru-style check). **Ours:** fact-level lexicon + back-translation rule.
- **Ablation (cheap):** ours without back-translation (lexicon only). **This is reported as a headline row, because it's fully independent of any translation model.** Also ours without the lexicon (back-translation facts only), and same-model (NLLB) back-translation instead of OPUS-MT.
- **Minimum positives:** we need **≥ 20 broken lines per language** in the test set for a usable recall CI. Two audited systems (NLLB + OPUS-MT) × 75 directions = 150 translations per language. If the probe and dev rates say that's not enough, Teammate A writes extra **multi-clause** directions (harder, never easier) until the expected count reaches 20. The count is stated in the results whatever it turns out to be.
- **Second question for honesty:** do the native-speaker labels agree with chrF? Spearman between sentence chrF (Spanish CA references; Hindi/Marathi references written by the labeller for 20 lines) and the ok/not-ok label.

**Sets:**
- **Dev set (overnight build, labelled "dev" everywhere):** 40 English directions written by the agent from the category list below, NLLB translations into mr/hi/es with back-translations, labelled by the agent (it reads Devanagari; marked `labeller: "agent-dev"`). Used for tuning τ, lexicons and rules. **Never reported as a result.**
- **Frozen test set (Saturday, Teammate A + speakers):** Teammate A writes 60 new English directions from the category list without looking at the dev set (target counts: 10 count/unit, 8 frequency/interval, 8 time-of-day, 6 food, 8 negation, 6 condition/hold, 5 day-of-week, 4 duration, 5 maximum), plus the 15 CA Board directions as a "CA" slice (Spanish has professional references for these). The lead runs NLLB once and saves the translations to `data/test/items.jsonl` **before** any checker run on them. Labels: Marathi + Hindi by a fluent family member (an external labeller, not the code author and not a registered builder), blind to checker output, using a one-page labelling guide ("ok = every number, time, food rule, 'do not', route, condition, day, duration and maximum in the English is said correctly"); **rater 1's labels are the ground truth, full stop.** The lead labels the same items independently, *after* rater 1 has finished, only to compute Cohen's κ. The lead never edits a test label, and disagreements are logged, not resolved. Spanish by a Spanish-reading teammate, anchored on the CA references. Then `sha256sum data/test/items.jsonl > data/test/FROZEN.sha256`, committed. No rule or lexicon changes after the first test run, except a logged "v2" that is re-reported separately.
- **Seeded stress set (secondary):** for 15 correct test translations per language, a speaker hand-writes one corrupted version (change a number, drop the "do not", swap morning/night, swap a day). Hand-written, not generated from our lexicon, to avoid leakage. Reported separately as "stress test", never mixed into the main result.

**Slices (lead with the expected worst):** by language; by fact kind (expected worst: condition/hold and negation in Marathi, because of verb-final negation like "घेऊ नका"); by line complexity (CA-style simple vs multi-clause); by system (NLLB vs frontier-chatbot translations).

**Failure gallery:** three real failures from the test run: input, translation, back-translation, our verdict, the correct reading, and the cause. Expected kinds (assumption): back-translation repairs an error and hides it; a lexicon miss on a synonym (a false alarm); a time word that is ambiguous ("रात्री" night vs bedtime).

**Leakage checks:** no test direction appears in dev (normalised string match + a manual skim); lexicons are frozen before the test run; the test hash is checked by `python -m eval`.

**The one command:** `python -m eval [--split dev|test]` → `results/metrics.json` + `results/metrics.md`. Every number has N, CI and the baseline next to it. The write-up copies from that file only.

**Probe (Nov 13, 11:38 PM CT, after kickoff; research only, not a result):** NLLB-600M on 12 agent-written directions × 3 languages (`docs/research/samples/nllb-probe-12-directions.json`; reading in `docs/research/probe-reading.md`). Agent's reading: clear critical breaks in Marathi 4/12, Hindi 3/12, Spanish 3/12. Dropped second sentences, "hold"→"stop/keep" and puff→"breath" appeared across languages. So positives exist, but **the probe does not show Marathi is clearly worse than Spanish.** That question stays open for the test set. The 12 probe lines may seed the dev set and must never enter the test set.

## 14. Rubric scorecard
| Line | Pts | What the judge will see from us | Self-score now | Biggest risk | Fix |
| --- | --- | --- | --- | --- | --- |
| Technical execution | 30 | `python app.py` works with no download; live NLLB mode; tests; one clean flow | 22 | 2.5 GB model scares a judge or is slow | Cache-first demo, paste mode, clear README "no download needed" |
| Originality | 20 | Fact-level automatic check; Marathi; measured against a back-translation baseline; prior art cited (Mehandru 2023, WMT CED) | 16 | "It's just back-translation" | Show the ablation: lexicon adds recall beyond back-translation |
| Impact + track fit | 20 | Brief's exact words; Riya and Aaji; Martos 2025 statistic; CA list lacks Hindi/Marathi | 17 | Persona feels invented | Real user voice Saturday; one real family tries it (with consent) |
| Testing + honesty | 15 | Per-language tables, N, CIs, three baselines, κ, failure gallery, worst slice first | 12 | Too few positives in test (NLLB too good) → wide CIs | Add OPUS-MT as a second system (more errors); stress set; report CIs plainly |
| Communication | 15 | One-page write-up with the headline number up top; 2-min video | 11 | Too many numbers | One takeaway sentence; one table |
| Finals: demo + clarity | 30 | Live demo with a judge's own line | 24 | Live model slow on a stage laptop | Cached golden inputs; recorded backup |
| Finals: technical depth | 30 | Rules + model split, ablation, leakage checks | 22 | "Why not train a QE model?" | Answer: auditable, data-poor setting; QE is the next week |
| Finals: impact | 20 | Pharmacist/clinic path | 14 | No real-user test | Saturday: one consented family try-out, written up |
| Finals: Q&A | 20 | §19 | 14 | Beginners can't explain the code | §17 explain tasks, `/explain quiz` |

## 15. Risks and premortem
"It's Sunday 9 PM and we lost. Why?"
1. **NLLB makes almost no critical errors on our directions, so the checker has nothing to catch.** (The red team rated this the most likely failure.) Already mitigated: OPUS-MT is a Must audited system, and the ≥ 20-positives rule applies. If the dev set still shows < 10% broken lines → make OPUS-MT the main audited system, keep the seeded stress set, and reframe the headline as "how often each free translator breaks facts". Cut: nothing else.
2. **NLLB too slow or too big on the laptop/judge machine.** Measured in the probe: ~8–11 s per generation (beam 4, padded batch of 12, 8 GB M-series CPU). Plan for it: cache-first demo; beam 2 and ≤ 5 lines per live request; OPUS-MT (300 MB) back-translates fast. If a batch of 3 lines still takes > 30 s → beam 1, cache everything, demo from cache, paste mode as the live path.
3. **Lexicon rules too brittle (many false alarms).** If the dev false-alarm rate is > 30% → lean on back-translation for kinds with poor lexicon coverage; report honestly.
4. **No fluent labeller available Saturday.** If no family member can label by Sat 3 PM → the lead labels blind *before* the checker is run on the test set (hash committed first), report it as a limitation, and add the Spanish teammate's labels as the clean slice.
5. **Beginners blocked; the lead does everything and burns out.** §17 lanes are independent of model code (test-set writing, labelling guide, lexicon review for Spanish, write-up, screenshots, video).
- **Plan B:** Finance, a scam-text filter for older adults tested on modern scams (`docs/research/research-finance.md`). **Switch gate: Sat 10:00 AM CT.** Switch only if NLLB can't run on the team's laptops at all *and* paste mode can't carry the demo. Otherwise commit.

## 16. Build plan
| Milestone | When (CT) | Done when |
| --- | --- | --- |
| M0 Python 3.11 env + model download + repo skeleton | Sat 12:30–1:15 AM (overnight) | `python -c "import transformers"`; NLLB loads |
| M1 Walking skeleton: page → /api/check → cached translation → stub verdict | Sat 1:15–2:30 AM | golden G1 renders end to end |
| M2 Facts + lexicons + verdict v1 + tests | overnight | pytest green |
| M3 Dev set (40) + `python -m eval --split dev` | overnight | `results/metrics.json` labelled dev |
| M4 UI states + polish round 1–2 + screenshots | overnight | `docs/screenshots/` |
| Humans: review, explain-back, test-set writing | Sat 9 AM–1 PM | 60 directions written, frozen translations |
| Labelling (speakers) | Sat 1–5 PM | labels + κ |
| **GATE: full demo flow works** | **Sat 6 PM** | 3 golden inputs + paste mode + test eval runs |
| First test eval | Sat 6–10 PM | metrics table + failure list |
| Harden: top failure modes, OPUS-MT row | Sun 9 AM–1 PM | rerun (logged as v2) |
| **FREEZE** | **Sun 1 PM** | |
| Write-up, video | Sun 1–5 PM | |
| Fresh-clone check, submit | **Sun by 9 PM** | confirmation email |

**Cut list, in order:** OPUS-MT row → seeded stress set → Spanish lexicon (keep Spanish as back-translation-only + CA references) → dark mode → paste-mode line-count helper → chrF-vs-label correlation.

## 17. Team plan (two teammates are beginners)
**Lead (integration, model, rules, Marathi/Hindi lexicons, rater 2).** Reviews every PR, writes explain-backs, owns `samjha/` and `eval/`.

**Teammate A: data and evaluation lane.** Files: `data/test/`, `docs/LABELLING-GUIDE.md`, `samjha/lexicons/spa.json` (review only), `docs/research/voice.md`.
1. Prompt: "Read AGENTS.md, docs/PRD.md §13 and docs/LABELLING-GUIDE.md if it exists. Help me write 60 English medicine directions for the Samjha test set, using the category counts in PRD §13. Don't open data/dev/. Write them to data/test/directions.jsonl as {"id": "t001", "en": "...", "category": "..."}. Ask me to approve each batch of 10. Don't write any code." Done-check: `wc -l data/test/directions.jsonl` = 60, and the lead confirms there is no overlap with dev.
2. Prompt: "Draft docs/LABELLING-GUIDE.md: a one-page guide for a bilingual family member labelling whether a translated medicine direction keeps every critical fact (number, unit, how often, time, food, 'do not', route, condition, day, duration, maximum). Include 5 worked examples using the dev set format but new sentences. Plain words, big headings." Done-check: the lead reads it in 3 minutes and understands.
3. Prompt: "Explain to me, as a beginner, what eval/metrics.py computes: recall, false-alarm rate and the Wilson interval. Use the tiny example in tests/test_metrics.py and walk me through the arithmetic by hand." Done-check: Teammate A explains recall and false alarms to the lead without notes.
4. Spanish labelling (if they read Spanish): label `data/test/items.jsonl` Spanish rows with the guide. Done-check: every es row has `label_ok`.

**Teammate B: story, UI copy and demo lane.** Files: `docs/WRITEUP.md`, `README.md` (copy sections), `static/copy.json` (if used), `docs/screenshots/`, video.
1. Prompt: "Read docs/PRD.md §0, §2, §3, §9 and docs/WRITEUP.md. Tighten the write-up draft to one page in plain words, keeping every number as a placeholder like {recall_mr} unless it's in results/metrics.json. Don't invent statistics." Done-check: `docs/WRITEUP.md` fits one printed page.
2. Prompt: "Using only public posts, help me find 2–3 real posts where someone describes translating medicine instructions for a parent or grandparent. Paraphrase them, remove names, and save them to docs/research/voice.md with links. Never post or log in." Done-check: file has ≥ 2 linked items or says "none found" honestly.
3. Prompt: "Run python app.py, open http://127.0.0.1:8000, click through all three example labels and paste mode, and list every piece of on-screen text that a 16-year-old or a grandparent might find confusing. Suggest clearer wording in a table. Don't change code." Done-check: table in `docs/ui-copy-review.md`; the lead applies the accepted rows.
4. Video: record the §18 script Sunday 2–4 PM with a real voice. Done-check: an unlisted link, under 2:00.

**Everyone, Saturday and Sunday (budgeted 30 min each day):** trace one line end to end (English → facts → NLLB → OPUS-MT back → lexicon check → verdict) out loud, using `/explain quiz samjha/check.py`. Two of three people must be able to defend the core in finals.

**What each person must be able to explain to a judge:** Lead: everything, especially the verdict rule and why back-translation alone isn't enough. A: how the test set was made, who labelled it, why it's frozen, and recall vs false alarms. B: who Riya is, the Martos statistic, what Samjha never says, and one failure.

## 18. Demo and video script (2:00)
| Time | Says | Shows |
| --- | --- | --- |
| 0:00–0:15 | "Free translators get medicine directions wrong far more often in some languages than others. In one 2025 study, 7% of Spanish sections had clinically important errors and 92% of Somali ones. Marathi isn't even on California's list of translated labels." | Title, then the Martos numbers as one bar row |
| 0:15–0:25 | "Riya fills her grandmother's pill box every Sunday. She speaks Marathi but can't really read it, so she can't check the translation she copies." | The persona card, then the Samjha screen |
| 0:25–1:05 | Live demo: paste Aaji's three insulin-label lines, pick Marathi, check. "Two lines keep every fact. This one doesn't: English says *before* breakfast, and the translation says something else. Samjha says don't rely on it, ask the pharmacist." Open Why?, then paste her phone's version: green. | Real screen, cursor, cards cascading |
| 1:05–1:35 | "We wrote 60 new directions, translated them with Meta's free NLLB model, and had a native speaker check every one. NLLB broke a fact in {err_mr} of Marathi lines vs {err_es} of Spanish. Samjha caught {recall_mr} of the broken Marathi lines, with {fa_mr} false alarms; a back-translation score caught {recall_b3_mr}." | `results/metrics.md` table, worst slice highlighted |
| 1:35–1:50 | "Where it fails: {failure_1}." | Failure gallery card |
| 1:50–2:00 | "Next: more languages, real pharmacies, and a pharmacist study. Samjha is a prototype, not medical advice." | Footer with disclaimer |

Numbers in braces are filled from `results/metrics.json` only.

## 19. Finals Q&A prep
1. **Why not just use ChatGPT?** It translates well (8/8 in our test), but families use whatever translation they have, and nothing tells them which line is wrong. Samjha audits any translation. We also audited chatbot translations: row {chatbot_row}.
2. **Why NLLB-600M?** The brief names it, it's free and local, covers all three languages both ways, and runs on a laptop. Bigger NLLB is a planned ablation.
3. **Why rules for the verdict, not a model?** It's a safety decision with little labelled data. Rules are auditable, and a native speaker can read and fix every lexicon entry. A learned QE model (e.g. CometKiwi) is gated, non-commercial and would be a black box.
4. **What's your baseline?** Trust-all, flag-all, digits-only, and back-translation chrF with a threshold tuned on dev (the automated version of Mehandru et al. 2023).
5. **How was ground truth built?** 60 directions written by a teammate who didn't write the code; translations frozen before the checker ran; labelled by a fluent family member blind to our output; second rater; κ = {kappa}.
6. **Where does it fail?** {worst slice}; back-translation with the same model can repair an error and hide it; lexicon synonyms cause false alarms.
7. **Leakage?** Dev and test written by different people; string-overlap check; lexicons frozen before the test run; test file hashed.
8. **Your N is small. Is the result meaningful?** We report Wilson CIs; the claim is the per-language gap and the recall difference vs the baseline, not a precise rate.
9. **What happens off-list?** "Couldn't check", never green. We don't vouch for what we can't parse.
10. **Same model both ways? Rules tuned by the lexicon author?** The test translations were produced and frozen before the checker ran; labels came from a fluent person blind to the checker; back-translation uses a different model (OPUS-MT); the lexicon-only row doesn't use back-translation at all; stress corruptions were hand-written by a speaker, not generated from our lexicon; the chatbot and OPUS-MT translations come from systems the rules were never tuned on. Limits: small N, one native labeller.
11. **Another week?** A pharmacist study; more languages (Gujarati, Punjabi, Bengali); a second back-translator to break the same-model blind spot; photo input; a learned QE score as one more signal, measured against the rules.

## 20. Open questions for the humans (ranked; each with our default)
1. **Who can label Marathi and Hindi Saturday (a fluent reader who didn't write the code)?** Default: a parent or grandparent of the lead, with consent; the lead as rater 2.
2. **Does a teammate read Spanish?** Default: yes for one teammate; otherwise Spanish is labelled against the 15 CA professional translations only and reported as N=15.
3. **Is the CA Board phrase use OK?** Default: store the 15 short phrase pairs with attribution as evaluation data; don't redistribute the PDF.
4. **Teammate names and lanes:** Default: Teammate A = data/eval, Teammate B = story/UI as in §17.
5. **Name "Samjha":** Default keep. Alternative: "LabelCheck".
6. **Real user voice:** none found tonight; Teammate B searches Saturday.
7. **A real family try-out (with consent):** Default: one session Sunday morning, notes only, no recording.
- P1 (probe note): see `docs/research/probe-reading.md`. The lead should re-read the 36 probe lines as a native speaker on Saturday morning (10 min) and correct the agent's reading.

### Red-team review (Nov 13 23:35 CT, fresh Sonnet subagent as a sceptical ML judge): what we changed and what's still open
- Fixed: the pitch no longer claims Marathi is worse before measuring; v1 is cut to 7 fact kinds + a sentence-count check ("hold" added after the probe); back-translation by a different model (OPUS-MT); OPUS-MT promoted to Must; ≥ 20 positives per language; rater-1 labels are ground truth and the lead labels only for κ, after rater 1; "Facts match" renamed "Key facts found"; the stress set cut to 15 per language; chatbot rows read from a saved file; N shown beside every on-screen number; a 30-min daily explain drill for everyone.
- Unresolved: (a) the persona is illustrative and no real user voice has been found yet (Teammate B, Saturday); (b) one native labeller per language is a single point of failure (open question 1); (c) the dev set is agent-written and agent-labelled, a weak proxy for tuning, which we state openly; (d) the red team suggested one polish round, but we keep two because the Phase B goal requires them.

## 21. Credits
Inspiration and prior art: Google Translate; Mehandru et al., EMNLP 2023 (arXiv 2310.16924); Martos et al., JAMA Netw Open 2025; Khoong et al., JAMA Intern Med 2019; California Board of Pharmacy translated directions; RxTran (Language Scientific); WMT Critical Error Detection tasks. Data: FLORES-200 (Meta, CC-BY-SA 4.0); test labels by an external volunteer labeller (credited by role, not as a builder); CA Board of Pharmacy translations (© State of California). Models: facebook/nllb-200-distilled-600M (Meta, CC-BY-NC 4.0); Helsinki-NLP OPUS-MT (Apache-2.0). Libraries: transformers, torch, sentencepiece, sacrebleu, FastAPI, uvicorn, pytest. Fonts: Noto Sans Devanagari (OFL). AI tools: Claude Code (Opus 5.5 overnight planning and build, Sonnet/Haiku 5.5 subagents for research), plus a Claude Sonnet 5.5 subagent as the chatbot baseline. All logged in `docs/AI-USAGE-LOG.md`.
