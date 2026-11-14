# Teardown: Canary Care (Sat Nov 14, 2026, Kettle stage 1, teardown agent)

https://www.canarycare.co.uk/families/ · maker Canary Care Global Ltd (UK; a forum post says the company "has since changed hands") · Core £419 / Plus £539 + £29/mo portal subscription, no long-term contract (shop.canarycare.co.uk, Nov 2026) · **alive** (new "Connect" hub and rebuilt portal 2026; Setup app updated 2026-10-16) · web portal + iOS/Android

Evidence: `raw/aside-canary.txt`, `raw/aside-canary-final.txt` (Aside), `raw/canary-{families,technology,index}.json` (public Next.js data), REA `ev_6b2506c1…` and export `ev_87c2b464…` (rows 4–6 of `rea-evidence.md`), screenshots `shots/canarycare-play-1..6.png` (legacy Play app), `shots/canarycare-setup-1..7.png` (Setup app).

## Why people use it (numbers + quotes, linked)
- Trustpilot 4.9 from 114 reviews: 107 five-star, 6 four-star, 1 three-star, **no 1–2★** (112 pulled). Play legacy app ~4.0 from 10 (cached), 1K+ downloads; iOS 4.6 from 5. (O)
- **Loved:** seeing Mum get up and go to bed with privacy kept; years of use for a parent with dementia; evidence that helped a care-home decision (Trustpilot 4★, 2019-07-15, https://uk.trustpilot.com/reviews/5d2c4b84ccd70b084c61491d); sensors alerted a family when a mother-in-law had a stroke and sat on the floor (Mumsnet 2026-06-27).
- **Hated or wished:** "the app needs to be slicker", misses the old kettle "3 rings" alert (3★, https://uk.trustpilot.com/reviews/5d45e210f01869069cc7e30a); a door sensor also needs a room sensor (4★); fit sensors lower than you'd think or grandma doesn't trigger them (5★, 2020-02-03); app logs you out frequently (iOS 4★, 2026-02-14); "a bit expensive at around £30 pm" (Alzheimer's Society forum, 2019); wants a panic button (4★).

## Job to be done
When my parent with memory problems lives alone, I want alerts if an expected thing doesn't happen (up by 9, fridge opened by lunch) and a record to show professionals, so I can intervene early and make care decisions with evidence.

## Core flow
1. Buy Core/Plus from the shop (or a council practitioner installs it). 2. Plug in the hub near the router or mobile signal. 3. Scan the QR code on the hub → Setup app. 4. Pair the hub by Bluetooth, join Wi-Fi or 4G. 5. Pair each sensor, starting furthest from the hub ("Pairing - 2:08" timer shown, O: Setup screenshot 6). 6. Set alert rules in the portal. Value: same day for events; ~2 weeks of data before averages are meaningful (third-party review). Friction: placement (height, door needs room sensor), 9 devices.

## Feature inventory
| Feature | What it does | Free/paid | Evidence | Many/few | Our call |
|---|---|---|---|---|---|
| Swim-lane timeline | Rows per sensor (Alerts, Visitor cards, Kitchen, Fridge, Stairs, rooms, doors) with dots merging into bars | Sub | Play 6 | ? | **Improve** to one activity bar |
| "Last recorded events" cards | CAPS label, bold detail, full timestamp; mixes months-old events | Sub | Play 2 | — | Cut |
| Alerts banner | "9 alerts in the past 24 hours", red/orange counts | Sub | Play 2 | — | **Avoid** |
| Rules | No movement in a window; no movement for X min in period Y; house unoccupied; remained too long (passive fall check); temperature; door at night; plug usage | Sub | rules post Mar 2025 (Aside) | Reviewers cite time-window alerts | **Keep one** time-window rule |
| Smart plug (the "kettle sensor") | On/off and duration of the appliance | £48 add-on / in Core | shop | Kettle is the product's name origin | Kettle does this by sound, plus more activities |
| Daily Diary, Reporting, Averages, exports | New 2026 portal | Sub | news post (REA-observed slug) | ? | Out of scope |
| Calling Circle | Several people get alerts and emails | Sub | families page | — | Local share only |
| Visitor cards | Carers tap in | B2B | Play 2–3 | Few | Cut |

## How it works (Observed / Inferred)
- O: Hub with Wi-Fi + 4G + Zigbee and up to 24 h battery backup; battery multi-sensors (motion, light, temperature; magnet = door), up to 12 months battery; smart plug; humidity and vibration sensors in Plus. "No cameras or microphones."
- O (REA): marketing site is Next.js/Turbopack fed by a headless CMS at cms.canarycare.co.uk; content prefetched as public JSON; only Google Tag Manager as third party.
- I: alerts are user-set rules over sensor events in time windows; no learned model is advertised.

## Trust and failure handling
- No accuracy claims. "Remained too long" is described as not an emergency falls alarm (O). Data "never shared with third parties" (O).
- Failure behaviour: hub battery covers power cuts and broadband dropouts (O); whether the family gets a "hub offline" alert was **not found**. A third-party review's "Wi-Fi only" claim contradicts the official pages.

## Paywall map
All features need the kit and £29/mo. Rebuildable: a timeline, a window rule. Not rebuildable: sensor hardware, council deployment.

## Does it need AI?
No: it is rules over sensor events. Kettle's AI is the sound-to-activity step Canary does with a plug per appliance. Chatbot test: `raw/chatbot-test.md`.

## Top 3 weaknesses
1. Alarm-first, stale dashboard (3 × 5 × 3): Kettle leads with a calm heartbeat and today's sentence.
2. Placement-sensitive sensors that silently miss (3 × 4 × 3): Kettle measures misses per activity and shows "not sure".
3. Cost: £419–539 + £29/mo (3 × 5 × 2): Kettle is free on an existing device.

## Our rebuild delta and how it becomes our baseline
Keep: calm "no cameras" promise, time-window rule, kettle as the emblem of a normal morning. Cut: lanes per sensor, alert banners, visitor cards. Add: activity labels with evidence, a heartbeat, the parent's pause. Baseline: none measurable (no published accuracy); compare on the feature matrix.

## Could not verify
Offline alerts; exact install minutes; 2026 portal screens (behind login); who pays in council deployments.
