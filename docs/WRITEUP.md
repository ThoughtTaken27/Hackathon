# Kettle
**Know the day went okay, without a camera.**

**Track:** AI + Health · **Live demo:** [kettle.parth-dev.workers.dev](https://kettle.parth-dev.workers.dev) · **Code:** [github.com/ThoughtTaken27/Hackathon](https://github.com/ThoughtTaken27/Hackathon) · **Video:** VIDEO_LINK · **One-page PDF:** [`docs/WRITEUP.pdf`](WRITEUP.pdf)

**Kettle helps an adult child who lives far from a parent with early memory loss** by turning the sounds of the parent's kitchen into a private, glanceable timeline of the day. The audio never leaves the room.

_This project is a prototype and is not medical advice._

| **84.1** | **83%** | **0 / 0** | **0** |
|---|---|---|---|
| macro F1 on a held-out real-home test (Apple: 31.8) | of kitchen activity caught; 0.3% false alarms | false urgent alerts: 12.3 h of home audio, 360 look-alikes | audio files saved or sent in a privacy check of the app |

## 1. The problem
About 28% of US adults 65+ who live in the community live alone ([ACL, 2023](https://acl.gov/news-and-events/announcements/acl-releases-2023-profile-older-americans)). **Meera, 34,** lives 300 miles from her dad **Ravi, 79,** who has early memory loss and lives alone. At 10 AM she wonders: did Dad get up and make breakfast? Calling every morning feels like checking up on him. A camera feels like being watched. None of the nine sensor kits we looked at publishes its miss or false-alarm rate.

## 2. What we built
- **In:** sound from a spare phone or laptop on Ravi's counter.
- **On device:** every 10 s it names the sound: cooking, washing up, eating, talking/TV, quiet. No audio is saved or sent.
- **Out:** Meera's phone shows a day bar and her checks: "kitchen activity by 10 AM: met at 8:05."
- **Urgent:** a smoke alarm, or a crash then a cry or 2 min of stillness, turns her screen red.
- **Consent:** Ravi agrees first, sees what Meera sees, can pause.

**A normal day vs. an off day.** Tuesday: cooking 7:40 to 8:00, washing up at 8:05, TV 9 to 11. Meera glances on the bus and doesn't call. Thursday: quiet until 10:30, morning check "not yet." Now the 10:45 call has a reason. **Why not a chatbot?** It can't listen all day, and we never send it audio.

## 3. What we added
Our own user (a parent living alone, the kitchen as the daily sign of life), our own question (did the morning happen, not "what sound is this"), and our own layers on public data: a kitchen detector, "Some activity" instead of a shrug, consent and pause, and urgent alerts.

## 4. How it works
1. **Hear.** CED-tiny, a 5.5M-parameter audio model pretrained on AudioSet, runs in the browser.
2. **Name.** An activity model trained on 8,920 clips from a real home (SINS).
3. **Catch the kitchen.** A detector reads all 527 sound scores, so a clink of cutlery isn't averaged away.
4. **Decide what to say.** "Some activity" when it can't name what a person is doing; "Not sure" only when it can't place the sound at all.
5. **Alert.** Danger detectors push an alert to the family.

Thresholds were set on development data, never on test sets.

## 5. Results on held-out data
| Test | Kettle | Baseline or before |
|---|--:|--:|
| Naming 9 activities, DCASE 2018 test, 7,791 clips (macro F1) | **84.1** [74.4, 86.7] | Apple 31.8 · always "Quiet" 5.0 |
| Same, each of 7 microphones alone (check across groups) | **79.9 to 85.6** | 4-mic average 85.3 |
| Kitchen activity caught, as the app shows it | **83.1%** [76.5, 90.2] | 81.1% before detector |
| Kitchen activity missed / false alarms | **225 of 1,183** / **21 of 6,608** (0.3%) | 0.1% false before |
| Other homes caught: Kitchen20 / DESED dish + frying | **78% / 88%** | 63% / 85% before |
| Moments labeled "Not sure" | **3.6%** | 16.3% before |
| Urgent caught, 60 runs each: smoke / crash+cry / crash+still / scream | **88% / 73% / 72% / 83%** | |
| False urgent alerts: 12.3 h home audio / 360 look-alikes | **0 / 0** | |

Brackets: 95% intervals from resampling sessions; percentages reweighted to the real activity mix. Every number is in `results/*.json` and reruns in `notebooks/kettle_reproduce.ipynb`.

## 6. Where it fails
- **A real kitchen.** At a teammate's home, cooking with metal pots read as "eating." Rules fixed; that kitchen not re-run.
- **Room and mic.** Through a simulated room and laptop mic it caught only 28% of dish and cooking clips. Mic placement matters.
- **New homes.** All DESED kitchen clips, incl. blenders: 43% caught (measured before the detector). One home taught it.
- **Look-alikes.** Rinsing while cooking reads as washing up; TV talk reads as conversation.
- **Urgent sounds** were synthetic alarms and recorded crashes, not real emergencies.

## 7. What we'd do next
1. **With more time, accuracy in real rooms comes first.** Record real kitchens with permission, train on audio passed through rooms and cheap mics, and test where the device sits. Boosting quiet audio lifted the simulated room from 28% to 68%, but false kitchen labels rose, so it isn't shipped.
2. **Background listening on the parent's own phone.** Today Kettle needs a device left on in one room. A native Android app can listen with the screen off and the phone free for calls; a tiny loudness check would wake the model only for sounds worth naming. We'd measure battery drain before claiming a number.

## 8. Sources and AI tools
**Datasets** (all public; audio git-ignored, only embeddings and labels committed):

- [SINS / DCASE 2018 Task 5](https://doi.org/10.5281/zenodo.1247102) dev set (CC BY-NC 4.0): trains the activity head; [eval audio](https://zenodo.org/records/1291760) + [labels](https://zenodo.org/records/1964758) (CC BY-NC-ND 4.0) for one frozen test run; [published results](https://dcase.community/challenge2018/task-monitoring-domestic-activities-results) for comparison.
- [DESED public eval](https://zenodo.org/records/3588172) (CC BY 4.0): real-home kitchen clips, tune half / test half.
- [Kitchen20](https://github.com/marc-moreaux/kitchen20): kitchen sounds for named sounds and the kitchen detector.
- [ESC-50](https://github.com/karolpiczak/ESC-50) (CC BY-NC 3.0): off-list "not sure" test, named sounds, privacy veto, alarm backgrounds.
- [TUT Sound Events 2016 "home"](https://zenodo.org/records/45759), dev + [eval](https://zenodo.org/records/996424) (non-commercial): real-home test, scored once.
- [Nonspeech7k](https://zenodo.org/records/6967442) test split (CC BY 4.0): cough, scream, cry etc. for urgent-alert tests.
- [free-spoken-digit-dataset](https://github.com/Jakobovski/free-spoken-digit-dataset) (CC BY-SA 4.0): close-voice test clips only.
- [AudioSet](https://research.google.com/audioset/) ontology (CC BY 4.0): the 527 sound tags CED-tiny outputs.
- Our own synthetic smoke/CO/timer alarms (`eval/synth_alarms.py`, NFPA 72 patterns), labels known by construction.

**Models:** [CED-tiny](https://huggingface.co/mispeech/ced-tiny) ([paper](https://arxiv.org/abs/2308.11957), Apache-2.0), pretrained on AudioSet, runs on the device as ONNX. On top of it, our own small trained parts: the activity head (logistic regression on SINS, `models/head.json`), the kitchen detector and second-opinion AudioSet-tag rules (`models/witness.json`) and the named-sound head (`web/public/model/sound_head.json`). Baselines and comparisons only: [CED-small](https://huggingface.co/mispeech/ced-small), [AST](https://huggingface.co/MIT/ast-finetuned-audioset-10-10-0.4593) (BSD-3), [LAION CLAP](https://huggingface.co/laion/clap-htsat-unfused) (Apache-2.0), Apple SoundAnalysis, DCASE 2018 baseline.

**Libraries:** [ONNX Runtime Web](https://github.com/microsoft/onnxruntime), PyTorch, torchaudio, Transformers, scikit-learn, NumPy/SciPy, Cloudflare Workers. Full licence list: [/credits](https://kettle.parth-dev.workers.dev/credits) and `docs/DATA-SOURCES.md`; every table: `docs/WRITEUP-LONG.md`.

**AI tools:** [Claude Code](https://claude.com/claude-code) (Anthropic) wrote most of the code and documents under our direction; Aside (Claude), an AI browser agent, built parts of the web app and ran evaluations; REA for the product teardown. Who wrote what: `docs/AI-USAGE-LOG.md`. Every number comes from our scripts (`results/*.json`, `notebooks/kettle_reproduce.ipynb`). Kettle is not an emergency device and doesn't replace a smoke or CO detector, or 911.
