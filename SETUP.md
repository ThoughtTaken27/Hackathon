# SETUP: everything, from a fresh clone (written for an agent to follow top to bottom)

Kettle has two runnable parts that share one frozen model:

| Part | Where | What it is | Who uses it |
|---|---|---|---|
| **Kettle (Python)** | repo root: `app.py`, `kettle/`, `eval/`, `static/` | The reference app + every measured number. Runs on one laptop, offline. | Judges reproducing results; the real-kitchen test |
| **Kettle web** | `web/` | The shareable version: the parent's laptop labels sound **in its browser** (same model, ONNX), the family member's phone sees the day through a tiny sync service on Cloudflare. | Testers with two devices; the demo video |

Live deployment: **https://kettle.parth-dev.workers.dev** (Cloudflare Workers, free plan).

Each step below has a **check**: a command whose output proves the step worked. Don't move on until it passes.

---

## 0. Ground rules (read first)

- **Never re-run the held-out test.** `eval/PREREGISTER.md` allows one run on the DCASE eval set; it happened Sat Nov 14 13:04 CT (`results/eval_run.json`). `python -m eval` re-scores from **saved predictions**; nothing in this guide re-reads eval audio.
- **Never retrain or edit the head.** `models/head.json` is frozen (sha256 `fa5de76a…`, `models/FROZEN`). `model.load()` refuses a head whose hash doesn't match. θ = 0.66 is fixed.
- **Every number in the README / write-up comes from `results/metrics.json`.** Don't type numbers by hand; `python -m eval.check_metrics` fails on bare numbers.
- **Secrets:** none are needed. No API keys anywhere. Cloudflare deploys use an interactive OAuth login by a human (step 6).
- **Don't push or deploy without the owner's OK** (Parth). Local commits are fine.
- Decisions and their reasons: `docs/DECISIONS.md`. What every module does: `docs/EXPLAIN.md`. The plan: `docs/PRD.md`.

## 1. Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | **3.11** exactly (3.12 untested) | `python3.11 --version` |
| Node.js | 20 or newer | `node --version` |
| git | any | `git --version` |
| Chrome/Chromium | for the browser tests (Playwright installs its own) | — |
| Disk | ~3 GB (PyTorch + Playwright browsers) | — |

macOS and Linux tested. CPU only; no GPU needed.

## 2. Python app (the reference)

```bash
git clone https://github.com/ThoughtTaken27/Hackathon.git kettle && cd kettle
git checkout main
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt          # runtime + tests/tools; ~2-5 min, mostly PyTorch
python -m playwright install chromium        # only for screenshots, privacy check and web e2e
export HF_HUB_OFFLINE=1                      # the model is committed; never fetch it
```

**Check:** `python smoke_test.py` ends with `PASS` (< 60 s, offline).

Run it:

```bash
python app.py        # http://localhost:8000
```

| URL | Screen |
|---|---|
| `/` | Opening page: both screens side by side, live; **Play a sample day** runs on both |
| `/today` | Meera's view (the family member's phone) |
| `/kitchen` | Dad's kitchen screen (asks for the microphone; consent first) |
| `/how-sure` | Every measured number with its error bars |

Environment: `KETTLE_PORT` (default 8000), `KETTLE_HOST` (default `127.0.0.1`; `0.0.0.0` to reach it from a phone on the same network).

### 2a. Verify the Python side

| What | Command | Pass looks like |
|---|---|---|
| Unit tests | `python -m pytest -q tests` | `62 passed` |
| Smoke | `python smoke_test.py` | `PASS` |
| Numbers regenerate | `python -m eval` (~6-7 min) then `python -m eval.check_metrics` | exit 0; `0 problems` |
| Reproduce notebook | `jupyter nbconvert --to notebook --execute notebooks/kettle_reproduce.ipynb --output /tmp/repro.ipynb` | runs < 2 min; ends with `ALL MATCH` |
| Privacy check | `python -m eval.privacy_check` (180 s, fake mic) | `pass: true`, 0 audio files, 0 outbound connections |

