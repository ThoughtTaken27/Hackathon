# Kettle demo video: faceless, voice-over only (record in ~40 minutes)

No camera, no actors, no faces. Only: **screen recordings of Kettle**, **3–4 free stock photos**, and **one voice-over**.
Length **1:55** (limit 2:00), in the brief's structure: problem ~15 s · demo ~60 s · how it works + baseline ~30 s · limit + next ~15 s.
**Bold** = exact words on a button or screen. 🎙 = what the narrator says.

---

## 1. Get ready (10 minutes)

### 1.1 Stock photos (5 minutes, free, no attribution required but we credit them anyway)
Download from **Unsplash** (unsplash.com, Unsplash License) or **Pexels** (pexels.com, Pexels License). Pick photos with **no recognisable face** (backs, hands, silhouettes) so nobody can be mistaken for a real patient:
| # | Search for | Used in |
|---|---|---|
| P1 | "elderly man kitchen" or "old hands tea cup" | 0:00 |
| P2 | "empty kitchen morning" | 0:05 |
| P3 | "woman looking at phone desk" (back or hands only) | 0:10 |
| P4 (optional) | "smoke detector ceiling" | 1:10 |
Write down each photo's page link and photographer name: paste them into the YouTube description and the credits (section 5).

**Photos the team picked (credited in the write-up's Sources):**
- P1 old man holding a cup: https://www.dreamstime.com/photos-images/old-man-holding-cup.html
- P2 empty kitchen: https://www.dreamstime.com/water-tap-professional-kitchen-restaurant-modern-equipment-devices-empty-morning-interior-made-stainless-steel-image143073683
- P3 person looking at a phone: https://www.istockphoto.com/photos/black-woman-looking-at-phone-from-behind (tip: lay a screenshot of Meera's red banner onto the blank phone screen in the editor)
- P4 smoke detector: https://sen.news/smoke-sensors-on-steep-ceilings/
Dreamstime and iStock previews carry watermarks and are licensed images: swap in free Pexels/Unsplash look-alikes if there's time.

### 1.2 The app, on one laptop (5 minutes)
Use the live site if it has tonight's update (open `https://kettle.parth-dev.workers.dev/api/push/key`: it should show `{"publicKey":…}`), otherwise run it locally: `cd web && npm install && node dev.mjs` → `http://localhost:8787`.

Two Chrome windows, side by side, so one screen recording captures both:
- **Left = Dad's kitchen laptop**: a normal window (~60% of the screen).
- **Right = Meera's phone**: an **Incognito** window (⌘/Ctrl+Shift+N), narrow (~420 px wide).
- Zoom both to **110–125%**, hide the bookmarks bar, close other tabs, turn on Do Not Disturb.

**Create the home (right window):** `/start` → **On my own phone or computer** → **Who is this for?** **My parent** → **What do you call them?** type **Dad** → **Where will the device listen?** **Kitchen** → **Your first name** type **Meera** → **Create our Kettle** → next to the link click **Copy** → then **Open my family view**.
**Join from the kitchen (left window):** paste the link → stop here (don't click yet; the recording starts on this screen).

Screen recorder ready: Mac **⌘+Shift+5 → Record Selected Portion**; Windows **Win+Alt+R** (Xbox Game Bar) or the Snipping Tool's video mode. Record without the address bar if you can (it shows "parth-dev" on the live site); otherwise crop it in the edit.

---

## 2. The recordings (15 minutes, 4 short clips)

### Clip A: he says yes (left window, ~20 s)
1. Screen: **This laptop listens for kitchen sounds.** Hover **Read this to me** for 2 s → click **Next**.
2. Screen: **Is it OK for Meera to see this?** → click **Yes, Meera can see this**.
3. Screen: **Where should this laptop live?** → **It's in place. Start listening** → Chrome asks for the microphone → **Allow**.
4. Sound check: clink a spoon on a mug or run the tap near the laptop for 10 s. Then click **Next** (or **Next anyway**), then **Do it later** on **Teach Kettle this kitchen**.
5. You're on **Listening for kitchen sounds**. Stop the recording.

### Clip B: a normal moment, both windows (~40 s)
Start recording both windows. Near the laptop, make real kitchen sound for 30 s: run the tap into a bowl, clink dishes, stir a pan. (Real sounds only, no phone speaker, no TV.)
- Left: the big chip changes to **Sounds like washing up** (or **cooking**).
- Right: within ~10 s a coloured block appears on Meera's day bar and the summary **So far today: …**. Click the block once to open its **why** card.
If it only says **Not sure what that is**, keep going 20 s more, closer to the laptop. Stop recording.

### Clip C: the urgent alert, both windows (~30 s)
Start recording both windows. Then:
1. Left (kitchen): click **I need help** (bottom row of buttons).
   - Left turns red: **Meera has been told you need help.** · *If you need help now, call 911 or a neighbour. Kettle can't call for help itself.*
2. Right (Meera): within ~5 s a **red banner** appears at the top: **URGENT · (time)** · **Dad pressed "I need help" at (time).** · *Dad pressed "I need help". Call Dad now.* · *Kettle is a prototype. It doesn't replace a smoke or CO detector, or 911.* The tab title becomes **● Urgent · Kettle**.
3. Wait 3 s, then right: click **I've seen this**. Stop recording.

*(Optional, only if someone has a real smoke detector within reach: press its **test button** next to the laptop for ~20 s instead of step 1. After about 20 s the left shows **Urgent: Kettle heard a smoke alarm.** and the right turns red with **Kettle heard a smoke alarm at …**. In our browser test this took 19.9 s, then 2.8 s to the family. If nothing happens in 40 s, use the button.)*

### Clip D: the evidence (one window, wide, ~60 s; no microphone needed)
1. Front page `/`: let the top sample day animate for 8 s. Scroll to the three big numbers (**84.1**, **89%**, **0**) and hold 3 s.
2. Click **How sure** in the top bar. Scroll slowly, holding 3 s on each:
   - the systems table: **Kettle, one microphone 84.1**, **Apple SoundAnalysis, zero-shot 31.8**, **Always "Quiet" 5.0**;
   - **Urgent alerts: what turns red, and how often it's right**: the line **0 false urgent alerts in 12.3 hours of ordinary home sound** and the row **Smoke or fire alarm, during cooking 88.3%**;
   - **Outside the research home: the test that changed Kettle** (the honest limit).
Stop recording.

---

## 3. The voice-over (read it in one take, calm and warm, ~265 words)
Record on a phone's voice memo, 20 cm from the mouth, in a quiet room with soft furnishings (a closet is perfect). **A real teammate's voice; no AI voice.** No names, no school.

| Time | Picture | 🎙 Narration |
|---|---|---|
| 0:00–0:05 | P1 (slow zoom in) | *"More than one in four Americans over sixty-five live alone."* |
| 0:05–0:10 | P2 | *"When a parent starts to lose their memory, the family is often hours away, and the warning signs happen when nobody's there."* |
| 0:10–0:16 | P3 | *"Daily calls feel like checking up. Cameras feel like being watched. So families are left guessing."* |
| 0:16–0:30 | Clip A | *"Kettle turns a spare laptop in the kitchen into a calm timeline of the day, from sound alone. The parent reads what it does in plain words, and nothing listens until they say yes."* |
| 0:30–0:52 | Clip B | *"Every ten seconds, a small sound model running right on the laptop names what it hears, like cooking or washing up, then forgets the sound. No audio is ever recorded or sent. Only the label reaches the family, and they can tap it to see why."* |
| 0:52–1:15 | Clip C (P4 for 2 s at the start if you have it) | *"And when something sounds wrong, like a smoke alarm, a crash and then a cry, or a call for help, Kettle doesn't wait. The family's screen turns red within seconds, and it can notify their phone, even with the app closed."* |
| 1:15–1:45 | Clip D (front page numbers, then How sure tables) | *"Under the hood: a small pretrained audio model, CED-tiny, running in the browser, with a classifier we trained on a public recording of a real home. On test recordings it had never heard, scored once, it reaches 84 macro F1. Apple's built-in sound classifier scores 32 on the same clips. For urgent sounds, it caught a smoke alarm during cooking 88 percent of the time, with zero false urgent alerts in over twelve hours of ordinary home sound."* |
| 1:45–1:55 | Clip D (the limit section), then end card | *"Where it falls short: in homes it never trained on, it often says 'not sure', and our alarm tests used synthetic sounds. Next, we test it with real families. Kettle: know the day went okay, without a camera."* |

**End card (last 3 s, plain background):** **Kettle · Know the day went okay, without a camera.** and below it **This project is a prototype and is not medical advice.**

### Every number you say, and where it comes from
| Spoken | Exact | Source |
|---|---|---|
| more than one in four over 65 live alone | ~28% of community-dwelling adults 65+ | ACL 2023 Profile of Older Americans |
| 84 macro F1 | 84.1 [74.4, 86.7], 7,791 held-out clips | `results/metrics.json` |
| Apple scores 32 | 31.8 [25.7, 37.9], same clips | `results/metrics.json` |
| smoke alarm during cooking 88 percent | 88.3% (53/60 held-out timelines) | `results/safety.json` |
| zero false urgent alerts in over twelve hours | 0 in 12.3 h | `results/safety.json` |

Don't say "it detects falls", "it calls 911", or any number for gunshots or shouting (not measured).

---

## 4. Edit (15 minutes: CapCut, iMovie, Clipchamp or DaVinci)
1. Put the voice-over on the timeline first. Lay pictures under it in the table's order.
2. Photos: slow zoom (Ken Burns) 5 s each.
3. Speed up the waits in clips B and C (2–4×) and add a small caption **"seconds later"** where you cut. Never hide that time passed.
4. Captions: auto-generate subtitles from the voice-over; check the numbers are spelled right.
5. Crop/blur the address bar if it shows "parth-dev". No real names anywhere (only **Dad** and **Meera**, both invented).
6. Optional quiet piano under 0:00–0:16 and the end card only.
7. Export 1080p MP4, **under 2:00**.

---

## 5. Upload (5 minutes)
1. YouTube → Upload → title **Kettle: know the day went okay, without a camera** → **Unlisted**. (If the channel shows a real name, use Google Drive → **Anyone with the link → Viewer** instead.)
2. Description: *"Prototype, not medical advice. Images: old man holding a cup and empty kitchen (Dreamstime), person looking at a phone (iStock), smoke detector (sen.news)"* followed by the four links above (or your Pexels/Unsplash replacements).
3. Open the link in an **incognito** window: it plays without signing in.
4. Paste the link into the submission form.
