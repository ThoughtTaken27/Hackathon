# Kettle: know the day went okay, without a camera

**Track:** Health · *Prototype, not medical advice. Kettle is not an emergency device and doesn't replace a smoke or CO detector, or 911.*

**Problem.** About 28% of US adults 65+ living in the community live alone ([ACL, 2023 Profile of Older Americans](https://acl.gov/news-and-events/announcements/acl-releases-2023-profile-older-americans)). Our users are adult children of a parent who lives alone with early memory loss. Calls feel like checking up, cameras like being watched, and none of the nine sensor kits we studied publishes how often it misses or false-alarms.

**What we built.** A spare phone or laptop in the parent's kitchen labels household sound every 10 seconds, on the device. No audio is kept or sent: only labels and times leave the room. The family sees a calm day bar and the checks they set ("kitchen activity by 10 AM: met at 8:05"). **Urgent sounds go red and notify the family's phone at once:** a smoke or CO alarm, a crash then a cry or stillness, screaming, shouting, a gunshot, or the "I need help" button. The parent says yes first, sees what the family sees, and can pause or hide labels. A chatbot can't do this: it can't listen to a kitchen all day, and we never send it the audio.

**How it works.** CED-tiny (AudioSet-pretrained, ONNX in the browser) → a frozen activity head trained on SINS (DCASE 2018 Task 5) → stretch-naming rules → 15 per-sound heads, of which only the 8 that passed precision ≥ 90% are shown → danger detectors + a sequence engine (smoke rhythm, crash → cry, crash → 2 min stillness) → encrypted Web Push to the family. Thresholds were picked on development data; test sets were scored after a written plan.

**Results** (all from `results/*.json`):

| Test | Result | N |
|---|---|---|
| Activities, held-out DCASE 2018 test (macro F1) | **84.1** [74.4, 86.7] | 7,791 clips, 91 sessions |
| Apple's built-in sound classifier, same clips | 31.8 [25.7, 37.9] | same |
| Published DCASE baseline (full set, not directly comparable) | 85.0 / 83.1 | — |
| Kitchen activity caught (the morning check) | 87.8% (1,039 of 1,183); false on 41 of 6,608 | held-out |
| Urgent: smoke alarm during cooking / crash then cry / crash then stillness / screaming | **88.3% / 81.7% / 83.3% / 83.3%** | 60 timelines each |
| False urgent alerts: ordinary home sound / look-alikes (TV dramas, dropped pans, timers, cans, fireworks) | **0 in 12.3 h / 0 in 360** | held-out |
| Live browser test: smoke alarm → room screen red → family page red | 19.9 s, then 2.8 s | 1 run |

**Where it fails.**

- **Homes it never heard:** in real homes (TUT-SED 2016) it named washing-up windows as kitchen activity only 52.7% of the time and said "Not sure" 41.8% (N = 55); real-home kitchen clips (DESED) were caught 43.0% (34 of 79), with 0 false kitchen labels in 191. It fails safe (grey, not wrong), but shows a lot of grey.
- **A teammate's real kitchen:** metal pots read as "eating" and plate clatter as "washing up". Naming a stretch from all its windows cut dish clatter called washing up or eating from 6 to 1 of 15 clips.
- **Urgent sounds are not from real homes:** smoke alarms are synthetic tones mixed into recorded everyday sound, crashes are breaking glass, and we had no gunshot or shouting recordings, so those two have no measured catch rate. A crash then someone quietly leaving looks like a fall.

**Privacy and limits.** A privacy check of the real app found 0 audio files written and 0 outside connections (`results/privacy_check.json`). Kettle reports activity, not intent or health. Prototype, not medical advice.

**Credits and AI tools.** Datasets: SINS/DCASE 2018 Task 5, ESC-50, Nonspeech7k, DESED, Kitchen20, TUT-SED 2016. Model: CED-tiny. Full list with licences: `/credits`. AI tools: Claude Code and Aside (both Claude, Anthropic), for code, evaluation scripts and drafting; every number comes from our scripts. Method, every pre-registration and all tables: [`docs/TECHNICAL.md`](TECHNICAL.md).