## 3. Kettle web, locally

```bash
cd web
npm install                  # onnxruntime-web + qrcode-generator (already vendored into public/; install is for tests)
node dev.mjs                 # http://localhost:8787  (same API as Cloudflare, households saved to web/.data/dev.json)
```

**Check:** `curl -s localhost:8787/api/health` prints `{"ok":true,...}`.

| URL | Screen |
|---|---|
| `/` | Landing: both real screens playing a sample day in device frames |
| `/start` | 3-step setup: who's here → names → pairing code / link / QR for the other device |
| `/pair` | Type a six-letter code (either device) |
| `/kitchen` | Parent's laptop: consent, model download (~33 MB once), microphone, live label, pause/off |
| `/family` | Family member's view: heartbeat, summary, day bar with evidence, checks, settings (invite, rename, delete) |
| `/how-sure` | Same numbers page as the Python app, from `public/data/results.json` |

To try both roles on one computer, open `/start` in a normal window and the kitchen link (or `/kitchen` + the code) in a private window.

### 3a. Verify the web side (run from the repo root, venv active, `node web/dev.mjs` running)

| What | Command | Pass looks like |
|---|---|---|
| JS core = Python, sync API | `cd web && npm test && cd ..` | `pass 21`, `fail 0` |
| Test inputs | `python web/test/prepare.py` | writes `web/.data/test/{fake-kitchen.wav, clips.f32, expect.json}` |
| Browser model = Python | `node web/test/parity-web.mjs web/.data/test` | `"same_label":90,"same_novel":90,"same_top_sound":90` |
| End to end (fake mic) | `python web/test/e2e.py http://localhost:8787 web/.data/test/fake-kitchen.wav web/.data/test` | `first label after ~12s`, `pause reached family`, `delete home: 200, afterwards: 404`, `errors: []` |

## 4. How the pieces fit (web)

```
parent's laptop (browser)                         Cloudflare (free)                      family member's phone
mic → 10-s ring buffer (RAM only)                  Worker: src/worker.js                  /family polls every 5 s
  → public/model/logmel.onnx (front end)           ├─ static files: web/public/          → core.today() draws the
  → public/model/ced-tiny.onnx (encoder)           ├─ /api/* → src/router.js               same day bar, summary,
  → public/js/head.js (frozen head, θ, novelty)    ├─ Durable Object "Household" per home  checks and heartbeat
  → label + scores + time ──POST /events──────────▶│  (SQLite: state + labels, 8 days)
                                                   └─ Durable Object "Codes" (6-letter codes, 48 h)
```

- **Shared logic:** `web/public/js/core.js` is a line-for-line port of `kettle/timeline.py`, `rules.py`, `heartbeat.py`, `live.py` (parent controls) and `view.py`. `npm test` compares it with Python's own output (`web/test/fixtures.json`).
- **Access:** no accounts. Creating a home returns two keys (kitchen, family). Links carry them in the `#fragment` (never sent to servers or logs); the server stores only SHA-256 hashes. Only the kitchen key can consent, pause, turn off or send labels; only the family key can set checks; either can delete the home.
- **Why two ONNX files:** as one graph, onnxruntime-web 1.22 fails to create the session (a raw wasm exception). Each half works and together they match Python (see `tools/export_onnx.py`).
- **Differences from the Python app, on purpose:** windows are 10 s apart (not 2 s) to keep sync light; the kitchen "Sounds like…" chip uses the latest 10-s window. Model, head, θ and every rule are unchanged.

## 5. Regenerating the web model and fixtures (only if the Python model or rules change)

