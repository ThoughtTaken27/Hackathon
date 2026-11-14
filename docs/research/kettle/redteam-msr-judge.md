# Red-team: sceptical MSR audio-ML judge on the Kettle PRD

Scored as if the plan is executed exactly as written.

## 1. Scores

| Line | Score | Reason |
| --- | --- | --- |
| R1 Technical execution | 22/30 | Offline demo mode and a committed head are strong. The scope (live WebSocket, 3 baselines, 4 encoders, Swift CLI, privacy audit, 3 design passes) is too large for the build time left, so something will crack. |
| R1 Originality | 13/20 | It is DCASE 2018 Task 5 plus a pretrained encoder and a UI. The twist (publishing misses and false alarms in a product category) is real but rests on an absence claim (§0, §14). |
| R1 Impact + track fit | 14/20 | Persona and brief wording are good. Meera is "300 miles away" but §5.5 and §8 admit there is no remote access. The health link is indirect and nothing was tested with a caregiver. |
| R1 Testing + honesty | 12/15 | Frozen run, CIs, slices, failures. Loses points because the evaluated unit (single 10-s window) is not the shipped product (§1 below). |
| R1 Communication | 11/15 | The pitch is clear. The UI spec is far larger than the one-page write-up can carry, and the numbers are still placeholders. |
| Finals Demo + clarity | 23/30 | The clink-to-label moment is good, and the fallbacks exist. |
| Finals Technical depth | 21/30 | A frozen encoder plus logistic regression is shallow. Depth depends on the ablations and on the answers to the weak points below. |
| Finals Impact | 14/20 | One home, one person, no user study. |
| Finals Q&A | 14/20 | Q2, Q7 and Q10 have thin answers (§6). |

The PRD's own self-score of R1 = 81 (§14) is about 8 points generous.

## 2. Five weakest technical points, ranked

1. **The thing measured is not the thing shipped (§13, §6, §10.4).**
   - Eval scores single 10-s windows on ~1,000 randomly sampled moments.
   - The product uses 2-of-3 smoothing, θ abstention, a 5-s "chip" window and a single laptop mic.
   - The pitch line (§0) says "measured missed activities and false alarms on a public week-long recording". That is not what is measured.
   - The sampled eval moments are non-contiguous, so smoothing cannot be evaluated on the eval set at all.
   - Fix (about 2 h):
     - Define a block-level metric on held-out dev folds, using contiguous sessions. A true activity segment is "caught" if a predicted block of the same class overlaps by at least 50%. A "false alarm" is a predicted block with no such overlap.
     - Report misses per day and false alarms per day.
     - Run the own-kitchen set through the full pipeline, including the 5-s chip.
     - Reword the §0 sentence to say "per 10-s window".
2. **Strawman baselines (§13.3).**
   - Every baseline is zero-shot and goes through a hand-written label map. The map was written by the team after looking at dev clips (probe 3).
   - The comparison is then "trained head vs untrained mapped head", which tells a researcher nothing.
   - No trained cheap baseline exists.
   - Fix (30 min): add (a) log-mel or MFCC mean/std plus logistic regression on the same training subset, (b) a linear probe on AST embeddings. Both use the same folds. Report Apple as "zero-shot, mapped", not as a competitor.
3. **Domain shift is asserted, not tested (§13.2, §13.7).**
   - The eval set is the same home and week (§13.2 admits it).
   - The own-kitchen set is about 40 minutes: 8 classes × 5 sessions × 1 min. That is roughly 240 windows, staged by the people recording, in one or two kitchens. It gets no meaningful CI and is not a "home" slice.
   - Fix (free): run leave-one-node-out CV on dev (train on 3 mic nodes, test on the 4th). It is a legitimate mic-shift proxy that needs no eval data.
   - Fix (for own-kitchen): label it "exploratory, N sessions, windows ≈ 240" and report a session-level Wilson interval.
   - Fix (if time): add EQ and noise augmentation chosen on the leave-one-node-out result.
4. **The calibration-based abstain is not shown to handle out-of-distribution input (§6, §13.6, Q7).**
   - A max-softmax threshold is known to be overconfident on off-list sounds.
   - The garbage slice (§13.6.6, 20 noise/music/speech clips) is the only check, and 20 clips is too few.
   - Fix: generate about 200 off-list clips (public-domain music, speech-only, noise, ESC-50 categories not in the 9). Report the risk-coverage curve and the confident-wrong rate at θ on those.
5. **The privacy proof has holes (§13.9, F10).**
   - Starlette spools uploads over 1 MB to a temp file. `/api/try` accepts 60 s of audio, which exceeds that, so the "never saved" claim breaks on exactly the demo path.
   - Chromium's fake mic reads a WAV file from disk, which collides with the "0 audio-like files" assertion.
   - A Python audit hook does not cover Chromium or the OS.
   - Fix: read the raw request body in `/api/try` instead of using `UploadFile`. Whitelist the fake-mic input file explicitly by path. Add a test that uploads 5 MB and checks that nothing new appears in `$TMPDIR`. State the threat model in one sentence.

## 3. Leakage risks

