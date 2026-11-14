# Pain points: what caregivers and older adults actually complain about (Sat Nov 14, 2026)

The core deliverable of the Kettle teardown. **418 items** collected (reviews, forum posts, Reddit comments, press reviews), **153** of which state at least one pain. Every item, with link, product, stars, date and a one-line text, is in [`coded-items.csv`](coded-items.csv). Every coded example per theme is in [`raw/theme-examples.md`](raw/theme-examples.md).

## Method (read this before quoting a number)

- **Sources.** App Store customer-review RSS (public JSON, GB/US/AU/CA/IE, fetched directly: Howz, Canary Care, Care Daily, StackCare, Caregiver Aware, Parents are OK, Assistiv, Snug). Read-only Aside browser research for Google Play, Trustpilot, the Alzheimer's Society forum, Mumsnet, Amazon Forum, Reddit and press reviews (transcripts in `raw/aside-*.txt`). Nothing was posted, liked or logged into.
- **Item counts by product:** Canary Care 123 (112 Trustpilot, 3 Play, 1 App Store, 7 forum/press), Reddit with no product named 112 (12 threads), Snug 53 (App Store 1–4★ only), Alexa Together / Emergency Assist 47, Howz 33 (15 App Store, 7 Play, 11 Trustpilot), Care Daily 19, Apple Sound Recognition 19, StackCare 6, Parents are OK 3, Caregiver Aware 2, Assistiv 1.
- **Why Snug is in.** It is the most-reviewed "is my parent OK" app (2,273 US ratings, 4.87★). Its 1–4★ reviews are the only large body of complaints written by **older adults themselves**. Its 327 five-star reviews are excluded so they don't swamp the sensor products.
- **Coding.** One coder (the teardown agent). Step 1: transparent keyword rules (`raw/code_items.py`). Step 2: the agent read every match and removed 32 false positives and added 12 misses (listed in the script). A theme counts only when the item states it as a *pain*. A 5★ review counts only when it contains a caveat ("but", "however", "wish"). **No second coder, so no agreement score.** Treat counts as ±20%.
- **Severity** (1–3) is the agent's judgement of the harm when the pain occurs: 3 = a person can be hurt or the relationship damaged (a missed fall, a parent who feels spied on); 2 = trust erodes or money is wasted; 1 = annoyance. **Rank = count × severity.**
- **Biases to state.** (1) Sensor-kit reviews are thin and glowing: Howz has 11 Trustpilot reviews, all 4–5★, and its page says it has "no recent history of asking for reviews"; Canary Care has 114 Trustpilot reviews with no 1–2★. Buyers who hated a £419 kit seem to return it rather than review it. (2) Reddit comments include founders posing as customers; they are tagged `[F]` and kept, but no theme rests on them alone. (3) The products differ (sensor kits, voice assistant, check-in apps, phone accessibility), so shares compare *pains in this market*, not products.

## The ranked themes

Share = items with this theme ÷ 153 items stating any pain (an item can carry several themes).

