# Kettle demo video: script, shot list and how to record it

Click-by-click shooting script: `docs/DEMO-SCRIPT.md`.

**Length: 1:55 (hard limit 2:00).** Upload as **unlisted** YouTube, then open the link in a private window to check it.
Round 1 is blind: **no faces, no names, no school, no teammate names on screen or in the voice.** A real human voice reads
the narration (no AI voice). The rubric wants numbers in the first 30 seconds.

Every number spoken below comes from a results file (right-hand column). If a file changes, the number in the script changes.
Run `python -m eval.check_metrics` and re-read this table before recording.

## The script (≈ 250 words spoken at a calm pace)

| Time | On screen | Narration (read exactly) | Number source |
|---|---|---|---|
| **0:00–0:15** Hook | Front page (`/`). The hero panel plays "A usual morning": "What Kettle heard" fills in on the left, the family's day bar grows on the right | "More than one in four Americans over sixty-five live alone. When a parent has early memory loss, the person who'd notice a change in their day often lives hours away. Kettle turns a spare laptop in the kitchen into a calm timeline of the day's activity, from sound alone, without recording anything." | 28%: `docs/DATA-SOURCES.md` (ACL 2023 Profile) |
| **0:15–0:28** Numbers | Front-page stat strip (84.1, 89%, 0 audio files), then cut to How sure's top table | "On held-out benchmark recordings it had never heard, scored once, Kettle reaches 84 macro F1, and it caught about nine in ten kitchen-activity moments. No audio is ever saved." | `results/metrics.json`: `dcase_eval.ours_ch0.macro_f1` 84.1, `meal_activity`: 1,039 of 1,183 raw (87.8%), 89.3% reweighted ("about nine in ten" is true of both); privacy check 0 files |
| **0:28–0:40** The parent says yes | Kitchen screen (laptop window): "This laptop listens for kitchen sounds." → "Is it OK for Asha to see this?" → press **Yes** → setup step 4 "Teach Kettle this kitchen" → "Ready for step 1 of 3?" | "The parent decides. Kettle explains itself in plain words, can read them aloud, and asks first. Then it spends three minutes learning this kitchen: quiet, washing up, cooking." | — |
| **0:40–0:58** Live: real cooking | Split screen: kitchen laptop left, family phone view right. Stir a real pan with a metal spoon, then run the tap. Kitchen chip changes to **"Sounds like cooking"**, then **"Sounds like washing up"**; on the phone, the blocks appear and the check turns **Met** | "Every ten seconds the laptop names what it hears and forgets the sound. Only the label leaves the kitchen. Far away, Asha sees the day fill in, and the check she set, kitchen activity by lunchtime, turns to met." | — |
| **0:58–1:08** Control and privacy | Kitchen: press **Pause → Pause for 15 minutes**. Phone heartbeat: **"Paused by Mom at …"**. Press **Resume listening** (it must be listening for the next scene). Then switch the laptop to another tab: the tab title reads **"● Listening · Kettle"** | "Mom can pause it any time, and Asha sees that honestly. It keeps listening while the laptop is used for other things." | — |
| **1:08–1:20** The parent controls what's shared | Kitchen: open **What Asha can see**, untick **Talking / TV**. Phone: **"Mom chose not to share: Talking / TV."** | "And Mom decides what's shared. If she'd rather keep the TV private, she unticks it, and Asha sees that she chose not to share it." | — |
| **1:20–1:38** How sure: misses, false alarms, baselines | How sure page: scroll the per-activity table slowly (Caught / Missed / False alarms), pause on Apple's 31.8 and "Always Quiet" | "We publish every activity's misses and false alarms separately. Apple's built-in sound classifier scores 32 on the same clips. Washing up is our weakest kitchen activity: 73 percent caught. And we can't test across age or sex: the training home had one person." | `results/metrics.json`: per-class recall, `baselines` (Apple 31.8) |
| **1:38–1:52** Honest failure → fix | How sure: "Kitchen naming after a live test in a real kitchen" table, then the named-sounds table with **hidden** next to frying and dishes, **yes** next to kettle and running water | "In a teammate's kitchen, cooking with metal pots showed as 'eating'. Each ten seconds was named from one loud tag. Now a whole stretch is named from its evidence, and every sound name had to pass a bar we wrote first. Hand-written rules passed one sound; a small trained classifier passes eight, and the rest stay hidden, not shown wrong." | `results/kitchen_naming.json`, `results/sound_head.json` |
| **1:52–1:55** Close | Family phone view, calm day bar. Small text: "Prototype, not medical advice" | "Kettle: know the day went okay, without a camera. A prototype, not medical advice." | — |