| Channel | PRD control | Sufficient? / change |
| --- | --- | --- |
| Dev folds for model selection (§13.2) | Folds are session-disjoint, and C is chosen by inner CV | Partly. Encoder, head, θ, smoothing and window are all picked on the same 4-fold CV that is then reported. Report dev as "optimistic (selection on the same folds)", or nest the selection. |
| Probe-based encoder choice (probe 2) | Done on dev clips | OK, but N=304 is noise. The 1/40-CPU claim is true. The "equals best" claim needs the full-dev ablation. |
| DCASE eval set (§13.2) | Separate cache, refusal flag, one run, hash logged | The flag only guards against accident. Add a pre-registered commit before fetch (seed, recipe, head sha). **The eval-harness code itself is untested on real eval data**, so a crash or bug mid-run forces a rerun and there is no protocol for that (§16 M6). Rehearse the exact eval path on a dev-fold stand-in with a dummy head. Write the rerun rule down: a rerun is allowed only for crashes, and both runs are reported. |
| Mic-fingerprint test (§13.2, §16 M2) | None | **Contradiction.** M2 says the eval sample is "fetched but not embedded or opened", yet the fingerprint needs eval spectra. Fix: allow unlabeled spectra only, with the rule (distance to dev-node centroids, threshold) written down before looking. Never join it to labels or scores before the frozen run. |
| Eval top-up to ≥50 per class and reweighting (§13.2, §13.5) | Seed fixed | The top-up uses labels, so reweighting is required for validity. The reweighting is also in §13.5 for dev. Missing: whether the bootstrap redraws weights, and per-class weight caps. Specify both. |
| Eval labels committed to the repo | Unmodified file | Fine for provenance, but anyone can peek. Note that labels were not read by the model-selection code, and verify with a grep of the eval-path imports. |
| θ and temperature (§13.7, Q7) | Dev-only | Needs a stated recipe: fit the temperature on out-of-fold dev logits, and pick θ on the same set. Do not reuse in-sample predictions. State which prior the dev set has (balanced vs reweighted). |
| Subsample and reweighting | Disclosed (§13.2) | Disclosure is adequate. Do not call the number "leaderboard-comparable". |
| Own-kitchen set (§13.7) | Scored once, labeller is not the code author | Adequate for labels. Weak as evidence: the recorder both stages and labels the sounds, so label noise is correlated with the performance. Say so. |
| Demo days (§7) | Labelled staged | **Leak.** Demo clips are dev clips, and the head is trained on ≤9k dev clips. The demo is in-sample. Use only clips from a held-out fold, or put a banner on the demo: "training clips". |

## 4. Under-specified or unmeasurable

- Block-level metric: no definition of match, overlap or tolerance (§13.5). Without one, "missed activities" has no meaning.
- Reweighting variance: the bootstrap CI procedure for reweighted precision and F1 is not given (§13.5).
- Latency: "2.6 s onset→label" comes from one loud onset (probe 4). The plan says "median, p90, N" over 20 synthetic transitions, with no spec for how the transitions are made or whether room noise is included.
- Privacy check: no threat model. It does not cover swap, the Chromium disk cache or crash dumps.
- 5-s chip window: the encoder was probed on 10-s inputs. There is no evidence of 5-s accuracy beyond the ablation line.
- θ: "lowest threshold keeping shown-label precision ≥ 0.9" (Q7). Precision on a balanced or a reweighted set? Over which classes?
- Mic fingerprint (Q5): "mean log-mel per node" has no decision rule.
- One-coder pain counts "±20%" (§5.1) are not a confidence statement.

## 5. Claims without evidence or overreaching

- §0: "the only one of these 'is Mum OK' products that tells you how often it's wrong". This is an absence claim from a non-exhaustive search of nine products.
- §14 and §0: "first published per-activity misses/false alarms in this product category". Same problem.
- §6: "zero-shot maps score 40–49 macro F1 vs ~82 for a trained head (probe 2)". N=304, hand-made maps, and the head's training set in that probe is not stated.
- §6: "CED-tiny … equals the best probe score". Differences at N=304 are inside the noise.
- Q8: "mostly because it hears cooking and washing up as doors and has no TV class". This is a causal story written before the result exists.
- §5.1 P1 and P7: "Kettle's design answers each one". Nobody has tested the design. The reviews show the pain, not that Kettle fixes it.
- §3: Meera views from Chicago at 11 AM. §5.5 and §8 say there is no relay, so only same-network use works. The persona moment is not buildable as written.
- §2: the 28% statistic is about all adults 65+. It is not about early memory loss.
- §5.1 P4: "inference 24–35 ms per window (probe 4)". This is one machine, and the live pipeline also decodes, resamples and runs WebSocket I/O.
- §4: "no published frozen-encoder result on SINS". Already hedged in §20.3. Keep it out of the write-up.
- §1: "Use public datasets only" is stretched by own-kitchen audio. §20.2 flags it but does not settle it.

## 6. Three finals questions §19 answers worst

1. **Q2, "One home, one person: haven't you just learned that house?"** The answer is evasive.
   - The "unknown mics" slice tests microphone shift, not home shift.
   - The own-kitchen set is about 240 windows.
   - A strong answer separates the two shifts: "mic shift is tested by leave-one-node-out and unseen eval nodes; home shift is tested only by our kitchens, N sessions, with wide intervals; we did not test people or homes beyond that". Then quote the numbers.
2. **Q7, "Isn't 'Not sure' hiding errors?"** The answer gives no evidence for out-of-distribution behaviour.
   - A strong answer shows the risk-coverage curve on dev, the fraction abstained, and the confident-wrong rate on the 200-clip off-list set. It also says plainly that max-softmax abstention is a known weak OOD detector.
3. **Q10, "How do you prove nothing is recorded?"** "Proof" is the wrong word. The proof has the gaps in §2.5.
   - A strong answer states the threat model: the design never calls a write on audio buffers (a code fact that can be inspected), plus a test that checks it, plus the known limits (swap, browser caches).
   - It then shows the 5 MB upload test result.
