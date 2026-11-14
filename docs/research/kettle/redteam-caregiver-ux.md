# Red team: caregiver and older-adult UX of Kettle

Read: PRD lines 1-349 (§0-§9; the architecture half was not needed), better-than.md, BRIEF extraction, RULES-AND-RUBRIC. Verdict: this is far less creepy than the incumbents, but five details still read as watching. All are copy or small-UI fixes.

## 1. Does this feel like surveillance?

**Ravi's side (79, alone, memory slipping).**
- The 56 px chip "Sounds like washing up" is a live commentary on him, in his own kitchen, in huge type. It is the demo's best moment and the most watched-feeling element. Fix: on the real kitchen screen keep a small status line ("Listening") and show the chip only in demo mode or behind a "What does it hear?" tap.
- Caregiver rules are invisible to him. Meera sets "Kitchen activity by 10:00 AM", but S2 only says "Meera can see this page too". That is inaccurate (she sees more: rules, summary) and it is a hidden check. Fix: S2 footer lists them: "Meera has set one check: kitchen activity by 10:00 AM."
- Pause is a public act. "Paused by Dad at 3:10 PM" is dignified, but it tells Meera he had company, and it teaches him that pausing gets noticed. Fix: show Meera neutral "Paused 3:10-4:10 PM" (no "by Dad", no reason), and say so on his Pause sheet.
- "Talking or TV · Kettle hears voices but can't tell a visit or a call from the TV" and "Empty room · … heard no one" are presence and visitor detection in plain words. Fix: "Talking or TV" and "Quiet".
- Minute-level times ("cooking 8:20-8:40") are a log of his life. Fix: round the summary to 15 minutes or to "this morning"; keep exact times in the evidence card only.
- A laptop on the counter has no light that says "on". Nothing tells a visitor it listens. Fix: a small printed "This laptop listens for kitchen sounds. Nothing is recorded." card for the counter (zero code).

**Meera's side.** The risk is her anxiety, not his privacy. The page is calm (no alert count, red only for a broken Kettle). Remaining issues: the rule "Missed" text "Not heard by 10:00 AM. Kettle was listening the whole time." reads as an accusation, and a live heartbeat invites refreshing every hour. Fix: add "A late morning is common." under Missed; keep "You might call to say hello."

## 2. Copy review (§9.4)

| Copy | Problem | Replacement |
| --- | --- | --- |
| "Kettle listens for kitchen sounds." | He will read "Kettle" as the appliance; the kettle is listening? | "This laptop listens for kitchen sounds. The program is called Kettle." |
| "writes down only the kind of sound" | "Writes down" contradicts "keeps nothing" for a worried reader | "It only notes the kind of sound, like 'dishes'. It keeps no recordings and no words." |
| "Meera sees this same page." | Not true (she sees rules) | "Meera sees a day timeline like this one." |
| "Your browser will ask to use the microphone. Choose Allow." | "browser" is jargon; "choose" is vague | "A box will pop up about the microphone. Press Allow." |
| Mic denied: "click the icon left of the address, set Microphone…Safari: Settings for localhost" | Technician text; he cannot do this | "Kettle can't hear the kitchen. Ask Meera or a helper to turn the microphone on." (steps in a fold) |
| Error: "Labels so far are kept. Close this page and start Kettle again" | "labels", "page" | "Kettle has stopped. Press Try again, or ask Meera for help." |
| "Pause until I resume" | He will forget; Meera sees an open-ended pause forever | "Pause until tomorrow morning" (cap at 12 h) |
| "Resumes by itself at 4:10 PM" | Good, but nobody sees the resume | Add a gentle "Kettle is listening again" status for 10 s |
| S1 not listening: "…Kettle can't tell you anything about the time since then." | Long, a little ominous | "Not listening since 10:42 AM (laptop asleep, closed or off). Nothing is known after that." |
| S1 never started: "It starts when Dad presses Yes, start" | Invites nagging | "Kettle isn't on yet. It starts when Dad chooses to turn it on." |
| "Kitchen activity by 10:00 AM" (rule title) | Fine | keep |
| Evidence "Frying 0.31 · Dishes 0.22" | Decimals mean nothing to Meera | "Frying · Dishes (mostly)" with the numbers behind "details" |
| "Not now" then "Kettle is off. Nothing is being heard." | Good, plain | keep |

