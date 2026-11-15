# Pre-registration: urgent alerts v3.5 (gunshot, shouting, faster stillness)

Written Sun Nov 15, before the first held-out run of these changes. The held-out half (`dev == False` in `eval/safety.py`)
is run once after this note is committed. Any rerun is disclosed in `results/safety.json` (`process_note`).

## What changes (both engines: `web/public/js/safety.js` and `kettle/safety.py`)
1. **Gunshot detector** `gunshot`: AudioSet 427 Gunshot/gunfire, 428 Machine gun, 429 Fusillade, 430 Artillery fire, 431 Cap gun.
   **Threshold:** no gunshot recordings could be fetched from this machine (Hugging Face and Zenodo are blocked by the network
   policy), so it has **no measured catch rate**. On development clips an ESC-50 *can opening* already scores up to 0.69 on these
   indices, so the usual 99.5th percentile would leave kitchen cans firing. Rule fixed now: tau = the **largest score of any
   development negative** (every non-danger dev clip: SINS folds 1-2, ESC-50 folds 1-3, Nonspeech7k half 0, synthetic seeds 0-29),
   never below 0.3. So no development clip fires it, by construction.
   **Rule U8:** a gunshot hit in one window with no TV/radio/music in the last 3 windows → Urgent at once, no check-in, 10-minute
   cooldown. With media on → a "Worth a look" note only (off in the app, like every concern note).
2. **Shouting rule U9:** the existing `shout` detector (8 Shout, 11 Yell, 13 Children shouting; tau from dev false fires) in
   **3 separate windows within 60 s**, no media → the "Are you OK?" check-in (30 s), told to the family at once. A single shout is nothing.
   No shouting clips are available: **catch rate not measured**.
3. **Crash then stillness:** `FALL_STILL_S` 600 s → 120 s (the person had been active in the 30 min before; 2 stray windows allowed).
4. **Crash then cry / screaming / crying:** the engine is unchanged; the app now tells the family when the check-in starts
   ("asking"), not after it ends. That is a UI change, so no new detector number.

## Not changed tonight (and why)
- Smoke-alarm second path (handover 3.5a) and looser T3 timing (3.5b): the simulator has no loudness, so the "loud" guard can't be
  checked, and kitchen timers are the obvious false alarm. Left as is; the honest number stays 68.3%.
- A thud alone: never urgent (1.06 false fires per hour of home audio would be ~25 false reds a day).

## Gate (decided now)
- **Ship only if ordinary home audio (every held-out SINS window, ~12 h) still gives 0 Urgent alerts per 24 h.** If not: raise the
  failing threshold on development clips only, rerun once, and disclose.
- Report, whatever they are: gunshot false fires per source on held-out clips (can opening, door knocks, fireworks, thunder);
  the new negative scenario "cans, knocks, fireworks and thunder while cooking" (60 timelines); the crash-then-stillness rate at 2 min.
- Known cost stated up front: a crash followed by someone quietly leaving the room now looks like a fall after 2 minutes, not 10.
