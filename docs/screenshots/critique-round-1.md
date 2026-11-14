# Design critique, round 1 (Sat Nov 14, 11:00–11:25 AM CT)

Inputs: `round-0/` (desktop light preview, 33 states) and the first 72 captures of `round-1/` (every kitchen state, how-sure, caregiver never/live-paused; desktop + phone, light + dark). The rest of round 1 was cut short by a 30-s request timeout while the machine was saturated (fetch + Apple + embeddings); those caregiver states were reviewed in `round-0/` and are re-captured in round 2.
Measured against: PRD §9, component-craft's ten laws, ui-patterns.md (incumbent screens), AGENTS.md bans.

## What works
- **Calm, not surveillant.** No alert counts (Canary's "9 alerts" banner), no live room location (havn's "ACTIVE NOW"), no red anywhere except the server-error state. The heartbeat is a sentence with a time, like Care Daily's "Looking good · 10 seconds ago", not an icon.
- **Words before colour.** Every rule card says its state in a sentence ("Can't tell: Kettle wasn't listening from 6:00–10:00 AM"); the dot only reinforces it.
- **Kitchen screen** reads from across a room: 40 px headline, 24 px body, a 96 px Pause, and every check Meera set is listed for the parent, so nothing is hidden from him.
- **How sure** leads with a verdict computed from the numbers, then the two macro-F1 figures with CI and N, then misses and false alarms as their own bold columns (the brief's ask).
- **CSS audit:** 0 FIX. Gradient hits are the hatch textures that encode "Not sure"/"Not listening" and the shimmer loader; `border-left` hits are the two-bar pause glyph and a chart axis, not side-stripe cards. No italic, no serif, no glow.

## Problems found (and fix status)
| # | Where | Problem | Law / source | Fix |
|---|---|---|---|---|
| 1 | caregiver, all states | `.empty-day { display:flex }` overrode `[hidden]`: "Nothing heard yet today." sat on top of a day that had vacuuming (live-paused phone) | law 4 (every state designed), correctness | Global `[hidden] { display:none !important }` — **fixed** |
| 2 | caregiver desktop | Day bar spent ~70% of its width on the future; at 393 px a 20-min block was ~6 px (unreadable, untappable); only one label fitted | PRD §9.4 narrow rules, law 10 | Bar spans 6 AM → a little after now (≥ 6 h; whole day once late) — **fixed**, decision logged |
| 3 | caregiver phone | Title wrapped to two lines beside a long "How sure is Kettle?" button | hierarchy | Button shortens to "How sure?" under 520 px — **fixed** |
| 4 | caregiver + kitchen, paused | Pause glyph drew as a rounded "( )" after the radius consolidation | glyph clarity | Square bars (radius 0) — **fixed** |
| 5 | kitchen phone | Hour ticks collided ("6 AM7 AM") | law 5 | Tick step chosen so each label gets ≥ 64 px — **fixed** |
| 6 | how-sure phone | Per-activity table cut off at the right ("Rig / wher / says") | law 10 | Below 520 px the precision and N columns drop (still in the desktop table and metrics.md) — **fixed** |
| 7 | kitchen mic-denied | "Steps for a helper" had no disclosure marker; looked like plain text | affordance | `summary` as a list item with its triangle — **fixed** |
| 8 | kitchen, every state | Content pinned top-left over a large empty area on a screen read from 1–2 m | composition | Main column vertically centred — **fixed** |
| 9 | kitchen consent | Copy says "Meera sees a day timeline like this one" but no timeline was shown | copy ↔ screen mismatch | A drawn example bar tagged "Example, not real" — **fixed** |
| 10 | caregiver never-started | A judge's first screen: an empty bar and "Kettle isn't on yet", with the sample day buried below the fold | first 15 seconds (AGENTS.md §4) | Intro card under the heartbeat with "Play a sample day" as the primary action — **fixed** |
| 11 | caregiver | Heartbeat line was `aria-live` and changes every second | a11y spam | Only state changes are announced, via one polite region; new blocks announced ("Washing up, 8:45 AM, how sure: high") — **fixed** |
| 12 | how-sure | Verdict capitalised names mid-sentence ("catches Vacuuming and TV") | copy | Lower-cased — **fixed** |
| 13 | rule-editor sheet | Closed sheet leaked into full-page captures (only translated off-screen) | law 6 | `visibility:hidden` when closed, delayed so the exit still animates — **fixed** |
| 14 | type and radius scale | 12 radii and 5 raw font sizes | law 1 | Radii now 0/4/6/8/12/16/20/pill (the PRD hierarchy); every size is one of the 8 tokens — **fixed** |
| 15 | activity colours | First palette failed `validate_palette.js` (slate pair ΔE 13 normal vision; teal/rose ΔE 3.8 for deuteranopes) | dataviz skill | Reference palette hues assigned so real neighbours pass CVD and normal-vision checks in both themes; red reserved — **fixed** |
| 16 | kitchen "starting" | Under heavy CPU load the headline stayed "Listening…" for 30 s | live latency | Re-check in round 2 with the machine idle (privacy-check run reached "Listening for kitchen sounds") |
| 17 | how-sure, dark | Plot PNGs are white boxes on the dark canvas | dark mode | Open: accept for now (dark mode is 3rd in the cut order); revisit in round 3 |

## Motion added this round
Block settle (scaleX from its left edge, 380 ms out-curve) + label fade-in (+120 ms, 4 px rise, 3 px blur) + summary blur-crossfade; press feedback `scale(.97)` 160 ms on every button; heartbeat "last heard" digits roll (160 ms) without moving the sentence; how-sure headline numbers count up once (600 ms). `prefers-reduced-motion`: animations off, 120 ms opacity only.

## Full round-1 capture (11:42–11:55 CT): all 33 states × desktop/phone × light/dark = 132 images, reviewed via 17 contact sheets in `round-1/sheets/` plus full-size files where needed
Sheet-by-sheet notes:
- **sheet-01 caregiver-error / caregiver-live:** error is the only red on any screen, with the time it stopped and "The day so far is shown below" — calm, factual. Live: the first minute of live blocks is invisible at a 7-hour scale (→ fix 23).
- **sheet-02 live-paused / never:** "Paused by Dad at 11:47 AM · resumes at 12:47 PM" reads as a fact, not a warning (good). Never-started: the intro card now gives a judge the sample day in one tap; on phone the now-tick crossed "The day appears here…" (→ 22).
- **sheet-03 never-top / paused (sample):** summary "So far today, after 1 earlier activity: …" is clumsy (→ 24). Working (typing) violet block at 7:45 is a real mislabel of a "moving about" stretch by the provisional head; leave it (honest), re-check with the final head.
- **sheet-04 quiet / rules-sheet:** "Not heard by 10:00 AM. Kettle was listening the whole time." + "First heard at 10:35 AM." is exactly the PRD's Missed copy; amber dot, no red. A long "Not sure" hatch over the quiet stretch: diagnosed as θ = 0.67 on the provisional head (quiet clips at 0.59), not the novelty gate (distances 6–21 vs threshold 29) → re-check after M3. Rule sheet: scrim + bottom sheet, 44 px fields; fine on phone.
- **sheet-05 stale / try-not-audio:** stale heartbeat in amber with "Nothing is known after that"; cross-hatched gap; Can't-tell on the 10 AM check. "That isn't audio Kettle can read. Try a WAV, MP3, M4A or OGG file." is designed and calm.
- **sheet-06 try-washing-up / try-white-noise:** the held-out washing-up clip came back "wasn't sure about any of this" (same θ cause as sheet-04); white noise correctly says not sure. The golden "clear" and "unclear" try clips will be chosen by a stated rule after the head is frozen.
- **sheet-07 tv / usual:** TV check now "over" (TV for 4 h 16 min, from 12:50 PM) and the morning check "Can't tell" because the laptop was asleep until 12:30: the scenario shows both states it was built for. Summary "TV from about 12:45 PM and again from about 2:45 PM" reads naturally.
- **sheet-08 usual-evidence / usual-full:** evidence card unfolds inline under the bar (not a modal): "Cooking 8:10–8:25 AM · 3 windows · how sure: high · Sounds Kettle heard: mostly dishes, some door and rain" — the room-tone labels are gone; "rain" on a cooking clip is the encoder's honest evidence (frying can sound like rain).
- **sheet-09/10 how-sure (+ empty, top):** meal-activity stats now sit under macro F1; empty state designed. Dark "top" capture fired before the data loaded (harness timing, → 25).
- **sheet-10/11 kitchen consent 1–2 / declined:** the example bar makes "a timeline like this one" concrete; teach-back step is one question with two big answers; vertically centred.
- **sheet-12 kitchen-error / listening:** "Kettle has stopped." with a helper fold; listening lists every check Meera set. Phone hour ticks collided after a viewport resize (→ 21).
- **sheet-13/14 mic-asking / mic-denied / no-mic / pause-menu:** each one decision per screen with a named way out ("Play a sample day instead"). Pause menu: three options, "Don't pause" as a quiet link.
- **sheet-15 paused / resumed:** "Meera sees: Paused by you at 11:47 AM. Starts listening again at 12:47 PM." — tells the parent exactly what the caregiver sees. Resumed chip showed a bare "…" (→ 20).
- **sheet-16 sample-day / starting:** sample-day Pause button was secondary-styled while live Pause is primary (→ 19). Starting: "Waiting for the first sound…" chip.
- **sheet-17 kitchen-weekly:** showed the sample-day screen instead of "Keep it on?" — the demo branch was checked before the weekly rule (→ 18, a real bug).

| # | Problem | Fix |
|---|---|---|
| 18 | Weekly "Keep it on?" never shown during a sample day | Demo screen checked after consent/off/paused/weekly — **fixed** |
| 19 | Sample-day Pause styled secondary | Primary, same as live — **fixed** |
| 20 | Resumed chip "…" | "Waiting for the first sound…" — **fixed** |
| 21 | Ticks collide after resize | Re-render on `resize`; harness waits 900 ms after resizing — **fixed** |
| 22 | Now-tick through the empty-day message | Hidden while the day has no blocks — **fixed** |
| 23 | Sub-minute live blocks invisible | `min-width: 3px` — **fixed** |
| 24 | "after 1 earlier activity" | "… One earlier activity is on the bar." — **fixed** |
| 25 | How-sure captured before data | Harness waits 3.5 s — **fixed** |

CSS audit after fixes: 0 FIX; 3 easings; radii = PRD hierarchy; 8 font sizes (all tokens); reduced-motion block present.
