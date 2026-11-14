# Teardown: Care Daily (People Power) (Sat Nov 14, 2026, Kettle stage 1, teardown agent)

https://caredaily.ai · maker People Power Company (US) · consumer "Family Care Pack" price **not found**; site is B2B "request a quote" (tiers Check-in, Insights, Protect, Longevity) · alive (iOS "Care Daily AI" updated 2026-11-13; Play v1.21.114 updated 2026-11-04) · iOS, Android

Chosen as one of the "best 2" because it has the most reviews among the remaining sensor products (iOS 11 ratings with 10 written; Play 4.6★ from 26, 9 written) and the best status design found. Evidence: `raw/aside-stack-caredaily-final.txt`, `raw/appstore-reviews.json`.

## Why people use it
- **Loved:** a "trusted circle" that shares alerts by SMS so family "don't need to download the app" (iOS 2019); peace of mind for a mom with early dementia, seeing wake-up, sleep and front-door opens (Play 5★, 2020-12-19).
- **Hated:** "Late-night notifications aren't always accurate" (same 5★ review); logs out after minutes, phone-number login by text (iOS 1★, 2020-08-14, after a utility-program migration); can't use a New Zealand number (Play 1★, 2025); dropped Google Home and old-phone baby-monitor features (Play 1–2★); smart plug not working, no response (iOS, 2021).

## Job to be done
When I share care with siblings, I want one status everyone can read (good / check in / help), with a plain daily summary, so we coordinate without everyone calling Mom.

## Core flow
Account → app guides device install step by step (O: reviews praise this) → add Trusted Circle (up to 10; they can respond by SMS without the app) → optional emergency call centre.

## Feature inventory
| Feature | What it does | Our call |
|---|---|---|
| **Three-state status** | Green shield "Looking good · Everything looks normal · 10 seconds ago"; orange "Check in · Something doesn't look right · Just now"; red "Help needed!" | **Take** the sentence + check-time pattern (green and "not listening" only; no red) |
| Supporting rows | "Sleeping since 10:35 PM", "Expected awake by 6:30 AM", "Last went outside 2 days ago" | **Take**: plain sentences |
| Daily Summary | Text timeline: sleep, left home 5:33 PM for 37 min, "made coffee 7:10 AM", "Refrigerator opened" ×3, "Medicine container opened 2 times" | **Take** the sentence style for Kettle's day summary; drop medicine |
| Trusted Circle | Access levels: app access vs no access; SMS alerts | Local share only |
| Falls by ambient radar, wandering, loneliness, leaks | Protect tier | Cut |
| AI claims | "AI Ambient Assistants", "drift detection", "HIPAA-compliant AI"; RCT with UC Berkeley (Levenson et al., *Clinical Gerontologist*, 2025) on lower caregiver anxiety and better caregiver sleep; $8M+ NIA funding | The RCT measures *caregiver* outcomes, not detection accuracy (to verify) |

## How it works
- O: gateway + entry and motion sensors; cloud; per-person behaviour learning; SMS circle. Same tablet layout as StackCare (I: shared platform).

## Trust and failure handling
The only product citing a peer-reviewed trial (caregiver outcomes; not opened at the primary source, so **unverified**). No detection accuracy.

## Paywall map
Quote-only. Rebuildable: the status sentence and the daily text summary over Kettle's labels.

## Does it need AI?
Rules + baselines on sensor events; the "AI assistant" wording is marketing (I).

## Top 3 weaknesses
1. Login/account friction and dropped features (3 × 5 × 2).
2. No published detection accuracy despite AI branding (3 × 4 × 5).
3. Opaque price and B2B pivot (3 × 5 × 1).

## Our rebuild delta and how it becomes our baseline
Keep: status sentence + "checked 10 s ago", plain daily summary sentences. Cut: radar, medicine, circle accounts. Add: activity evidence and measured accuracy. Baseline: none measurable.

## Could not verify
Family Care Pack price; the Levenson 2025 RCT details at the primary source.
