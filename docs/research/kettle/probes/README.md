# Kettle stage-2 probes (Sat Nov 14, 2026, 09:31–10:00 CT)

Each probe answers one question with a number. Scripts are research tools, not product code; stage 3 rebuilds the product modules from `docs/PRD.md` §10. They need the git-ignored probe venv (`.venv-probe/`) and write audio only into `data/raw/` (git-ignored).

| # | Question | Answer (short) | Report | Script / raw |
| --- | --- | --- | --- | --- |
| 1 | Can we get SINS clips without 46 GB? | Yes: one HTTP range read per clip; Zenodo caps at 133 req/min → 1.97 clips/s (6k ≈ 51 min, 12k ≈ 101 min); eval labels public (Zenodo 1964758); folds session-disjoint | `01-data-access.txt` | `probe_data.py`, `data_dev.json`, `data_eval.json` |
| 2 | Which encoder? | CED-tiny: 81.6 quick linear-probe macro F1 (AST 75.8, CLAP 80.2, CED-small 81.1; test N=155), 0.014 s/window CPU vs AST 0.52 s | `02-encoders.txt` | `probe_encoders.py`, `probe_score.py`, `encoders_timing.jsonl`, `scores_probe_dev.json` |
| 3 | What does Apple's built-in classifier get? | 40.0 macro F1 zero-shot with a map frozen before scoring; no TV class; cooking/washing up heard as doors | `03-apple-baseline.txt` | `apple_classify.swift`, `maps/apple_map.json` |
| 4 | Live latency? | 24–35 ms inference; onset→label 2.6 s (loud onset) / 7.6 s (activity change) at 10-s windows, hop 2 s; Chromium on localhost is a secure context | `04-live-latency.txt` | `probe_live_server.py`, `probe_live_drive.py`, `live_*.json` |
| 5 | Can we prove nothing is saved, without sudo? | Yes on the probe server: audit hook + lsof + file snapshot + magic bytes, 0 audio writes | `05-nothing-saved.txt` | `probe_live_drive.py` |
| 6 | Own-kitchen domain shift | Planned for the team (no unattended recording) | `06-own-kitchen-plan.txt` | — |

Frozen zero-shot maps (written before any score was computed): `maps/apple_map.json`, `maps/audioset_map.json`, `maps/clap_prompts.json`.
