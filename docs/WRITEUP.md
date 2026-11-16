# Kettle
**Track:** Health

**Track:** AI + Health · **Team:** three high school students · **Try it:** [kettle.parth-dev.workers.dev](https://kettle.parth-dev.workers.dev) · **Code:** [github.com/ThoughtTaken27/Hackathon](https://github.com/ThoughtTaken27/Hackathon) · **Video:** VIDEO_LINK

## The problem
About 28% of US adults 65+ who live in the community live alone ([ACL, 2023](https://acl.gov/news-and-events/announcements/acl-releases-2023-profile-older-americans)). Their kids want to know one thing most days: did Dad get up, make breakfast, and is he okay? Calling at 9 AM feels like checking up. A camera feels like being watched. None of the nine sensor kits we looked at publishes how often it misses or false-alarms.

## What we built
A spare phone or laptop sits on the parent's kitchen counter and listens. Every 10 seconds it names what it hears (cooking, washing up, eating, talking or TV, quiet) on the device itself. No audio is saved or sent, only labels and times. On their own phone, the family sees a calm day bar and the checks they picked: "kitchen activity by 10 AM: met at 8:05." If a smoke alarm goes off, or there's a crash followed by a cry or 2 minutes of stillness, the family's screen turns red right away. The parent agrees first, sees exactly what the family sees, and can pause it any time. A chatbot can't do this job. It can't listen to a kitchen all day, and we never give it the audio.

**A normal day vs. an off day.** Tuesday: cooking 7:40 to 8:00, washing up at 8:05, TV from 9 to 11. You glance at it on the bus and don't call. Thursday: the bar shows quiet until 10:30 and the morning check says "not yet." Now the 10:45 call has a reason, and you aren't calling every morning just in case.

## How it works
CED-tiny, a small audio model pretrained on AudioSet, runs in the browser. On top of it: an activity model trained on 8,920 clips from a real home (SINS, DCASE 2018 Task 5); a kitchen detector that reads all 527 sound scores at once, so a clink of cutlery isn't lost in a 10-second average; rules that say "Some activity" when it heard a person but can't name the activity, and "Not sure" only when it can't place the sound at all; and danger detectors that send the family a push alert. Every threshold was chosen on development data. Test sets were scored once.

## Results
| Held-out test | Result |
|---|---|
| Activity naming, DCASE 2018 test, 7,791 clips, 91 sessions (macro F1) | **84.1** [74.4, 86.7] vs Apple's built-in sound classifier 31.8 |
| Kitchen activity, what the app shows (caught / right when it says kitchen / false on other moments) | **83.1%** [76.5, 90.2] / 96.9% / 0.3% |
| Kitchen sounds from other kitchens, Kitchen20 / DESED (before the kitchen detector) | **78% / 88%** (63% / 85%) |
| "Not sure" on held-out windows (before the "Some activity" rule) | **3.6%** (16.3%) |
| Urgent alerts on synthetic alarms and recorded crashes in home audio: smoke while cooking / crash then cry / crash then stillness / screaming, 60 timelines each | **88.3% / 73.3% / 71.7% / 83.3%** |
| False urgent alerts: 12.3 h of ordinary home sound / 360 look-alikes (TV, dropped pans, timers) | **0 / 0** |
| Live browser test: smoke alarm turns the room screen red, then the family's | 19.9 s, then 2.8 s later |

**Where it fails.** When one of us tested it at home, Mom was cooking with metal pots and Kettle said "eating." We fixed the rules that caused it, but haven't re-run that kitchen yet. The bigger problem: when we replay test clips through a simulated room and laptop mic (echo, quieter, background hiss), Kettle catches only 28% of dish and cooking clips. Mic placement matters a lot. Our urgent sounds are synthetic alarms and recorded crashes mixed into home audio, not real emergencies, and we had no gunshot or shouting recordings to measure. A privacy check of the running app found 0 audio files written and 0 outside connections.

## What we'd do next
1. **Accuracy in real rooms.** Record a few real kitchens with permission, train on audio that has been through rooms and cheap mics, and test where the laptop actually sits. In one quick test, boosting quiet audio raised the simulated room from 28% to 68% of DESED dish and cooking clips, but false kitchen labels on other recordings went up too, so it isn't shipped yet.
2. **Running in the background on the parent's own phone.** Right now Kettle needs a device left on in one room, with the screen on. A native Android app can keep the mic on with the screen off and the phone free for calls and texts. To save battery, a tiny loudness check would run all the time and wake the model only when there's sound worth naming. We'd measure the drain before claiming a number. It also needs room-free labels, since a phone in a pocket isn't "in the kitchen."

## Sources and AI tools
Datasets: SINS/DCASE 2018 Task 5, AudioSet (via CED), ESC-50, DESED, Kitchen20, Nonspeech7k, TUT-SED 2016. Model: CED-tiny. Licences and links: [/credits](https://kettle.parth-dev.workers.dev/credits). AI tools: Claude Code and Aside (Claude, Anthropic) for code, evaluation scripts and drafting; every number comes from our scripts (`results/*.json`). Full method: `docs/TECHNICAL.md`.

_Prototype, not medical advice. Kettle is not an emergency device and doesn't replace a smoke or CO detector, or 911._
