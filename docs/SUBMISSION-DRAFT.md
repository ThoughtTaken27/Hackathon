# Submission draft (every form field, from the real state of the repo)

**Parth presses the button. Nobody else opens or submits the form.** Form: the Airtable link in `docs/BRIEF.md` line 88.
You can resubmit as often as you like before Sun 11:59 PM ET; judges see the latest version (brief p.18). Submit a first version
tonight once the links below work, then resubmit Sunday after the own-kitchen set and the video.

Status of this draft: numbers filled by `python tools/writeup_numbers.py` from `results/metrics.json` (held-out run done Sat 13:15 CT). Own-kitchen and video slots stay open until Sunday.

**Headline to lead with (from results):**
<!-- lead:start -->
On the official DCASE 2018 test set (run once with a frozen model; 1,113 moments × 7 microphones = 7,791 clips from 91 sessions), Kettle scores **84.1** macro F1 (95% CI 74.4–86.7) on one microphone and 85.3 on four: level with the official 2018 baseline (85.0 known / 83.1 unseen microphones, full set) and below the best entry (90.4 / 88.4). A Mac already hears a kettle, but Apple's built-in sound classifier scores 31.8 on the same clips. Our contribution isn't the leaderboard: it's publishing every activity's misses and false alarms, and a "Not sure", consent and pause design built around them.
<!-- lead:end -->

| Form field | What to paste |
|---|---|
| Project name | Kettle |
| Track | AI + Health |
| One-line pitch | A laptop already in a parent's kitchen turns household sounds into a calm day timeline for the adult child far away, keeps no audio and no words, and publishes how often it misses an activity and how often it raises a false alarm. |
| Team details | Every member's name, email and school, typed by Parth (not in this repo: Round 1 is blind) |
| Code link | GitHub repo URL (Parth pushes branch `kettle` and makes the repo public), plus the notebook: `notebooks/kettle_reproduce.ipynb` (opens in Colab from GitHub) |
| Write-up link | The GitHub README, or `docs/WRITEUP.md` exported as a Google Doc set to "anyone with the link can view" |
| Demo video link | Unlisted YouTube, recorded Sunday from `docs/PRD.md` §18 (leave blank on the first submission; it's optional) |
| What we added | Our own question (can one laptop microphone do a sensor kit's job, and how often is it wrong: misses vs false alarms, per activity and per activity session), our own setting (a distant caregiver of a parent with early memory loss, with the parent's consent and pause as product states), and our own data (two teammates' kitchens, recorded and labelled by a teammate who didn't write the code). The dataset (SINS / DCASE 2018 Task 5) is public; nothing in the brief suggested it. |
| Credits | See the "Sources" section of the write-up (datasets, models, libraries, products studied, AI tools: Claude Code, REA, Aside), all linked. |

## Write-up text to paste (one page)
See `docs/WRITEUP.md` (kept in sync; numbers only from `results/`).

## Before pressing submit (brief p.18)
- [ ] Open the repo link and the write-up link in a private window: both open without signing in.
- [ ] The README's first screen shows what Kettle is, how to run it, and the results table.
- [ ] `python smoke_test.py` passes on a fresh clone (README steps).
- [ ] Every teammate's name and email spelled right.
- [ ] No personal names or school in the write-up or video (Round 1 is blind).
