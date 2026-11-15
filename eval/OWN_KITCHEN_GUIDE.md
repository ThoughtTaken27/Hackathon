# Own-kitchen test set: step-by-step guide

This guide is for the Lane A teammate. You record kitchen sounds, write down when each sound happens, and check the file format. You do not write code.

Read the whole guide once before you record anything.

## 1. Why this set exists

Kettle was trained and tested on SINS, a public dataset of sounds from one home and one person, recorded with a different microphone. This set asks a harder question: what happens in a new home, with a new person, using the laptop's own microphone?

We expect Kettle to score worse on this set than on SINS. That is the point. It is the honest worst case, and we will report it as one.

This set is exploratory and small. It has few sessions and few people. Do not treat its numbers as a fairness result for all homes.

## 2. Rules before you start

- **The labeller must not be the person who wrote Kettle's code.** That is Parth. You label. Parth does not.
- **Every person who can be heard signs `eval/own_kitchen/CONSENT.md` first.** Use initials only. Do not write full names anywhere in the repo.
- **No conversation, no phone calls, no identifiable speech.** For the "social_activity" class, read the scripted small-talk card in section 8, with two teammates who have both signed the consent form. If you cannot do that, skip the class and write `skipped` in `eval/own_kitchen/NOTES.md`.
- **Radio or TV is allowed only if no identifiable person is talking about themselves.** If in doubt, skip that session.
- **Do not record anyone who has not agreed.** If someone walks in and does not want to be recorded, pause, and stop the recording until they leave.
- **Audio stays on the recorder's laptop** in `data/private/own_kitchen/`. This folder is git-ignored. Never commit it, upload it, or share it outside the team.
- Only labels and Kettle's predictions go into the repo.

## 3. Equipment and placement

- Use the laptop that will run Kettle. Use its built-in microphone.
- Put the laptop on the kitchen counter, about 1 to 2 metres from the sink and the hob.
- Plug the laptop in.
- Record with any app that saves WAV or M4A files. Examples: QuickTime Player, "New Audio Recording" on a Mac, or Voice Recorder on Windows.
- Save one file per session. Name it so you can find it later, for example `k1-cook-01.m4a`.

## 4. What to record

Use these 9 activity names exactly. They match the left column of `eval/own_kitchen/labels_template.csv` and the rules in Kettle. Spelling and underscores matter.

| Activity name | What it means |
| --- | --- |
| `absence` | Quiet, empty kitchen. Nobody moving. |
| `cooking` | Cooking on the hob, chopping, stirring. |
| `dishwashing` | Washing up at the sink. |
| `eating` | Eating or drinking at the table or counter. |
| `other` | Moving about: walking, opening cupboards, closing a door. |
| `social_activity` | Scripted small talk only (see section 8). |
| `vacuum_cleaner` | Vacuum cleaner running. |
| `watching_tv` | TV or radio on, with no one talking about themselves. |
| `working` | Typing on a laptop. |

Targets:

- 8 activities (skip `social_activity` if you cannot do the script).
- At least 5 sessions for each activity.
- About 1 minute per session.
- At least 2 different days. Ideally 2 different kitchens.

Each session is one continuous stretch of one activity. Do not mix activities inside one session. Start the recorder, do the activity for about a minute, then stop.

Roughly 40 minutes of audio is the goal.

## 5. Labelling

Fill in `eval/own_kitchen/labels.csv` while you record. Use this header, exactly:

```
file,start_s,end_s,activity,session,notes
```

- `file`: the audio file name, for example `k1-cook-01.m4a`.
- `start_s` and `end_s`: seconds from the start of that audio file. Use numbers, not clock times.
- `activity`: one of the 9 names in section 4.
- `session`: a short id, for example `k1-cook-01`.
- `notes`: optional. For example `kettle boiling in background`.

Rules:

- One row for each continuous stretch of one activity.
- After each session, listen back. Fix the start and end times if they are wrong.
- Never change an activity label to match what Kettle predicts. Label what you hear, not what the app says.
- Write down anything odd in `notes`. Odd sounds are useful for the write-up.

## 6. The straddle rule (fixed before scoring)

Kettle looks at 10-second windows of audio. Any window that is not fully inside one labelled row is dropped and not scored.

So leave at least 10 seconds for each row. If a row is shorter than 10 seconds, the whole row is dropped.

This rule is fixed now. It is not changed after scoring.

## 7. Checking and scoring

1. Run the format check from the repo folder:

   ```
   python -m eval.own_kitchen_check
   ```

2. The check only looks at the format. It reports:
   - missing or wrong column names
   - activity names that are not in the list
   - rows that overlap in the same file
   - audio files that are listed but not present
   - rows shorter than 10 seconds

3. Fix what it reports, in plain words. Edit your labels, not the check.
4. When it prints `ready to score`, tell Parth.
5. Parth runs the scoring once, with the frozen model:

   ```
   python -m eval --split own-kitchen
   ```

6. Open `results/metrics.md` and read the own-kitchen numbers.
7. In `eval/own_kitchen/NOTES.md`, write three sentences:
   - What got worse compared with SINS.
   - The most likely cause.
   - One thing you would test next time.

Do not run the scoring yourself more than once. The test is run once.

## 8. Scripted small-talk card

Two consenting teammates read these lines aloud. Keep the lines neutral. Do not use names, places, or personal details.

1. "Did you see the weather forecast for the weekend?"
2. "I think it might rain on Saturday, so we should bring a coat."
3. "This soup needs a little more salt, I think."
4. "Can you pass me that wooden spoon, please?"
5. "The bus was late again this morning."
6. "I heard the new bakery down the road has good bread."

Read them at a normal speaking pace. Pause between lines. Record the session as `social_activity` only while the card is being read.

## 9. What to say to a judge

Say these three things in your own words:

- **How the labels were made.** A teammate who did not write the code listened to each recording and wrote down the start, end and activity by hand. Everyone who could be heard had signed a consent form first.
- **Why the code author did not label.** Parth wrote Kettle's code. If he also labelled the test data, he could shape the labels to fit the model. A different person labels so the test is fair.
- **What was dropped and why.** Any 10-second window that crossed two activities was dropped before scoring, using a rule fixed in advance. Sessions with no consent, or with a conversation, were removed or skipped and written down in `NOTES.md`.

## Scoring the whole timeline (added Sun Nov 15, handover v3.2 §3.4)

```bash
python -m eval.own_kitchen_check                              # format checks on labels.csv
python -m eval.own_kitchen --timeline --session <first>       # development session: look, tune
python -m eval.own_kitchen --timeline --session <second>      # test session: score once, report whatever it says
```

Runs every 5 s window through `kettle/timeline.blocks` with the old rule (before Sun Nov 15) and the new one (rules 2c/2d,
named sounds) and writes `results/own_kitchen_timeline_<session>.json`: right / wrong activity / unnamed kitchen activity per
meal stretch, false meal blocks on the others. Dry-run checked on stitched sample clips (5 of 5 stretches right, both rules).
