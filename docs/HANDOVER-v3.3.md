# Kettle v3.3 handover: where everything stands, and what's left

Written Sun 15 Nov 2026, ~1:25 PM CT, at the end of a Claude Code session on branch **`claude/dreamy-fermi-m2iux4`**
(pull request [ThoughtTaken27/Hackathon#1](https://github.com/ThoughtTaken27/Hackathon/pull/1), not merged yet).
It picks up from `docs/HANDOVER-v3.2.md` (Parth's, ~12:15 PM) and `docs/HANDOVER-v3.1.md` (Shaurya's). **Read this first;
v3.2 §0–9 still hold for ground rules and environment.** Where they disagree, this file wins. v3.2 §10–11 are this session's
running notes; this file replaces them as the summary.

---

## 0. In one minute

- **The branch contains everything:** latest `main` (v3.2: rules 2c/2d, safety layer) + a usability round + the v3.2
  accuracy plan worked through. Merge conflicts are resolved. All checks green (§5).
- **Not merged, not deployed.** The live site (https://kettle.parth-dev.workers.dev) still runs the OLD version. Merging needs a
  teammate; deploying needs **Parth's OK and his Cloudflare login** (v3.1 §0.11).
- **What humans must do next, in order:** (1) merge PR #1, (2) record a real kitchen (§4), (3) deploy, (4) video by ~5 PM rough cut
  / 7 PM unlisted upload, (5) submit by 9 PM (Parth presses Submit).
- **Headline honesty points for the write-up/video:** named sounds now pass or fail a pre-registered bar (only TV passes);
  two accuracy experiments were measured and **not shipped** because they failed gates written in advance; a real-kitchen
  measurement still doesn't exist.

## 1. Deadlines (CT)

| When | What |
|---|---|
| now | Merge PR #1 (a teammate who can explain it; checklist in the PR) |
| ASAP | Real-kitchen recording (§4), scored with the ready script |
| ~5:00 PM | Rough video cut (v3.2 §7) |
| 7:00 PM | Video uploaded, unlisted |
| 9:00 PM | Submit target (Parth presses Submit) |
| 10:59 PM | Hard close |

Feature freeze was 1 PM. Everything below in §6 is bug fixes, measurement or packaging only.

## 2. What changed on this branch (all pushed)

### 2.1 Usability round (owner's hands-on test, ~10:30 AM–12:40 PM)
- **Kitchen setup is 4 steps**; step 4 is "Teach Kettle this kitchen". Until taught, a green "First, teach Kettle this kitchen"
  card sits at the top of the listening screen. **Each teaching step waits for "I'm ready. Start step N".**
- **Condensed** kitchen screen and landing page (kitchen listening screen 1229 → 1015 px tall at 1280 wide; landing 7345 → 6569 px).
- **Background listening:** worker clock (`web/public/js/tick.js`), one listening tab per home (BroadcastChannel), "Keep it in a
  small window" next to Pause, "● Listening" in the tab title, warning before closing, mic restart if windows stop, audio resume,
  "N moments noted while out of sight" on return. Still a browser tab: closing it stops Kettle (the screen says so).
- **On-device quiet and voices rules** (`web/public/js/sense.js roomRules`, web only):
  - Quiet: a window at or below the kitchen's taught quiet level (+3 dB), or −55 dBFS before setup, is Quiet.
  - Voices: an unnamed window whose loudest speech class is ≥ 0.5 (above body sounds) is Conversation.
  - Speech indices are fixed (0, 4, 5, 70), so the rule survives the voice-tag removal.
- **Muted mic:** says "Kettle hears nothing at all"; exact silence is never sent as "Not sure".
- **Landing:**
  - Neutral names; Parth's example switcher is kept.
  - The hero list slides instead of redrawing, and shows allow-listed sound names.
  - **Sample days rebuilt** from clips the frozen model labels as their recorded activity (a golden-path demo, disclosed in
    `demo_cache/scenarios.json _about` and DECISIONS). "A usual morning" opens with one quiet clip.
- **Sound check through the real page:** `web/test/sound_check.cjs` (Chromium fake mic → `/kitchen` → what reached the
  server) → `results/sound_check_web.json`.

### 2.2 Handover v3.2 accuracy plan (~12:45–3:20 PM)
| Item | Outcome | Evidence |
|---|---|---|
| 3.5 voice tags | **Done.** Speech/Conversation/Chatter/Hubbub/Narration off `kettle/evidence_labels.json` | tests both sides |
| 3.1 named sounds | **Done.** Context rules (kettle louder than frying/tap/dishes/hum; tap louder than frying; microwave ≥ 0.5 and above hum; "Timer or appliance beep" never uses smoke/fire classes). Pre-registered bar: precision ≥ 90%, recall ≥ 40% on test halves. **Only "TV or radio" passes; 14 names hidden** (computed on the device for the privacy veto and safety, never sent or listed). Checks on hidden sounds say "Can't tell"; kettle check needs 2 windows | `eval/PREREGISTER-SOUNDS.md`, `eval/sounds.py` → `results/sounds.json`: kettle precision 16.0 → 44.0%, running water 47.8 → 67.1%, microwave 11.9 → 54.5%, TV 97.8% |
| 3.3 confetti / TV | **Measured, not shipped** (no dev gain). Cause found: in Kitchen20, 80.9% of the time is "Not sure" because whole sessions are "unlike anything it learned", not short gaps | `eval/confetti.py` → `results/confetti.json` |
| 3.2 trained judge | **Measured, not shipped.** Fails the gate written before the run (cutoff 0.9: wrong activity 4 → 0, false meal 41 → 30, right 218 → 212; 0.8: +18 right but +1 false on Kitchen20). `models/judge.json` not written; Kitchen20 TEST untouched | `eval/judge.py` → `results/judge.json` |
| 3.4 real kitchen | **Scorer ready**, recording missing (§4) | `eval/own_kitchen.py --timeline` |
| 3.6 safety | **Wired, minimal:** smoke/fire alarm, crash then cry or stillness, screaming, "I need help". "Are you OK?" (read aloud) on the kitchen first; Urgent → red banner on the family view until "I've seen this". Server stores only kind, time, check-in outcome. No push; not wired: CO, repeated distress, worth-a-look notes | browser: synthetic smoke alarm → banner in 12 s; 17 ordinary/confusing sounds → no alert |
| §6 keep | How sure "Kitchen naming after a live test" + named-sound table + "Tried and not shipped" (`tools/export_accuracy.py` → `web/public/data/accuracy.json`); FAQ/README/family footer alert wording made accurate; `/family` without a link no longer throws; F4 gone | |

Every change: `CHANGELOG.md`, `docs/DECISIONS.md` rows (Sun Nov 15 11:30–14:50), `docs/EXPLAIN.md` ("Usability round",
"Second pass after a hands-on test"), `docs/AI-USAGE-LOG.md`, `docs/DATA-SOURCES.md`.

## 3. Numbers you may quote (all from files; never type them by hand)

| Claim | File |
|---|---|
| Held-out benchmark 84.1 macro F1 etc. (unchanged) | `results/metrics.json` |
| Rules 2c/2d before → after (SINS dev 130 → 132 of 132 right; Kitchen20 test wrong activity 9 → 7; DESED dish clatter called washing/eating 6 → 1 of 15) | `results/kitchen_naming.json` (test halves not pristine: see its `process`) |
| Named sounds before → after, shown/hidden | `results/sounds.json` |
| Judge and confetti: not shipped, why | `results/judge.json`, `results/confetti.json` |
| Sound check through the real page (home clips 17/20; 0 of 162 confusing windows given a confident activity; round 2: room tone Quiet 3/3, close voices Conversation 9/9) | `results/sound_check_web.json` |
| Safety detectors (scream 29/32, glass 13/16, 0 false Urgent in 12.3 h) | `results/safety.json` |

Run `python -m eval.check_metrics` before anything goes into the write-up.

## 4. Real-kitchen recording (needs a person; the single most valuable thing left)

Ask Parth (his mom's OK first; `eval/own_kitchen/CONSENT.md`, initials only). Steps are in `eval/OWN_KITCHEN_GUIDE.md`:
1. Laptop on the counter 1–2 m from the stove, QuickTime → New Audio Recording, 20–30 min. A written log of clock times:
   cooking, washing up (tap running), eating, quiet. A second short session (another meal) = the held-out test.
2. Audio → `data/private/own_kitchen/` (git-ignored; **never to any cloud model**). Labels →
   `eval/own_kitchen/labels.csv` (`file,start_s,end_s,activity,session,notes`), from the template.
3. Score:
   ```bash
   python -m eval.own_kitchen_check
   python -m eval.own_kitchen --timeline --session <first>     # dev: look, tune
   python -m eval.own_kitchen --timeline --session <second>    # test: once, report whatever it says
   ```
   Output: `results/own_kitchen_timeline_<session>.json`, old rule vs new rule per labelled stretch.
4. Put the result on How sure (extend `tools/export_accuracy.py` + `web/public/js/beyond.js accuracy()`), README and write-up.
Not applied by this scorer: the web-only quiet/voices rules (say so if quoting it).

## 5. Checks (green at the last commit)

On this cloud box (`/home/user/Hackathon`, `.venv` has everything incl. torch and soundfile):
```bash
cd web && npm test && cd ..                         # 137 pass, 0 fail
python -m pytest -q tests                            # 79 passed
python smoke_test.py                                 # PASS
python -m eval.check_metrics                         # 0 problems
cd web && node dev.mjs                               # http://localhost:8787 (restart it after changing web/src/*)
python web/test/e2e.py http://localhost:8787 web/.data/test/fake-kitchen.wav <out>   # errors: []
```
On Parth's Mac use v3.2 §1 (`.venv-probe`, `HOME=/Users/parth`, port 8799). After changing sample days, kinds or witness:
`tools/export_web_fixtures.py`, `tools/export_safety_fixtures.py`. After changing a results file the page shows:
`tools/export_accuracy.py`. Regenerate named sounds: `python -m eval.beyond && python -m eval.sounds && python -m eval.beyond`.

Data only on this box (git-ignored): `data/raw/kitchen20`, `data/emb/ced-tiny/kitchen20/all.npz`. DESED is only on Parth's Mac,
so `eval/kitchen_naming.py` runs there only.

## 6. What's left, ranked by points

1. **Merge PR #1** (the checklist's last box: a teammate can explain it; start with `docs/EXPLAIN.md`). If `main` moved, merge it in,
   rerun §5, push.
2. **Real-kitchen recording + score** (§4). Testing & honesty 15, finals Q&A. Turns "looks better" into a number.
3. **Deploy** with Parth's OK (v3.1 §0.11), then open the live site in a private window and click through: landing, `/start`,
   kitchen (allow mic), family, How sure.
4. **Write-up and video** (v3.2 §7): the story is "Parth's mom's cooking showed as eating; we found why (one tag per 10 s), fixed it
   with stretch-level evidence, held our sound names to a pre-registered bar, and here's what still fails". Numbers from §3 files.
5. Optional, only if 1–4 are done:
   - F5, a sample day that tells the failure-and-fix story.
   - Revisit the judge with the real-kitchen session as its test. Any new gate is decided before running.

## 7. Things a judge may ask (answers in the files)

| Question | Answer |
|---|---|
| "Why does the family only see TV as a named sound?" | The other 14 missed the pre-registered bar; `results/sounds.json`, `eval/PREREGISTER-SOUNDS.md` |
| "Did you cherry-pick the demo?" | Yes, the sample days (disclosed). Real error rates: How sure, `results/metrics.json` |
| "Why not ship the judge? It removed every wrong call." | It named fewer real meals and failed the gate we wrote first; choosing a looser gate after seeing results is p-hacking |
| "Is it an emergency device?" | No. It raises a few urgent notes, asks "Are you OK?" first, and can't call for help; the family sees the note only when the page is open |
| "Did you test it in a real kitchen?" | Informally yes (badly: that's what started today's work); measured: only if §4 happens |

## 8. Gotchas found this session
- **Route names are lowercase letters only** (`web/src/router.js`: `[a-z]+`). `alert_seen` silently 404'd; the route is `seen`.
- `eval/beyond.py` crashed on `MEAL` containing `"kitchen"` (fixed: `if c in C`). Its other outputs are unchanged.
- `core.KINDS_SHOWN` must equal `kinds.json` `shown` (a test checks). `kettle/kinds.py named()` returns shown names only (what is
  sent); `sense.js kindsOf(..., withHidden=true)` gives the device-only list that safety uses.
- **`git pull --rebase` on this branch replays already-merged commits and stops on conflicts.** Use `git merge origin/main`.
- Headless Chromium can't hide a tab, so background listening was tested with another tab in front and the pop-out window, not a
  real minimised laptop over hours.
- The dev server keeps homes in `web/.data/dev.json`; restart `node dev.mjs` after editing `web/src/*`.