| Rank | Theme | Count | Share | Sev | Score | Products it hits | Seed theme? Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **The parent feels watched / loses dignity** | 17 | 11% | 3 | 51 | Reddit (cameras, check-in apps) | Seed. **Confirmed**, strongest on Reddit; absent from sensor reviews because those buyers already chose "no cameras" |
| 2 | **Burden on the older adult** (must tap, wear, talk or charge something; daily ritual annoys) | 25 | 16% | 2 | 50 | Snug, Alexa, Reddit (pendants, watches, phones on silent) | Seed "nothing for the older adult" **reframed**: the louder pain is products that make the parent *do* something |
| 3 | **Missed a real problem** | 15 | 10% | 3 | 45 | Alexa Emergency Assist (smoke alerts 2 of 15), Apple SR, Howz, Snug, Canary (sensor mounted too high), Reddit | Seed. **Confirmed** |
| 4 | **Hub / Wi-Fi / battery / power** | 19 | 12% | 2 | 38 | Apple SR (8: 8–36% battery/day), Howz hub down, Alexa Wi-Fi range, Reddit | Seed. **Confirmed**, and for sound specifically it is *phone battery drain* |
| 5= | **Subscription price** | 16 | 10% | 2 | 32 | Snug ($20/mo "a joke"), Parents are OK ($9.90/mo), Alexa Together ($20/mo), Canary (~£30/mo "a bit expensive") | Seed. **Confirmed, moderate** |
| 5= | **False alarms / alert fatigue** | 16 | 10% | 2 | 32 | Apple SR (30 knock alerts in an hour), Alexa (TV → glass-break), Snug (police at the door), bed mats, Care Daily | Seed. **Confirmed**, and *sound* classifiers are a main source |
| 7 | **Consent overridden** ("I didn't ask, I just did it") | 8 | 5% | 3 | 24 | Reddit (cameras), pendants refused | Seed. **Confirmed, low count, high severity** |
| 8 | **Product discontinued or changed under you** | 11 | 7% | 2 | 22 | Alexa Together (ended Jun 25 2024), Care Hub, Echo Connect, Alexa Guard, WithU, Canary Care changed hands | **Emergent** (not a seed) |
| 9 | **App bugs, logouts, sign-in** | 21 | 14% | 1 | 21 | Snug, Howz (logs out weekly), Canary (logs out), Care Daily, Alexa (Remote Assist crash) | Seed. **Confirmed, frequent but low severity** |
| 10= | **"No news" is ambiguous / silent failure** | 6 | 4% | 3 | 18 | Howz ("hub forever going down… no information"), Snug (sporadic texts, stopped asking) | Seed. **Confirmed, low count**; also *observed* in Howz's own store screenshot (a "Back Door" sensor last seen 13 months earlier) |
| 10= | **Wants a "no activity by X o'clock" alert** | 9 | 6% | 2 | 18 | Alexa Together users mourning it; Reddit smart-home builders | **Emergent.** Said independently in 3 threads: consumer sensors fire *on* motion, people need the *absence* |
| 12 | Cancel / refund / support | 13 | 8% | 1 | 13 | Snug, Alexa, Care Daily | Emergent, low severity |
| 13 | Raw data, not meaning | 5 | 3% | 2 | 10 | Canary, Reddit | Seed. **Weak in user voice**, but *observed* in incumbent UIs (see `ui-patterns.md`) |
| 14 | Hardware install | 9 | 6% | 1 | 9 | Howz, Canary (2), Reddit | Seed. **Mostly not confirmed**: 28 positive items praise easy setup |
| 15 | One caregiver only, siblings can't share | 7 | 5% | 1 | 7 | Snug ("only one of my emergency contacts"), Reddit | Seed. **Weak**: incumbents already share (Alexa 10, Care Daily 10, havn unlimited) |
| 16 | Cold start (weeks to learn a routine) | 1 | 1% | 1 | 1 | Canary (third-party review) | Seed. **Not confirmed by users.** It is a *vendor* fact (Howz 8–15 days, havn 7–14, Canary ~2 weeks) that nobody complains about |

What people **love** (176 items rated 4–5★): easy setup (28), peace of mind (27), "not intrusive / no cameras" (17), good support (13), seeing the parent is up and about (11), independence (11), the kettle or meals as a signal (8). Canary's Trustpilot items are short paraphrases, so these are undercounts.

## Each theme, with examples (paraphrased; full list in `raw/theme-examples.md`)

### 1. The parent feels watched (17, sev 3)
- A daughter put a security camera in for her 80-year-old mum, who "hated it and said it felt like spying." https://www.reddit.com/r/eldercare/comments/1s53zl0/
- A self-described older adult: if their kids surveilled them the way the thread suggests, they would "move and never tell them where I went." https://www.reddit.com/r/AgingParents/comments/1ppwtci/
- A caregiver testing a no-camera sensor prototype: it still "looks like spying" and is ugly; hide it in home decor. https://www.reddit.com/r/TechForAgingParents/comments/1q0f2nx/
- Counter-voice (2 items): "This is not micromanaging… this is preventing fatal issue!!" https://www.reddit.com/r/CaregiverSupport/comments/1kwze56/ The tension is real; the product has to serve both.

### 2. Burden on the older adult (25, sev 2)
- An older Snug user with ADHD: the app stopped early reminders, so the last-minute notice now sets off alerts to family. https://apps.apple.com/us/app/id1122758716?see-all=reviews (2026-02-18)
- "The person being monitored has to actually use Alexa, or the peace of mind is lost." (Livingetc, 2022) https://www.livingetc.com/advice/alexa-together
- A father with an Apple Watch locked himself out in a snowstorm for 45 minutes and forgot the watch could call for help. https://www.reddit.com/r/AgingParents/comments/1rquxw3/
- Ten Snug reviews complain about the daily quote shown at check-in: the daily ritual itself becomes an irritant.

### 3. Missed a real problem (15, sev 3)
- Alexa Emergency Assist: "call for help" worked, but smoke alerts came through about 2 of 15 tests even though the Echos flashed. https://www.amazonforum.com/s/question/0D5at00000enGSyCAM/alexa-emergency-assist-not-consistently-acting-on-alarm
- Howz: bought after dad fell and lay on the floor 2 hours; the app "works a couple of times, then completely fails." https://apps.apple.com/gb/app/id1103148692?see-all=reviews (2019-09-22)
- Apple SR: a deaf parent got no baby-crying alert. https://www.reddit.com/r/deaf/comments/1d4rs2s/

