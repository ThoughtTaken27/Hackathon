# UI patterns: what to take, what to avoid, and Kettle's screens in words (Sat Nov 14, 2026)

Sources: store screenshots and public site images saved in `shots/` (public pages only; **never shipped in the app**), plus detailed screenshot descriptions in `raw/aside-*.txt`. Measurements are estimated from the saved images (pixel ratios on the screenshot, not device points) and marked ≈.

## What each incumbent's main screen actually puts first

| Product | First thing the caregiver sees | Measured / observed | Reads as |
|---|---|---|---|
| Howz (`shots/howz-1.webp`, Play) | A 24-hour clock dial; the centre says the **last event** ("Movement in Bedroom · 2 hours ago") | Dial ≈ 73% of screen width; 24 hour numbers around it; day = amber, night = navy ring; activity = small grey/green dots *outside* the ring; three icon-only round buttons (grey walker, green door, green network) with no labels | Calm and branded, but **the day's meaning is not on the screen**: you see the last motion, not "did he eat". Dots are tiny; icon-only status buttons are ambiguous (grey = ok? off?) |
| Howz timeline (`shots/howz-site-timeline.jpg`) | A list: "Movement in Kitchen 16:37", "Fridge Door closed 16:34", "Toilet opened 15:59" | Rounded cards grouped by burst ("16:02–16:07 (2)"), green room icons, ≈ 5 events per screen | **Raw sensor events, not activities.** Toilet events listed to the minute feel surveillant |
| Howz settings (`shots/howz-site-alerts.jpg`) | Grouped toggles: Day (First activity, Late start, Low day activity, Temp < 16c), Night (Up in the night, No night activity), 24 h (Unexpected activity, Door opened, Door left open) | iOS-style list, green toggles | **Good:** plain-language rule names the family understands |
| Howz devices (Play) | Green tiles per sensor with last-seen time and temperature | Demo shows "Back Door" last seen 13 months before the screenshot date with no warning styling | **Anti-pattern:** a dead sensor looks the same as a live one ("no news" ambiguity) |
| Canary Care dashboard (`shots/canarycare-play-2.png`) | Yellow banner: red "3", orange "6", "9 alerts in the past 24 hours"; then "Last recorded events" | Banner ≈ 6% of height; event cards ≈ 12% each, ≈ 5 per screen; CAPS grey label + bold detail + full timestamp; events from November mixed with August and February | **Alarming and stale**: alert counts lead, and old events sit beside today's |
| Canary Care timeline (`shots/canarycare-play-6.png`) | Swim lanes per sensor (Alerts, Visitor cards, Kitchen, Fridge, Stairs, Sitting room, back door, front door) over ~22 h | 8 lanes ≈ 100 px each on 1200; right-aligned 16 px labels; door lanes drawn as solid red dashed lines across the whole day; sitting room also red | **Red means nothing in particular** (doors, rooms and alerts share it). Dense, engineer-facing |
| StackCare (Play, described) | Four cards: Sleep 7.2 h, Bathroom 16 times "TYPICAL", Activity 2:28 PM, Temperature | Big olive numbers; one-word tag; pill gauge green-middle, orange/red ends | **Good:** a typical-range gauge explains "normal" at a glance. Bad: bathroom counts at 4 AM are intimate |
| Care Daily (Play, described) | A shield: green "Looking good · Everything looks normal · 10 seconds ago"; orange "Check in · Something doesn't look right"; red "Help needed!" | 3 states, one headline sentence each, 3 supporting rows | **Best status language found**: a sentence plus *when it was last checked* |
| Caregiver Aware (Play, described) | "Mom's House": "Morning Activity: Up and Active" (green), "Last Motion: Today at 12:00 PM", trends with arrows | Household-level hours of activity vs a goal line | Calm; "Rise and Shine" naming is warm. Household totals hide who did what |
| havn (site images, described) | "Current Status: Living Room · ACTIVE NOW · entered 1:50 PM"; counts Toilet 05, Fridge 10, Shower 02; sleep efficiency 80% | Two-digit zero-padded counts; red alert cards ("22°C Room High Temperature Alert") | Live location of the parent ("ACTIVE NOW in Living Room") is the most surveillant pattern found |
| Alexa Together (reviews, described) | An activity feed grouped by type ("Entertainment"), never the content | "First activity of the day detected for Michael at 4:39 AM" push | Good privacy grain (type, not content). Reviewer: alerts at varying times "made her a bit anxious" |
| Apple Sound Recognition (REA, on this Mac) | A notification per sound | System strings (REA `ev_b1d3865a…`): titles "Loud Kettle", "Loud Water Running", "Loud Door Knock"; body "Sound levels hit 85 decibels, which may be from a kettle." | Hedged, honest copy ("may be from"), but one alert per event = alert fatigue for a caregiver |

## Patterns worth taking (and where they came from)

