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
