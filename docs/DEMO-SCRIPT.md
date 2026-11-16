# Demo video: what to click, what to say (shooting script)

Companion to `docs/VIDEO.md` (timing, numbers and their sources). Every button name below was checked by clicking through the
app on Sun Nov 15 (Playwright walkthrough on the merged branch). **Bold** = the exact text on the button.

**Record it in 3 takes, then cut together.** Total after editing: about 1:55.

| Take | What | Raw length | Used in the video |
|---|---|---|---|
| 1 | Setting up: the parent says yes, Kettle starts learning the kitchen | ~1 min | 0:28–0:40 |
| 2 | Live: real cooking, family phone, pause, other tab, what's shared | ~3 min | 0:40–1:20 |
| 3 | Front page and How sure page (no microphone needed) | ~2 min | 0:00–0:28 and 1:20–1:55 |

---

## Before you press record (≈ 15 min, off camera)

1. Start the app on the recording laptop (merged branch):
   ```bash
   cd web && npm install && node dev.mjs
   ```
2. Open **two Chrome windows** side by side:
   - **Left = kitchen laptop:** a normal window, about 1200 px wide.
   - **Right = family phone:** an **Incognito** window (Ctrl+Shift+N, Mac ⌘+Shift+N), narrow, about 420 px wide.
3. Zoom both to 110%. Turn on Do Not Disturb. Plug the laptop in. Have ready: a pan, a metal spoon and the tap.
4. Warm up the sound model so the video never shows "Getting Kettle ready…": open `http://localhost:8787/kitchen` in the left
   window once and wait about 20 s, then close that tab. The model stays cached.

---

## Take 1: the parent says yes (left and right windows)

