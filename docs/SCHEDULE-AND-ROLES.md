# 48-hour schedule and roles

Rule: **one end-to-end flow working by Sat 6 PM CT**, then Sunday is for measuring and storytelling. Times are Central (CT = ET − 1h).

## Roles

The team is max 3 people (official rule). Assign names at kickoff in `docs/DECISIONS.md`.

| Role | Owns | Note |
| --- | --- | --- |
| **Builder** | Pipeline (input → normalize → rules → output) and the app UI | Streamlit or Gradio in Colab / Hugging Face Spaces |
| **Evaluator** | Test set, ground-truth labels, metrics, baseline comparison, fairness table, failure-case gallery | Must not be the author of the code being tested |
| **Storyteller** | Problem research, one-page write-up, 2-minute video, finals slides, credits + AI-tools list | Also helps with UI |

Everyone, regardless of role, must be able to explain every part of the code before submitting.

## Timeline

| When (CT) | Goal | Done when |
| --- | --- | --- |
| Fri 11 PM – 12 AM | Read brief, lock idea + track, split roles (`KICKOFF.md`) | One-sentence problem statement agreed, `DECISIONS.md` written |
| Fri 12 – 2 AM | Repo/Colab skeleton, API calls working, responses cached | Each external API returns real data |
| Fri 2 AM – Sat 9 AM | **Sleep** | |
| Sat 9 AM – 1 PM | Core pipeline v1; Evaluator builds test set in parallel | Typed input → output works for 5 examples |
| Sat 1 – 6 PM | Photo/extra input, UI, safety disclaimers | **Full demo flow works end to end** |
| Sat 6 – 10 PM | First full evaluation run, baseline vs. ours | First metrics table exists |
| Sat night | **Sleep** | |
| Sun 9 AM – 1 PM | Fix worst failure modes, rerun eval; stretch goal only if ahead | Final metrics + fairness table |
| Sun 1 – 5 PM | Write-up, record video, clean README | Video < 2:00, write-up = 1 page |
| Sun 5 – 9 PM | Everyone rehearses explaining every part; final checks; **submit by 9 PM** | Confirmation email received |
| Sun 10:59 PM | Hard close | |

## Check-ins

Short group check-ins (10 minutes): Sat 9 AM, 1 PM, 6 PM, 10 PM; Sun 9 AM, 1 PM, 5 PM. Each person says: done, next, blocked. If the full flow isn't working at Sat 6 PM, cut scope immediately.
