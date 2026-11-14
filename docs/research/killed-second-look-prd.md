# PRD: Second Look

Status: v2.1 · built overnight Sat Nov 14 00:00–00:40 CT (see §22 for where the build differs from this plan) · written Fri Nov 13, 11:50–11:58 PM CT · brief received Fri Nov 13, 10:47 PM CT · track: **AI + Finance**
Every claim has a source link or says "assumption". Every number has its N or says "not measured yet". Research lives in `docs/research/`.

## 0. The pitch
- **One sentence:** Second Look tells an older adult, in big plain words, whether a text message looks like a scam, shows the tricks it spotted inside her own message, and hands her a safe next step and a one-tap "ask Ana", using a free model that runs on her own device.
- **The sentence a judge repeats to another judge:** "They trained a scam filter on old texts, proved on real 2022–24 scams how much it misses, fixed it, and measured how often it would wrongly flag grandma's real bank and pharmacy texts."
- **Why this wins (three lines):**
  1. It obeys the Finance brief literally: beats a simple rule, precision and recall not accuracy, **trained on earlier data and tested on later data** (dated, real, user-reported scams: IMC'25, CC BY 4.0).
  2. It adds all three kinds of "make it your own" (own user, own data, own question) plus the checks a researcher would ask for: a duplicate audit (the 2022 Mendeley set reuses UCI 2012 texts heavily: 4,380 of its 4,844 legit rows match after normalising, `docs/research/samples/uci-mendeley-overlap.txt`), an era-shortcut control, and a fairness check on the texts older adults depend on.
  3. Older adults and their caregivers are the Gold sponsor's users (Arecibo AI), and the demo takes 20 seconds with any text a judge types.

## 1. The brief and track fit
Lines from `docs/BRIEF.md` we answer, and how:

| Brief says | We do |
| --- | --- |
| "Build an AI tool that helps a person … make a safer or fairer money decision, and show that it beats a simple rule." | The decision is "tap/pay/reply, or check first". We beat a keyword + link rule (what paid blockers do) and report both |
| "Compare your model with at least one simple baseline and report both results." | Four baselines: majority, keyword rule, the brief's own tutorial model (UCI-only TF-IDF), a frontier chatbot on a sample |
| "For rare events such as fraud, report precision and recall rather than accuracy." | Recall, false-alarm rate, precision, PR-AUC, each with N and Wilson 95% CI |
| "If your data has dates, train on earlier data and test on later data." | Train ≤ 2021, test 2022–2024 (IMC'25 dated rows) |
| "This project is a prototype and is not financial advice." | On the screen footer and in the write-up |
| Judges: "whether you chose the right measure of success … compared … fairly … whether a real person could trust your tool enough to act on it. Teams that check for unfair treatment of a group, even when age or gender isn't a direct input, really stand out." | Our own question: false alarms on the texts older adults rely on (bank fraud alerts, one-time codes, pharmacy, clinic, Medicare, delivery) vs everyday personal texts. Three bands so it says "ask someone" instead of guessing |
| 4.2.1 "Make it your own": "Collect or write examples of scams that are common … today", "Have your filter explain why it flagged a message", "Design for a specific user, such as an elderly relative, and test the tool with them." | All three: modern dated scams, a learned tactic tagger with highlighted words, Dolores + a consented user test (notes only) |
| §3 "Where does it fail? Show at least one example your model gets wrong" | A failure gallery of 3 real test-set errors |
| "AI must be central." | Both the verdict and the "why" are learned models; no LLM, no lookup |
| Hacker Guide mistake: "Reusing a tutorial dataset without asking a new question of it" | Our question is new: does the filter still work on later scams, and who does it wrongly flag? |

**Why Finance over the others** (from `docs/research/track-triage.md`, weighted out of 55): Finance 49, Health 41, Climate 37. Languages excluded by the owner. Health's best idea (HeatRx) is mostly lookup + rules, which fails "AI must be central", with no public ground truth and close prior art (Leeward). Climate has the weakest sponsor fit and a demo that's a number for tomorrow, against official forecasts we can't beat.

## 2. Problem
- **Statistic:** "In 2024, people reported $470 million in losses to these scams, more than five times the 2020 number." FTC Data Spotlight, *Top text scams of 2024*, Apr 14 2025, https://www.ftc.gov/news-events/data-visualizations/data-spotlight/2025/04/top-text-scams-2024 (opened by scout Nov 13 2026; re-open to confirm wording before the write-up). The same page's top five: fake package delivery, phony jobs, fake fraud alerts, bogus toll notices, "wrong number" texts.
- **Why filters miss:** a 2026 study of 175,430 Reddit-reported messaging scams (Jun 2020–Dec 2025) reports reply-based scams growing at a 99.98% compound annual rate vs 57.29% for click-based, and "reply-based scams also show the lowest detector performance" (Lu, Medeiros, Butler, Traynor, https://www.alphaxiv.org/abs/2605.16656, opened via alphaxiv; check the arXiv original before citing).
- **Voice of the user** (Aside browser, read-only; full list with links in `docs/research/voice-second-look.md`):
  - Families' best defence is a rule, not an app: a parent is asked to call family before paying anything; top reply "one rule beats every tool" (r/TechForAgingParents, 2026-11-01).
  - A mother "gets a scam attempt about every other month" and is upset enough to cry explaining them (X, 2026-05-04).
  - Real texts get buried too: a carrier blocks the bank's login-code texts (X, 2026-11-12); patient reminder texts silently filtered so patients miss appointments (X, 2026-11-09); Truecaller blocked Costco customer service (App Store 2★, 2026-10-30).
  - Keyword blockers decay: "worked for a few weeks, then stopped" (Dont Text, 1★, 2026-01-07); spam returns after months (Textkiller 1★, RoboKiller 1★, 2026).

## 3. Who it's for
**Dolores, 77**, widowed, lives alone in Mesa, Arizona. iPhone, large text setting on. Gets a few odd texts a week (assumption; the kinds match the FTC's 2024 top five: toll notices, "your package is on hold", "Hi, is this Linda?"). Her daughter **Ana, 44**, a hospital shift worker, set a family rule: "forward it to me before you tap anything". Ana often answers hours later; by then Dolores has either worried all afternoon or tapped. Assumption: illustrative persona, not a real person.

**The moment:** 2:10 PM on a Tuesday, a text: "E-ZPass: You have an unpaid toll balance of $6.99. Pay now to avoid a $50 late fee." Dolores did drive to Tucson last month. She opens Second Look from her home screen, pastes, taps Check. Big answer: **Looks like a scam.** "Rushes you", "Threatens a fee", "Has a link" are highlighted in her own message. "Don't tap the link. If you're worried, call E-ZPass using the number on your statement." One button: **Send to Ana**.

**What she does today instead:** forwards to Ana and waits, or asks a chatbot (which hedges at 55–80% confidence on real bank and pharmacy texts; `docs/research/chatbot-test-scam.md`), or pays a blocker ~$100/year that sorts messages silently.

## 4. What already exists (teardown summary)

| Product | Link | Why people use it | Price | Biggest weakness | Evidence |
| --- | --- | --- | --- | --- | --- |
| Google Messages scam detection (Gemini) | droid-life Oct 14 2026 | Built in, zero effort | Free (Android) | Android only; no published accuracy; no "why" a person can learn from | `teardown-google-messages-scam.md` |
| Bitdefender Scamio | bitdefender.com | Paste anything, get a verdict | Free with signup | Chat wrapper; reviewers say verdict without reason; no accuracy | `teardown-scamio.md` |
| RoboKiller | App Store id1022831885 · 4.50★ (414,654) | Set-and-forget blocking | Trial then ~$100/yr (reviewer) | Silent; decays; billing traps | `teardown-spam-blockers.md` |
| Truecaller | App Store id448142450 · 4.45★ (253,024) | Caller ID + spam | Freemium | False alarms (blocked Costco) | `teardown-spam-blockers.md` |
| Textkiller | App Store id1514005355 · 4.31★ (12,999) | Keyword/sender filtering | Subscription | Keyword rules leak and decay | `teardown-spam-blockers.md` |
| A frontier chatbot | — | Free, smart | Free/paid | Anecdote only (12-text smoke test, not a measurement): 11/12, missed the "wrong number" opener, 55–80% confidence on legit look-alikes; your private texts go to a cloud | `chatbot-test-scam.md` |

- **We rebuild from** the paid keyword blockers (their method is our "simple rule" baseline) and the paste-a-text checkers (Scamio, chatbots: their UX is our flow). Those are the two things families already use.
- **Past projects:** GitHub has many TF-IDF smishing detectors (e.g. SimeonMataka/Smishing-Detection-System, IsaacFigNewton/Smishing-Detector; `gh search repos "smishing detection"`, Nov 13 2026), the ones we looked at train and test on a random split of old data. `gh search repos "scam text elderly"` returned nothing. In what we searched (two GitHub queries, Nov 13), we found none that test on later data, check false alarms on look-alike legit texts, or audit duplicates. That's a limited search, not proof none exist; Phase B adds a Devpost check.

## 5. What we build differently
- **Keep:** paste a text → one verdict (the 10% that delivers value).
- **Cut:** blocking, number lookups, accounts, subscriptions, inbox access, URL reputation services.
- **Add (each measured):**
  1. **Dated training and testing:** trained on texts up to 2021, tested on real scams reported in 2022–2024. We report how much the brief's own tutorial model (trained on 2012 data) misses.
  2. **Three bands instead of silent blocking:** "Looks like a scam", "Ask someone first", "No scam signs found". The middle band routes to the family rule people already trust.
  3. **The why, learned and shown:** a tactic tagger trained on IMC'25's lure labels highlights the exact words ("rushes you", "pretends to be a company", "money or a fee", "asks you to reply", "has a link"). Measured per tactic.
  4. **The look-alike legit check:** how often it wrongly flags real-style bank alerts, codes, pharmacy, clinic, Medicare and delivery texts.
  5. **Leakage audit:** de-duplication across sources, with the number of duplicates removed reported.
- **Why would Dolores use ours instead of the original?** It answers in words she can read, tells her what in the message is the trick so she gets better at spotting it, never hides her pharmacy text in a junk folder, costs nothing, needs no account, and makes no network calls, so her messages don't go to a company. (The prototype is a local web page on a computer, not a phone app yet.) When it isn't sure, it says so and helps her ask Ana in one tap.
- **Who will care:** Dolores (fewer losses, less worry), Ana (fewer midnight "is this real?" texts, a reason she can check), clinics and banks (their real texts get read), judges (an honest, dated evaluation with failures shown).
- **Free in ours, paid elsewhere:** filtering itself (RoboKiller charges after a trial). We can offer it because the training data is public (UCI CC BY 4.0, IMC'25 CC BY 4.0, Mendeley CC BY 4.0) and the model is a few MB of scikit-learn running locally.

## 6. Does this need AI?

| Step | Lookup / rules / model | Why |
| --- | --- | --- |
| Clean the text (placeholders for links, phones) | Rules | Same treatment for every source prevents leakage; regex is auditable |
| Scam score 0–1 | **Model** (TF-IDF word 1–2-grams + char 3–5-grams → logistic regression) | Scams change wording constantly; a fixed keyword list decays (reviews). A learned model generalises across phrasings and gives coefficients we can show |
| Band | Rules on the score | Thresholds fixed on dev, written in `models/thresholds.json`. **Safety floor:** if the tagger finds "asks you to reply or chat" or a request for a code/money, the band is at least "Ask someone first", because reply-bait is the expected worst slice and "No scam signs found" must not land on it. The floor is measured as an ablation (with vs without) |
| Tactics + highlighted words | **Model** (one-vs-rest logistic regression on IMC'25 `lure_principles`, mapped to 4 plain tactics) + pattern spans for "has a link" / money amount | The learned part says which trick; the highlight shows the words with the biggest positive coefficients for that tactic |
| What to do now | Fixed templates | Safety copy must never be generated |

- **Model judges see:** a classifier (predicts scam vs legit) and a multi-label tagger (classifies tactics). Cheapest that works: no GPU, no torch at runtime, millisecond inference, inspectable weights. Comparison model: `sentence-transformers/all-MiniLM-L6-v2` embeddings + LR (Apache-2.0), eval only; we switch only if it's better on **dev** by a margin outside the CI.
- **No-AI baseline:** keyword + link rule (link or phone AND any of urgency/money/authority words from a list we write before seeing test data). **Brief's tutorial baseline:** same TF-IDF + LR trained on UCI 2012 only. **Chatbot baseline:** a Claude subagent labels a 200-message stratified test sample once; transcript saved to `results/chatbot_baseline.jsonl`.
- **What ours does that they can't, measurably:** higher recall on later scams than the keyword rule and the tutorial model at a false-alarm rate on look-alike legit texts we state; tactic tags with measured F1; runs offline at $0. Versus the chatbot: we expect it to be strong; our claim is "within X points at zero cost and with no message leaving the device", only if the numbers show it.
- **"LLMs format, rules decide":** there is no LLM at runtime. The band is a rule on a measured model's score; the advice is a template.

## 7. The core flow (5 steps, each visible in the demo)
1. Paste a text into the big box (or tap a sample chip: "Toll notice", "Bank alert", "Hi, is this Linda?").
2. Tap **Check** (Enter also works).
3. The answer band appears in big type with an icon and word (never colour alone).
4. The message re-renders with the tactic words highlighted; chips list the tactics in plain words.
5. "What to do now" (2–3 fixed lines) and **Send to Ana** (copies "Mom checked this text with Second Look: it says *Looks like a scam* because it rushes you and has a link. Can you look? [message]").

- **60-second test (script):** "Dolores gets this toll text [paste]. She taps Check. Big red-brown 'Looks like a scam'. It shows why: these words rush her, this one threatens a fee, there's a link. It tells her not to tap and how to check safely. One tap sends it to her daughter. Now a real Chase fraud alert: 'Ask someone first', not 'scam'; it doesn't bury her bank. Now you type one."
- **Interactive moment:** the judge types any text; the answer and highlights update.
- **Three golden-path inputs** (synthetic, in `demo_cache/golden.json`): (1) E-ZPass toll with link → scam; (2) Chase-style fraud alert "Reply YES or NO" → expected ask/no-signs (shows false-alarm care); (3) "Hi, is this Linda? It's Karen from the book club" → whatever the model says; if it misses, it becomes our honest failure on screen.

## 8. Features

| Feature | Must / Should / Won't | Rubric line it moves | Done-check |
| --- | --- | --- | --- |
| `data.py`: download, normalise, de-duplicate, dated split | Must | Technical 30, Testing 15 | `python -m secondlook.data` prints counts per split + duplicates removed |
| Scam model + thresholds | Must | Technical 30 | `python -m secondlook.model` writes `models/scam.joblib` + `models/thresholds.json` |
| Tactic tagger + highlight spans | Must | Originality 20, Comms 15 | `tactics("Pay now…")` returns ≥1 tactic with spans |
| One-screen app (`app.py`, `static/`) | Must | Technical 30, Demo 30 | `python app.py` → page works offline; `smoke_test.py` passes < 60 s |
| `python -m eval` with 5 baselines (incl. style-only), slices, CIs, era controls | Must | Testing 15, Depth 30 | writes `results/metrics.json`, `metrics.md`, `failures.md` |
| Modern synthetic legit set (AI-written, labelled "synthetic, train/dev only", logged in AI-USAGE-LOG) | Must | Testing 15 | `data/train/modern_legit_synthetic.jsonl` ~300 rows, each with a format source URL |
| Frozen test set (look-alike legit by Teammates A + B, test-A/test-B halves) | Must (Saturday) | Testing 15 | `data/test/MANIFEST.txt` hash committed before first test run |
| Send to Ana (copy to clipboard) | Must | Impact 20 | button copies text; works without clipboard permission fallback (select-all text box) |
| Chatbot baseline on 200-sample | Should | Testing 15, Q&A 20 | `results/chatbot_baseline.jsonl` + transcript |
| MiniLM embedding comparison (ablation) | Should | Depth 30 | row in metrics table |
| "How we know" panel (N, recall, false alarms from `results/metrics.json`) | Should | Comms 15 | panel numbers match file |
| Consented user test with a teammate's grandparent (notes only, synthetic texts) | Should | Impact 20 | `docs/user-test.md` |
| Colab notebook that imports the modules and shows eval | Should | Technical 30 | runs top to bottom on fresh runtime |
| Share-sheet / iOS shortcut, inbox reading, other languages, URL lookups | Won't | — | — |

## 9. Design and UX spec
**Screen list:** one screen (`static/index.html`). Desktop: two columns (left: input; right: result). Phone (≤ 640 px): stacked, result scrolls into view.

**Components and state tables (exact copy):**

*Input card*
| State | Copy / behaviour |
| --- | --- |
| Idle | Label "Paste the text message you're not sure about". Placeholder "For example: USPS: Your package is on hold…". Chips: "Toll notice" · "Bank alert" · "Hi, is this Linda?". Button **Check this text** |
| Empty submit | Inline under box: "Paste a message first, or tap one of the examples." Box gets focus |
| Too long (> 1,000 chars) | "That's longer than a text message. We'll check the first 1,000 characters." |
| Loading (> 150 ms only) | Button label "Checking…", button disabled; no spinner flash for fast responses |

*Result card*
| State | Copy |
| --- | --- |
| Before first check | "Your answer will show here. Second Look makes no network calls: your text stays on this computer." |
| Band: scam | Icon ⚠ + **"Looks like a scam"** · sub: "This message uses tricks scammers use." |
| Band: ask | Icon ? + **"Ask someone first"** · sub: "Some signs worry us, but real companies send texts like this too." |
| Band: no signs | Icon ○ + **"No scam signs found"** · sub: "That doesn't make it safe. Never pay or share a code because of a text." |
| Tactic chips | "Rushes you" · "Pretends to be a company or agency" · "Money, a prize or a fee" · "Asks you to reply or chat" · "Has a link" · "Has a phone number to call" |
| What to do now (scam) | "Don't tap the link or reply." · "If you're worried, contact the company using the number on your card, bill or their official website." · "Delete the text." |
| What to do now (ask) | "Don't tap anything yet." · "Ask someone you trust to look at it." · "Check by calling the number on your card or statement, not the one in the text." |
| What to do now (no signs) | "If it asks for money or a code, stop and ask someone." |
| Send button | **Send to Ana** (persona name configurable in one constant); after tap: "Copied. Paste it in your message to Ana." |
| Score line (small) | "Scam score 0.93 · model trained on texts up to 2021 · How we know →" |
| Error (server down) | "Something went wrong on our side. Your text wasn't sent anywhere. Try again." |
| Garbage input (no letters) | "We couldn't read words in that. Paste the text of the message." |

**Footer (always visible):** "Prototype, not financial advice. It can be wrong. Never pay or share a code because of a text."

**Token plan:**
- Palette (CSS variables, light + dark): `--bg #FAF8F5`, `--surface #FFFFFF`, `--ink #1C1B1A`, `--ink-2 #55514C`, `--line #E6E1DA`, `--scam #B3261E` (on `--scam-bg #FCEDEB`), `--ask #8A5A00` (on `--ask-bg #FFF4DC`), `--clear #2E6B3F` (on `--clear-bg #EAF4EC`), `--focus #1F5FBF`, highlight `--hl #FFE08A`. Every pair ≥ 4.5:1 contrast; verify with the component-craft audit. Dark mode mirrors with `--bg #141312`.
- Type: system stack (`-apple-system, "Segoe UI", Roboto, sans-serif`); base **20 px**/1.5 (older readers); scale 16 / 20 / 24 / 32 / 44; band headline 44/1.1 weight 700; tabular numbers for the score.
- Spacing unit 8 px (8/16/24/32/48). Radii: cards 16, chips 999, buttons 12. Touch targets ≥ 48 px.
- Motion: result card enters with opacity 0→1 + translateY 8→0, 220 ms `cubic-bezier(0.2, 0.8, 0.2, 1)`; highlights fade in staggered 40 ms each (max 6); button press scale 0.98 for 100 ms. `prefers-reduced-motion`: no transforms, opacity only, 0 stagger.

**Reference patterns (pattern and measurement only, never copied source):** status/verdict card anatomy (icon + headline + one-line reason + actions) from aisdkagents.com/ai-components and affectui.com/components; chip rows from useplanes.com/components; inline highlight treatment from uiarc.dev/components. Apply the bundled `component-craft`, `emil-design-eng` and `apple-design` rules for press states and motion.

**The one orchestrated moment:** band headline appears first, then the highlights light up in the message one by one, then the advice. It teaches the "why" in order.

**Trust display:** every verdict shows the highlighted words, the score, the training cut-off ("trained on texts up to 2021") and a "How we know" link with the test N, recall and false-alarm rate from `results/metrics.json`.

## 10. Architecture
- **Stack:** Python 3.11, scikit-learn, joblib, FastAPI + uvicorn, one static page (HTML + CSS + vanilla JS). No torch in the app's `requirements.txt` (MiniLM comparison lives in `requirements-eval-extra.txt`). Judge runs `pip install -r requirements.txt && python app.py` in < 5 min with no keys; trained model and processed splits are committed.
- **Repo layout:** `secondlook/{data,model,tactics,advice}.py` · `app.py` · `static/{index.html,style.css,app.js}` · `eval/{__main__,metrics,baselines}.py` · `data/raw/` (downloaded once; IMC'25 9.5 MB, UCI, Mendeley; committed with credits since all are CC BY 4.0) · `data/{train,dev,test}/` · `models/` · `results/` · `demo_cache/golden.json` · `smoke_test.py` · `tests/`.

| Module | Owner | Inputs → outputs | Done-check |
| --- | --- | --- | --- |
| `secondlook/data.py` | Lead | raw files → rows `{"id","text","label","source","year","scam_type","tactics","category"}`; `normalise(text) -> str`; `dedupe(rows) -> (rows, n_removed)`; `split(rows) -> {"train","dev","test_candidates"}` | counts printed; no normalised text appears in two splits (assert) |
| `secondlook/model.py` | Lead | `train(rows) -> Pipeline`; `score(text) -> float`; `band(p) -> str` | `models/scam.joblib` loads in < 1 s; `score("hi mom")` < `score(golden toll)` |
| `secondlook/tactics.py` | Lead | `tactics(text) -> [{"tactic","label","score","spans"}]` | unit tests for link/money span patterns |
| `secondlook/advice.py` | B (copy), Lead | `advice(band, tactic_ids) -> [str]` | copy matches §9 table |
| `app.py` | Lead | `POST /api/check {"text"}` → `{"band","score","tactics","advice","model","share_text"}`; `GET /api/metrics` → summary from `results/metrics.json` | `smoke_test.py` |
| `eval/` | Lead (metric code), A (test data) | splits → `results/metrics.json`, `metrics.md`, `failures.md` | metric code unit-tested on a hand-computed 6-row example |

- **Data flow:** text → `normalise` → `model.score` → `band` (thresholds.json) → `tactics` (tagger + spans) → `advice` templates → JSON → page renders band, highlights, advice, share text.
- **Caching / no-key mode:** no runtime network calls at all. `data.py` downloads once with a 30 s timeout and one retry, then reads `data/raw/`; if download fails it uses the committed copy and prints which. `demo_cache/golden.json` holds the three golden inputs and their expected outputs for the smoke test.

## 11. Data, models, licences

| Source | Use | Licence | Key? | Hit once and cached? |
| --- | --- | --- | --- | --- |
| UCI SMS Spam Collection (5,574: 4,827 ham / 747 spam; ~2011–12), https://archive.ics.uci.edu/dataset/228/sms+spam+collection, HF `ucirvine/sms_spam` parquet | Train (era 2012); held-out ham slice "everyday personal texts" | CC BY 4.0 (UCI page, checked 11:53 PM CT) | No | Yes: parquet fetched to scratchpad tonight; `samples/hf-sms-spam.json` |
| IMC'25 "Fishing for Smishing" (Agarwal et al., ACM IMC 2025, doi 10.1145/3730567.3764431), https://github.com/reportsmishing/Smishing-Dataset-IMC25 | Train scams ≤ 2021; **test scams 2022–24**; tactic labels | CC BY 4.0 (GitHub) | No | Yes: full CSV fetched (33,869 rows; 22,078 English); profile in `samples/imc25-profile.txt`, sample `samples/imc25-fishing-for-smishing-sample.csv` |
| Mendeley SMS Phishing Dataset (Mishra & Soni 2022), https://data.mendeley.com/datasets/f45bkkt8pr/1 | Second-source test after de-duplication | CC BY 4.0 | No | Yes: `samples/mendeley-sms-phishing-sample.csv`; overlap in `samples/uci-mendeley-overlap.txt` |
| Look-alike legit set (ours, Saturday) | Test slice "texts older adults rely on" | Ours (synthetic, from public official formats; each row cites its format source URL) | — | — |
| scikit-learn, FastAPI, uvicorn, joblib | Model + app | BSD / MIT | — | — |
| sentence-transformers/all-MiniLM-L6-v2 | Eval-only comparison | Apache-2.0 | No | Not yet (Phase B) |

Dated-data facts (English IMC'25 rows with a year in the `time` field; `samples/imc25-profile.txt`): 2012–16: 13 · 2017: 123 · 2018: 168 · 2019: 287 · 2020: 556 · 2021: 805 · 2022: 762 · 2023: 480 · 2024: 8 · none: 18,876. So **train-period dated scams ≈ 1,952, test-period ≈ 1,250**. The year is parsed from a free-text field; Phase B must spot-check 30 parsed dates by eye and report the parse rule.

## 12. Safety and honesty rules
- **Never "safe".** The lowest band is "No scam signs found" with "That doesn't make it safe."
- Advice is fixed templates; it never tells anyone to pay, reply, call a number from the message, or share a code.
- Public or synthetic data only. The look-alike set is written from public message formats with made-up numbers (555 phone numbers, fake order IDs). No one's real texts. The user test uses synthetic texts and records notes only, with the participant's and a parent's consent.
- Every number comes from `python -m eval`. Dev numbers are labelled "dev set, N=…" until the test run.
- **Known limits we'll state openly:** no public, licensed, post-2018 real legit SMS set exists that we could find (scout check Nov 13, 11:57 PM CT: ExAIS_SMS has no licence; the 2024 IEEE Access "Super SMS" set couldn't be verified), so modern legit training text is synthetic and modern legit test text is written by two teammates; English only; masked text in IMC'25 (links/phones replaced) means we can't learn from domains; user-reported scams over-represent the scams people notice; legit texts are 2012-era plus our look-alike set, so era can be a shortcut (we test it); no live phone integration.

## 13. Evaluation plan
_v2 after the red team (Nov 13, 11:57 PM CT). The red team's main point holds: if nearly all legit text is from 2012 and all scams are 2017–24, the model can learn "era / source / masking style" instead of "scam", and recall will look high for the wrong reason. This plan is built to expose that, not hide it._

- **Headline metrics (why they matter for Dolores), all with N and Wilson 95% CI:**
  - *Recall* on 2022–24 scams = share that get "Looks like a scam" or "Ask someone first" (a miss can cost her money).
  - *Legit texts flagged* = share of **modern** legit texts (look-alike set) that get "scam" **or** "ask". This is the headline false-alarm number, printed next to recall, so the middle band can't hide false alarms.
  - Also reported: *hard false alarms* (legit → "scam" only), precision at each band, PR-AUC, and the full band distribution per slice.
- **Thresholds:** fixed on dev only and written to `models/thresholds.json` before any test run. `t_low` = highest threshold with dev recall ≥ 0.95; `t_high` = lowest threshold with ≤ 5% of dev modern legit in "scam". If `t_low > t_high`, use one threshold. The reply-bait safety floor (§6) is on in the headline and reported off as an ablation.
- **Baselines:** (B0) always "legit"; (B1) keyword + link rule, word list committed before any test run; (B2) the brief's tutorial: TF-IDF + LR trained on UCI only; (B3) chatbot on a 200-message stratified test sample: a fresh subagent sees **only the message text** (no labels, no repo), transcript saved to `results/chatbot_baseline.jsonl`. Ours: (M1) TF-IDF + LR; (M2, Should) MiniLM + LR.
- **Normalisation (same for every source and for user input):** lowercase; URLs → `<url>`; phone numbers → `<phone>`; IMC'25 `<NAMED_ENTITY>` removed; digits → `0`; whitespace collapsed. Unit-tested.
- **De-duplication:** exact match on normalised text, then **near-duplicates**: TF-IDF char 3–5-gram cosine ≥ 0.9 between any test row and any train/dev row (sparse matrix product; no new dependency) → drop from test. Report both counts in `results/metrics.json` (this is where the Mendeley/UCI overlap number comes from, regenerated by code).
- **Modern legit text in training (the fix for the era shortcut):** `data/train/modern_legit_synthetic.jsonl`, ~300 legit transactional texts (bank alerts, codes, pharmacy, clinic, delivery, utility, school, family) written by the overnight build from public official formats, clearly labelled **synthetic, AI-written, train/dev only** and logged in `docs/AI-USAGE-LOG.md`. Plus any real modern public ham the scout finds (`docs/research/` note). Never in test.
- **Splits:**
  - *Train:* UCI (minus a 20% random ham hold-out) + IMC'25 English dated ≤ 2021 + modern synthetic legit (80%).
  - *Dev:* 15% random of train-period scams/ham + modern synthetic legit (20%). All tuning, threshold picking and Sunday fixes use dev only.
  - *Test (frozen Saturday, SHA-256 in `data/test/MANIFEST.txt`), split in two halves by a fixed seed:* **test-A** (run Saturday night: diagnostics, slices, failure gallery) and **test-B** (run **once**, Sunday after the fixes, for the headline). Any fix made after looking at test-A failures is reported as such, and test-B is the number we quote.
  - Test contents: IMC'25 English dated 2022–24 (~1,250 scams before de-dup) · look-alike legit (~200, see below) · UCI 20% held-out ham ("everyday 2012 texts": reported but **not** the headline, since it matches the training era) · Mendeley rows that survive de-dup (second-source slice).
- **Look-alike legit test set (~200 rows, two authors):** Teammate A writes ~100 and Teammate B writes ~100, each from public official message formats (each row cites its format source URL; made-up 555 numbers and order IDs). Each blind-checks the other's rows ("could this be a real message from that company? yes/no"); disagreements are logged and dropped, never edited. Neither is a code author; the lead never writes or edits test rows. With N ≈ 200, 0 flagged would still have a Wilson upper bound ≈ 1.9%; we print the interval.
- **Era-shortcut controls (the red team's requirement):** (1) train with modern synthetic legit vs without it, and compare "legit flagged" on the look-alike test; (2) a style-only model (length, uppercase ratio, digit ratio, has `<url>`, has `<phone>`) as an extra baseline: if it scores close to M1, the task is being solved by style; (3) report false alarms on 2012 ham vs modern look-alikes side by side.
- **Slices (lead with the expected worst):** recall by `scam_type` (expect worst: "wrong number" and "hey mum/dad", small N, CI shown); legit flagged by category (bank alert, code, pharmacy, clinic, Medicare, delivery, personal); recall by year (2022 vs 2023); source (IMC vs Mendeley).
- **Fairness check (the brief's "even when age … isn't a direct input"):** legit flagged on the texts older adults depend on (look-alike categories) vs everyday personal texts (look-alike "family" rows and 2012 ham).
- **Tactic tagger:** per-tactic precision/recall/F1 on test-period IMC'25 rows against the dataset's `lure_principles`. Phase B reads the IMC'25 paper's method section and states how those labels were made (they may be model-assisted, so they're "dataset labels", not human ground truth). Chips map: authority → "Pretends to be a company or agency"; time/urgency → "Rushes you"; need and greed → "Money, a prize or a fee"; reply → from `scam_type` ∈ {wrong number, hey mum/dad} → "Asks you to reply or chat"; "Has a link" / "Has a phone number to call" are pattern spans, not learned. Highlights use unigram coefficients only (bigrams are noisy).
- **Ablations (cheap):** drop char n-grams; B2 (no IMC'25); without modern synthetic legit; safety floor off; tagger with vs without undated rows.
- **Failure gallery:** 3 real test-A errors with text, score, band, tactics, and our best explanation.
- **One command:** `python -m eval` (dev by default; `--split test-A` / `--split test-B`) → `results/metrics.json`, `results/metrics.md`, `results/failures.md`. `test-B` refuses to run twice unless `--i-know` and logs each run in `results/test_runs.log`.

## 14. Rubric scorecard

| Line | Pts | What the judge will see | Self-score now | Biggest risk | Fix |
| --- | --- | --- | --- | --- | --- |
| Technical execution | 30 | `pip install && python app.py` works offline; clean small modules; tests | 22 | Install friction or a crash on odd input | Fresh-clone test Sun; garbage-input state; no torch |
| Originality | 20 | Dated test, look-alike false-alarm check, era-shortcut control, learned "why" | 12 | "Another spam filter" first impression | Lead the write-up with the question, not the filter |
| Impact + track fit | 20 | Dolores + Ana; brief's words everywhere; FTC stat; user test notes | 15 | Persona feels invented | Consented user test with a real grandparent (synthetic texts) |
| Testing + honesty | 15 | 5 baselines incl. style-only, CIs, slices, failures, test-A/test-B | 12 | Small N in reply-bait slices | Report CIs; say so plainly |
| Communication | 15 | One page, numbers in top third, 2:00 video | 11 | Too many numbers | One headline table, one chart |
| Finals: demo + clarity | 30 | 20-second paste flow, judge types their own | 24 | Judge's text gets a weird answer | Embrace it: show the score and say why |
| Finals: depth | 30 | Dated split, near-dup removal, thresholds on dev, era-shortcut controls | 22 | "Why not a transformer?" | MiniLM ablation row |
| Finals: impact | 20 | Older adults + caregivers (sponsor) | 15 | Scale question | iOS Shortcut / share-sheet as next step |
| Finals: Q&A | 20 | §19 prep | 13 | Beginners can't explain | `/explain quiz` drills Sunday |

## 15. Risks and premortem
"It's Sunday 9 PM and we lost. Why?"
1. **The dates don't hold up** (parsed years wrong) → if spot-check fails on > 3 of 30, fall back to a *source* split (train UCI + IMC dated ≤ 2021 only; test 2022+ with stricter parsing) and say so. Cut: drop 2024 (N = 8).
2. **The model learned era, not scam** (flags all modern legit) → that's a finding; report it, then add Mendeley-unique ham to training in an ablation. Don't hide it.
3. **The look-alike set is late or tiny** (Teammate A stuck) → minimum 60 rows by Sat 6 PM gate; the lead can't write it, so B helps.
4. **It looks like every other spam filter** → write-up opens with the question and the leakage number; video shows the "Ask someone first" on a real bank alert.
5. **Beginners can't explain** → each lane has a module they own and a `/explain quiz` on Sunday.
6. **The style-only baseline scores close to ours** (the task is solved by masking/length, not content) → report it as the headline finding, show the modern-legit ablation, and lead the write-up with "what the filter really learned". That is still a strong, honest result.
7. **Test contamination by Sunday fixes** → fixes use dev only; test-B is run once and every run is logged in `results/test_runs.log`.
- **Plan B:** HeatRx (Health: medication list + heat forecast → hot-day plan). **Switch gate:** Sat 9:30 AM CT, only if the IMC'25 + UCI data can't be loaded and split within 30 minutes (the brief's own rule). Otherwise stay.

## 16. Build plan
- **Overnight (Phase B):** M1 skeleton (data download + stub model + page) · M2 real model + tagger + thresholds on dev · M3 unit tests (normalise, dedupe, metrics) · M4 `python -m eval` on **dev** with all baselines · M5 design pass · M6 review + fresh-clone test.
- **Sat 9 AM–6 PM:** Teammate A and B each write ~100 look-alike test rows (guide in `eval/LOOKALIKE_GUIDE.md`) and blind-check each other's; B does copy, README, user-test plan; lead reviews, spot-checks dates, freezes test set by 4 PM. **GATE 6 PM:** full flow + dev eval green; record a rough backup video.
- **Sat 6–10 PM:** first frozen-test run → metrics, slices, failures. Chatbot baseline.
- **Sun 9 AM–1 PM:** fix the top failure mode using dev examples only, MiniLM ablation, then run **test-B once** for the headline. **FREEZE 1 PM.**
- **Sun 1–5 PM:** write-up, video. **5–9 PM:** ship checklist, submit by 9 PM CT.
- **Cut list (in order):** MiniLM ablation → chatbot baseline → "How we know" panel → Colab notebook → dark mode → staggered highlight motion.

## 17. Team plan (two teammates are beginners)
**Lead (Parth):** data, model, tactics, eval, integration; reviews every PR. Explains: dated split, dedup, thresholds, why logistic regression.

**Teammate A: test data owner** (branch `a/lookalike`; may touch only `data/test/lookalike_test.jsonl`, `eval/LOOKALIKE_GUIDE.md` notes, `docs/DATA-SOURCES.md`)
1. Prompt: *"Read eval/LOOKALIKE_GUIDE.md and docs/PRD.md §13. Help me find the public pages where Chase, Wells Fargo, Bank of America, CVS, Walgreens, USPS, UPS, Medicare and one utility describe the texts they really send. List each URL and the message format. Don't write the test rows for me."* Done-check: `docs/DATA-SOURCES.md` lists ≥ 8 format sources with URLs.
2. Write ~100 look-alike legit texts yourself (B writes the other ~100), one per line in the JSONL format the guide shows (`text`, `category`, `format_source_url`), with made-up numbers (555 phones, fake order IDs). Done-check: `python -m eval.check_lookalike` reports 0 errors.
3. Prompt: *"Run python -m eval.freeze and explain what the hash in data/test/MANIFEST.txt proves."* Done-check: MANIFEST committed.
4. Explains to a judge: how the look-alike set was built, why the lead didn't write it, what a false alarm costs Dolores.

**Teammate B: story and user owner** (branch `b/writeup`; may touch `docs/WRITEUP.md`, `README.md`, `secondlook/advice.py` copy strings, `docs/user-test.md`)
1. Write ~100 look-alike legit texts yourself from the format sources A found (same guide, categories split with A). Then blind-check A's rows (you see only text): prompt *"Open data/test/lookalike_blind.csv. For each row, I'll answer 'could this be a real message from this company? yes/no'. Don't suggest answers."* Done-check: `lookalike_blind_answers.csv` complete.
2. Prompt: *"Read docs/PRD.md §9 and secondlook/advice.py. Check every user-facing sentence is under 15 words and has no jargon; suggest edits, then I'll choose."* Done-check: smoke test still passes.
3. Run a 10-minute user test with your grandparent (written consent from them; synthetic texts only; notes, no recording). Prompt: *"Make a 5-question user-test script for an older adult using Second Look with three synthetic texts."* Done-check: `docs/user-test.md` with what confused them.
4. Fill `docs/WRITEUP.md` and the video script from `results/metrics.json` only. Done-check: every number in the write-up appears in the file.
5. Explains: who Dolores is, what the three bands mean, one failure and why.

## 18. Demo and video script (2:00)

| Time | Says | Shows |
| --- | --- | --- |
| 0:00–0:15 | "Americans reported $470 million lost to text scams in 2024, five times 2020. The blockers families buy either miss new scams or silently hide real bank texts." | FTC number, then two app-review lines |
| 0:15–0:25 | "Dolores is 77. Her rule with her daughter: forward it before you tap. Her daughter answers hours later." | Persona card |
| 0:25–1:05 | Paste the toll text → "Looks like a scam", highlights. Paste a real-style bank alert → "Ask someone first". Tap Send to Ana. Type a new one live. | Real screen |
| 1:05–1:35 | "We trained on texts up to 2021 and tested on {N} real scams reported in 2022–24. The brief's tutorial model caught {r_B2}; a keyword rule {r_B1}; ours {r_M1}, with {fa_M1} false alarms on real-style bank and pharmacy texts. And we checked it isn't just spotting new-looking texts: {era_control_result}." | Metrics table, one chart |
| 1:35–1:50 | "Where it fails: {failure_1}." | Failure card |
| 1:50–2:00 | "Next: a share-sheet button on the phone and a study with families. Prototype, not financial advice." | Footer |

## 19. Finals Q&A prep
1. **Why logistic regression, not a transformer?** Millisecond CPU inference, inspectable weights that power the highlights, no GPU for judges; the MiniLM row shows what a transformer adds (or doesn't) on dev and test.
2. **What's your baseline?** Majority, keyword + link rule, the brief's tutorial model, and a chatbot on 200 samples. Numbers in the table.
3. **How do you know there's no leakage?** Normalised-text de-duplication across all splits (count reported); time split; same placeholders for all sources; thresholds fixed on dev; test frozen and hashed before the first run.
4. **Where does it fail?** Reply-bait ("wrong number", "hey mum") with no link or money words; legit texts with urgency (real fraud alerts). Show the failure gallery.
5. **Why not just ChatGPT?** It's a baseline we measured: {chatbot numbers}. Ours is free, offline, needs no account, and Dolores's texts never leave her phone.
6. **How did you build ground truth?** Dataset authors' labels for scams; look-alike legit written by a teammate who didn't write code, from official formats, blind-checked by the third teammate.
7. **Is the model learning "old vs new" instead of scam?** That's our shortcut check: false alarms on modern legit look-alikes vs 2012 texts. {result}.
8. **What would you change with another week?** Real legit texts donated with consent by families; a share-sheet integration; a study with an older-adult group; retraining monthly on new reports and measuring drift.
9. **Fairness?** False-alarm rate on the texts older adults rely on vs everyday texts; recall by scam type.
10. **Why three bands?** A wrong "safe" costs money; a wrong "scam" costs trust. The middle band sends the hard cases to the family check people already trust.

## 20. Open questions for the humans (ranked; each with our default if nobody answers)
1. **Persona name "Ana" on the button:** default keep a constant `HELPER_NAME = "Ana"` for the demo.
2. **Who on the team can run the user test with a grandparent (with consent)?** Default Teammate B; if nobody can, cut it and say so.
3. **IMC'25 date parsing quality:** default spot-check 30 rows Saturday 9 AM; fall back per §15.1.
4. **Committing raw data (≈ 11 MB):** default commit (CC BY 4.0, credited) so judges run offline.
5. **Chatbot baseline model:** default a Claude subagent (Sonnet) labelling 200 test texts once, transcript saved; disclose as "run through Claude Code".
6. **Modern real legit SMS:** default synthetic train + teammate-written test. Lead to check by hand (Aside can open it): the IEEE Access Jan 2024 ~68K-message SMS dataset (DOAJ https://doaj.org/article/9751aa8f14824fa388257bb9bcecdfb3). If its licence allows, add it as a real modern-legit test slice.
7. **IMC'25 label provenance:** default read the paper's method section in Phase B and state it; if tactic labels are model-made, call them "dataset labels".
8. **Aside research:** worked (no fallback needed). HeatRx voice-of-user for Plan B is in `docs/research/voice-heatrx.md`.

## 22. Where the build differs from this plan (Phase B, Sat Nov 14 00:40 CT)
- **Near-duplicate cut-off 0.8, not 0.9:** a unit test showed a one-letter typo copy scores 0.886.
- **Safety floor narrowed:** reply-bait lifts to "ask" only with scam score ≥ 0.15 (picked on dev); the unconditional version flagged 7.9% of everyday 2012 texts (vs 1.5%) for 2 extra scams. Code requests always lift.
- **Reply tagger** trains with legit texts as negatives (otherwise "hi mom, landed safe" looked like reply-bait). Other tactics: scams only.
- **"No scam signs found"** shows only link/phone chips; learned tactic chips appear only with "scam"/"ask".
- **Chip copy:** "Pretends to be a company or agency" → "Says it's from a company" (real banks say who they are too; fits a phone).
- **Unknown input:** non-English or non-Latin text → "We can't check this one" (advice: ask someone), counted as flagged in the eval.
- **Golden input 2 (Chase-style fraud alert) is called "Looks like a scam" (0.615)**, not "ask" as §7 hoped. Kept honest; the team decides whether to demo it as a known false alarm.
- **Raw data not committed** (`data/raw/` stays git-ignored); processed splits and models are, so the app and eval run offline.
- **Thresholds:** t_low 0.4191, t_high 0.5995 (`models/thresholds.json`), rounded down/up so rounding never moves a dev row.
- **test-A/test-B split keeps near-duplicate groups together** (review finding); test runs are logged before they start.
- **Palette:** neutral canvas `#F6F6F5` instead of warm `#FAF8F5`; section labels in sentence case; disclaimer footer sticky on desktop.
- **Not built yet:** B3 chatbot baseline, MiniLM ablation, Colab notebook, user test (all Should; need the frozen test set or a human).

## 21. Credits
Datasets: UCI SMS Spam Collection (Almeida & Gómez Hidalgo, CC BY 4.0) · IMC'25 "Fishing for Smishing" (Agarwal et al., CC BY 4.0) · Mendeley SMS Phishing Dataset (Mishra & Soni, CC BY 4.0). Prior art and inspiration: Google Messages scam detection, Bitdefender Scamio, RoboKiller, Truecaller, Textkiller (public listings and reviews only); GitHub smishing detectors cited in §4. Evidence: FTC Data Spotlight (Apr 2025); Lu et al. 2026 (alphaxiv 2605.16656). Libraries: scikit-learn, FastAPI, uvicorn, joblib; sentence-transformers/all-MiniLM-L6-v2 (eval only). AI tools: Claude Code (Anthropic) for research, planning and code, logged in `docs/AI-USAGE-LOG.md`; Aside browser for read-only voice-of-user research.

This project is a prototype and is not financial advice.