### 4. Hub / Wi-Fi / battery / power (19, sev 2)
- Apple Sound Recognition used 8%, 12%, 20–30% and 36% of a day's battery in four separate reports. https://www.reddit.com/r/iOSBeta/comments/1dt7x1n/
- Howz: "The hub is forever going down; without this there is no information from the sensors." https://apps.apple.com/gb/app/id1103148692?see-all=reviews (2023-04-29)
- Alexa Together's Remote Assist "works only within Wi-Fi range" (The Verge, 2022). https://www.theverge.com/23066024/alexa-together-review-elder-care-urgent-response

### 5. Subscription price (16, sev 2)
- Snug: "20 dollars a month for basic routine. What a joke." (2026-02-14)
- Parents are OK: $9.90/month after a two-week trial called "overpriced." (2026-10-13)
- Alzheimer's Society forum: Canary Care and Just Checking "a bit expensive at around £30 pm." https://forum.alzheimers.org.uk/threads/help-with-my-nan.116791
- Context (observed prices): Canary £419–539 + £29/mo; Howz kit £149 + £9/mo (2020, consumer) or £45–65/mo per user (2026, councils); StackCare $95/mo Wi-Fi, $119/mo LTE, 90-day minimum; Alexa Together was $19.99/mo; Emergency Assist $5.99/mo.

### 6. False alarms (16, sev 2)
- Apple SR after iOS 27: about 30 "knock" alerts in an hour of errands from the user's own small noises. https://www.reddit.com/r/iphone/comments/1wj4koo/
- Alexa Emergency Assist: TV sounds triggered false glass-break alerts 3–4 times in as many weeks (Reviewed.com, 2024). https://www.reviewed.com/accessibility/content/alexa-emergency-assist-review
- Snug: one missed check-in sent two police officers to the door. (2023-06-01)
- Bed pressure pads "throw a lot of false alarms" as people shift. https://www.reddit.com/r/dementia/comments/1x2t3sf/

### 7. Consent overridden (8, sev 3)
- Ring cameras in every room; mom unplugs them, "doesn't really know what they are," and "I didn't ask, I just did it." https://www.reddit.com/r/AgingParents/comments/1rquxw3/
- A caregiver downvoted for not wanting cameras: "My parents are the ones insisting" on privacy. https://www.reddit.com/r/AgingParents/comments/1c7g5pi/

### 8. Discontinued or changed under you (11, sev 2)
- Alexa Together ended June 25, 2024; families who had just bought Echos for a parent learned a month later. https://www.amazonforum.com/s/question/0D56Q0000DKo8aKSQR/alexa-together-discontinued-how-to-manage-as-a-remote-caregiver
- "Used it for years on a frail 90-year-old grandmother… immensely disappointing." https://www.reddit.com/r/alexa/comments/1cgy3w6/alexa_together_discontinued/
- Emergency Assist smoke and CO detection "withdrawn entirely in the UK." https://www.reddit.com/r/alexa/comments/1whxxpd/

### 9. App bugs and logins (21, sev 1)
- Howz logs out about once a week; Canary Care "logs you out frequently" (2026-02-14); Alexa Remote Assist crashed the iPhone app.

### 10. "No news" is ambiguous (6, sev 3) and the "no activity by X" wish (9, sev 2)
- Snug: "Some days it texts me and some days it doesn't." (2025-04-06)
- "Sensors fire on motion, but you need the opposite: an alert when there's NO motion for X hours." https://www.reddit.com/r/smarthome/comments/1u388rh/
- Alexa Together's first-activity and no-movement alerts were "VERY valuable"; routines couldn't replicate them. https://www.reddit.com/r/alexa/comments/1cgy3w6/alexa_together_discontinued/

## What this means for Kettle (one paragraph)

The pains that hurt most are about **people, not sensors**: the parent feeling spied on, being made to do something every day, and alerts that either cry wolf or stay silent when it matters. Two of those are *sound-specific* risks for Kettle: Apple's and Amazon's sound detectors are the main public examples of false alarms (TV → glass break, small knocks → "door knock") and of phone battery drain. So Kettle must (1) never ask the parent to do anything, (2) show the parent the same view and let them pause it, (3) publish its false-alarm and miss rates per activity instead of hiding them, (4) run plugged in, and (5) make "no news" unambiguous with a visible heartbeat. Cold start and install, which we expected to be big, are not what users complain about. See `better-than.md`.
