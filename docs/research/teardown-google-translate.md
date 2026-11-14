# Teardown: Google Translate, as used for medication instructions (Nov 13 2026, overnight agent)
https://translate.google.com · Google · free · alive · web, iOS, Android

## Why people use it (numbers + quotes, linked)
- iOS App Store: 4.29★ from 84,157 ratings, free (public iTunes JSON, https://apps.apple.com/us/app/google-translate/id414706506, accessed Nov 13 2026). Observed.
- It's the default tool clinicians and families reach for: Khoong et al. 2019 studied it *because* emergency doctors use it for discharge instructions (JAMA Intern Med 2019;179(4):580–582; summary opened at https://psnet.ahrq.gov/issue/assessing-use-google-translate-spanish-and-chinese-translations-emergency-department).
- Voice of the user: no Reddit thread could be opened from here (the Reddit JSON is blocked and searches returned none). A prescriber survey (Annals of Family Medicine, reported by US Pharmacist, https://www.uspharmacist.com/article/survey-finds-gaps-in-nonenglish-medication-instructions): 91.8% of 169 prescribers did not tell patients they could ask for a non-English label. So families fill the gap themselves. Inferred: with a phone translator.

## Job to be done
When my grandmother gets an English pharmacy label, I want to turn it into a language she reads, so she takes the medicine correctly without me there.

## Core flow (steps, seconds to value, friction)
Open app → pick target language → type or photograph the label → read the output. About 10–20 s to first value. Friction: none to translate. The real friction is that **nothing tells you which line is wrong.** A bilingual helper must re-read everything, and a non-bilingual grandchild can't check at all.

## Feature inventory
| Feature | What it does | Free/paid | Evidence | Used by many? | Our call |
| --- | --- | --- | --- | --- | --- |
| Text translate | 240+ languages incl. Hindi, Marathi | free | product page | many | keep (as a translator we audit) |
| Camera translate | OCR + translate a label | free | app listing | many | cut (out of scope this weekend) |
| Back-translation | User can swap direction manually | free | product | few (manual) | **improve: automate and compare facts** |
| Confidence / warning per line | none | — | observed absence | — | **add** |

## How it works (Observed / Inferred)
- Observed: neural MT, sentence-level output, no per-sentence confidence shown to the user.
- Inferred: general-domain training; medical label shorthand ("1 tab PO BID", "hold if SBP<100") is out of domain.

## Trust and failure handling
- Observed: no per-line uncertainty, no "check with a pharmacist" for dose lines. (A medical disclaimer on Google's help page could not be verified; the fetch was truncated.)
- Evidence of harm: Khoong 2019 found 92% of Spanish and 81% of Chinese instructions correct; "2 percent in Spanish and 8 percent in Chinese, had the potential to cause clinically significant harm" (UCSF press release, opened: https://www.ucsf.edu/news/2019/02/413376/google-translates-doctors-orders-spanish-and-chinese-few-significant-errors). Martos et al. 2025 (JAMA Netw Open, opened) found the same pattern for a different neural MT (Azure): clinically impactful errors in 7% of Spanish sections vs 52% Chinese, 41% Vietnamese, 92% Somali (148 sections, 34 instructions).

## Paywall map
Free. The Cloud Translation API is paid and needs a key, so **we can't use it as a live baseline without a key**. We'll use free open models (NLLB-200, OPUS-MT) as stand-ins and let the user paste any translator's output.

## Does it need AI? (+ chatbot test)
Translation is a real model task. The *check* (did dose, frequency, timing and negation survive?) is mostly rules over extracted facts, plus a model step (back-translation). Chatbot test: `docs/research/chatbot-test-translation.md`. A frontier chatbot translated all 8 test lines correctly into Hindi and Marathi.

## Top 3 weaknesses (pain × fixable × measurable)
1. No per-line "don't rely on this" signal (5 × 5 × 5).
2. Quality collapses for poorly served languages, and the user can't tell (5 × 3 × 5).
3. Medical shorthand and conditionals ("hold if…") are out of domain (4 × 3 × 4).

## Our rebuild delta and how it becomes our baseline
Keep: translate a line. Cut: camera, conversation, 240 languages. Add: **a per-line safety verdict (facts match / check this line) with the evidence**. Baseline: "trust every line" (what a Google Translate user does today) vs our flags, on the same translations.

## Could not verify
Google's medical-use disclaimer; Hindi/Marathi-specific error rates for Google Translate; any Reddit post (blocked).
