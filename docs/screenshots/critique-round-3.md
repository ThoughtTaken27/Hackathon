# Design critique, round 3 (Sat Nov 14, 13:42–14:05 CT)

Capture: `round-3/` — 34 states × desktop/phone × light/dark = 136 images, with the round-2 fixes. Every image reviewed via the 17
contact sheets in `round-3/sheets/` (full-size files opened where needed). A fresh "older adult and caregiver" usability subagent
(Sonnet 5.5, no prior context) walked Ravi (79, kitchen laptop, 1–2 m) and Meera (34, phone, between meetings) through the
screens; its findings are below with what changed.

## My review
- Round-2 fixes all landed: the kitchen column is centred at ≤ 960 px, the 28 px status dot reads from across a room,
  "Read this to me" is a full 64 px button, the mic prompt has a way out, no demo tag on "Kettle has stopped", the phone title is one
  line, the summary is 17 px on phone, "last heard just now", lighter half-height "Not sure", closest guesses on unclear uploads.
- Late-start check copy reads correctly ("Can't tell: Kettle started at 12:30 PM, after this check's time"), but on a never-started
  day it said "Kettle started, after this check's time" → now "Can't tell: Kettle hasn't heard anything yet today." (test added).
- Stability check (component-craft law 5): during a live sample day, unchanged blocks moved 0 px; nodes removed fell from 4 to 1 after
  keying blocks by start time (the remaining one is a real merge of two blocks). `results/stability.json`.
- CSS audit: 0 FIX; radii = 0/4/6/8/12/16/20/pill; 8 font sizes, all tokens; 3 easings; reduced-motion honoured; hatches/shimmer
  are the only gradients; the only `border-left` rules are the pause glyph and a chart axis.

## Usability walkthrough (subagent) → changes
| # | Finding (who; risk) | Change |
|---|---|---|
| U1 | Quiet morning: card said "Not heard by 10:00 AM" while the bar showed sounds Kettle couldn't name just before 10 (Meera; false alarm / contradiction); "You might call to say hello" missing | Card now: "No clear kitchen activity by 10:00 AM. Kettle heard sounds it couldn't name (9:30–10:00 AM)." and keeps "You might call to say hello." (test) |
| U2 | "Met at 8:05 AM (cooking)" rested on a medium-confidence block whose evidence was mostly door sounds (Meera; false reassurance) | Met now says "how sure: medium/high" (test). Not-sure blocks already never satisfy a check |
| U3 | Pause menu kept "Listening for kitchen sounds" and made 15 min the dark default; "Don't pause" a tiny link; Turn it off disappears when paused (Ravi; could feel tricked) | While choosing: "How long should Kettle stop listening?"; three equal options; a real "Cancel" button; "Turn it off" stays on the paused screen |
| U4 | Paused / asleep / stopped days still read "So far today: …" like a settled day (Meera; false reassurance) | The summary adds "Nothing is known after {time}." whenever Kettle is paused, asleep, off or blocked |
| U5 | The microphone was never named before it failed; the denied screen put the blame on Ravi (Ravi; tricked) | Consent: "It uses this laptop's microphone…"; denied: "The laptop's microphone is switched off for Kettle. This isn't something you did wrong." |
| U6 | "Kettle stopped working" had no next step (Meera) | "…Dad's screen asks him to press Try again; a call is the only way to know more. Below: the day before it stopped." |
| U7 | Weekly question didn't say what happens if ignored; "Keep it on" was the dark default; "Paused from 1:42–1:42 PM" looked broken (Ravi) | "If nobody answers, Kettle pauses tomorrow until you choose."; equal-weight answers; sub-minute pauses read "Paused for under a minute." |
| U8 | "How sure" opens with jargon about the wrong activities (Meera) | Opens with: "For the kitchen, on test clips it had never heard: Kettle caught X% of cooking, Y% of washing up and Z% of eating. When it isn't sure, it says 'Not sure'…" (numbers from metrics.json) |
| U9 | "Checks Meera set" can read like a to-do list for Ravi | "Checks Meera set (they only read the timeline; Kettle tells her nothing else):" |
| Skipped | Remove "Play a sample day instead" from Ravi's mic screens | PRD §9.4 specifies it there (the judge's fallback when a laptop has no mic); kept as the secondary button |
| Skipped | "Stay paused" button | Scope; "Pause until tomorrow morning" covers it |
