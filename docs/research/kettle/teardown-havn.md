# Teardown: havn by cortekAI (Sat Nov 14, 2026, Kettle stage 1, teardown agent)

https://www.havnwellness.com · maker cortekAI, LLC (Boston; LinkedIn 11–50 staff, ~20 followers) · price **not published** (plans: Essentials ≤4 sensors; Whole House unlimited) · **alive but pre-launch**: announced Oct 26 2026 (PR Newswire), US availability from Nov 30, sign-ups reviewed by hand · iOS/Android app + web, partner portal

Evidence: `raw/aside-havn-assistiv-apple.txt` (Aside: press release, site, FAQ, LinkedIn), REA `ev_e6dad2f5…`, export `ev_5be0ef0f…`, analysis `ev_7183f4fc…` (rows 10–12 of `rea-evidence.md`), exported bundles in `rea/havn/files/`.

## Why people use it
- No reviews, Reddit threads or X posts found. Press release syndicated (Yahoo Finance, Morningstar, KSN) with no independent coverage. (O)
- Both homepage testimonials are signed with a first name and initial that match the names of two people LinkedIn lists as havn employees. **Names match; same people not proven.** (O; I: possibly staff quotes. Names deliberately omitted here.)
- The only outside voice: a home-care agency owner quoted in the release.

## Job to be done
When I worry about Mom alone, I want passive sensors that learn her routine, notice a fall or an unusual gap, and let me talk to her room-to-room, so I don't need cameras, wearables or constant calls.

## Core flow
Request access (form) → invite within 24 h → plug one sensor per room into an outlet (under 15 min per room; "2 minutes per sensor" Wi-Fi) → app-guided setup → **7–14 days** baseline (shipped copy; the FAQ says "a day or two") → alerts. REA: onboarding routes `/onboarding/otp`, `/onboarding/pricing`, `/onboarding/setup`, `/onboarding/complete`; a build flag disables full self-serve onboarding.

## Feature inventory
| Feature | What it does | Paid | Evidence | Our call |
|---|---|---|---|---|
| Room sensors | Motion (presence, steps, posture, gait, occupancy), microphone + speaker, temperature; plug-in, Wi-Fi, **no battery** | Sub | site, FAQ | Kettle: one existing device |
| Sound classification | On-device; listens for help requests ("havn, help") and fall-like sounds; everything else dropped | Sub | FAQ | Kettle classifies *activities*, keeps nothing |
| 4-second clip to caregivers | Sent on a flagged event so they can tell a dropped pan from a fall; deleted on resolution or ≤30 days | Sub | FAQ | **Avoid**: Kettle sends no audio ever |
| Caregiver call-in | Tone + spoken notice; the resident **can't decline** | Sub | FAQ | Avoid |
| Alerts + escalation | Falls, unusual inactivity → everyone on account → phone calls → EMS; resident asked aloud first; can't be paused overnight | Sub | FAQ, release | Out of scope (emergency) |
| Status card | "Living Room · ACTIVE NOW · entered 1:50 PM · 1 person" | Sub | homepage images | **Avoid** (live location) |
| Daily counts | Steps 800, standing 4:30, Toilet 05, Fridge 10, Shower 02; sleep efficiency 80% | Sub | homepage images | Avoid intimate counts |
| Voice messages to resident | Recorded clip played "Now / Good Morning / Good Night / Scheduled" | Sub | images | Out of scope |
| Resident sees everything, can switch off | Transparency for the older adult | Sub | FAQ | **Keep** (Kettle's parent view + pause) |
| Unlimited family members | Sharing | Sub | LinkedIn, release | Local only |
| Agency dashboard, reseller margin | Partner channel; `admin.havnwellness.com` | B2B | partners page, REA | Cut |

## How it works (Observed / Inferred)
- O (REA): a Vite single-page app serves marketing and the family web app; API at `/api`; Microsoft Entra External ID sign-in; separate partner admin portal; **no analytics or third-party scripts** on the page.
- O: "The sensor sends a room summary to the cloud, where a second layer of intelligence puts the whole house together." I: on-device sound/motion classifiers + cloud baseline model per resident.
- O (FAQ fine print): "We reserve the right to use and sell anonymized data."
- O (REA, shipped copy): "havn uses motion and environmental sensors only — no video, no images" and "Never stores conversations or video — motion and environment only", **contradicting** the FAQ's microphone and 4-second clips.

## Trust and failure handling
- No accuracy, fall-detection rate or false-alarm rate published anywhere (O). Large dogs can be confused with the resident (FAQ). No battery: down in a power cut; flags sensor offline and whole-home connection loss (O).

## Paywall map
Everything is subscription + hardware; price unknown. Rebuildable: a sound-to-activity classifier and timeline. Not rebuildable: fall detection with escalation (safety-critical, unvalidated).

## Does it need AI?
Yes (sound and motion classification, baselines). It is the closest incumbent to Kettle's mechanism, which proves demand for sound-based home sensing, and it publishes nothing about accuracy.

## Top 3 weaknesses
1. Privacy story contradicts itself (mic + clips vs "motion only") (4 × 5 × 4): Kettle's privacy check proves no audio is written.
2. No published accuracy (4 × 4 × 5): Kettle publishes per-activity numbers.
3. Live-location UI and intimate counts (3 × 5 × 2): Kettle shows kitchen activities only, never "where Mom is now".

## Our rebuild delta and how it becomes our baseline
Keep: resident transparency, "no wearables". Cut: escalation, call-in, clips, counts, live location. Add: published accuracy, evidence per bar, consent gate. Baseline: none measurable; compare on the matrix and on privacy behaviour.

## Could not verify
Price; whether "toilet/fridge/shower" counts come from sound or motion; real-world reviews; which privacy statement matches the device.
