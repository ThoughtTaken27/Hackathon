# Kettle demo video: the 3-person shoot (complete script)

**Read this whole file once, together, before anyone films anything (10 minutes).**
Everything on-screen below was checked by clicking through the current app (Sun Nov 15, evening, `main` + urgent alerts).
**Bold** = the exact words on a button or screen. 🎙 = narrator voice-over (recorded separately, afterwards).

- **Length:** 1:55 (the brief's limit is 2:00). The brief's structure: ~15 s problem · ~60 s demo · ~30 s how it works and the baseline · ~15 s limitation and next step. This script follows it exactly.
- **Story:** Ravi, 79, early memory loss, lives alone. His daughter Meera, 34, lives 300 miles away. One evening Kettle shows her a normal day, then Ravi drops a pan and goes down, and Meera's phone turns red within seconds. He presses **I'm OK** and her screen turns amber. (Same invented people as the write-up.)
- **Blind review rule (Round 1):** judges must not learn who we are. **No faces, no real names, no school, no house number or street, no family photos in frame.** Shoot hands, backs, feet and screens. In the app, type only the invented names **Dad** and **Meera**.

---

## 0. One-page cheat sheet (print this or keep it open on a phone)

| Time | Who's on camera | What happens | Screen must show |
|---|---|---|---|
| 0:00–0:15 | Ravi (back, hands) | Alone in the kitchen, kettle on, slow movements | — (camera only) |
| 0:15–0:27 | Ravi's hand + laptop | Presses **Yes, Meera can see this** | Kitchen laptop: **Is it OK for Meera to see this?** |
| 0:27–0:42 | Ravi stirring; Meera's phone | Cooking → label appears; check turns Met | Laptop chip **Sounds like cooking**; phone: day bar fills, check **Met** |
| 0:42–1:02 | Ravi's feet, the pan on the floor, the laptop | Pan crashes, Ravi kneels down, groans | Laptop turns red: **Are you OK?** (it speaks) |
| 1:02–1:10 | Meera's phone | Red notification, opens it | **Kettle: urgent** → red banner **URGENT · …** |
| 1:10–1:17 | Ravi's hand | Presses **I'm OK** | Phone banner turns amber: **Dad pressed "I'm OK"** |
| 1:17–1:45 | Screen recording | How sure page: score vs Apple, urgent alerts table | **84.1**, **31.8**, **0 false urgent alerts in 12.3 hours** |
| 1:45–1:55 | Screen recording | One honest limit, next step, disclaimer | **Prototype, not medical advice** |

**Golden rules on set:** no TV, radio or music anywhere in the house during takes · nobody talks in the kitchen during the cooking and fall shots (the narrator records later) · use real sounds, never a phone speaker · after the crash, **no kitchen sounds** (Kettle cancels a fall if cooking resumes within 2 minutes).

---

## 1. Roles (decide who is who in the first minute)

| Role | On camera | Also responsible for |
|---|---|---|
| **Ravi, the grandpa** (actor) | Hands, back of head, cardigan, slippers, feet. Never the face. | Makes every kitchen sound (stirring, the crash, the groans). Presses the buttons on the kitchen laptop **on camera**. |
| **Meera, the adult child** (actor) | Hands holding the phone, over-the-shoulder at a desk or on a sofa. Never the face. | Owns the **family phone**: turns on alerts, screen-records the phone during takes, reacts. |
| **Narrator + director** | Never on camera. Voice only. | Runs the clock and this script, films with the camera phone, starts and stops the laptop screen recording, records the voice-over afterwards, edits. |

Wardrobe for Ravi: a cardigan or sweater, slippers or socks, an older-looking watch if anyone has one. Grey hair is not needed: we never see the face.

---

## 2. Equipment and the set (20 minutes, before filming)

### 2.1 What you need
- **Kitchen laptop** (Chrome), plugged in, volume at about 70% (it reads "Are you OK?" aloud, and we want that on the recording).
- **Meera's phone:** Android with Chrome is best (alerts work in a normal tab). iPhone works only if Kettle is added to the Home Screen first (Share → **Add to Home Screen**, then open it from that icon).
- **Camera phone** for the acted shots, on a tripod or a stack of books. Landscape, 1080p, 30 fps. Clean the lens.
- **Props:** a frying pan, a wooden or metal spoon, an onion or vegetables (or just stir an empty pan), a **metal baking tray or pot lid** for the crash (loud, safe to drop), a **cushion or folded yoga mat** for Ravi to kneel onto, a mug and a kettle.
- **Screen recorders:** laptop: Mac **⌘+Shift+5 → Record Entire Screen**, Windows **Win+Alt+R** (Xbox Game Bar), or OBS. Phone: Android quick settings **Screen record** (turn on "Record audio: none" and "Show touches: on"); iPhone Control Center **Screen Recording**.

### 2.2 Where things go (kitchen)
```
            [ window / wall: plain, nothing personal ]
   STOVE  [pan]       COUNTER        [KITCHEN LAPTOP, screen toward the room]
     ↑ 1 m from the laptop             ↑ within 1–2 m of the stove and sink
   Ravi stands here                    SINK
   ┌──────────────┐
   │ cushion on   │  ← Ravi kneels onto this (out of frame until the fall shot)
   │ the floor    │     The tray is dropped on the hard floor next to it, ~1.5 m from the laptop
   └──────────────┘
   CAMERA PHONE: on the counter or tripod at waist height, 2 m back, framing Ravi from behind
                 (shoulders down) with the laptop screen visible at the edge of frame.
```
- The laptop must be **within 1–2 m** of where the sounds happen (the app's own setup says so: a TV as loud as the cooking cut what Kettle caught from 84% to 40%).
- **Turn off** the TV, radio, music, smart speakers, the dishwasher and the extractor fan. Close the windows if there's traffic.
- Remove anything personal from frame: photos, mail, school things, house numbers, fridge magnets with names.
- Light: kitchen lights on plus a lamp; no window behind Ravi (it turns him into a silhouette, which is fine for the opening shot only).

### 2.3 Meera's place
A different room (desk or sofa), different light (a lamp), a laptop bag or work mug nearby so it reads "at work, far away". Camera over her right shoulder, phone screen visible and in focus. Phone at **full brightness**, **Do Not Disturb off**, other apps' notifications silenced (Settings → Notifications), ringer on.

---

## 3. Which server: decide in 30 seconds

The phone notification needs the deployed site with tonight's urgent-alert code.

1. On any browser open **`https://kettle.parth-dev.workers.dev/api/push/key`**.
   - It shows `{"publicKey":"B…"}` → **Plan A** (real phone notification). Use `https://kettle.parth-dev.workers.dev` everywhere below.
   - It shows `not found` or an error → the live site is the old build. **Parth deploys `main` now** (`SETUP.md`, Cloudflare deploy), then check again. If it can't be deployed by **8:20 PM**, use Plan B.
2. **Plan B (no deploy):** run it on the kitchen laptop: `cd web && npm install && node dev.mjs` (http://localhost:8787). Meera's "phone" becomes a second Chrome window on the same laptop, narrow (about 420 px), recorded with the screen recorder. The family page still turns red within ~5 s and the tab title changes to **● Urgent · Kettle**, but there is no lock-screen notification (that needs HTTPS). In the narration, say "her screen" instead of "her phone buzzes". **Never fake a notification.**

When filming on the live site, **crop the address bar** in the edit (it shows "parth-dev", which could identify us), or set browser zoom so the address bar isn't in the recorded area.

---

## 4. Setup off camera (15 minutes, in this order)

### 4.1 Meera creates the home (Meera's phone)
1. Open the site → **Set up** (or go to `/start`).
2. **Where are you right now?** → tap **On my own phone or computer**.
3. **A little about them:**
   - **Who is this for?** → **My parent**
   - **What do you call them? (optional)** → type **Dad**
   - **Where will the device listen?** → **Kitchen**
   - **Your first name** → type **Meera**
   - Tap **Create our Kettle**.
4. **Now connect the device in Dad's kitchen** shows a six-letter code (like **JV3 C42**) and a link. Tap **Copy** next to the link and send it to the kitchen laptop (email or chat to yourself), or just read the code aloud.
5. Tap **Open my family view**.

### 4.2 Ravi's laptop joins (kitchen laptop) — **film this part (Take 1)**
Open the copied link in Chrome (or go to `/listen` and type the six letters). Start the laptop screen recording now.
1. Screen: **This laptop listens for kitchen sounds.** with six plain sentences, including *"If it hears a smoke alarm, screaming, or a crash and then a cry, it asks "Are you OK?" here and tells Meera if nobody answers."* → click **Next**. (Optional: hover **Read this to me** for 2 s.)
2. Screen: **Is it OK for Meera to see this?** / *Meera will see the kinds of sound and when they happened. Nothing else.* → **Ravi's hand** clicks **Yes, Meera can see this**. ← This is shot 0:15–0:27. Film it twice: screen recording + camera phone over Ravi's shoulder.
3. Screen: **Where should this laptop live?** (Near the stove and sink · Away from the TV · Plugged in · Screen on, this page open) → **It's in place. Start listening**. Chrome asks for the microphone → **Allow**.
4. Screen: quick sound check. Ravi stirs the pan for 10 s. If it says **Kettle heard something it couldn't name.**, click **Try again** once, stirring closer; if it still can't, click **Next anyway** (that's fine).
5. Screen: **Teach Kettle this kitchen** → click **Start teaching (3 minutes)** and do it now, off camera. It makes the labels better in *this* kitchen:
   - **I'm ready. Start step 1** → everyone silent for 40 s.
   - **I'm ready. Start step 2** → run the tap / rinse dishes for 1 minute.
   - **I'm ready. Start step 3** → stir, chop, fry for 1 minute.
   - You see **Thank you. Kettle learned this kitchen.** (If a step says **Kettle could hardly hear that**, move the laptop closer and click **Try this step again**.)
6. Screen: **Listening for kitchen sounds**, with buttons **Pause**, **Turn it off**, **Keep it in a small window**, **I need help**. Leave it there.

### 4.3 Meera turns on alerts and sets a check (Meera's phone, family view)
1. Scroll to **Urgent alerts** → tap **Turn on alerts** → the browser asks → **Allow**. It now says **Alerts are on for this phone.**
2. Tap **Send a test alert**. A notification **Kettle: test alert** must arrive within a few seconds. **If it doesn't, stop and fix it** (Plan B, or check notifications are allowed for Chrome in the phone's settings).
3. **Your checks** → **Edit** → tap **Remove** on each existing check → **Add a check** → choose **Kitchen activity by** and set the time **about one hour from now** → **Save**. (A check whose time has already passed honestly says "Can't tell", so it must be later than now.)

### 4.4 Rehearse the fall once (5 minutes) — then clean up
Do the whole fall scene once without recording (section 6, shots 4–6) to check the app hears it in *your* kitchen.
- If **Are you OK?** appears within ~30 s of the groans: great, the real detection works. Go to 4.5.
- If not after 40 s: do it once more with the tray dropped **closer** (1 m) and **louder, longer** groans. If it still doesn't trigger, use **the fallback** in section 6 (Ravi presses **I need help**). It's honest: it's a real feature, and the family is told the same way.

**4.5 Clean the slate before the real take.** Rehearsal alerts stay in Meera's **Urgent alerts in the last 24 hours** list. On Meera's phone tap **I've seen this** on every banner. For a perfectly clean list, delete the home (**Settings** → **Delete everything** → tap again to confirm) and repeat 4.1–4.3 (skip teaching the second time; tap **Do it later**). On the kitchen laptop, **reload the page** before every fall take (it resets the safety engine).

---

## 5. Recording settings (check before every take)
- Laptop: Chrome zoom **125%** (⌘/Ctrl + plus), bookmarks bar hidden (⌘/Ctrl+Shift+B), no profile picture visible, other tabs closed, notifications off.
- Phone: brightness max, battery saver off, screen timeout 10 minutes, the family view open and scrolled to the top.
- Camera phone: lock focus and exposure on the laptop screen (tap and hold), landscape.
- Slate each take: the director shows the take number on a sticky note to the camera for 1 s, then claps once **only before** the laptop starts listening (a clap is loud enough to be called a crash).

---

## 6. The shot list and the script (in story order)

Narration lines are read in the edit, over the pictures. Timings are for the final cut; record each shot with a few seconds of spare at both ends.

### Shot 1 — The problem (0:00–0:15) · camera phone
- **Picture:** Ravi from behind, alone in a quiet kitchen. Hand fills the kettle, puts a single mug down, pauses, looks at the window. Slow. Then a close-up of the single mug.
- **Sound:** natural room sound, quiet.
- 🎙 *"More than one in four Americans over sixty-five live alone. When a parent like Ravi starts to lose his memory, his daughter, three hundred miles away, has two bad options: call every day and feel like she's checking up, or put in a camera and make him feel watched."*

### Shot 2 — He says yes (0:15–0:27) · laptop screen recording + camera over the shoulder
- **Picture:** the laptop screen **Is it OK for Meera to see this?**, Ravi's hand moves into frame and clicks **Yes, Meera can see this**.
- 🎙 *"Kettle turns a spare laptop in his kitchen into a calm timeline of his day, from sound alone. He reads what it does in plain words, and nothing listens until he says yes."*

### Shot 3 — A normal day (0:27–0:42) · camera + laptop recording + Meera's phone recording
Take 2 starts here. Start all three recordings, then:
1. Ravi stirs the pan steadily for **20–30 s** at the stove (real sound, no talking). Optional: rinse a plate under the tap for 10 s.
2. **Wait for** the laptop chip to read **Sounds like cooking** (or **Sounds like washing up** at the sink). It updates every 10 s.
3. Cut to Meera's phone: within ~10 s her **The kitchen today** page shows a coloured block on the day bar, the summary **So far today: cooking around …**, and her check **Kitchen activity by …** turns **Met**. Meera's thumb taps the coloured block to show **why** (the evidence card).
- 🎙 *"Every ten seconds, a small sound model running on the laptop names what it hears, then forgets the sound. No audio is recorded or sent; only a label like 'cooking' reaches Meera, and the check she set turns to met."*

### Shot 4 — The fall (0:42–1:02) · camera phone (main), laptop recording running
**Safety first: nobody actually falls. Ravi kneels slowly onto the cushion. The crash is the tray, dropped by hand.**
1. Silence in the room for 10 s (no stirring now).
2. Ravi holds the **metal tray** at waist height, about **1–1.5 m from the laptop**, and **drops it flat onto the hard floor**. Camera: low angle on his slippers and the tray hitting the floor.
3. Ravi lowers himself onto the cushion (camera: knees and a hand on the floor, never the face).
4. Within 5–10 s, Ravi **groans and cries out without words**, loud and long, 3 times over ~20 s: *"Ohhh… ahhh… ohhh."* **No words** (speech can be mistaken for TV), no other sounds, nobody else talks, **no cooking sounds** afterwards.
5. **Wait for** the laptop to turn red: **Are you OK?** · *Kettle heard a crash, then a groan or cry at 8:14 PM.* · *Meera has been told. Press I'm OK to let them know you're fine.* · *If nobody answers in 60 seconds, Kettle tells Meera that nobody answered.* The laptop also **speaks**: *"Are you OK? Kettle heard a crash, then a groan or cry. Meera has been told. Press I'm OK, or I need help."* Hold the shot on the red screen and let the voice play.
- **If no "Are you OK?" within 40 s → fallback:** Ravi reaches up and presses **I need help** (bottom row of buttons). The laptop shows **Meera has been told you need help.** Carry on with Shot 5; Meera's banner will say **Dad pressed "I need help"**. In the narration swap the line for the fallback line below.
- 🎙 *"Then something goes wrong. Kettle hears a crash, then a cry, and does two things at once: it asks Ravi if he's OK…"*
  - Fallback 🎙 *"Then something goes wrong. Ravi can't get up, so he presses the help button on the screen…"*

### Shot 5 — Meera is told at once (1:02–1:10) · Meera's phone recording + camera over her shoulder
- **Plan A picture:** her phone buzzes. The lock-screen notification: **Kettle: urgent** · *Heard a crash, then a groan or cry at 8:14 PM. Asking "Are you OK?" on the kitchen screen now.* She taps it. The family view opens with the red banner: **URGENT · 8:14 PM** · **Kettle heard a crash, then a groan or cry at 8:14 PM.** · *Asking "Are you OK?" on the kitchen screen now. Call Dad if you can.* · button **I've seen this** · *Kettle is a prototype. It doesn't replace a smoke or CO detector, or 911.*
- **Plan B picture:** the family window turns red within ~5 s, and the tab title reads **● Urgent · Kettle**.
- Meera's hand picks up the phone to call (dial screen with **no real name or number visible**: save a contact named "Dad" first, or just show her thumb hovering over the call button).
- 🎙 *"…and tells Meera, right away. Not after a minute, not after a missed call. Now."*

### Shot 6 — He's OK (1:10–1:17) · camera on Ravi's hand + Meera's phone
1. Ravi's hand (from the floor) reaches up and presses **I'm OK** on the laptop. The laptop shows a short thank-you.
2. Cut to Meera's phone: within ~5 s the banner turns **amber**: **UPDATE · 8:14 PM** · **Kettle heard a crash, then a groan or cry at 8:14 PM.** · *Dad pressed "I'm OK" at 8:15 PM. Worth a call when you can.* (Plan A also sends a quieter notification: **Kettle: they said they're OK**.) Meera exhales and lowers the phone.
- 🎙 *"He presses 'I'm OK', and her screen turns from red to amber. She still calls. But now she knows."*
  (Fallback version: skip pressing I'm OK; the banner stays red with **Dad pressed "I need help". Call Dad now.** 🎙 *"Her screen says exactly what happened, and that he asked for help."*)

### Shot 7 — How it works and how good it is (1:17–1:45) · laptop screen recording, no actors
Open the site's **How sure** page (top bar link **How sure**). Scroll slowly; pause 2–3 s on each item:
1. The headline numbers and the systems table: **Kettle, one microphone 84.1** and **Apple SoundAnalysis, zero-shot 31.8**, **Always "Quiet" 5.0**.
   🎙 *"Under the hood: a small pretrained audio model, CED-tiny, runs in the browser, with a classifier we trained on a public dataset of a real home. On held-out test recordings it had never heard, scored once, it reaches 84 macro F1. Apple's built-in sound classifier scores 32 on the same clips; always guessing 'quiet' scores 5."*
2. The card **Urgent alerts: what turns red, and how often it's right**: the sentence **0 false urgent alerts in 12.3 hours of ordinary home sound** and the table row **Smoke or fire alarm, during cooking 88.3%**.
   🎙 *"For urgent sounds, it caught a smoke alarm during cooking 88 percent of the time, and in over twelve hours of ordinary home sound it raised zero false urgent alerts."*

### Shot 8 — One honest limit, and what's next (1:45–1:55) · screen recording
1. Still on How sure, scroll to **Outside the research home: the test that changed Kettle** (or the urgent card's limits list).
   🎙 *"Where it fails: in homes it never trained on, it often says 'not sure' instead of guessing, and our alarm tests used synthetic sounds. Next, we test it in real kitchens with real families."*
2. End card (in the edit, plain background, 3 s): **Kettle · Know the day went okay, without a camera.** and below it **This project is a prototype and is not medical advice.**
   🎙 *"Kettle. Know the day went okay, without a camera."*

**Narration word count:** about 270 words → about 1:50 at a calm pace. If you run long, cut the optional line in Shot 3 ("and the check she set turns to met") first.

---

## 7. Every number you say, and where it comes from
Say only these. If a results file changes, the number changes.

| Spoken | Exact value | Source |
|---|---|---|
| "more than one in four Americans over sixty-five live alone" | about 28% of community-dwelling adults 65+ | ACL 2023 Profile of Older Americans (cited in the write-up) |
| "84 macro F1" | 84.1 [74.4, 86.7], 7,791 clips, 91 sessions | `results/metrics.json` |
| "Apple … scores 32" | 31.8 [25.7, 37.9], same clips | `results/metrics.json` |
| "always guessing quiet scores 5" | 5.0 [1.6, 7.8] | `results/metrics.json` |
| "smoke alarm during cooking 88 percent" | 88.3% (53/60 held-out timelines) | `results/safety.json` |
| "over twelve hours … zero false urgent alerts" | 0 in 12.3 h (4,416 held-out windows) | `results/safety.json` |
| "it often says 'not sure'" (no number spoken) | 41.8% of washing-up windows in real homes said Not sure | `results/real_homes.json` |

Don't say: "it detects falls" (it hears a crash then a cry, or a crash then stillness), "it calls 911" (it can't), "it works in any home" (it doesn't yet), or any accuracy for gunshots or shouting (not measured).

---

## 8. Editing (CapCut, iMovie, DaVinci Resolve or Clipchamp; 25 minutes)
1. **Voice-over first:** the narrator reads section 6's lines in one go, in a quiet room with soft furnishings (a closet works), phone 20 cm from the mouth, in a calm, warm voice. Record 2 takes, pick the best. **Real human voice only, no AI voice.**
2. Lay the voice-over on the timeline, then cut the pictures to it in story order (shots 1–8).
3. **Cut the waiting:** keep 1 s before and after each screen change; speed up any wait over 3 s (2–4×) or jump-cut it, and add a small on-screen caption **"12 seconds later"** where you cut (honesty: never hide that time passed).
4. Keep the laptop's own spoken *"Are you OK?"* audible under the narration (narration −3 dB there).
5. Captions: add the narration as subtitles (most viewers watch muted). Big, bottom-centre.
6. **Crop or blur**: the address bar (if it shows "parth-dev"), any real names, faces, house numbers, and the phone's status-bar carrier name.
7. Music: none, or very quiet piano under shots 1 and 8 only. Never under the fall.
8. Export 1080p, MP4, **under 2:00** (aim for 1:55).

---

## 9. Upload and final checks (10 minutes)
1. YouTube → Create → Upload video → title **"Kettle: know the day went okay, without a camera"** → **Visibility: Unlisted** → no names in the title, description or channel name visible in the video. (If the YouTube channel shows a real name, upload to Google Drive instead and set **Anyone with the link → Viewer**.)
2. Open the link in a **private / incognito window**: it plays, without signing in.
3. Watch it once, all the way, with sound, and tick: under 2:00 · no faces · no real names · no school · every number matches section 7 · the disclaimer is on screen · the notification shown was real.
4. Paste the link into the submission form.

---

## 10. If something goes wrong on set
| Problem | Do this |
|---|---|
| The label says **Not sure what that is** while cooking | Stir louder and closer to the laptop for 20 s more; or do the 3-minute teaching (4.2 step 5). It's honest to show "Not sure" for a moment. |
| The family view doesn't update | Wait 10 s (it checks every 5 s). Pull to refresh once. Check both screens show the same home (Meera's view title **The kitchen today**). |
| **Are you OK?** never appears after the fall | Use the **I need help** fallback (Shot 4). Don't fake it. |
| The red alert appears during cooking (a false alarm) | Note it, reload the kitchen page, press **I've seen this** on the phone, and reshoot. Tell the team: it's a real failure case worth knowing for Q&A. |
| No phone notification (Plan A) | Check Chrome notifications are allowed in the phone's settings; tap **Send a test alert** again. If still nothing by 8:30 PM, switch to Plan B and say "her screen". |
| The page says **This home isn't available** | The home was deleted (4.5). Go to the site → **Set up** and redo 4.1–4.3. |
| "Kettle can't hear the kitchen" | The microphone is blocked: click the icon left of the address bar → Microphone → Allow → **Try again**. |
| Running out of time | Priority: Shots 4–6 (the alert) and Shot 7 (the numbers). Shot 2 and the teaching can go. |

---

## 11. Timeline for tonight (Central time)
| When | What |
|---|---|
| now → +10 min | Read this together; pick roles; check the live site (section 3). |
| +10 → +30 | Set up (section 4), rehearse the fall once. |
| +30 → +55 | Film shots 1–6 (2 good takes of shots 4–6). Screen-record shots 7–8. |
| +55 → +70 | Record the voice-over. |
| +70 → +95 | Edit, export. |
| +95 → +105 | Upload unlisted, check in incognito, paste into the form. |
Hard deadline: the form closes at **10:59 PM CT**. Team target: submitted by **9:30 PM CT**; resubmitting later with a better video is allowed.
