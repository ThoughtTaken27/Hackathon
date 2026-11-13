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