Would he remember he paused? No. "Paused. Kettle isn't listening." with the resume time is right, but add the same line to the heartbeat of the idle screen after resume.

## 3. Top-10 pain points

1. Parent feels watched: **partly** (audio handling is strong; live chip, hidden rules, visible pauses still feel watched).
2. Burden on the parent: **partly** (no taps, but a laptop must stay open, awake, plugged in with a tab running; he will close the lid).
3. Missed a real problem: **partly** (rates published, but a rule only fires if Meera opens the page, and falls are out of scope, honestly stated).
4. Hub / Wi-Fi / battery: **partly** (no hub, but sleep and lid-close are the new dead-sensor).
5=. Price: **answered**.
5=. False alarms: **answered** (Not sure state, smoothing, no pushes, published FP counts).
7. Consent overridden: **partly** (see §4).
8. Discontinued: **answered** (local, open source; someone still has to restart the server).
9. App bugs / logouts: **answered**.
10a. "No news" ambiguous: **answered** (best feature in the PRD).
10b. "No activity by X" alert: **partly** (rule exists, but with no push it is a check, not an alert; users asked for the alert).

## 4. Consent and dignity

Not yet real consent. One tap on three lines, probably set up by Meera standing behind him, is a moment, not an ongoing agreement, and MCI means he may not recall it. Points:
- **No teach-back or witness.** Add one question after the three lines: "Is it OK for Meera to see this?" with two big buttons, and record "Dad agreed on Nov 14" on her screen.
- **He forgets he agreed.** The kitchen screen must re-explain itself permanently, not only on first run. Days later it should say: "Kettle has been listening in this kitchen since Monday. Meera sees the kinds of sounds, not recordings or words. [Pause] [Turn it off]".
- **Re-consent weekly.** "Kettle has been on for a week. Keep it on? [Keep it on] [Turn it off]". No answer within a day means it pauses, never keeps listening.
- **There is no Turn off, only Pause.** Add it. A parent who cannot say no stops using the laptop instead.
- **If he unplugs or closes it,** Meera sees "Not listening since…", which is neutral and correct. Never word it as a failure ("stopped working" is for crashes only), and never let her message him through the app.
- **Visitors** did not consent. The counter card helps; so does "Talking or TV" instead of visit wording.

## 5. "Wow" in the first 10 seconds (ranked)

1. **Split screen, no talking:** kitchen laptop left, Meera's phone right. Presenter clinks two plates under a tap; within about 3 s the phone's bar grows a "Washing up" block. Then speaks a sentence; the block says "Conversation" and a visible counter reads "0 words kept". The judge sees input, output and the privacy claim in 8 s.
2. **Numbers cold open:** on screen, white text: "Apple's own sound classifier: 41. Kettle: 82. Same recordings, nobody else publishes this." Then the plates clink. This hits Communication (numbers in the first 30 s) but is less visceral.
3. **The dignity beat:** Ravi presses the 96 px Pause button and the phone shows "Paused 3:10 PM". Memorable, but it needs context and is better at second 40 than second 5.

## 6. The five changes, ranked

1. **Add "Turn it off" and a weekly "Keep it on?"** plus a permanent re-explainer on the idle kitchen screen (about 1 h; moves Impact, Q&A on consent).
2. **Show Ravi the rules Meera set** and fix "Meera sees this same page" (30 min).
3. **Demote the 56 px chip on the real kitchen screen** (small "Listening", chip only in demo mode); the demo video keeps it (1 h).
4. **Rewrite the flagged copy** above, in particular rename "Kettle listens" to "This laptop listens", cap Pause at tomorrow morning, remove "visit", "heard no one", technician mic text (1-2 h).
5. **Neutral pause display and 15-minute rounding** in Meera's summary, plus the printed counter card in the README for the setup step (1 h).
