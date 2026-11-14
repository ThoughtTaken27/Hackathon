# Design round 4 (final check after judge rounds; Sat Nov 14, 16:20–16:35 CT)

Capture: `python tools/screenshots.py 4` → 136 screenshots (34 states × 1440×900 and 393×852 × light and dark) + 17 contact sheets.
New this round: the capture fails if any screen shows an uncaught page error, a server traceback, or "Traceback" / "Exception" /
"undefined" / "NaN" on screen. Result: **136 screens, 0 problems** (`docs/screenshots/round-4/index.md`).
Every sheet opened and read (sheet-01 … sheet-17), plus the full-length How-sure page cropped and read at full size.

## What holds up
- **Caregiver view:** heartbeat is still the first line in every state (green "Listening · last heard just now", amber "Not listening since 6:30 PM (laptop asleep, closed or off). Nothing is known after that.", red "Kettle stopped working… Below: the day before it stopped"). Quiet thin line vs cross-hatched not-listening stays distinct in both themes.
- **Checks:** every state of the rule copy reads as a plain sentence: Met with "how sure", "Can't tell: Kettle started at 12:30 PM, after this check's time", and the quiet morning's new Missed copy "No clear kitchen activity by 10:00 AM. Kettle heard sounds it couldn't name for 1 h 15 min before then." (duration instead of a clock range: easier to read on a phone, no second time to reconcile with the deadline).
- **Parent's screens:** consent → teach-back → listening → pause menu → paused ("Meera sees: Paused by you at 4:22 PM") → resumed; the caregiver sees "Paused by Dad at 4:22 PM · resumes at 5:22 PM" at the same time. Mic denied / no mic / mic asking all give a plain sentence and a next step, no jargon.
- **Garbage and not-sure inputs:** non-audio → "That isn't audio Kettle can read. Try a WAV, MP3, M4A or OGG file."; white noise and the unclear clip → hatched "Kettle wasn't sure about any of this" with closest guesses and the 66% bar explained.
- **How sure:** lead sentence in kitchen terms, then the fair comparison; the strict kitchen-session sentence (new, addendum item 9) renders under the θ paragraph and reads plainly.

## Issues found, and what we did
| # | Issue | Fix |
|---|---|---|
| 1 | How-sure θ table header said "Meal sessions missed" while the text says "kitchen sessions" and "noticed" | Header is now "Kitchen sessions not noticed" (`static/howsure.js`) |
| 2 | White noise shows "Sounds Kettle heard: mostly speech, some music and television" | Kept: it is the encoder's real top evidence for broadband noise, shown under "Kettle wasn't sure", and the honest answer to "what did it hear". Noted for Q&A |
| 3 | Phone rules sheet: the "TV on for more than (hours)" select truncates to "(hou" at 393 px | Left (cosmetic, the field still reads as TV hours with the number beside it); listed in MORNING-BRIEF polish |
| 4 | Weekly "Keep it on?" gives both buttons equal weight | Kept on purpose: neither answer is the default for the parent (consent design, pain theme 7) |
| 5 | Kitchen page after ~30 s of listening shows only a thin green tick on a 6 AM–6 PM bar | Expected at full-day scale (min block width applies); the sample day shows the full bar. No change |

No regressions from round 3 in hierarchy, contrast or copy. Calm, not surveillant: no camera imagery, no red except "stopped".

## Recapture after the judge-round-2 copy change (16:45 CT)
Full recapture: 136 screens, 0 problems. The How-sure lead now reads "close to the official 2018 DCASE baseline's published 85 (known microphones) / 83.1 (unseen), but not directly comparable… not yet a real kitchen. For context only, Apple's built-in sound classifier (zero-shot, a different label set) scores 31.8%", and it reads well in all four size/theme variants (sheet-10). Left for Lane B: the overall-score row still shows Apple's 31.8% as a third big tile next to Kettle's; shrinking it to a footnote is a one-line change in `static/howsure.js` if the team agrees with judge round 2.