Spoken numbers to double-check against the files right before recording: 28% · 84 (84.1) · "nine in ten" (87.8% raw / 89.3% reweighted) · 32 (31.8) ·
73% (72.6 washing up) · "passes eight" (`results/sound_head.json` v2_head shown; rules: `results/sounds.json`).

## Shot list and layout

- **Screen:** 1920×1080, browser zoom 110%, dark theme (the app's default). Hide bookmarks, extensions and notifications.
  **Crop or hide the address bar**: the live site's address contains a teammate's name. Recording on `localhost` avoids it.
- **Two windows side by side** for 0:40–1:20: kitchen screen on the left (normal window, about 1200 px wide), family view on the
  right (a private window resized to phone width, about 420 px). The two pages use separate storage, so both roles work on one laptop.
- **Cursor:** slow, deliberate; click only what the narration names. No typing on camera except the pairing code, if shown.
- **Audio:** record the narration separately in a quiet room (phone voice memo is fine), then lay it over the screen recording.
  Keep the real kitchen sounds quietly under the narration at 0:40–1:20: they prove it's live.
- **Captions:** burn in short captions for the numbers (e.g. "84.1 macro F1 · held-out · scored once").

## Setup before recording (≈ 20 minutes)

1. Merged branch, on the recording laptop:
   ```bash
   cd web && npm install && node dev.mjs
   ```
   Open `http://localhost:8787`. Hard-refresh every page (Ctrl+Shift+R) so the newest version loads.
2. **Fresh home:** follow `docs/DEMO-SCRIPT.md` Take 1 (exact buttons: **On my own phone or computer** → **My parent** → **Mom** →
   **Kitchen** → first name "Asha" → **Create our Kettle** → **Copy** the kitchen link into the left window).
3. **Checks:** in the family view, **Edit** (next to Your checks) → **Remove** the defaults → add a preset whose time is still ahead
   (afternoon: **Evening meal by 8**; morning: **Lunch by 2**) → **Save**. A check whose time has passed says "Can't tell".
4. **Rehearse the kitchen sounds** 1–2 m from the laptop: a pan stirred with a metal spoon, the tap running into a bowl.
   **Use real sounds, not a phone playing a video**: sound from a speaker reads as TV to the model.
6. **Backup take first:** record one rough run of the whole thing before the good take. If the live part misbehaves, use the
   front page's **"Two screens"** section (pick **A usual morning**) for 0:40–0:58 and say "a sample day, real recordings through the same model".
7. Mute notifications; plug the laptop in; close other tabs that make noise.

## After recording

- Trim to **≤ 1:58**. Check that every on-screen number matches the narration.
- Check for names: watch it once just for names, faces, school, the address bar and the browser profile picture.
- Upload **unlisted**; title "Kettle: a calm day timeline from kitchen sounds (AI + Health)"; description: one line, the repo link
  and "Prototype, not medical advice". Open the link in a private window.
- Paste the link into the submission form and `docs/SUBMISSION.md`.

## If you only have 30 minutes

Record the front page (0:00–0:28), the How sure page (1:20–1:52) and the front page's **"Two screens"** section playing
**A usual morning** (instead of the live kitchen). That covers the hook, the numbers, the demo, the honest failure and the fix.
