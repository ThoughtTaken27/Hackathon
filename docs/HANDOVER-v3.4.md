# Kettle v3.4 handover: trained sound head, "Talking / TV", drag to read the day

Written Sun 15 Nov 2026, ~4:00 PM CT, on branch **`claude/adoring-gates-8oyfjq`**. It builds on
`claude/dreamy-fermi-m2iux4` (handover v3.3, PR [ThoughtTaken27/Hackathon#1](https://github.com/ThoughtTaken27/Hackathon/pull/1)).
It contains every commit of that branch plus the commits below. **v3.3 still holds for everything not listed here.**

## 1. What this branch adds (all pushed, all checks green)

| Change | Evidence |
|---|---|
| **Trained sound head (named sounds v2).** One logistic regression per sound on the CED-tiny embedding (+ AudioSet log-odds where tune CV chose it). Pre-registered before its one test run. **8 of 15 names pass** the unchanged bar (precision ≥ 90%, recall ≥ 40% on the test halves), up from 1 with the rules: kettle, chopping, running water, cupboards/drawers, timer beep, talking/TV, typing, footsteps. Hidden: frying (87.2%), dishes (87.9%), microwave (82.6%), glass, vacuum, door; blender failed on tune | `eval/PREREGISTER-SOUNDS-V2.md`, `eval/sound_head.py` → `results/sound_head.json`, `web/public/model/sound_head.json` |
| Device + Python twin use the head when the embedding is there; same privacy veto; kinds without a head keep v1 rules (all hidden) | `web/public/js/sense.js kindsOf/headProb`, `kettle/kinds.py named/head_prob`, parity `web/test/sound_head.test.mjs` |
| **"Talking / TV"** replaces "TV" (activity), "Talking or TV" (ambiguous state) and "TV or radio" (sound name), JS and Python | `core.js`, `labels.py`, `timeline.py`, `view.py`, `rules.py`, `kinds.json` |
| **Drag to read the day** on phones: a line + "9:42 AM · Cooking" bubble selects the stretch under the finger; tap/click/arrow keys still work; vertical swipes still scroll | `web/public/js/ui.js dayBar`, `web/public/css/app.css .scrub`; screenshot `docs/screenshots/family-drag-phone.png` |
| Family checks offer all 8 shown sounds; the "Morning drink by 9" preset is back (kettle passes) | `family.js` (unchanged code, reads `KINDS_SHOWN`) |
| **Not shipped:** rule 2g (fill "Not sure" from the sound head): Kitchen20 tune "Not sure" 80.9 → 75.0%, short of the 10-point gate written first | `eval/sound_fill.py` → `results/sound_fill.json` |
| How sure, write-up block, video script, demo script updated from the files | `tools/export_accuracy.py`, `web/public/js/beyond.js`, `docs/WRITEUP.md`, `docs/VIDEO.md`, `docs/DEMO-SCRIPT.md` |

## 2. Numbers you may quote

| Claim | File |
|---|---|
| 8 of 15 sound names pass (was 1); per-sound precision/recall rules → head, N | `results/sound_head.json` (`v1_rules`, `v2_head`) |
| e.g. kettle precision 44.0% → 100% (recall 40.9%, N=22: wide interval); timer beep 34.0% → 93.3%; running water 67.1% → 95.7% | same |
| Rule 2g not shipped, why | `results/sound_fill.json` |

Disclose with any of these: the test halves were scored once before with the rules (v1), so this is their second use; every
choice in the head came from the tune halves; these are 10-second public clips, not a real kitchen.

## 3. Checks (green at the last commit)

```bash
cd web && npm test && cd ..                 # 140 pass, 0 fail, 4 skipped
.venv/bin/python -m pytest -q tests         # 79 passed
.venv/bin/python smoke_test.py              # PASS
.venv/bin/python -m eval.check_metrics      # 0 problems
KETTLE_CHROME=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome .venv/bin/python web/test/e2e.py http://localhost:8787 web/.data/test/fake-kitchen.wav <out>   # errors: []
```
Regenerate: `python -m eval.sound_head` (writes results, the device file and `kinds.json` shown flags; **do not rerun to
"improve" it: that would be another look at the test halves**), then `python tools/export_sound_head_fixtures.py`,
`python tools/export_web_fixtures.py`, `python tools/export_accuracy.py`. Kitchen20 embeddings are not in git: clone
`marc-moreaux/kitchen20` into `data/raw/kitchen20` and embed (`eval/other_homes.py fetch()` does it, ~5 min on CPU).

## 4. Next, for humans (unchanged order from v3.3 §6)
1. Merge this branch (it includes PR #1). 2. Real-kitchen recording; score it with `eval/own_kitchen.py --timeline` (note:
pass the embedding to `kinds.named` there if you want the v2 head's names in that report). 3. Deploy with Parth's OK. 4. Video:
the named-sounds line is now "rules passed one sound; a small trained classifier passes eight, the rest stay hidden".

## 5. Gotchas
- `KINDS_SHOWN` in `core.js` must equal `kinds.json` shown and `sound_head.json` shown (`web/test/sound_head.test.mjs`).
- `kindsOf(sense, as, off, withHidden, emb)`: without `emb` it falls back to the v1 rules (tests use that path).
- `eval/confetti.py` builds events without the embedding, so its kinds come from the v1 rules; `eval/sound_fill.py` is the v2 version.
- The scrubber swallows the stretch button's own click after a pointer interaction (else it would toggle twice); keyboard
  Enter on a stretch still toggles it.

## 6. Added after 4:00 PM (same session)
- **Merged to `main`:** PR #1 (v3.3 branch, incl. Parth's official-template write-up) + everything above. `main` = this branch.
- **Neutral by default, any room:** "Your parent" until setup names someone; the chosen room names every screen; room-aware
  setup on the room screen; `/listen` alias; Python twin + demo app neutral. Not done: per-room privacy rules in
  `people.js ROOMS` (`showsSounds`, `showsActivities`) are not enforced, so they are not shown anywhere.
- **Real-home test (instead of our own recording):** `python -m eval.real_homes` (needs TUT-SED 2016 in `data/raw/tut2016`:
  `curl -L -o audio.zip https://zenodo.org/api/records/45759/files/TUT-sound-events-2016-development.audio.zip/content`, same for
  `.meta.zip`, unzip both there). Result in `results/real_homes.json`, on How sure and in the write-up. Scored once; don't rerun
  to tune. Our own kitchen recording (v3.3 §4) is still the best next measurement.
