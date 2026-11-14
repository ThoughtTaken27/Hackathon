# Teardown: paid SMS spam blockers (RoboKiller, Textkiller, Truecaller) (Nov 13 2026, overnight agent)
Public surface only: App Store search JSON (`itunes.apple.com/search`, fetched 11:47 PM CT) and recent reviews read through the Aside browser (`voice-second-look.md`). No app installed, no login.

| App | Rating (count) | Price on listing | Last version | Link |
| --- | --- | --- | --- | --- |
| RoboKiller | 4.50 (414,654) | Free + subscription | 2026-10-29 | https://apps.apple.com/us/app/robokiller-spam-call-blocker/id1022831885 |
| Truecaller | 4.45 (253,024) | Free + Premium | 2026-11-09 | https://apps.apple.com/us/app/truecaller-premium-caller-id/id448142450 |
| Textkiller | 4.31 (12,999) | Free + subscription | 2025-02-26 | https://apps.apple.com/us/app/textkiller-spam-text-blocker/id1514005355 |

## Why people use them
Set-and-forget relief from daily spam; a happy reviewer reports 95–98% fewer spam texts (Textkiller 5★, 2026-10-30).

## Job to be done
"When strangers keep texting my phone, I want them gone without thinking about it."

## Core flow (Observed from listings/reviews; Inferred where noted)
Install → enable the iOS SMS filter extension → pay after a trial → unknown-sender texts are sorted into a junk folder. The user never sees a reason. Inferred: blocklists of numbers and keyword rules, plus crowd reports; iOS message-filter extensions only see unknown senders.

## Trust and failure handling
No published accuracy. Reviews report decay (spam returns after months; keyword rules leak), false alarms (Truecaller blocked Costco customer service) and billing traps (RoboKiller $9.99/week trial billed outside Apple; ~$100/year, reviewer's figure).

## Paywall map
Filtering is paid after a 7-day trial (RoboKiller, reviewer). Everything they charge for is a blocklist or keyword list; nothing proprietary we'd need.

## Does it need AI?
Their main job is a lookup (number blocklist) plus keyword rules. That is our **"simple rule" baseline** (brief: "show that it beats a simple rule"): a keyword + link rule written from the same tactics, scored on the same test set.

## Top 3 weaknesses (pain × fixable × measurable)
1. Silent false alarms that hide real bank codes and clinic reminders (X, 2026-11-09 and 11-12): 5×4×5.
2. No "why": the older adult learns nothing and the family can't check the call: 4×5×4.
3. Rules decay as scams change: 4×3×5 (measurable with dated data).

## Our rebuild delta
Keep: one verdict per message. Cut: blocking, accounts, subscriptions, number lookups. Add: a learned classifier tested on dated modern scams, the tactics it found highlighted in the text, an "ask someone first" band instead of silent blocking, and a measured false-alarm rate on legit look-alikes. Their approach becomes our keyword-rule baseline.

## Could not verify
Their actual algorithms; whether iOS 26 limits third-party SMS filters (one reviewer's guess).
