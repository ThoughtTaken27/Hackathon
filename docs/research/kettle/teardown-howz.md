# Teardown: Howz (Sat Nov 14, 2026, Kettle stage 1, teardown agent)

https://www.howz.com/reassure · maker Intelesant Ltd (Manchester, UK) · consumer: £149 kit + £9/mo (2020 archived shop; consumer shop now removed) · councils/NHS/agencies: £45–65/mo per user + kit £168.85–576.50 ex VAT (G-Cloud 15, Jan 2026) · **alive** (iOS update 2026-11-11; Play update 2026-08-31) · iOS, Android, web (my.howz.com), care portal (care.howz.com)

Evidence: `raw/aside-howz.txt` (Aside, read-only), `raw/appstore-reviews.json`, REA `ev_19b89bee…` (row 1 of `rea-evidence.md`), screenshots `shots/howz-*.webp` (Play), `shots/howz-site-*.jpg` (public site images).

## Why people use it (numbers + quotes, linked)
- iOS GB 4.7★ from 127–130 ratings, 15 written reviews (11 five-star). Play UK 4.2★ from 12, 1K+ downloads, 7 written. Trustpilot 4.3 from 11–12, no 1–3★, newest review Jun 2021, page says "no recent history of asking for reviews". (O)
- **Loved:** knowing Dad is "up, come downstairs and has put the kettle on" without cameras (iOS 2021-07-11); a kettle plug "is a clever check" that started conversations with Mum (Trustpilot 2019-07-17); easy self-install, responsive support; one user with no battery changes in 12 months (Trustpilot 2021-04-22).
- **Hated:** "The hub is forever going down; without this there is no information" (iOS 2★, 2023-04-29); logs out weekly (iOS 3★, 2022-09-23); app failed repeatedly right after Dad's 2-hour fall (iOS 1★, 2019-09-22).

## Job to be done
When I live far from a parent who lives alone, I want to see without asking that they got up, made a drink and moved around, so I can relax or call only when something is off.

## Core flow (steps, seconds to value, friction)
1. Buy a kit (now through a council, NHS team or a "Howz Local" care agency; consumer pricing no longer published). 2. Plug in the hub; stick on pre-paired sensors (hub, smart plug for kettle/toaster, motion, door) (~20 min, O: help centre). 3. Create an account on my.howz.com or the app; add family as "VIPs". 4. **Wait ~8 days** while Howz learns the routine (help centre; T&Cs say 8–15; Play says ~7), then Howz emails the alerts it picked. 5. Toggle alerts. Time to first value: minutes for raw events, ~8 days for alerts. Friction: kit purchase now B2B; hub dependence.

## Feature inventory
| Feature | What it does | Free/paid | Evidence | Used by many? | Our call |
|---|---|---|---|---|---|
| 24-h clock dial (Home) | Ring amber (day) / navy (night), dots outside the ring for events, centre shows the last event | Subscription | Play screenshot 1 | Unknown | **Cut** (hard to read; hides meaning) |
| Activity list | "Movement in Kitchen 16:37", "Toilet opened 15:59", bursts grouped "(2)" | Sub | site image | Many reviews mention seeing movement | **Improve**: activities, not sensor events |
| Activity by sensor chart | Rows per sensor, dots on a 00–22 axis | Sub | Play 2 | ? | Cut |
| Insights | Current routine, routine over time, night activity, food, bathroom tiles with red/blue badges | Sub | Play 9 | ? | Cut (bathroom counts are intimate) |
| Alerts | Day: First activity, Late start/wakeup, Low day activity, Temp < 16 °C; Night: Up in the night, No night activity; 24 h: Unexpected activity, Door opened, Door left open | Sub | Play 10, site image | Reviews praise low-activity warnings | **Keep one**: "no kitchen sound by HH:MM" |
| Devices tiles | Sensor name, last seen, temperature | Sub | Play 4, 8 | — | **Improve**: dead sensor must look dead (demo shows one last seen 13 months earlier) |
| Privacy Mode, Away From Home | Pause monitoring | Sub | Play description | ? | **Keep** as the parent's Pause |
| Shared access, multiple homes | VIPs by email | Sub | Play | 1 review uses 2 homes | Out of scope |
| Bluetooth health devices, wearable button, smart meter | Info only | Sub | howz.com/sense | ? | Cut |

## How it works (Observed / Inferred)
- O: Zigbee-style wireless sensors to a hub (102×102×28 mm); cloud; family app. Marketing site is Astro + Google Analytics/GTM (REA `ev_19b89bee…`), static; app data on separate origins.
- O: routine learned over ~8 days, then alert thresholds set and emailed. I: thresholds are per-person time windows on event counts (e.g. first kettle use), not a published model.
- O: "Motion sensors only — no cameras or microphones" (Play listing). Play data-safety: may share app activity with third parties.
- Recent product line (O): "AI assessment report" add-on at £65/mo for care providers.

## Trust and failure handling
- Claims: none on accuracy. Medical disclaimer: "not a medical device" (Play). O: no published false-alarm or miss rate.
- Failure modes reported: hub outages = silence; app logouts; app failing to open after an update. O (screenshot): a stale "Back Door" sensor tile with no warning style.

## Paywall map
Everything sits behind kit + subscription. Rebuildable in 48 h: the timeline view, a time-window rule, a pause. Not rebuildable: the sensor network, B2B care-portal integrations.

## Does it need AI?
Mostly rules over sensor events (a plug turned on = kettle used). The "learned routine" is a statistical baseline. A no-AI baseline (fixed time windows) covers most of it. Kettle needs AI where Howz doesn't: turning *sound* into activities. Chatbot test: `raw/chatbot-test.md`.

## Top 3 weaknesses (pain × fixable × measurable, 1–5 each)
1. Silence is ambiguous when the hub drops (4 × 5 × 4): Kettle's heartbeat line.
2. Raw sensor events instead of meaning (3 × 5 × 3): Kettle's labelled activity blocks with evidence.
3. Hardware + ~8-day wait before alerts (2 × 5 × 4): Kettle needs no install and labels from the first window.

## Our rebuild delta and how it becomes our baseline
Keep: "did he make a drink / move about" reassurance, plain alert names, pause. Cut: dial, per-sensor charts, bathroom insights, devices grid. Add: activity-level kitchen detail from sound with measured accuracy. Baseline: Howz publishes no accuracy, so the comparison is the feature matrix (hardware, cost, cold start, what leaves the home), not a metric.

## Could not verify
Current consumer price; Howz's alert thresholds; any accuracy figure; behaviour of alerts when the hub is offline (whether an offline alert is sent).
