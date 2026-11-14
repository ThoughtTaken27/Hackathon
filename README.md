# Kettle

**A laptop already in a parent's kitchen turns household sounds into a calm day timeline for the adult child who lives far away, keeps no audio and no words, and publishes how often it misses an activity and how often it cries wolf.**

Track: AI + Health ("manage an ongoing one better"). Built for an adult child caring from a distance for a parent with early memory loss (invented persona: Meera, 34, and her father Ravi, 79, who consents on his own kitchen screen and can pause it).

> **This project is a prototype and is not medical advice.** Kettle is not an emergency device: it can't detect falls or call for help.

_Results table, screenshots and limits are filled in from `results/` as the build finishes (see below)._

## Run it (no keys, no account, no network)

Python 3.11. About 5 minutes on a fresh machine (most of it is installing PyTorch).

```bash
git clone <this repo> kettle && cd kettle
python3.11 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python smoke_test.py        # golden path, offline, < 60 s; prints PASS
python app.py               # then open http://localhost:8000
```

- **Caregiver view:** http://localhost:8000/ . With no kitchen laptop set up, press **Play a sample day** (real recordings from a public research home, through the same model, played fast) or **Try your own sound** (drop any audio file; it's read in memory and never saved).
- **Kitchen screen:** http://localhost:8000/kitchen on the laptop that sits in the kitchen (Chrome or Edge; the microphone needs `localhost`). The parent reads three lines, presses "Yes", and can pause or turn it off any time.
- **How sure is Kettle?** http://localhost:8000/how-sure : measured misses and false alarms per activity, from `results/metrics.json`.

Everything the model needs is in the repo: CED-tiny weights (`models/ced-tiny`, Apache-2.0), the trained head (`models/head.json`, plain numbers) and 90 sample clips (`demo_cache/`, SINS dev set, CC BY-NC 4.0).

## How it works

```
kitchen mic ─► 10-s windows every 2 s (RAM only) ─► CED-tiny (frozen, 192-d) ─► logistic head (9 activities)
             ─► "Not sure" below a confidence threshold ─► 2-of-3 smoothing ─► day bar blocks + evidence
             ─► caregiver checks (rules she sets: Met / Not yet / Missed / Can't tell) + heartbeat
```

## Team tooling

This repo also holds the team's Claude Code setup: [`AGENTS.md`](AGENTS.md) (operating manual), `.claude/` (hooks, skills, agents), and planning docs in [`docs/`](docs/) (`PRD.md`, `DECISIONS.md`, `WRITEUP.md`, `EXPLAIN.md`, `AI-USAGE-LOG.md`, `DATA-SOURCES.md`). Commands: `/start`, `/done`, `/explain <module>`, `/checkin`, `/ship-check`.
