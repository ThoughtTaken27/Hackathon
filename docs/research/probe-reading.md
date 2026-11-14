# NLLB-600M probe: lead agent's reading (Nov 13, 11:38 PM CT; after kickoff)

Research only, **not a result**. 12 agent-written directions × 3 languages, `facebook/nllb-200-distilled-600M`, beam 4, CPU (8 GB Apple silicon), throwaway scratchpad script. Raw output: `docs/research/samples/nllb-probe-12-directions.json`. The back-translation here is NLLB itself; Phase B uses OPUS-MT. Reading by the overnight agent (reads Devanagari): **not a blind native-speaker label.** These 12 lines may seed the dev set, and must never enter the test set.

**Speed:** 12 lines forward + 12 back took 237 s (mr), 260 s (hi), 202 s (es). That's ~8–11 s per generation with beam 4 and padded batches. It must be cached; use beam 1–2 and short batches live.

| # | English | Marathi | Hindi | Spanish |
| --- | --- | --- | --- | --- |
| 1 | 1 tablet by mouth twice daily **with food** | ✗ "with food" and "by mouth" dropped (दररोज दोनदा 1 टॅबलेट खा) | ok | ok |
| 2 | 2 capsules at bedtime | ok | ok | ok |
| 3 | Do not take with alcohol | ? became "do not drink alcohol" (मद्यपान करू नका) | ok | ok |
| 4 | half tablet every morning. **Do not crush or chew.** | ✗ 2nd sentence dropped | ✗ 2nd sentence dropped | ✗ 2nd sentence dropped |
| 5 | 1 **puff** every 4–6 h as needed for wheezing. Max 8 puffs/24 h | ✗ puff→"breath", "you need to breathe" | ✗ puff→"breath" | ✗ "soplo … para suspirar"; **max-8 sentence dropped** |
| 6 | **Hold** this medicine if BP < 100 | ✗ "stop this medicine" (थांबा) | ✗ "**keep** this medicine" (रखें) | ✗ "**Mantenga**" (keep) |
| 7 | 10 units under the skin before breakfast | ok | ok | ok |
| 8 | 1 tablet Mon/Wed/Fri only | ok | ok | ok |
| 9 | 3 pills morning + 3 at bedtime | ok | ok | ok |
| 10 | 1 at noon … 1 in the evening | ? noon→afternoon (दुपारी) | ok | ? evening→"noche" |
| 11 | Do not stop … without talking to your doctor | ok | ok | ok |
| 12 | 1 tablet every 8 h for 7 days | ok | ok | ok |

**Agent count of clear critical breaks:** Marathi 4/12 (1, 4, 5, 6), Hindi 3/12, Spanish 3/12, plus 1–2 borderline per language.

## What it changes
1. **Positives exist** (~25–35% on harder lines), so the measurement is viable. Multi-sentence and conditional lines break most. Teammate A's test set should include enough of them, but at natural rates (no cherry-picking).
2. **The probe does not show Marathi is clearly worse than Spanish for NLLB.** The errors here are mostly language-independent (dropped second sentence, "hold" mistranslated). The pitch stays a question, and "dropped sentences" may become the headline failure mode.
3. **"Hold" moves into v1** (7 kinds): it breaks in all three languages and is the clearest demo of a dangerous change ("keep"/"stop" vs "skip this dose").
4. **Sentence-count check:** a cheap rule (source has 2 sentences, translation has 1) would have caught #4 and #5 in Spanish. Add it to v1 as a structural fact.
5. **Same-model back-translation faithfully reports these errors** here (e.g. "keep this medicine"), so the back-translation route works. OPUS-MT keeps it independent.