1. **One-sentence status with the check time** (Care Daily: "Looking good · Everything looks normal · 10 seconds ago"). Kettle: "Listening · last checked 40 s ago" plus a one-line day summary.
2. **Plain-language rule names the family already uses** (Howz: "Late start", "Low day activity"; Caregiver Aware: "Rise and Shine"; Canary: "No Movement Detected"). Kettle's one rule reads "No kitchen sound by 11:00".
3. **Show "typical" in context, not a bare number** (StackCare pill gauge with a green middle). Kettle: later, a faint "usual" band on the day bar; for now, the honest per-activity "How sure is Kettle?" panel.
4. **Type, not content** (Alexa Together's feed showed "Entertainment", never the song). Kettle shows "TV" or "Conversation", never words.
5. **Hedged evidence copy** (Apple: "may be from a kettle"). Kettle: "Sounds like dishes (pots and pans 0.36, cutlery 0.19)".
6. **Burst grouping** (Howz: "16:02–16:07 (2)"). Kettle merges consecutive windows into one block with a start and end time.
7. **Calm palette with one accent** (Howz green/amber/navy; Care Daily green/orange/red reserved for state). Kettle reserves colour for activities and uses grey for "not listening" and hatching for "not sure"; red is never used for an ordinary activity.
8. **Resident sees what the family sees** (havn). Kettle puts the same day bar on the kitchen device.

## Anti-patterns to avoid

1. **Leading with alarm counts** (Canary's red/orange "9 alerts in the past 24 hours" banner).
2. **Raw sensor events as the timeline** (Howz "Toilet opened 15:59"; Canary swim lanes). Users want meaning ("he had breakfast"), and three Reddit threads ask for exactly that.
3. **Live location of the person** (havn "ACTIVE NOW · Living Room"). Kettle shows what *happened in the kitchen*, minutes late by design, never where Dad is right now.
4. **Intimate counts** (bathroom visits at 4 AM, toilet opened/closed, shower counts). Kettle has no bathroom device and no such class.
5. **Dead sensors that look alive** (Howz device tile last seen 13 months ago). Kettle's heartbeat is the first line and turns grey with a time.
6. **Red for non-urgent things** (Canary door lanes, havn temperature cards).
7. **A clock face for a day** (Howz 24-number dial): hard to read at a glance and hides durations. A left-to-right bar is faster to read.
8. **Icon-only status buttons** (Howz's three round buttons). Every Kettle state has words.
9. **One push per detected sound** (Apple SR, Alexa smart alerts). Kettle sends nothing by default.

## Kettle's main screens, first sketch in words

Design rules from above: big type, the result and its "why" visible without scrolling, words for every state, no red for ordinary life, "Prototype, not medical advice" on every screen.

1. **Caregiver: "Dad's kitchen today"** (laptop 1440×900 and phone 393×852)
   - Line 1, the heartbeat: green dot "Listening · last checked 40 s ago" / grey "Not listening since 10:42 AM, the laptop may be asleep or the mic off" / blue "Paused by Dad at 2:14 PM".
   - Line 2, one sentence: "A normal morning so far: cooking 8:20–8:40, dishes 8:45, TV from 9:10." (built from the blocks by a template, not an LLM).
   - The day bar, 6 AM to midnight, left to right: coloured labelled blocks (Cooking, Dishes, Eating, TV, Conversation, Vacuum, Working, Other); "Quiet" drawn as a thin neutral line (heard, nothing happening); "Not listening" as a gap with a grey hatch; "Not sure" as a hatched block with a "?" label.
   - Tap or hover a block: the evidence card, "Sounds like dishes · how sure: high · pots and pans 0.36, cutlery 0.19 · 8:45–8:52 (4 windows)".
   - The rule line: "No kitchen sound by 11:00? Off / On", and its state in words.
   - Footer: "No audio saved. No words kept. Only these labels." · "How sure is Kettle?" link · "Prototype, not medical advice."
2. **Parent: the kitchen device** (the same laptop or an old phone on a stand)
   - Very large type: "Kettle is listening for kitchen sounds." The same day bar, larger, with fewer labels.
   - One huge button: **Pause listening** (and "Resume"). Paused state reads "Paused. Nothing is being heard." and shows on the caregiver screen.
3. **First run: consent, on the parent's device**
   - Three short lines read aloud: what it listens for, that it keeps no audio and no words, that you can pause anytime. Two buttons: "Yes, start" and "Not now". Nothing listens before "Yes, start".
4. **"How sure is Kettle?"**
   - The per-activity table from `results/metrics.json` in plain words: "Catches TV almost always; often confuses cooking with eating; 'Other' is its weakest", with N and the date of the eval run. Numbers are read from the results file, never typed.
5. **Demo: "Play a sample day"** (no mic, no keys)
   - Replays a cached day built from real SINS clips' labels so a judge with no microphone sees the full flow; clearly badged "Sample day (recorded data)".
- Designed states to cover in stage 3: before the first window ("Listening… the first label appears in about 10 seconds"), not listening, paused, not sure, quiet, garbage input (white noise or music, which shows "Not sure" or "Other", never a confident wrong activity, and is measured), and the rule firing vs not listening.
