# Kettle: know the day went okay, without a camera

**Track:** AI + Health · **Try it:** [kettle.parth-dev.workers.dev](https://kettle.parth-dev.workers.dev) · **Code:** [github.com/ThoughtTaken27/Hackathon](https://github.com/ThoughtTaken27/Hackathon) · **Video:** VIDEO_LINK

_This project is a prototype and is not medical advice._

## The problem
About 28% of US adults 65+ who live in the community live alone ([ACL, 2023](https://acl.gov/news-and-events/announcements/acl-releases-2023-profile-older-americans)). **Our user:** Meera, 34, lives 300 miles from her dad Ravi, 79, who has early memory loss and lives alone. At 10 AM she wonders: did Dad get up and make breakfast? Calling every morning feels like checking up on him. A camera feels like being watched. None of the nine sensor kits we looked at publishes how often it misses or false-alarms.

## What we built
A spare phone or laptop sits on Ravi's kitchen counter and listens. Every 10 seconds it names what it hears (cooking, washing up, eating, talking or TV, quiet) on the device itself. No audio is saved or sent, only labels and times. Meera's phone shows a calm day bar and the checks she picked: "kitchen activity by 10 AM: met at 8:05." If a smoke alarm goes off, or there's a crash followed by a cry or 2 minutes of stillness, her screen turns red right away. Ravi agrees first, sees exactly what Meera sees, and can pause it any time. A chatbot can't do this job: it can't listen to a kitchen all day, and we never give it the audio.

**A normal day vs. an off day.** Tuesday: cooking 7:40 to 8:00, washing up at 8:05, TV from 9 to 11. Meera glances at it on the bus and doesn't call. Thursday: the bar shows quiet until 10:30 and the morning check says "not yet." Now the 10:45 call has a reason.

## What we added
Our own user and setting (one adult child, one parent living alone, the kitchen as the daily sign of life), our own question (did the morning happen, not "what sound is this"), and our own layers on a public dataset: a kitchen detector over all 527 sound scores, "Some activity" instead of a shrug, consent and pause on the parent's screen, and urgent alerts to the family.

## How it works
CED-tiny, a small audio model pretrained on AudioSet, runs in the browser (ONNX). On top of it: an activity model trained on 8,920 clips from a real home (SINS, DCASE 2018 Task 5); a kitchen detector that reads all 527 sound scores at once, so a clink of cutlery isn't lost in a 10-second average; rules that say "Some activity" when it heard a person but can't name the activity, and "Not sure" only when it can't place the sound at all; and danger detectors that push an alert to the family. Every threshold was chosen on development data. Test sets were scored once.

## Results
| Held-out test | Result |
|---|---|
| Activity naming, DCASE 2018 test, 7,791 clips, 91 sessions (macro F1) | **84.1** [74.4, 86.7] vs always "Quiet" 5.0, Apple's sound classifier 31.8 |
| Same, each of the 7 microphones on its own (a check across groups) | 79.9 to 85.6 |
| Kitchen activity, what the app shows: caught / missed / false alarms | **83.1%** [76.5, 90.2] / 225 of 1,183 / 21 of 6,608 (0.3%) |
| Kitchen20 kitchen clips / DESED dish and frying clips, caught (before the kitchen detector) | **78% / 88%** (63% / 85%) |
| "Not sure" on held-out windows (before the "Some activity" rule) | **3.6%** (16.3%) |
| Urgent alerts on synthetic alarms and recorded crashes in home audio, 60 timelines each: smoke while cooking / crash then cry / crash then stillness / screaming | **88.3% / 73.3% / 71.7% / 83.3%** |
| False urgent alerts: 12.3 h of ordinary home sound / 360 look-alikes (TV, dropped pans, timers) | **0 / 0** |

**Where it fails.** When one of us tested it at home, cooking with metal pots read as "eating." We fixed the rules that caused it but haven't re-run that kitchen yet. The bigger problem: replayed through a simulated room and laptop mic (echo, quieter, background hiss), Kettle catches only 28% of dish and cooking clips, so mic placement matters a lot. On a broader set of real-home kitchen clips (DESED, including blenders) it caught 43% before tonight's changes. Urgent sounds are synthetic alarms and recorded crashes, not real emergencies, and we had no gunshot or shouting recordings to measure. A privacy check of the running app found 0 audio files written and 0 outside connections.

## What we'd do next
1. **Accuracy in real rooms.** Record a few real kitchens with permission (protocol in `docs/REAL-KITCHEN-PROTOCOL.md`), train on audio that has been through rooms and cheap mics, and test where the laptop actually sits. In one quick test, boosting quiet audio raised the simulated room from 28% to 68% of DESED dish and cooking clips, but false kitchen labels went up too, so it isn't shipped yet.
2. **Running in the background on the parent's own phone.** Right now Kettle needs a device left on in one room, with the screen on. A native Android app can keep the mic on with the screen off and the phone free for calls and texts. To save battery, a tiny loudness check would run all the time and wake the model only when there's sound worth naming. We'd measure the drain before claiming a number, and labels would need to stop assuming a kitchen.

## Sources and AI tools
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

**Models:** [CED-tiny](https://huggingface.co/mispeech/ced-tiny) ([paper](https://arxiv.org/abs/2308.11957), Apache-2.0), pretrained on AudioSet, runs on the device as ONNX. On top of it, our own small trained parts: the activity head (logistic regression on SINS, `models/head.json`), the second-opinion AudioSet-tag rules (`models/witness.json`) and the named-sound head (`web/public/model/sound_head.json`). Baselines and comparisons only: [CED-small](https://huggingface.co/mispeech/ced-small), [AST](https://huggingface.co/MIT/ast-finetuned-audioset-10-10-0.4593) (BSD-3), [LAION CLAP](https://huggingface.co/laion/clap-htsat-unfused) (Apache-2.0), Apple SoundAnalysis, DCASE 2018 baseline.

**Libraries:** [ONNX Runtime Web](https://github.com/microsoft/onnxruntime), PyTorch, torchaudio, Transformers, scikit-learn, NumPy/SciPy, Cloudflare Workers. Full licence list: [/credits](https://kettle.parth-dev.workers.dev/credits) and `docs/DATA-SOURCES.md`; every table: `docs/WRITEUP-LONG.md`.

**AI tools:** [Claude Code](https://claude.com/claude-code) (Anthropic) wrote most of the code and documents under our direction; Aside (Claude), an AI browser agent, built parts of the web app and ran evaluations; REA for the product teardown. Who wrote what: `docs/AI-USAGE-LOG.md`. Every number comes from our scripts (`results/*.json`, `notebooks/kettle_reproduce.ipynb`). Kettle is not an emergency device and doesn't replace a smoke or CO detector, or 911.