**Right window (family), create the home:**
1. Go to `http://localhost:8787/start`.
2. Click **On my own phone or computer**.
3. "Who is this for?" Click **My parent**.
4. "What do you call them?" Click **Mom**.
5. "Where will the device listen?" Click **Kitchen**.
6. "Your first name": type **Asha** (an invented name; never a real teammate's).
7. Click **Create our Kettle**.
8. Step 3 shows a six-letter code and a link. Next to the link, click **Copy**.

**Left window (kitchen), start recording here:**
9. Paste the copied link into the address bar and press Enter. You see **"This laptop listens for kitchen sounds."**
   🎙 *"The parent decides. Kettle explains itself in plain words, can read them aloud, and asks first."*
10. (Optional, 2 s) hover **Read this to me**. Then click **Next**.
11. You see **"Is it OK for Asha to see this?"** Click **Yes, Asha can see this**.
12. "Where should this laptop live?" Click **It's in place. Start listening**. Chrome asks for the microphone: click **Allow**.
13. "Quick sound check": stir the pan or clink two plates for about 10 s. You see **"Kettle heard cooking."** Click **Next**.
14. "Teach Kettle this kitchen" (Setup, step 4 of 4).
    🎙 *"Then it spends three minutes learning this kitchen: quiet, washing up, cooking."*
    Click **Start teaching (3 minutes)**.
15. You see **"Ready for step 1 of 3?"** Click **I'm ready. Start step 1**. **Stop recording Take 1 here.**
16. Off camera, finish teaching: keep quiet for 40 s → **I'm ready. Start step 2** → run the tap for a minute →
    **I'm ready. Start step 3** → stir and chop for a minute. You see **"Thank you. Kettle learned this kitchen."**
    (If a step says "Kettle could hardly hear that", move closer and click **Try this step again**.)

**Right window (family):**
17. Click **Open my family view**.
18. Set a check that will say **Met** at the time you record. Click **Edit** next to Your checks, click **Remove** on each existing
    check, then click a preset whose time is **later than now** (afternoon → **Evening meal by 8**; morning → **Lunch by 2**).
    Click **Save**.
    (A check whose time has already passed honestly says "Can't tell", because Kettle wasn't listening then.)

---

## Take 2: live (both windows visible side by side)

Start recording with the left window showing **"Listening for kitchen sounds"** and the right window showing the family view.

| Step | Do | Wait for (on screen) | Say 🎙 |
|---|---|---|---|
| 1 | Stand 1–2 m from the laptop. Stir a real pan with a metal spoon for ~20 s | Left: chip **"Sounds like cooking"** | *"Every ten seconds the laptop names what it hears and forgets the sound. Only the label leaves the kitchen."* |
| 2 | Run the tap into a bowl for ~20 s | Left: chip **"Sounds like washing up"** | — |
| 3 | Wait 10–20 s; don't click anything on the right (it refreshes itself every 5 s) | Right: summary **"So far today: cooking around …"**, coloured blocks on the bar, check **"Kitchen activity by 8:00 PM · Met at … (cooking …)"** | *"Far away, Asha sees the day fill in, and the check she set turns to met."* |
| 4 | Left: click **Pause** | A menu: **A guest or carer is here (2 hours)**, **Pause for 15 minutes**, **Pause for 1 hour**, **Pause until tomorrow morning**, **Cancel** | *"Mom can pause it any time…"* |
| 5 | Click **Pause for 15 minutes** | Left: **"Paused. Kettle isn't listening."** Right (within ~5 s): **"Paused by Mom at … · resumes at …"** | *"…and Asha sees that honestly."* |
| 6 | Left: click **Resume listening** | Left: **"Kettle is listening again."** | — |
| 7 | Left: open a new tab (Ctrl+T), show it for 3 s, then click back to the Kettle tab | The Kettle tab's title reads **"● Listening · Kettle"** | *"It keeps listening while the laptop is used for other things."* |
| 8 | Left: scroll down and click **What Asha can see**. Untick **Talking / TV** | Right (within ~5 s): **"Mom chose not to share: Talking / TV."** under the summary | *"And Mom decides what's shared. If she'd rather keep the TV private, she unticks it, and Asha sees that she chose not to share it."* |
| 9 | Left: tick **TV** again (so the rest of the recording isn't affected) | Note disappears | — |

Stop recording Take 2.

If the live sounds misbehave, don't fight it: use Take 3's **Two screens** fallback below and say *"a sample day: real
recordings played through the same model"*.

---

## Take 3: front page and How sure (one wide window, no microphone)

**Front page (0:00–0:28):**
1. Go to `http://localhost:8787/`. Don't click for 10 s: the panel **"Your parent's kitchen, today"** plays a sample day
   ("What Kettle heard" on the left, "What the family sees" on the right).
   🎙 *"More than one in four Americans over sixty-five live alone… Kettle turns a spare laptop in the kitchen into a calm
   timeline of the day's activity, from sound alone, without recording anything."*
2. Scroll slowly down to the three big numbers (**84.1**, **83%**, **0**) and stop for 3 s.
   🎙 *"On held-out benchmark recordings it had never heard, scored once, Kettle reaches 84 macro F1, and it caught about nine in
   ten kitchen-activity moments. No audio is ever saved."*
3. (Fallback for Take 2 only) Scroll to the **Two screens** section and click **A usual morning**. Let it play for 15 s.

**How sure (1:20–1:55):**
4. In the top bar click **How sure**.
5. Scroll slowly to the per-activity table (**Caught / Missed / False alarms**), then to the systems table, and stop on
   **Apple SoundAnalysis** and **Always "Quiet"**.
   🎙 *"We publish every activity's misses and false alarms separately. Apple's built-in sound classifier scores 32 on the same
   clips. Washing up is our weakest kitchen activity: 73 percent caught. And we can't test across age or sex: the training home
   had one person."*
6. Scroll to **"Kitchen naming after a live test in a real kitchen"**, then to the named-sounds table, where **hidden** sits
   next to frying and dishes and **yes** next to kettle and running water.
   🎙 *"In a teammate's kitchen, cooking with metal pots showed as 'eating'. Each ten seconds was named from one loud tag. Now
   a whole stretch is named from its evidence, and every sound name had to pass a bar we wrote first. Hand-written rules passed one sound; a small
   trained classifier passes eight, and the rest stay hidden, not shown wrong."*
7. Go back to the right window's family view (or the front page) for the last 3 s.
   🎙 *"Kettle: know the day went okay, without a camera. A prototype, not medical advice."*

---

## Editing order

| Clip | Source | Length |
|---|---|---|
| Hook + numbers | Take 3, front page steps 1–2 | 0:00–0:28 |
| Parent says yes | Take 1, steps 9–15 (speed up step 12–13 waits 2×) | 0:28–0:40 |
| Live | Take 2, steps 1–8 (cut the waits) | 0:40–1:20 |
| How sure + honest failure | Take 3, steps 4–6 | 1:20–1:52 |
| Close | Take 3, step 7 | 1:52–1:55 |

Before uploading, check:
- No names on screen except the invented "Mom" and "Asha".
- No address bar showing a real domain (`localhost` is fine).
- No browser profile picture.
- Every number you say matches the screen at that moment.
