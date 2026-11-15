# Data sources and APIs

Reachability checked from the Claude Code cloud container on **Nov 13, 2026**. Credit every source we use in the write-up.

| Source | Use | Key? | Status Nov 13 | Notes |
| --- | --- | --- | --- | --- |
| [NLM RxNorm API](https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getApproximateMatch.html) (`rxnav.nlm.nih.gov/REST`) | Drug-name normalization, misspellings | No | ✅ 200 | ~20 req/s limit. Interaction API discontinued Jan 2024: don't use |
| NLM RxClass (`rxnav.nlm.nih.gov/REST/rxclass`) | Drug → class (ATC, etc.) | No | ✅ 200 | |
| [CDC Heat & Medications guidance](https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html) | Source table for HeatRx rules | — | ✅ | Encode by hand after kickoff; it's not complete, say so |
| [NWS API](https://www.weather.gov/documentation/services-web-api) (`api.weather.gov`) | US 7-day forecast | No (send a User-Agent) | ✅ 200 | Good fallback for Open-Meteo |
| [Open-Meteo](https://open-meteo.com/) forecast + archive | Forecast + historical heatwave replay, any country | No | ⚠️ **429 from cloud container** | Shared cloud IP used up the daily quota. Works from a laptop/Colab. Cache responses |
| [NOAA NCEI daily summaries](https://www.ncei.noaa.gov/access/services/data/v1) | Historical temps (heatwave replay) | No | ✅ 200 | |
| [Meteostat bulk](https://dev.meteostat.net/bulk/) | Historical daily station data | No | ✅ 200 | |
| [NWS HeatRisk](https://www.wpc.ncep.noaa.gov/heatrisk/data.html) | Official heat-risk levels | No | — | GeoTIFF/KML only; awkward. Compute heat index ourselves for the MVP |
| [openFDA drug shortages](https://open.fda.gov/apis/drug/drugshortages/how-to-use-the-endpoint/) | Shortage Radar | No | ✅ 200 | ~1,700 records, imbalanced |
| [CMS Medicare Part D](https://catalog.data.gov/dataset/medicare-part-d-prescribers-by-provider-and-drug) (`data.cms.gov`) | Prescriptions by drug/location (stretch map) | No | ✅ 200 | Provider file is huge: filter via API or use state-level file |
| [CDC/ATSDR SVI](https://www.atsdr.cdc.gov/place-health/php/svi/index.html) | Social vulnerability overlay (stretch) | No | ✅ 200 | |
| MediaPipe Pose (PyPI `mediapipe`) | ChairCheck pose tracking | No | ✅ PyPI reachable | Pretrained: credit it |
| [CDC STEADI chair-stand norms](https://www.cdc.gov/steadi/) | ChairCheck thresholds by age/sex | — | — | |
| Hugging Face | Pretrained models, Spaces hosting | Optional | ✅ 200 | |
| [ESC-50 full set](https://github.com/karolpiczak/ESC-50) (Piczak 2015; `raw.githubusercontent.com/karolpiczak/ESC-50`) | All 2,000 clips, 50 categories, 5 folds: sound-type calibration and safety-alert evaluation, held out from the frozen head (`eval/esc50_all.py`) | No | ✅ Nov 15, 2026 | CC BY-NC 3.0. Accessed 2026-11-15. Audio git-ignored in `data/clips/esc50_all/`; only CED-tiny embeddings/scores cached |
| [Nonspeech7k](https://zenodo.org/records/6967442) (Rashid et al., IET Signal Processing 2023), test split only | 725 human non-speech clips (breath, cough, crying, laugh, screaming, sneeze, yawm): sound-type calibration and safety-alert evaluation, held out from the frozen head (`eval/nonspeech7k.py`) | No | ✅ Nov 15, 2026 | Licence per Zenodo metadata: CC-BY-4.0 (cc-by-4.0). Accessed 2026-11-15. Audio git-ignored in `data/clips/nonspeech7k/` |
| Synthetic alarms (our own code, `eval/synth_alarms.py`) | 960 generated clips: NFPA 72 smoke (t3), CO (t4), kitchen-timer and no-alarm over pink noise / benign ESC-50 backgrounds at 20/10/0/-5 dB SNR: safety-alert evaluation, held out from the frozen head | No | ✅ Nov 15, 2026 | Synthetic, labels known by construction; regenerable from seed, no audio saved. Accessed 2026-11-15. Backgrounds use ESC-50 (CC BY-NC 3.0) |

## Practices

- **Cache every API response to disk** (e.g. `cache/` folder, git-ignored) so demos, evaluation and the video don't depend on the network or rate limits.
- Commit small, curated sample data needed to run the demo. Keep big raw downloads out of git.
- Synthetic test data must be clearly labeled synthetic, and the labeling process written down (who labeled, from what source).

## Prior art studied for Kettle (credit in the write-up; accessed Nov 14, 2026; details in `docs/research/kettle/`)

| Product / work | Link | What we took (patterns only, no code or assets) |
| --- | --- | --- |
| Howz (Intelesant) | https://www.howz.com/reassure | Plain alert names ("Late start"), pause; anti-pattern: raw sensor events, stale sensors |
| Canary Care | https://www.canarycare.co.uk/families/ | Time-window rule, "no cameras" promise; anti-pattern: alert-count banner |
| havn (cortekAI) | https://www.havnwellness.com | Resident sees what family sees; anti-pattern: live location, audio clips |
| Assistiv Home Sensing | https://www.assistiv.services/home-sensing | Acoustic activity set (cooking, conversation, TV, silence) |
| Apple Sound Recognition / SoundAnalysis | https://support.apple.com/guide/iphone/use-sound-recognition-iphf2dc33312/ios | Hedged copy; built-in classifier as a zero-shot **baseline** |
| Alexa Together / Emergency Assist | https://www.aboutamazon.com/news/devices/alexa-together-launches-to-help-customers-remotely-care-for-loved-ones | "Type, not content" feed; no-activity rule |
| StackCare | https://stackcare.com | "Up & About Check", "system offline" notice |
| Care Daily (People Power) | https://caredaily.ai | Status sentence + "checked 10 s ago" |
| Snug | https://apps.apple.com/us/app/snug-daily-safety-check-in/id1122758716 | Older adults' own complaints about check-in burden |
| DCASE 2018 Task 5 baseline + results | https://github.com/DCASE-REPO/dcase2018_baseline · https://dcase.community/challenge2018/task-monitoring-domestic-activities-results | Published comparison numbers (baseline 83.1, best 88.4 unknown-mic macro F1) |

## Kettle data, models and statistics (stage 2, accessed Sat Nov 14, 2026; probes in `docs/research/kettle/probes/`)

| Source | Use | Licence | Key? | Status Nov 14 | Notes |
| --- | --- | --- | --- | --- | --- |
| [SINS / DCASE 2018 Task 5 dev](https://doi.org/10.5281/zenodo.1247102) (Zenodo 1247102) | Train head, dev folds, demo clips | CC BY-NC 4.0 | No | ✅ range reads work | 23 zips, 46 GB; 72,984 clips, 4 nodes × 4 ch; Zenodo caps guests at **133 requests/min** (`x-ratelimit-limit`) → ~2 clips/s; index built in 35 s (probe 1) |
| [SINS / DCASE 2018 Task 5 eval audio](https://zenodo.org/records/1291760) (v1.0.0) | One frozen test run | CC BY-NC-ND 4.0 | No | ✅ range reads work | Same audio zips as v2; never commit (ND) |
| [DCASE 2018 Task 5 eval labels](https://zenodo.org/records/1964758) (v2.0.0) | Eval ground truth | CC BY-NC-ND 4.0 | No | ✅ | `meta.txt` + `evaluation_setup/map.txt` (1.wav → EvalNode1_ex50_156.wav); 7 nodes, 72,972 clips. Which nodes are the 3 unseen arrays is not stated: verify |
| [DCASE 2018 Task 5 results](https://dcase.community/challenge2018/task-monitoring-domestic-activities-results) | Published comparison | page | No | ✅ | Baseline 83.1, best 88.4 macro F1 (unknown mic) |
| [CED-tiny](https://huggingface.co/mispeech/ced-tiny) (rev `ace276d2…`) | Encoder + AudioSet evidence | Apache-2.0 | No | ✅ | 21 MB weights; 0.014 s per 10-s window on CPU (probe 2) |
| [CED-small](https://huggingface.co/mispeech/ced-small) | Ablation | Apache-2.0 | No | ✅ | |
| [AST AudioSet](https://huggingface.co/MIT/ast-finetuned-audioset-10-10-0.4593) | Ablation, zero-shot baseline | BSD-3-Clause | No | ✅ | 0.52 s/window CPU |
| [LAION CLAP htsat-unfused](https://huggingface.co/laion/clap-htsat-unfused) | Zero-shot baseline | Apache-2.0 | No | ✅ | |
| Apple SoundAnalysis `.version1` (macOS 27.2.1) | Zero-shot baseline | Apple SDK | No | ✅ | 303 classes; 0.08 s/clip; frozen map `probes/maps/apple_map.json` |
| [ACL 2023 Profile of Older Americans](https://acl.gov/news-and-events/announcements/acl-releases-2023-profile-older-americans) | Problem statistic | US gov | — | ✅ opened | Quote: "Of older adults 65 and older living in the community, 59% lived with their spouse/partner in 2023. About 28% lived alone." |
| Unverified, do not quote yet | — | — | — | ⚠️ | ACL PDF count (16.2 M living alone); AARP/NAC long-distance caregiver share; Alzheimer's Association dementia living-alone share; Pew 26% (2025 short read): seen in snippets only |

## Added in stage 3 (build, Sat Nov 14, 2026)

| Source | Use | Licence | Notes |
| --- | --- | --- | --- |
| [ESC-50](https://github.com/karolpiczak/ESC-50) (K. J. Piczak, ACM MM 2015) | 200 off-list clips (20 non-household categories) to test "Not sure" | CC BY-NC 3.0 | Fetched to `data/clips/offlist/` (git-ignored), never committed; repeated to 10 s |
| DCASE 2018 Task 5 results page (re-opened by a scout, Nov 14) | Published numbers | page | Baseline 84.5 dev / 85.0 known-mic / 83.1 unknown-mic; best entry Inoue_IBM_task5_1 90.0 / 90.4 / 88.4 (tied at 88.4 with two Tanabe_HIT entries; no rank column); ranking metric = macro F1 on unknown mics; the pages don't map EvalNode ids to known/unknown |
| Caregiver Aware (Cognitive Systems; Wi-Fi motion via smart plugs) | studied in stage 1 (`docs/research/kettle/feature-matrix.md`); no URL recorded there | patterns only | "Rise and Shine" check naming |
| WellNest (Devpost) | https://devpost.com/software/wellnest-rplons | — | Prior hackathon project (simulated events, no accuracy); cited as prior art |
| Libraries | PyTorch 2.15 (BSD-3), torchaudio (BSD-2), transformers 5.23 (Apache-2.0), scikit-learn 1.9 (BSD-3), NumPy/SciPy (BSD-3), soundfile/libsndfile (BSD-3/LGPL), PyAV 18.1 (BSD-3; FFmpeg LGPL), FastAPI/Starlette (MIT), uvicorn (BSD-3), matplotlib (PSF-based), Playwright 1.65 (Apache-2.0), Pillow (HPND), nbconvert (BSD-3) | as listed | Pinned in `requirements.txt` / `requirements-dev.txt` |
| Dataviz validator | `validate_palette.js` from Claude Code's bundled dataviz skill | — | Used to validate the activity colours; reference palette hues adopted |
| AudioSet ontology label names | via `models/audioset_labels.json` (from the AST config, same 527-label order) | CC BY 4.0 (Google) | Evidence names and zero-shot maps |

## Added in the improvement round (Sat Nov 14, 2026, evening)

| Source | Use | Licence | Notes |
| --- | --- | --- | --- |
| [ESC-50](https://github.com/karolpiczak/ESC-50) clips 20–35 of 22 categories (352 clips) | Test the 18 named sound types, the privacy veto (8 sensitive categories) and the appliance hold | CC BY-NC 3.0 | `eval/esc50_kinds.py`; audio in `data/clips/esc50_kinds/` (git-ignored); only embeddings + AudioSet scores committed (`results/cache/ced-tiny_esc50kinds.npz`); no overlap with the off-list clips 0–9 |
| AudioSet ontology classes (via CED-tiny's output layer) | Zero-shot sound types, e.g. Boiling, Water tap, Doorbell, Smoke detector | CC BY 4.0 (Google) | Index lists in `eval/beyond.py` KINDS |
| [free-spoken-digit-dataset](https://github.com/Jakobovski/free-spoken-digit-dataset) (Jackson, Nicolas, Theo recordings) | Close-voice test clips for the on-device voices rule (`web/test/sound_check.cjs`, `results/sound_check_web.json` round 2) | CC BY-SA 4.0 | Accessed 2026-11-15; downloaded to a scratch folder, never committed |
| [Kitchen20](https://github.com/marc-moreaux/kitchen20) (Moreaux et al. 2019), re-embedded Nov 15 on a second machine | Named-sound positives (`eval/sounds.py`), judge training/dev (`eval/judge.py`), stitched confetti check (`eval/confetti.py`) | see the dataset's README | Accessed 2026-11-15; `data/raw/kitchen20` and its embeddings git-ignored |
| [TUT Sound Events 2016, development, "home"](https://zenodo.org/records/45759) (Mesaros, Heittola, Virtanen 2016) | Real-home test, scored once (`eval/real_homes.py` → `results/real_homes.json`): 10 recordings in real homes, events labelled by the dataset authors | Zenodo licence "other-nc" (non-commercial research use) | Accessed 2026-11-15; audio in `data/raw/tut2016`, git-ignored; only per-window labels and times are committed |
