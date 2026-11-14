# Design critique, round 2 (Sat Nov 14, 13:31–13:45 CT)

Capture: `round-2/` — 34 states (the "unclear clip" input added) × desktop/phone × light/dark = 136 images, final frozen head.
Every image reviewed through the 17 contact sheets in `round-2/sheets/`; full-size files opened where needed.
A fresh subagent design critic (Sonnet 5.5, no prior context) reviewed the same sheets independently (its report is summarised below).

## My review, sheet by sheet
- **01 caregiver-error / live:** legend now lists only what's on today's bar (live: Vacuuming, Not sure, Paused, Quiet). Live checks read "Can't tell: Kettle wasn't listening from 6:00–10:00 AM" on a day Kettle started at 1:31 PM: true but reads like a fault (→ fix B4).
- **02 live-paused / never:** "Paused by Dad at 1:32 PM · resumes at 2:32 PM" calm and factual; intro card leads the never-started page.
- **03 never-top / paused (sample):** the frozen head shows the first quiet hour as hatched "Not sure" (SINS quiet clips sit near θ). The hatch is louder than the thin Quiet line, so an uncertain empty kitchen looks like more happened than real cooking (→ fix B1).
- **04 quiet / rules-sheet:** Missed copy exactly as specified; the phone rule sheet clips the check select and "Remove" (→ B9).
- **05 stale / try-not-audio, 06 try-unclear / try-washing-up, 07 try-white-noise / tv:** designed results for every input; the unclear clip doesn't show its closest guesses like the bar's Not-sure card does (→ B2); on desktop the result lands below the fold (→ B3). TV afternoon: with the frozen head several later TV clips are "Not sure", so the TV check honestly says Can't tell (3 h 32 min heard; laptop asleep until 12:30) — scenario description corrected rather than the clips changed.
- **08 usual / usual-evidence:** evidence "mostly door, some dishes and cupboard" on a cooking block is honest encoder evidence. Medium-confidence blocks at 70% opacity read as a different, pale activity (→ B6).
- **09–10 how-sure (+ empty, top):** held-out numbers lead; verdict "Kettle catches quiet and TV almost always. It most often mixes up moving about and working (typing). Moving about is its weakest activity." comes after the Apple sentence and is the plainer of the two (→ B8).
- **11–12 kitchen consent / declined / error:** example bar works; error screen showed the "Sample day" tag beside "Kettle has stopped" (→ B7).
- **13–17 kitchen listening / mic / pause / paused / resumed / sample / starting / weekly:** round-1 fixes hold (weekly screen in sample day, primary Pause, ticks, resumed chip). Content still hugs the left on a 1440-wide screen (→ B7).

## Fresh critic (subagent) — verdict: needs-fix (close); no hard bans; "calmer than every incumbent in ui-patterns.md"
Top six: (1) kitchen hierarchy for a 79-year-old — too many equal-weight blocks, centre the column (max 960 px), bigger body; (2) kitchen composition — bigger status dot, demo tag under the message and never on the error screen; (3) caregiver phone top third cluttered — smaller title and summary, hide the demo caption on phone; (4) "Can't tell" on a day Kettle started late reads as failure — say it started late, mute the card; (5) medium-confidence opacity reads as another activity, evidence "Details" lacks affordance; (6) how-sure hierarchy — plain verdict first, "Overall score" instead of jargon. Calm-vs-surveillant notes: "last heard 0 s ago" is a live-presence cue; the caregiver page never says Dad can see and pause it. Confusions: "Read this to me" is the smallest control but the one a person with memory loss needs most; "A box will pop up…" has no way out if nothing pops up.

## What changed (and what we didn't take)
| # | Change | Source |
|---|---|---|
| B1 | "Not sure" blocks drawn half-height with a light hatch (less ink than activity, more than Quiet) | my review |
| B2 | Unclear uploads show "Closest guesses: … (below the 66% bar…)" | my review / PRD §9.4 |
| B3 | Try results scroll into view (reduced motion: instant) | my review + critic |
| B4 | Checks: "Can't tell: Kettle started at 1:31 PM, after this check's time." and Can't-tell/Not-yet/Under in regular weight; test added | critic 4 (kept the state Can't tell: never Met, never Missed) |
| B5 | "Listening · last heard just now" under 10 s; caregiver footer "Dad sees the same day on his kitchen screen and can pause Kettle any time." | critic §3 |
| B6 | Medium confidence = inner ring, not opacity; evidence "Details" underlined with its disclosure triangle | critic 5 |
| B7 | Kitchen: column max 960 px, 28 px status dot, demo tag under the message and hidden on error, "Read this to me" a full 64 px button, "No box appeared? Try again" on the mic prompt, "Checks Meera set:" | critic 1, 2 + confusions |
| B8 | How sure: plain verdict first (24 px), Apple comparison second (17 px), heading "Overall score (higher is better): macro F1…" | critic 6 |
| B9 | Rule sheet fields can't overflow on phone | critic confusions |
| B10 | Phone: title 24 px, summary 17 px, demo caption hidden | critic 3 |
| Skipped | Collapsing Meera's checks behind a toggle on the kitchen screen | PRD §9.3: every check is listed to the parent so nothing is hidden from him; wording tightened instead |
| Skipped | Hiding the legend on phone | colour is never the only cue; the legend is the cheap guarantee |
| Skipped | Sticky section anchors on how-sure | scope; the page already leads with the verdict and numbers |

CSS audit after fixes: see round 3.
