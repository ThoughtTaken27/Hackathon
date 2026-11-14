# Teardown: California Board of Pharmacy standardized translated directions (Nov 13 2026)
https://www.pharmacy.ca.gov/publications/translations.shtml · State of California · free PDFs · alive

## Why people use it
- Legal backbone for translated labels in California: 16 CCR 1707.5 requires the Board to publish translations of the standard directions "into at least five languages other than English" (https://www.law.cornell.edu/regulations/california/16-CCR-1707.5, opened by a scout).
- Page title (opened): "Translations of Pill Directions as Specified in 16 California Code of Regulations Section 1707.5". The California Endowment "funded a project with national patient literacy researchers to develop and vet translations".

## Job to be done
When a California pharmacist prints a label for a patient with limited English, they want a vetted translation of the standard directions.

## Core flow
Download a PDF → copy the matching phrase onto the label. 15 English/translation pairs (counted in the Spanish PDF, saved at `.overnight/research-src/ca_translations_spanish.pdf (local only, not committed: reuse terms unclear)`).

## Feature inventory
| Feature | Evidence | Our call |
| --- | --- | --- |
| 15 vetted directions (1–3 pills × morning/noon/evening/bedtime) | Spanish PDF, observed | **use as professional reference translations for Spanish** (credit the source; the licence is "Copyright © State of California", so check reuse terms; we store derived pairs, not the PDF, in the final repo) |
| Languages: Chinese, Farsi, Korean, Russian, Spanish, Vietnamese | page, observed | **No Hindi, no Marathi, no Punjabi.** This gap is our setting |
| Disclaimer: Board "cannot ensure that a particular translation is appropriate for a particular patient" | PDF p.1, observed | echo in our UI |

## How it works
Fixed human-vetted phrase list, no free text. Anything off-list (insulin units, "hold if", inhaler max doses, day-of-week) isn't covered.

## Top 3 weaknesses
1. Covers only 15 simple directions; real labels say more (5 × 4 × 4).
2. No South Asian languages (5 × 4 × 5).
3. Static PDFs, unusable by families at home (3 × 5 × 2).

## Our rebuild delta
Keep: the idea of critical slots in a fixed grammar (number × pill × time). Add: free-text lines, Hindi/Marathi, and a checker. Baseline use: the Spanish pairs are professional references for chrF and for a "known-good" control set.

## Could not verify
Whether the Board's 15 match the 16 phrases in 1707.5(a)(4); reuse licence.