```bash
python tools/export_onnx.py          # → web/public/model/{logmel,ced-tiny}.onnx + parity.json; must print PARITY PASS
python tools/export_web_fixtures.py  # → web/public/model/{head,evidence}.json, web/public/data/sample-days.json, web/test/fixtures.json
python web/test/prepare.py && node web/test/parity-web.mjs web/.data/test > web/public/model/parity-web.json
cd web && npm test
```

`web/public/data/results.json` is the Python app's `/api/results` response (`results/metrics.json` plus `failures`, `privacy_check`, `eval_run`, `runtime`). Rebuild it with:

```bash
python -c "import json,app; json.dump(app.api_results(), open('web/public/data/results.json','w'))"
```

 Bump `?v=` on the CSS/JS links in `web/public/*.html` after changing assets so browsers don't serve stale files.

## 6. Deploy Kettle web (needs the owner's OK and a human login)

```bash
cd web
npx wrangler deploy --dry-run        # check: lists HOUSEHOLD, CODES, ASSETS bindings; no errors
npx wrangler login                   # opens the browser: a human signs in to Cloudflare (free account) and presses Allow
npx wrangler deploy                  # prints https://kettle.<account>.workers.dev
```

**Check (live):**

```bash
B=https://kettle.parth-dev.workers.dev
curl -s $B/api/health                                             # {"ok":true,...}
curl -s -o /dev/null -w "%{http_code} %{size_download}\n" $B/model/ced-tiny.onnx   # 200 22110100
python web/test/e2e.py $B web/.data/test/fake-kitchen.wav web/.data/test        # same pass lines as 3a; it deletes its own test home
```

`wrangler.toml` holds everything: static assets from `public/`, two SQLite-backed Durable Objects (free-plan compatible, migration tag `v1`). Free-plan limits: ~100k requests/day (a kitchen sends ~8.6k/day while listening; an open family view polls every 5 s while visible). No secrets or environment variables are needed.

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: soundfile` | wrong or half-installed venv | activate `.venv`, `pip install -r requirements-dev.txt` |
| App tries to download from Hugging Face | not offline | `export HF_HUB_OFFLINE=1` (weights are in `models/ced-tiny`) |
| Port 8000/8787 in use | an old server | `lsof -iTCP:8000 -sTCP:LISTEN` and stop it, or set `KETTLE_PORT` / `PORT` |
| Kitchen page: "Kettle couldn't load." | model download blocked/failed | check network; files must be served from `/model/` and `/vendor/ort/` |
| Kitchen page: "Kettle can't hear the kitchen." | microphone permission denied | browser site settings → Microphone → Allow; must be `https://` or `localhost` |
| Family view: "Not listening since…" | laptop asleep, lid closed, tab closed | keep it plugged in, lid open, tab open (Kettle holds a screen wake lock) |
| Page looks unstyled/old after an update | cached CSS/JS | bump the `?v=` query on asset links |
| `wrangler deploy` asks to log in | no Cloudflare session | step 6: a human runs `npx wrangler login` |

## 8. Map of the repo

```
app.py, kettle/        Python app: audio, encoder, head, live gate, timeline, rules, heartbeat, view text
static/                Python app pages (/, /today, /kitchen, /how-sure)
eval/                  evaluation harness (pre-registration, dev folds, held-out re-score, privacy check, own-kitchen set)
results/               every measured number (metrics.json is the source of truth) + saved predictions
models/                CED-tiny weights (Apache-2.0) + frozen head.json
demo_cache/            90 held-out sample clips (SINS dev, CC BY-NC 4.0) + sample-day scenarios
tests/                 Python unit tests (62)
tools/                 screenshots, notebook builder, write-up numbers, ONNX + web exports
notebooks/             kettle_reproduce.ipynb (reproduces every headline number from committed caches)
docs/                  PRD, DECISIONS, EXPLAIN, write-up, submission draft, design critiques, research
web/                   Kettle web: public/ (pages, JS, CSS, model, vendor), src/ (Worker, router, household), test/, dev.mjs
```
