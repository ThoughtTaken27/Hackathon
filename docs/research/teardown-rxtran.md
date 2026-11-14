# Teardown: RxTran (Language Scientific), paid pharmacy-label translation (Nov 13 2026)
https://www.rxtran.com/services/ · Language Scientific Inc. · price not published (call/email) · alive · B2B service for pharmacies

## Why people use it
- Pharmacies buy it to meet translated-label laws (NYC 2010 chain-pharmacy law, NY Education Law §6829, CA 16 CCR 1707.5). Its vendor pages summarise those laws (https://www.rxtran.com/regulatory/new-york-city-regulations; not checked against the primary law).
- Customers are pharmacies, not families. No consumer reviews were found.

## Job to be done
When a pharmacy must print a label in a patient's language, it wants a vetted translation of the SIG (directions) and warning stickers, so it complies with the law and avoids errors.

## Core flow
Inferred: the pharmacy system sends SIG codes → pre-translated, human-reviewed phrase library → printed bilingual label. Seconds to value: instant for library phrases; free-text directions need human translation.

## Feature inventory
| Feature | What it does | Free/paid | Evidence | Our call |
| --- | --- | --- | --- | --- |
| SIG + auxiliary-label translation | phrase library | paid | services page | keep the idea: a phrase library is the gold standard |
| Consumer Medication Information in 20 languages | leaflets | paid | services page | cut |
| "Linguistic testing" | human QA | paid | services page | replace with an automatic, measured check |
| Patent US 11,836,454 B2 "reliable translation in near real-time" | per a snippet: the user confirms the intended meaning before display | — | https://patents.google.com/patent/US11836454 (claims not read) | note as prior art; ours is automatic fact comparison, not user confirmation |

## How it works
Observed: human translators plus phrase libraries. Inferred: no automatic fact check is exposed to patients or families.

## Trust
Human review is the trust story. It doesn't reach the family at home who gets an English-only label.

## Paywall map
Everything is paid and B2B. Proprietary phrase libraries can't be rebuilt in 48 h. **What we can rebuild on public data:** a small, open, checked phrase set (CA Board directions + our own lines) and an automatic checker anyone can run for free.

## Does it need AI?
Their core is human translation. Ours: model translation + rule-based fact check + model back-translation.

## Top 3 weaknesses
1. Doesn't reach families with English-only labels from pharmacies outside these laws (5 × 4 × 3).
2. Hindi and Marathi coverage unknown and not published (4 × 4 × 3).
3. No published accuracy numbers (3 × 5 × 4).

## Our rebuild delta
Keep: phrase-level thinking, with critical slots (dose, frequency, time, negation). Add: an open checker that works on *any* translation. Baseline: not directly comparable (paid, human). We cite it as the "gold" way, which costs money.

## Could not verify
Prices, language list, patent claims, whether they run automated back-translation.
