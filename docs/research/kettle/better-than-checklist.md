# Better-than checklist: every top-10 pain theme → where Kettle answers it

Source themes: [`better-than.md`](better-than.md) (418 coded reviews; top 10 by count × severity, 11 rows because 10a and 10b tie).
Each row names the place in the app, the test or number that proves it, and the screenshot (final design round,
`docs/screenshots/round-4/`; earlier rounds kept). "Cut" means we deliberately don't build it, with the reason.

| # | Pain theme (count, score) | Where Kettle answers it | Proof (command or number) | Screenshot | Status |
|---|---|---|---|---|---|
| 1 | Parent feels watched (17, 51) | Kitchen screen shows the same day bar Meera sees, lists every check she set, says "Meera sees the kinds of sounds, not recordings or words"; one big Pause; caregiver sees "Paused by Dad at …"; speech is only ever "Conversation"; evidence never shows who is speaking | `python -m eval.privacy_check` → `results/privacy_check.json` (0 audio writes, 0 outside connections, 5 MB upload read in memory); `tests/test_privacy_grep.py` (no ASR, no audio writes, no MediaRecorder) | `kitchen-listening-*`, `kitchen-paused-*`, `caregiver-live-paused-*`, `howsure` (#privacy) | Built |
| 2 | Burden on the older adult (25, 50) | After "Yes, Meera can see this" the parent does nothing: no taps, no wearable, no charging; Pause is optional | Sample day plays with zero parent input (`smoke_test.py`); README setup has no parent step after placement | `kitchen-consent-1-*`, `kitchen-listening-*` | Built |
| 3 | Missed a real problem (15, 45) | "How sure is Kettle?" lists every activity's **missed** count, recall, N and 95% CI; scope stated on every caregiver page: "Kettle is not an emergency device. It can't detect falls or call for help." | `results/metrics.json` (`dev.ours_ch0.per_class[*].missed`, eval run); failure gallery `results/failures.md` | `howsure-*`, `caregiver-usual-*` (footer) | Built |
| 4 | Hub / Wi-Fi / battery (19, 38) | One laptop on its charger; no hub, no extra sensors; runs offline | `results/runtime.json` (seconds per 2-s hop, server CPU %) from the live privacy-check run; `smoke_test.py` offline | `kitchen-listening-*` | Built (30-min CPU run: see MORNING-BRIEF) |
| 5= | Subscription price (16, 32) | Free, open source, no hardware to buy, no account | README install (fresh-clone timing in M8) | — (README) | Built |
| 5= | False alarms (16, 32) | **False-alarm** count per activity on "How sure"; "Not sure" hatching below θ and for sounds unlike all 9 activities; 2-of-3 smoothing; **no push alerts** (checks only show state) | `dev.not_sure` (θ, coverage, shown-label precision); `offlist` (confident wrong with and without the novelty gate); `dev.session_level` (false-alarm blocks per hour, smoothing on vs off) | `howsure-*` (#not-sure), `caregiver-try-white-noise-*`, `caregiver-try-unclear-*` | Built |
| 7 | Consent overridden (8, 24) | Listening starts only after two steps on the kitchen laptop (explainer, then "Is it OK for Meera to see this?"); only the kitchen laptop itself (127.0.0.1) can consent, pause, resume or stream audio; weekly "Keep it on?" that pauses if unanswered | `tests/test_heartbeat_consent.py` (audio refused before consent and while paused; weekly pause); smoke test (audio before consent is dropped) | `kitchen-consent-1-*`, `kitchen-consent-2-*`, `kitchen-weekly-*` | Built |
| 8 | Discontinued under you (11, 22) | Local-first: model weights, sample clips and code in the repo; no server of ours | `smoke_test.py` passes with no network (`HF_HUB_OFFLINE=1`); fresh-clone test (M8) | — | Built |
| 9 | App bugs, logouts (21, 21) | No accounts, no login, one local page | Screenshot sweep of every state: zero sign-in screens | all of `round-4/` (136 screens, 0 page errors) | Built |
| 10a | "No news" is ambiguous (6, 18) | Heartbeat is the first line: "Listening · last heard 40 s ago" / "Not listening since 10:42 AM (laptop asleep, closed or off). Nothing is known after that." Quiet is a thin line (heard, nothing happening); Not listening is a cross-hatch; checks say "Can't tell" instead of "Missed" when Kettle wasn't listening | `tests/test_heartbeat_consent.py::test_silence_is_listening_but_no_input_is_stale`, `tests/test_timeline.py::test_quiet_is_not_the_same_as_not_listening`, `tests/test_rules.py::test_not_listening_gives_cant_tell_never_missed` | `caregiver-stale-*`, `caregiver-tv-*`, `caregiver-error-*` | Built |
| 10b | Wants "no activity by X" (9, 18) | Up to 3 caregiver-set checks: "Kitchen activity by 10:00 AM", "Some sound of activity by …", "TV on for more than N hours", each Met / Not yet / Missed / Can't tell, labelled "Rules you set. Kettle doesn't learn Dad's routine and doesn't send alerts." | `tests/test_rules.py` (normal day, late start, not listening, paused, not-sure never counts) | `caregiver-usual-*` (Met), `caregiver-quiet-*` (Missed), `caregiver-tv-*` (Can't tell), `caregiver-rules-sheet-*` | Built |

## Explicit cuts (from `better-than.md` "won't build")
| Not built | Why |
|---|---|
| Fall / emergency detection, smoke / CO / glass | Safety-critical and unvalidatable this weekend; the screen says Kettle isn't an emergency device |
| Push alerts when a check is missed | No relay without a cloud (theme 8) and alerts are the false-alarm pain (theme 5=); checks show state when Meera looks |
| Learned "unusual day" model | SINS has no clock times, so it couldn't be measured honestly |
| Accounts, cloud sync, hosted share link | Themes 8 and 9; remote viewing is a private VPN set up once (README) |
| Phone as the kitchen microphone | Needs HTTPS on the home network; a Could for another week |

## Parth's addendum items (k3-addendum.md) → where they live
| # | Item | Where | Proof | Status |
|---|---|---|---|---|
| A1 | Draft submission by Sat 9 PM CT | `docs/SUBMISSION-DRAFT.md` | every form field filled from the repo's real state; Parth presses submit | Built (numbers filled from `results/`) |
| A2a | Reliability (calibration) plot + ECE with CI | `results/reliability_dev.png`; "How much to trust 'how sure'" on `/how-sure` | `dev.calibration` (ECE before/after temperature with session-bootstrap CIs; temperature cross-fitted) | Built |
| A2b | Plain cost story for θ | write-up "Results"; `/how-sure` trade-off table; `results/theta_tradeoff_dev.png` | `dev.theta_tradeoff` (kitchen sessions not noticed vs false kitchen blocks per 16-h day, through the shipped timeline, incl. the shipped θ) | Built |
| A4 | Caregiver metric (kitchen activity) in the headline | `results/metrics.md` (first section after the held-out table), write-up, README, `/how-sure` | `dev.meal_activity`, `dcase_eval.meal_activity` (missed vs false alarms with N and CI) | Built |
| A6 | Reproduce notebook < 5 min, outputs saved | `notebooks/kettle_reproduce.ipynb` | executed with nbconvert: 38 s, last cell "ALL MATCH (within 0.1 points)" | Built |
| A9–A10 | Timeline "misses 17 of 33 kitchen sessions" while windows catch 95% | `results/metrics.md` (θ cost section: three rules × θ, before/after bridging), write-up θ paragraph, `/how-sure` calibration section | Cause measured on dev: fragmentation by short "Not sure" stretches (all 18 strict misses had 64–94% merged kitchen coverage; 0 wrong kitchen activity). Timeline rule 2b (bridge ≤ 30 s "Not sure" inside one activity) added after the frozen run: strict 15 → 26 of 33, false kitchen blocks 3.87 → 3.23/day; headline rule (merged ≥ 50%) 33 of 33. `tests/test_timeline.py`, `tests/test_theta_tradeoff.py` | Built (DECISIONS 16:55) |
